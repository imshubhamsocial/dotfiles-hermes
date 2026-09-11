"""
Contract & Unit Tests for Multimodal Vision Token Optimization
==============================================================
Verifies:
1. Exact vision token calculation: tokens = (ceil(W/P) * ceil(H/P)) + ceil(H/P) + 2
2. Dynamic downsampling & aspect-preserving patch budgeting
3. Strict token budget adherence (never exceeds allocated budget)
4. Pillow image downsampling directly on CPU with 0 MiB VRAM overhead
"""

import io
import math
import pytest
from pathlib import Path
from PIL import Image


class VisionTokenCalculator:
    """CPU-only image patch budgeting math."""
    DEFAULT_PATCH_SIZE = 14

    @classmethod
    def calculate_tokens(cls, width: int, height: int, patch_size: int = 14) -> tuple[int, tuple[int, int]]:
        gw = math.ceil(width / patch_size)
        gh = math.ceil(height / patch_size)
        tokens = (gw * gh) + gh + 2
        return tokens, (gw, gh)

    @classmethod
    def calculate_optimal_patch_grid(cls, width: int, height: int, budget: int, patch_size: int = 14) -> tuple[int, int]:
        aspect = width / height
        # Find largest gw, gh such that (gw * gh) + gh + 2 <= budget and gw / gh ~= aspect
        best_gw, best_gh = 1, 1
        for gh in range(1, 100):
            gw = max(1, int(round(gh * aspect)))
            tokens = (gw * gh) + gh + 2
            if tokens <= budget:
                best_gw, best_gh = gw, gh
            else:
                break
        return best_gw, best_gh

    @classmethod
    def downsample_image(cls, image_bytes: bytes, budget: int, patch_size: int = 14) -> tuple[bytes, int, tuple[int, int]]:
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        gw, gh = cls.calculate_optimal_patch_grid(w, h, budget, patch_size)
        target_w = gw * patch_size
        target_h = gh * patch_size
        resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        resized.save(out, format="PNG")
        tokens, _ = cls.calculate_tokens(target_w, target_h, patch_size)
        return out.getvalue(), tokens, (target_w, target_h)


class TestGemmaVisionTokenBudget:
    """Core algorithmic tests for vision token budgeting."""

    def test_gemma_vision_token_formula(self):
        tokens_28, grid_28 = VisionTokenCalculator.calculate_tokens(28, 28, patch_size=14)
        assert grid_28 == (2, 2)
        assert tokens_28 == 8

        # 1280x720 720p screenshot with patch_size=14
        tokens_720p, grid_720p = VisionTokenCalculator.calculate_tokens(1280, 720, patch_size=14)
        assert grid_720p == (92, 52)
        assert tokens_720p == 4838

    def test_optimal_patch_grid_budget_adherence(self):
        grid_w, grid_h = VisionTokenCalculator.calculate_optimal_patch_grid(
            width=1280,
            height=720,
            budget=256,
            patch_size=14,
        )
        tokens = (grid_w * grid_h) + grid_h + 2
        assert tokens <= 256, f"Optimized tokens {tokens} exceeds budget 256"
        ar = grid_w / grid_h
        assert 1.4 <= ar <= 2.2

    def test_optimal_patch_grid_square_image(self):
        grid_w, grid_h = VisionTokenCalculator.calculate_optimal_patch_grid(
            width=1024,
            height=1024,
            budget=128,
            patch_size=14,
        )
        tokens = (grid_w * grid_h) + grid_h + 2
        assert tokens <= 128
        assert abs(grid_w - grid_h) <= 2

    def test_dynamic_downsampling_pipeline(self, tmp_path):
        img = Image.new("RGB", (1280, 720), color=(73, 109, 137))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()

        opt_bytes, opt_tokens, dims = VisionTokenCalculator.downsample_image(
            raw_bytes,
            budget=256,
            patch_size=14,
        )

        assert opt_tokens <= 256
        assert len(opt_bytes) > 0
        downsampled_img = Image.open(io.BytesIO(opt_bytes))
        assert downsampled_img.size == dims


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
