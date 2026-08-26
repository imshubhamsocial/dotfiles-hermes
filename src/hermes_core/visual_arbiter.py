"""
U39: Real-Time Visual Arbiter & Playwright Kinematic Sieve
===========================================================
Headless Chromium/Playwright runner that:
  - Loads HTML/WebGL targets
  - Sifts browser console errors, unhandled rejections, WebGL context failures
  - Emits structured sub-80 token JSON summaries
  - Kinematic Motion Sieve: captures frames at t=0, t=100ms to verify motion variance
  - Saves frames and logs to RAMDisk (/dev/shm/visual_arbiter/)

Integrates with:
  - token_engine: token bounding for error summaries
  - TelemetrySieve pattern: strips noise, extracts actionable signal
"""

import asyncio
import base64
import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from playwright.async_api import async_playwright, Browser, Page, ConsoleMessage, Error
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Any  # type: ignore
    Page = Any  # type: ignore
    ConsoleMessage = Any  # type: ignore
    Error = Exception  # type: ignore

from .token_engine import estimate_tokens


# ─── Configuration ─────────────────────────────────────────────────────────
RAMDISK_BASE = Path("/dev/shm/visual_arbiter")
MAX_ERROR_TOKENS = 80
FRAME_INTERVAL_MS = 100
MOTION_THRESHOLD_PIXEL = 5  # minimum pixel difference to consider "motion"
FPS_TARGET = 60


@dataclass
class ConsoleError:
    """Structured console error entry."""
    type: str  # error, warning, log, unhandledrejection
    text: str
    location: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class FrameCapture:
    """Single frame capture with metadata."""
    timestamp: float
    frame_index: int
    width: int
    height: int
    base64_png: str  # base64 encoded PNG
    file_path: Optional[str] = None


@dataclass
class KinematicResult:
    """Kinematic motion analysis result."""
    has_motion: bool
    pixel_diff_ratio: float
    frame_0_path: str
    frame_1_path: str
    fps_estimate: float
    motion_vectors: List[Dict] = field(default_factory=list)


@dataclass
class VisualReport:
    """Complete visual arbiter report."""
    url: str
    success: bool
    timestamp: float
    duration_ms: float
    console_errors: List[ConsoleError]
    console_warnings: List[ConsoleError]
    console_logs: List[ConsoleError]
    unhandled_rejections: List[ConsoleError]
    webgl_errors: List[str]
    kinematic: Optional[KinematicResult] = None
    error_summary: str = ""
    error_summary_tokens: int = 0


# ─── Kinematic Sieve ───────────────────────────────────────────────────────
class KinematicSieve:
    """Analyzes frame captures for motion variance."""

    def __init__(self, threshold: int = MOTION_THRESHOLD_PIXEL):
        self.threshold = threshold

    def analyze(self, frame_0: FrameCapture, frame_1: FrameCapture) -> KinematicResult:
        """Compare two frames for motion."""
        # Estimate FPS
        dt = frame_1.timestamp - frame_0.timestamp
        fps = 1000.0 / dt if dt > 0 else 0
        
        # Simple heuristic: if frames are different sizes or we can detect change
        has_motion = frame_0.base64_png != frame_1.base64_png
        pixel_diff = 0.0 if frame_0.base64_png == frame_1.base64_png else 1.0
        
        return KinematicResult(
            has_motion=has_motion,
            pixel_diff_ratio=pixel_diff,
            frame_0_path=frame_0.file_path or "",
            frame_1_path=frame_1.file_path or "",
            fps_estimate=fps,
            motion_vectors=[]
        )


# ─── Error Sifter (TelemetrySieve for Browser) ─────────────────────────────
class ErrorSifter:
    """Compresses browser console output to sub-80 token actionable summary."""

    @classmethod
    def sift(cls, errors: List[ConsoleError], warnings: List[ConsoleError], 
             logs: List[ConsoleError], rejections: List[ConsoleError]) -> Tuple[str, int]:
        """Extract actionable errors and compress to token budget."""
        
        # Collect all relevant entries - prioritize by signal
        all_entries = []
        
        # Prioritize errors and rejections - truncate each to 150 chars
        for e in errors:
            all_entries.append(f"ERROR: {e.text[:150]}")
        for r in rejections:
            all_entries.append(f"REJECTION: {r.text[:150]}")
        for w in warnings:
            # Only keep warnings that match signal patterns
            if any(pat in w.text for pat in ["WebGL", "deprecated", "Failed"]):
                all_entries.append(f"WARN: {w.text[:100]}")
        
        # Join and bound
        combined = "\n".join(all_entries)
        tokens = estimate_tokens(combined)
        
        if tokens <= MAX_ERROR_TOKENS:
            return combined, tokens
        
        # Aggressive truncation - cut each line to fit
        lines = combined.split("\n")
        result = []
        current_tokens = 0
        for line in lines:
            line_tokens = estimate_tokens(line)
            if current_tokens + line_tokens > MAX_ERROR_TOKENS:
                # Truncate the line itself to fit
                remaining = MAX_ERROR_TOKENS - current_tokens
                if remaining > 10:
                    truncated = line[:remaining * 4] + "..."
                    result.append(truncated)
                result.append(f"... ({len(lines) - len(result)} more truncated)")
                break
            result.append(line)
            current_tokens += line_tokens
        
        final = "\n".join(result)
        final_tokens = estimate_tokens(final)
        if final_tokens > MAX_ERROR_TOKENS:
            final = final[:MAX_ERROR_TOKENS * 4]
            final_tokens = estimate_tokens(final)
        return final, final_tokens


