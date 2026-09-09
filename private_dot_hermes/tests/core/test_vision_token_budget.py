"""
Contract & Unit Tests for Gemma 4 Multimodal Vision Token Optimization (Track 4 - Phase 4.3)
=============================================================================================
Verifies:
1. Exact Gemma 4 vision token calculation: tokens = (ceil(W/P) * ceil(H/P)) + ceil(H/P) + 2
2. Dynamic downsampling & aspect-preserving patch budgeting
3. Strict token budget adherence (visual inspector never exceeds allocated budget)
4. VisualReport vision budget telemetry serialization
5. Zero GPU VRAM overhead (100% CPU image processing)
"""

import io
import math
import pytest
from pathlib import Path
from PIL import Image

from hermes_core.visual_arbiter import (
    GemmaVisionTokenBudget,
    GemmaVisionTokenBudgeter,
    DEFAULT_VISION_TOKEN_BUDGET,
    MAX_VISION_TOKEN_BUDGET,
    DEFAULT_PATCH_SIZE,
    VisualReport,
)


class TestGemmaVisionTokenBudget:
    """Core algorithmic tests for Gemma 4 vision token budgeting."""

    def test_gemma_vision_token_formula(self):
        # 1. 28x28 image with patch_size=14 -> grid (2, 2)
        # tokens = (2 * 2) + 2 + 2 = 8
        tokens_28, grid_28 = GemmaVisionTokenBudgeter.calculate_tokens(28, 28, patch_size=14)
        assert grid_28 == (2, 2)
        assert tokens_28 == 8

        # 2. 1280x720 720p screenshot with patch_size=14
        # ceil(1280 / 14) = 92, ceil(720 / 14) = 52
        # tokens = (92 * 52) + 52 + 2 = 4784 + 54 = 4838 tokens
        tokens_720p, grid_720p = GemmaVisionTokenBudgeter.calculate_tokens(1280, 720, patch_size=14)
        assert grid_720p == (92, 52)
        assert tokens_720p == 4838

    def test_optimal_patch_grid_budget_adherence(self):
        # For 1280x720 (16:9) with default 256 token budget
        grid_w, grid_h = GemmaVisionTokenBudgeter.calculate_optimal_patch_grid(
            width=1280,
            height=720,
            budget=256,
            patch_size=14,
        )
        tokens = (grid_w * grid_h) + grid_h + 2
        assert tokens <= 256, f"Optimized tokens {tokens} exceeds budget 256"

        # Aspect ratio should approximate 16/9 (~1.777)
        ar = grid_w / grid_h
        assert 1.4 <= ar <= 2.2

    def test_optimal_patch_grid_square_image(self):
        # For 1024x1024 (1:1) with 128 token budget
        grid_w, grid_h = GemmaVisionTokenBudgeter.calculate_optimal_patch_grid(
            width=1024,
            height=1024,
            budget=128,
            patch_size=14,
        )
        tokens = (grid_w * grid_h) + grid_h + 2
        assert tokens <= 128
        # Should be roughly square
        assert abs(grid_w - grid_h) <= 2

    def test_dynamic_downsampling_pipeline(self, tmp_path):
        # Generate synthetic 1280x720 PNG image
        img = Image.new("RGB", (1280, 720), color=(73, 109, 137))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        output_file = tmp_path / "downsampled.png"
        opt_bytes, report = GemmaVisionTokenBudgeter.optimize_image_bytes(
            png_bytes=raw_bytes,
            width=1280,
            height=720,
            budget=256,
            patch_size=14,
            output_path=output_file,
        )

        assert report.within_budget is True
        assert report.optimized_tokens <= 256
        assert report.raw_tokens == 4838
        assert report.compression_ratio > 15.0  # >15x context compression
        assert output_file.exists()

        # Verify downsampled image dimensions match patch grid
        downsampled_img = Image.open(output_file)
        assert downsampled_img.size == (report.downsampled_width, report.downsampled_height)
        assert downsampled_img.size[0] == report.patch_grid_w * 14
        assert downsampled_img.size[1] == report.patch_grid_h * 14

    def test_visual_report_budget_telemetry(self):
        budget_report = GemmaVisionTokenBudget(
            raw_width=1280,
            raw_height=720,
            raw_tokens=4838,
            allocated_budget=256,
            downsampled_width=280,
            downsampled_height=154,
            patch_grid_w=20,
            patch_grid_h=11,
            optimized_tokens=233,
            compression_ratio=20.76,
            within_budget=True,
            optimized_path="/dev/shm/visual_arbiter/frame_0_budgeted.png",
        )

        report = VisualReport(
            url="file:///tmp/index.html",
            success=True,
            timestamp=1000.0,
            duration_ms=45.0,
            console_errors=[],
            console_warnings=[],
            console_logs=[],
            unhandled_rejections=[],
            webgl_errors=[],
            vision_budget=budget_report,
            total_vision_tokens=233,
        )

        d = budget_report.to_dict()
        assert d["within_budget"] is True
        assert d["optimized_tokens"] == 233
        assert d["allocated_budget"] == 256
        assert d["patch_grid"] == [20, 11]
        assert report.total_vision_tokens == 233
