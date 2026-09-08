"""
FastMCP In-Memory Transport & Lifecycle Benchmark Suite (Issue #29)
===================================================================
Benchmarks in-memory MCP tool registration, schema extraction, and sub-1ms dispatch latency.
"""

import time
import pytest
from hermes_core.fastmcp import HermesFastMCPManager, ToolCallResult
from hermes_core.vfs import HermesMemoryFS
from hermes_core.schema_anchors import InstructorSchemaEngine
from hermes_core.qwen_mm_core import QwenMMCoreReader


def test_fastmcp_in_memory_tool_dispatch_latency():
    """Verify tool calls dispatch in memory with sub-1ms latency."""
    manager = HermesFastMCPManager(name="BenchManager")

    @manager.register_tool(name="calculate_sum", description="Sums two integers")
    def calculate_sum(a: int, b: int) -> int:
        return a + b

    # Warmup
    manager.call_tool("calculate_sum", {"a": 1, "b": 2})

    # Benchmark 100 iterations
    latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        res = manager.call_tool("calculate_sum", {"a": 10, "b": 20})
        latencies.append((time.perf_counter() - t0) * 1000)
        assert res.success is True
        assert res.data == 30

    avg_latency_ms = sum(latencies) / len(latencies)
    print(f"FastMCP In-Memory Dispatch Latency: {avg_latency_ms:.3f} ms (p95: {sorted(latencies)[95]:.3f} ms)")
    assert avg_latency_ms < 1.0, f"Dispatch latency exceeded 1.0ms SLA: {avg_latency_ms:.3f}ms"


def test_fastmcp_multi_hop_proxying():
    """Verify nested MCP proxy routing (Issue #21)."""
    parent = HermesFastMCPManager("Parent")
    child = HermesFastMCPManager("Child")

    @child.register_tool(name="child_tool")
    def child_tool(msg: str) -> str:
        return f"Echo: {msg}"

    parent.register_proxy_server("child", child)
    res = parent.call_tool("child_tool", {"msg": "hello"})
    assert res.success is True
    assert res.data == "Echo: hello"


def test_hermes_memory_fs():
    """Verify in-memory VFS transport (Issue #13)."""
    vfs = HermesMemoryFS()
    vfs.write_text("/src/main.py", "print('hello')\n")
    assert vfs.exists("/src/main.py")
    assert vfs.read_text("/src/main.py") == "print('hello')\n"
    assert vfs.listdir("/src") == ["main.py"]

    # Snapshot & restore
    snap = vfs.snapshot()
    vfs.remove("/src/main.py")
    assert not vfs.exists("/src/main.py")
    vfs.restore(snap)
    assert vfs.exists("/src/main.py")


def test_instructor_schema_generation():
    """Verify JSON schema generation (Issue #17)."""
    def sample_func(name: str, age: int = 18):
        """A test function."""
        pass

    schema = InstructorSchemaEngine.generate_tool_schema(sample_func)
    assert schema["name"] == "sample_func"
    assert "name" in schema["parameters"]["properties"]


def test_qwen_mm_pillow_downsampling():
    """Verify Pillow base64 validation and image downsampling (Issue #22)."""
    import io
    from PIL import Image
    
    # Create large 2000x2000 image
    img = Image.new("RGB", (2000, 2000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    downsampled = QwenMMCoreReader.downsample_image(raw_bytes, max_dim=512)
    with Image.open(io.BytesIO(downsampled)) as d_img:
        assert d_img.width <= 512
        assert d_img.height <= 512