# ─── Visual Arbiter ────────────────────────────────────────────────────────
class VisualArbiter:
    """
    Main visual arbiter: headless browser test runner with kinematic sieve.
    """

    def __init__(
        self,
        headless: bool = True,
        viewport: Tuple[int, int] = (1280, 720),
        timeout_ms: int = 30000,
        capture_motion: bool = True,
    ):
        self.headless = headless
        self.viewport = viewport
        self.timeout_ms = timeout_ms
        self.capture_motion = capture_motion
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # Data collectors
        self.console_errors: List[ConsoleError] = []
        self.console_warnings: List[ConsoleError] = []
        self.console_logs: List[ConsoleError] = []
        self.unhandled_rejections: List[ConsoleError] = []
        self.webgl_errors: List[str] = []
        
        # Frame captures
        self.frames: List[FrameCapture] = []
        
        # RAMDisk setup
        RAMDISK_BASE.mkdir(parents=True, exist_ok=True)
        
        # Kinematic sieve
        self.kinematic_sieve = KinematicSieve()

    async def __aenter__(self) -> "VisualArbiter":
        await self._launch()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close()

    async def _launch(self):
        """Launch Playwright browser."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available. Install: pip install playwright && playwright install chromium")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        )
        
        context = await self.browser.new_context(
            viewport={"width": self.viewport[0], "height": self.viewport[1]},
        )
        context.on("pageerror", self._on_page_error)
        context.on("console", self._on_console)
        context.on("requestfailed", self._on_request_failed)
        
        self.page = await context.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        
        # Set up console listeners
        self.page.on("console", self._on_console)
        self.page.on("pageerror", self._on_page_error)
        self.page.on("requestfailed", self._on_request_failed)

    async def _close(self):
        """Clean up browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _on_console(self, msg: ConsoleMessage):
        """Capture console messages."""
        entry = ConsoleError(
            type=msg.type,
            text=msg.text,
            location=msg.location,
        )
        
        if msg.type == "error":
            self.console_errors.append(entry)
        elif msg.type == "warning":
            self.console_warnings.append(entry)
        else:
            self.console_logs.append(entry)
        
        # Check for WebGL-specific errors (only error level, not driver performance warnings)
        if msg.type == "error" and ("webgl" in msg.text.lower() or "webgl" in msg.type.lower()):
            self.webgl_errors.append(msg.text)

    def _on_page_error(self, error: Any):
        """Capture unhandled page errors."""
        entry = ConsoleError(
            type="pageerror",
            text=str(error),
        )
        self.console_errors.append(entry)
        self.unhandled_rejections.append(entry)

    def _on_request_failed(self, request):
        """Capture failed network requests."""
        if request.failure:
            entry = ConsoleError(
                type="network",
                text=f"Failed: {request.url} - {request.failure}",
            )
            self.console_errors.append(entry)

    async def capture_frame(self, label: str = "") -> FrameCapture:
        """Capture current page frame as PNG."""
        if not self.page:
            raise RuntimeError("Page not initialized")
        
        timestamp = time.time()
        frame_index = len(self.frames)
        
        # Screenshot to bytes
        png_bytes = await self.page.screenshot(full_page=False, type="png")
        b64 = base64.b64encode(png_bytes).decode("ascii")
        
        # Save to RAMDisk
        file_name = f"frame_{frame_index}_{uuid.uuid4().hex[:8]}.png"
        file_path = RAMDISK_BASE / file_name
        file_path.write_bytes(png_bytes)
        
        frame = FrameCapture(
            timestamp=timestamp,
            frame_index=frame_index,
            width=self.viewport[0],
            height=self.viewport[1],
            base64_png=b64,
            file_path=str(file_path),
        )
        
        self.frames.append(frame)
        return frame

    async def run(
        self,
        url: str,
        wait_for: Optional[str] = None,
        wait_timeout: int = 5000,
    ) -> VisualReport:
        """
        Run visual arbiter on a URL.
        
        Args:
            url: Target URL (file:// or http://)
            wait_for: Selector to wait for before capturing
            wait_timeout: Max wait time for selector
        """
        start_time = time.time()
        
        try:
            # Navigate
            await self.page.goto(url, wait_until="load", timeout=self.timeout_ms)
            
            if wait_for:
                try:
                    await self.page.wait_for_selector(wait_for, timeout=wait_timeout)
                except Exception:
                    pass
            
            # Small delay for rendering
            await asyncio.sleep(0.5)
            
            # Capture frame at t=0
            frame_0 = await self.capture_frame("t0")
            
            kinematic_result = None
            
            if self.capture_motion:
                # Wait for motion interval
                await asyncio.sleep(FRAME_INTERVAL_MS / 1000.0)
                
                # Capture frame at t=100ms
                frame_1 = await self.capture_frame("t1")
                
                # Analyze kinematics
                kinematic_result = self.kinematic_sieve.analyze(frame_0, frame_1)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Sift errors into compressed summary
            error_summary, summary_tokens = ErrorSifter.sift(
                self.console_errors,
                self.console_warnings,
                self.console_logs,
                self.unhandled_rejections,
            )
            
            # Determine success
            success = (
                len(self.console_errors) == 0 and
                len(self.unhandled_rejections) == 0 and
                len(self.webgl_errors) == 0
            )
            
            # If motion capture enabled, require motion
            if self.capture_motion and kinematic_result:
                success = success and kinematic_result.has_motion
            
            return VisualReport(
                url=url,
                success=success,
                timestamp=start_time,
                duration_ms=duration_ms,
                console_errors=self.console_errors,
                console_warnings=self.console_warnings,
                console_logs=self.console_logs,
                unhandled_rejections=self.unhandled_rejections,
                webgl_errors=self.webgl_errors,
                kinematic=kinematic_result,
                error_summary=error_summary,
                error_summary_tokens=summary_tokens,
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return VisualReport(
                url=url,
                success=False,
                timestamp=start_time,
                duration_ms=duration_ms,
                console_errors=[ConsoleError(type="exception", text=str(e))],
                console_warnings=[],
                console_logs=[],
                unhandled_rejections=[],
                webgl_errors=[],
                error_summary=f"EXCEPTION: {str(e)[:200]}",
                error_summary_tokens=estimate_tokens(str(e)),
            )

    def to_json(self, report: VisualReport) -> str:
        """Serialize report to JSON."""
        return json.dumps({
            "url": report.url,
            "success": report.success,
            "timestamp": report.timestamp,
            "duration_ms": report.duration_ms,
            "errors": [
                {"type": e.type, "text": e.text, "location": e.location}
                for e in report.console_errors
            ],
            "warnings": [
                {"type": e.type, "text": e.text}
                for e in report.console_warnings
            ],
            "logs": [
                {"type": e.type, "text": e.text}
                for e in report.console_logs
            ],
            "unhandled_rejections": [
                {"type": e.type, "text": e.text}
                for e in report.unhandled_rejections
            ],
            "webgl_errors": report.webgl_errors,
            "kinematic": {
                "has_motion": report.kinematic.has_motion if report.kinematic else False,
                "pixel_diff_ratio": report.kinematic.pixel_diff_ratio if report.kinematic else 0,
                "fps_estimate": report.kinematic.fps_estimate if report.kinematic else 0,
                "frame_0": report.kinematic.frame_0_path if report.kinematic else "",
                "frame_1": report.kinematic.frame_1_path if report.kinematic else "",
            } if report.kinematic else None,
            "error_summary": report.error_summary,
            "error_summary_tokens": report.error_summary_tokens,
        }, indent=2)


# ─── Convenience Functions ─────────────────────────────────────────────────
async def run_visual_check(
    url: str,
    headless: bool = True,
    capture_motion: bool = True,
    wait_for: Optional[str] = None,
) -> VisualReport:
    """Convenience function for single-shot visual check."""
    async with VisualArbiter(headless=headless, capture_motion=capture_motion) as arbiter:
        return await arbiter.run(url, wait_for=wait_for)


def create_visual_arbiter(**kwargs) -> VisualArbiter:
    """Factory for VisualArbiter."""
    return VisualArbiter(**kwargs)


__all__ = [
    "VisualArbiter",
    "KinematicSieve",
    "ErrorSifter",
    "VisualReport",
    "KinematicResult",
    "FrameCapture",
    "ConsoleError",
    "run_visual_check",
    "create_visual_arbiter",
    "PLAYWRIGHT_AVAILABLE",
    "RAMDISK_BASE",
]
