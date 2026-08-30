#!/usr/bin/env python3.13
"""
Multi-Modal Local Document Ingestion Engine (Roadmap 6 - Milestone 6c)
====================================================================
Unified document parser for local RAG and offline inspection:
  - PDF: pypdf extraction + page indexing
  - HTML/Web: trafilatura clean text extraction
  - GGUF: gguf metadata, layer, and tensor architecture inspection

Usage:
    python3.13 bin/ingest_document.py <filepath> [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import tiktoken


def ingest_pdf(path: Path) -> dict:
    import pypdf
    reader = pypdf.PdfReader(str(path))
    pages_text = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_text.append({"page": idx + 1, "text": text.strip()})

    full_text = "\n\n".join(p["text"] for p in pages_text)
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = len(enc.encode(full_text))

    return {
        "format": "pdf",
        "path": str(path),
        "page_count": len(reader.pages),
        "total_tokens": tokens,
        "pages": pages_text,
        "text": full_text
    }


def ingest_gguf(path: Path) -> dict:
    import gguf
    reader = gguf.GGUFReader(str(path))
    metadata = {}
    for key, field in reader.fields.items():
        val = field.parts[field.data[0]] if hasattr(field, "parts") and field.data else str(field)
        # Clean scalar/string representation
        if isinstance(val, (bytes, bytearray)):
            try:
                val = val.decode("utf-8")
            except Exception:
                val = f"<binary {len(val)} bytes>"
        elif hasattr(val, "tolist"):
            val = val.tolist()
        metadata[key] = str(val)[:200]

    tensors = [
        {"name": tensor.name, "shape": list(tensor.shape), "type": str(tensor.tensor_type)}
        for tensor in reader.tensors[:20]
    ]

    return {
        "format": "gguf",
        "path": str(path),
        "file_size_bytes": path.stat().st_size,
        "tensor_count": len(reader.tensors),
        "key_metadata": {k: metadata[k] for k in list(metadata.keys())[:15]},
        "sample_tensors": tensors
    }


def ingest_text(path: Path) -> dict:
    import trafilatura
    content = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix in [".html", ".htm"]:
        extracted = trafilatura.extract(content) or content
    else:
        extracted = content

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = len(enc.encode(extracted))
    return {
        "format": path.suffix.lstrip("."),
        "path": str(path),
        "total_tokens": tokens,
        "char_count": len(extracted),
        "text": extracted
    }


def ingest_file(path_str: str) -> dict:
    p = Path(path_str)
    if not p.exists():
        return {"error": f"File not found: {path_str}", "success": False}

    ext = p.suffix.lower()
    try:
        if ext == ".pdf":
            res = ingest_pdf(p)
        elif ext == ".gguf":
            res = ingest_gguf(p)
        else:
            res = ingest_text(p)
        res["success"] = True
        return res
    except Exception as e:
        return {"error": f"Ingestion error on {path_str}: {e}", "success": False}


def main():
    parser = argparse.ArgumentParser(description="Multi-Modal Local Document Ingestion Engine")
    parser.add_argument("path", help="Path to PDF, GGUF, HTML, or TXT file")
    parser.add_argument("--json", action="store_true", help="Output full JSON result")
    args = parser.parse_args()

    result = ingest_file(args.path)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if not result.get("success"):
            print(f"[-] Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)
        print(f"[+] Ingested [{result['format'].upper()}] format: {result['path']}")
        if result["format"] == "pdf":
            print(f"    Pages:  {result['page_count']} | Tokens: {result['total_tokens']}")
            print("-" * 60)
            print(result["text"][:1000] + ("..." if len(result["text"]) > 1000 else ""))
        elif result["format"] == "gguf":
            print(f"    Size:   {result['file_size_bytes'] / (1024*1024):.2f} MiB | Tensors: {result['tensor_count']}")
            print("    Key Metadata:")
            for k, v in result["key_metadata"].items():
                print(f"      - {k}: {v}")
        else:
            print(f"    Tokens: {result['total_tokens']} | Chars: {result['char_count']}")
            print("-" * 60)
            print(result["text"][:1000] + ("..." if len(result["text"]) > 1000 else ""))


if __name__ == "__main__":
    main()
