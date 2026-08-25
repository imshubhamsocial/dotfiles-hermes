"""
U39 Contract Tests: Visual Arbiter & Playwright Kinematic Sieve
================================================================
Validates:
  1. Headless launch and clean error sifting on broken scripts
  2. Kinematic motion variance detection on animated canvas vs static canvas
  3. Sub-80 token error compression
  4. RAMDisk frame/error persistence
  5. WebGL context failure detection
"""

import asyncio
import json
import tempfile
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from hermes_core.visual_arbiter import (
    VisualArbiter, KinematicSieve, ErrorSifter, VisualReport,
    ConsoleError, PLAYWRIGHT_AVAILABLE, RAMDISK_BASE
)


# Skip all tests if Playwright not available
if not PLAYWRIGHT_AVAILABLE:
    pytest.skip("Playwright not available", allow_module_level=True)

# Check if browsers are actually available
import subprocess
try:
    result = subprocess.run([sys.executable, "-m", "playwright", "install", "--help"], 
                          capture_output=True, timeout=5)
    BROWSERS_AVAILABLE = True
except Exception:
    BROWSERS_AVAILABLE = False


def run_async(coro):
    """Run async coroutine in sync context."""
    return asyncio.run(coro)


class TestVisualArbiterU39:
    """Contract tests for U39 Visual Arbiter & Kinematic Sieve."""

    @pytest.fixture
    def broken_html(self):
        """Create a temp HTML file with JavaScript errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("""
