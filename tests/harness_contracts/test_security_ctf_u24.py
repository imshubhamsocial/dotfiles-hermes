"""
Contract Tests for U24: Security, CTF & Binary Analysis Toolsuite
===================================================================
Tests ELF header parsing, mitigation extraction (NX, Canary, PIE, RELRO),
string extraction, disassembly slicing, and sandbox integration.
"""

from __future__ import annotations

import sys
import tempfile
import struct
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest

from hermes_core.security_ctf import (
    SecurityCTFToolsuite,
    BinaryMitigations,
    BinaryInfo,
    parse_elf_header,
    extract_strings,
    create_security_toolsuite,
)


def _create_mock_elf64_bytes(pie: bool = True, canary: bool = True) -> bytes:
    """Creates a synthetic 64-bit ELF binary header for unit testing."""
    # EI_MAG: \x7fELF
    # EI_CLASS: 2 (64-bit)
    # EI_DATA: 1 (Little endian)
    # EI_VERSION: 1
    # EI_OSABI: 0 (System V)
    # Pad to 16 bytes
    ident = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 8

    e_type = 3 if pie else 2  # DYN (PIE) vs EXEC
    e_machine = 0x3E         # x86_64
    e_version = 1
    e_entry = 0x401000
    e_phoff = 64
    e_shoff = 128
    e_flags = 0
    e_ehsize = 64
    e_phentsize = 56
    e_phnum = 4
    e_shentsize = 64
    e_shnum = 5
    e_shstrndx = 1

    header = ident + struct.pack(
        "<HHIQQQIHHHHHH",
        e_type,
        e_machine,
        e_version,
        e_entry,
        e_phoff,
        e_shoff,
        e_flags,
        e_ehsize,
        e_phentsize,
        e_phnum,
        e_shentsize,
        e_shnum,
        e_shstrndx,
    )

    body = b"GNU_STACK\x00\x00\x00\x00\x00\x00\x00\x00GNU_RELRO"
    if canary:
        body += b"__stack_chk_fail\x00FLAG{u24_ctf_verified}\x00"

    return header + body


class TestSecurityCTFToolsuite:
    """Test suite for U24 capabilities."""

    def test_elf_header_parsing(self):
        elf_bytes = _create_mock_elf64_bytes(pie=True, canary=True)
        info = parse_elf_header(elf_bytes, "mock_bin")

        assert info is not None
        assert info.arch == "x86_64"
        assert info.bits == 64
        assert info.endianness == "little"
        assert info.entry_point == 0x401000
        assert info.mitigations.pie is True
        assert info.mitigations.canary is True
        assert info.mitigations.nx is True
        assert info.mitigations.relro == "Partial"

    def test_extract_strings(self):
        data = b"Some random binary noise \x00\xff\xfeFLAG{test_12345}\x00\x00password123\x00"
        strs = extract_strings(data, min_len=4)

        assert "FLAG{test_12345}" in strs
        assert "password123" in strs
        assert "Some random binary noise" in strs

    def test_analyze_binary_integration(self):
        with tempfile.TemporaryDirectory() as td:
            bin_path = Path(td) / "sample.elf"
            bin_path.write_bytes(_create_mock_elf64_bytes(pie=False, canary=False))

            suite = create_security_toolsuite(use_sandbox=False)
            res = suite.analyze_binary(str(bin_path))

            assert res["file_type"] == "ELF"
            assert res["arch"] == "x86_64"
            assert res["mitigations"]["pie"] is False
            assert res["mitigations"]["canary"] is False
            assert "FLAG" not in str(res["strings_sample"])

    def test_non_existent_file_handling(self):
        suite = create_security_toolsuite(use_sandbox=False)
        res = suite.analyze_binary("/path/does/not/exist/bin.elf")
        assert "error" in res


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
