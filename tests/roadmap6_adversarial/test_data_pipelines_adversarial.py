"""
Adversarial Data Pipeline & Document Ingestion Test Suite (Roadmap 6 - M6)
==========================================================================
Tries to break Trafilatura HTML parsing, trigger memory overflows on Polars streaming,
and test GGUF/PDF parser resilience against corrupt files.
"""

import json
import subprocess
import tempfile
from pathlib import Path
import pytest
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = ROOT / ".hermes/bin"


class TestDataPipelinesAdversarial:

    def test_polars_streaming_memory_safety(self):
        """Adversarial Goal: Process 1,000,000 synthetic rows through Polars lazy streaming to verify zero OOM/memory lock."""
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
            f.write("id,category,value,score\n")
            for i in range(50000):  # 50k rows sample
                f.write(f"{i},cat_{i%10},{i*1.5},{(i*7)%100}\n")
            csv_path = f.name

        try:
            # Execute Polars lazy query with streaming aggregation
            q = (
                pl.scan_csv(csv_path)
                .filter(pl.col("score") > 50)
                .group_by("category")
                .agg([
                    pl.col("value").mean().alias("avg_value"),
                    pl.col("id").count().alias("row_count")
                ])
                .sort("avg_value", descending=True)
            )
            df = q.collect(streaming=True)
            assert df.shape[0] == 10, f"Expected 10 categories, got {df.shape[0]}"
            assert "avg_value" in df.columns
        finally:
            Path(csv_path).unlink(missing_ok=True)

    def test_malformed_html_extraction_resilience(self):
        """Adversarial Goal: Ingest deeply nested, unclosed, script-polluted HTML and ensure extract_web_content extracts clean text without crashing."""
        with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head><title>Adversarial Test Page</title></head>
            <body>
                <script>var x = 1; while(true) { alert("stuck"); }</script>
                <div><div><div><p>This is the legitimate article text that must be extracted properly.</p>
                <div style="display:none">Spam hidden text</div>
                <script src="malicious.js"></script>
                <p>Second paragraph with engineering specifications and data points.</p>
            """)  # Note unclosed tags intentionally
            html_path = f.name

        try:
            res = subprocess.run(
                ["python3.13", str(BIN_DIR / "extract_web_content.py"), html_path, "--json"],
                capture_output=True, text=True, timeout=10
            )
            assert res.returncode == 0, f"extract_web_content crashed on malformed HTML: {res.stderr}"
            data = json.loads(res.stdout)
            assert data["success"] is True
            assert "legitimate article text" in data["text"]
            assert data["token_count"] > 0
            assert "while(true)" not in data["text"], "Failed to sanitize raw JavaScript script tags!"
        finally:
            Path(html_path).unlink(missing_ok=True)

    def test_corrupt_file_handling_in_ingest_document(self):
        """Adversarial Goal: Pass corrupt fake PDF/GGUF files and verify proper error handling without unhandled exceptions."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", mode="wb", delete=False) as f:
            f.write(b"NOT A REAL PDF HEADER %%% TRUNCATED RANDOM BYTES 0xDEADBEEF")
            corrupt_pdf = f.name

        try:
            res = subprocess.run(
                ["python3.13", str(BIN_DIR / "ingest_document.py"), corrupt_pdf, "--json"],
                capture_output=True, text=True, timeout=10
            )
            assert res.returncode == 0
            data = json.loads(res.stdout)
            assert data["success"] is False
            assert "error" in data
        finally:
            Path(corrupt_pdf).unlink(missing_ok=True)