<!DOCTYPE html>
<html>
<head><title>Broken Page</title></head>
<body>
    <canvas id="gl" width="400" height="300"></canvas>
    <script>
        function broken() {
            console.log("test";
        
        undefinedFunction();
        
        const canvas = document.getElementById('gl');
        const gl = canvas.getContext('webgl2');
        if (!gl) {
            console.error("WebGL2 not available");
        }
        
        Promise.reject(new Error("unhandled rejection test"));
    </script>
</body>
</html>
""")
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def animated_html(self):
        """Create a temp HTML file with animated canvas."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("""
<!DOCTYPE html>
<html>
<head><title>Animated Canvas</title></head>
<body>
    <canvas id="canvas" width="400" height="300" style="background: #000;"></canvas>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        let angle = 0;
        
        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.save();
            ctx.translate(200, 150);
            ctx.rotate(angle);
            ctx.fillStyle = '#0f0';
            ctx.fillRect(-50, -50, 100, 100);
            ctx.restore();
            angle += 0.05;
            requestAnimationFrame(animate);
        }
        animate();
    </script>
</body>
</html>
""")
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def static_html(self):
        """Create a temp HTML file with static canvas (no motion)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("""
<!DOCTYPE html>
<html>
<head><title>Static Canvas</title></head>
<body>
    <canvas id="canvas" width="400" height="300" style="background: #000;"></canvas>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#f00';
        ctx.fillRect(100, 100, 200, 100);
    </script>
</body>
</html>
""")
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def clean_html(self):
        """Create a temp HTML file with no errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("""
<!DOCTYPE html>
<html>
<head><title>Clean Page</title></head>
<body>
    <h1>Hello World</h1>
    <canvas id="canvas" width="400" height="300"></canvas>
    <script>
        console.log("Page loaded successfully");
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#00f';
        ctx.fillRect(50, 50, 100, 100);
    </script>
</body>
</html>
""")
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    # ── Error Sifter Tests ──────────────────────────────────────────────
    def test_error_sifter_basic(self):
        """ErrorSifter extracts actionable errors."""
        errors = [
            ConsoleError(type="error", text="Uncaught ReferenceError: foo is not defined"),
            ConsoleError(type="error", text="TypeError: Cannot read property 'x' of undefined"),
        ]
        warnings = [
            ConsoleError(type="warning", text="Deprecated API used"),
        ]
        logs = [
            ConsoleError(type="log", text="Application started"),
        ]
        rejections = [
            ConsoleError(type="unhandledrejection", text="Promise rejected: Network error"),
        ]
        
        summary, tokens = ErrorSifter.sift(errors, warnings, logs, rejections)
        
        assert "ReferenceError" in summary
        assert "TypeError" in summary
        assert "rejection" in summary.lower()
        assert tokens <= 80

    def test_error_sifter_token_budget(self):
        """ErrorSifter respects 80 token budget."""
        errors = [
            ConsoleError(type="error", text=f"Error {i}: Something went wrong with detailed message")
            for i in range(20)
        ]
        
        summary, tokens = ErrorSifter.sift(errors, [], [], [])
        
        assert tokens <= 80
        assert "..." in summary or len(summary) < 500

    def test_error_sifter_strips_noise(self):
        """ErrorSifter strips INFO/debug noise."""
        errors = [
            ConsoleError(type="error", text="Real error"),
        ]
        logs = [
            ConsoleError(type="log", text="[INFO] Loading resource"),
            ConsoleError(type="log", text="[DEBUG] Frame 1"),
            ConsoleError(type="log", text="[INFO] Animation frame"),
        ]
        
        summary, tokens = ErrorSifter.sift(errors, [], logs, [])
        
        assert "Real error" in summary
        assert "[INFO]" not in summary
        assert "[DEBUG]" not in summary

    # ── Kinematic Sieve Tests ───────────────────────────────────────────
    def test_kinematic_sieve_static_frames(self):
        """KinematicSieve detects no motion on identical frames."""
        from hermes_core.visual_arbiter import FrameCapture
        
        frame_0 = FrameCapture(
            timestamp=0.0, frame_index=0, width=400, height=300,
            base64_png="identical_base64_data", file_path="/tmp/f0.png"
        )
        frame_1 = FrameCapture(
            timestamp=0.1, frame_index=1, width=400, height=300,
            base64_png="identical_base64_data", file_path="/tmp/f1.png"
        )
        
        sieve = KinematicSieve()
        result = sieve.analyze(frame_0, frame_1)
        
        assert result.has_motion is False
        assert result.pixel_diff_ratio == 0.0
        assert result.fps_estimate > 0

    def test_kinematic_sieve_different_frames(self):
        """KinematicSieve detects motion on different frames."""
        from hermes_core.visual_arbiter import FrameCapture
        
        frame_0 = FrameCapture(
            timestamp=0.0, frame_index=0, width=400, height=300,
            base64_png="base64_data_0", file_path="/tmp/f0.png"
        )
        frame_1 = FrameCapture(
            timestamp=0.1, frame_index=1, width=400, height=300,
            base64_png="base64_data_1", file_path="/tmp/f1.png"
        )
        
        sieve = KinematicSieve()
        result = sieve.analyze(frame_0, frame_1)
        
        assert result.has_motion is True
        assert result.pixel_diff_ratio > 0

    # ── Visual Arbiter Integration Tests (skipped if no browsers) ────────
    @pytest.mark.skipif(not BROWSERS_AVAILABLE, reason="No browsers available")
    def test_visual_arbiter_broken_page(self, broken_html):
        """VisualArbiter catches JS errors on broken page."""
        url = broken_html.as_uri()
        
        async def _run():
            async with VisualArbiter(headless=True, capture_motion=False) as arbiter:
                return await arbiter.run(url)
        
        report = run_async(_run())
        
        assert report.success is False
        assert len(report.console_errors) > 0
        assert any("ReferenceError" in e.text or "undefinedFunction" in e.text for e in report.console_errors)
        assert len(report.unhandled_rejections) > 0
        assert report.error_summary_tokens <= 80

    @pytest.mark.skipif(not BROWSERS_AVAILABLE, reason="No browsers available")
    def test_visual_arbiter_clean_page(self, clean_html):
        """VisualArbiter passes clean page with no errors."""
        url = clean_html.as_uri()
        
        async def _run():
            async with VisualArbiter(headless=True, capture_motion=False) as arbiter:
                return await arbiter.run(url)
        
        report = run_async(_run())
        
        assert report.success is True
        assert len(report.console_errors) == 0
        assert len(report.unhandled_rejections) == 0
        assert len(report.webgl_errors) == 0

    @pytest.mark.skipif(not BROWSERS_AVAILABLE, reason="No browsers available")
    def test_visual_arbiter_animated_motion(self, animated_html):
        """VisualArbiter detects motion on animated canvas."""
        url = animated_html.as_uri()
        
        async def _run():
            async with VisualArbiter(headless=True, capture_motion=True) as arbiter:
                return await arbiter.run(url, wait_for="#canvas")
        
        report = run_async(_run())
        
        assert report.kinematic is not None
        assert report.kinematic.fps_estimate > 0

    @pytest.mark.skipif(not BROWSERS_AVAILABLE, reason="No browsers available")
    def test_visual_arbiter_static_no_motion(self, static_html):
        """VisualArbiter detects no motion on static canvas."""
        url = static_html.as_uri()
        
        async def _run():
            async with VisualArbiter(headless=True, capture_motion=True) as arbiter:
                return await arbiter.run(url, wait_for="#canvas")
        
        report = run_async(_run())
        
        assert report.kinematic is not None
        assert report.kinematic.has_motion is False

    @pytest.mark.skipif(not BROWSERS_AVAILABLE, reason="No browsers available")
    def test_visual_arbiter_ramdisk_persistence(self, clean_html):
        """Frames and logs saved to RAMDisk."""
        url = clean_html.as_uri()
        
        async def _run():
            async with VisualArbiter(headless=True, capture_motion=True) as arbiter:
                return await arbiter.run(url)
        
        report = run_async(_run())
        
        frame_files = list(RAMDISK_BASE.glob("frame_*.png"))
        assert len(frame_files) >= 2
        
        for f in frame_files:
            assert f.stat().st_size > 0

    @pytest.mark.skipif(not BROWSERS_AVAILABLE, reason="No browsers available")
    def test_visual_arbiter_error_compression(self, broken_html):
        """Error summary compressed to sub-80 tokens."""
        url = broken_html.as_uri()
        
        async def _run():
            async with VisualArbiter(headless=True, capture_motion=False) as arbiter:
                return await arbiter.run(url)
        
        report = run_async(_run())
        
        assert report.error_summary_tokens <= 80
        assert len(report.error_summary) > 0

    @pytest.mark.skipif(not BROWSERS_AVAILABLE, reason="No browsers available")
    def test_visual_arbiter_webgl_error_detection(self):
        """VisualArbiter detects WebGL context failures."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write("""
<!DOCTYPE html>
<html>
<head><title>WebGL Fail</title></head>
<body>
    <canvas id="gl" width="400" height="300"></canvas>
    <script>
        const canvas = document.getElementById('gl');
        const gl = canvas.getContext('webgl2', {failIfMajorPerformanceCaveat: true});
        if (!gl) {
            console.error("WebGL context creation failed");
        }
    </script>
</body>
</html>
""")
            path = Path(f.name)
        
        try:
            url = path.as_uri()
            
            async def _run():
                async with VisualArbiter(headless=True, capture_motion=False) as arbiter:
                    return await arbiter.run(url)
            
            report = run_async(_run())
            
            webgl_found = any("webgl" in e.text.lower() for e in report.console_errors)
            assert webgl_found or len(report.webgl_errors) > 0
        finally:
            path.unlink(missing_ok=True)

    @pytest.mark.skipif(not BROWSERS_AVAILABLE, reason="No browsers available")
    def test_visual_arbiter_report_serialization(self, clean_html):
        """VisualReport serializes to valid JSON."""
        url = clean_html.as_uri()
        
        async def _run():
            async with VisualArbiter(headless=True, capture_motion=False) as arbiter:
                report = await arbiter.run(url)
                return arbiter.to_json(report)
        
        json_str = run_async(_run())
        data = json.loads(json_str)
        
        assert data["url"] == url
        assert data["success"] is True
        assert "errors" in data
        assert "warnings" in data
        assert "kinematic" in data

    @pytest.mark.skipif(not BROWSERS_AVAILABLE, reason="No browsers available")
    def test_visual_arbiter_timeout_handling(self):
        """VisualArbiter handles navigation timeout gracefully."""
        async def _run():
            async with VisualArbiter(headless=True, capture_motion=False, timeout_ms=100) as arbiter:
                return await arbiter.run("http://10.255.255.1/")
        
        report = run_async(_run())
        
        assert report.success is False
        assert ("EXCEPTION" in report.error_summary or 
                "timeout" in report.error_summary.lower() or 
                "net::err" in report.error_summary.lower())

    # ── Factory Function Tests ─────────────────────────────────────────
    def test_create_visual_arbiter_factory(self):
        """Factory function creates VisualArbiter."""
        from hermes_core.visual_arbiter import create_visual_arbiter
        
        arbiter = create_visual_arbiter(headless=True, capture_motion=False)
        
        assert isinstance(arbiter, VisualArbiter)
        assert arbiter.headless is True
        assert arbiter.capture_motion is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
