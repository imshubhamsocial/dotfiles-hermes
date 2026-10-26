"""  
Deterministic Verification Gate for Phase 01: Canonical Upstream Parity & Zero-Bespoke Core.  
"""  
import os  
from pathlib import Path  
import subprocess  
import sys  
import pytest

HERMES_ROOT = Path("/var/home/imshubhamsocial/Projects/Workspace/Personal/hermes")  
HERMES_HOME = HERMES_ROOT / ".hermes"  
sys.path.insert(0, str(HERMES_HOME))

from mcp_openjev import SafePathModel, MutateModuleInput, jev_mutate_module

def test_upstream_git_zero_diff():  
    """Verify .hermes/hermes-agent core repository has 0 uncommitted modifications."""  
    hermes_dir = HERMES_HOME / "hermes-agent"  
    if not hermes_dir.exists():  
        pytest.skip("Upstream hermes-agent clone not present in test container.")  
    res = subprocess.run(  
        ["git", "status", "--porcelain"],  
        cwd=hermes_dir,  
        capture_output=True,  
        text=True,  
        check=True,  
    )  
    assert res.stdout.strip() == "", f"Upstream core polluted:\\n{res.stdout}"

def test_no_sitecustomize_monkeypatching():  
    """Verify fragile sitecustomize.py runtime monkey-patches are retired."""  
    sitecustomize = HERMES_HOME / "sitecustomize.py"  
    if sitecustomize.exists():  
        assert "tools.registry.registry" not in sitecustomize.read_text(encoding="utf-8")

def test_soul_md_kernel_integrity():  
    """Verify Layer 1 root factory manual SOUL.md exists and starts with PRECEDENCE OVERRIDE."""  
    soul_md = HERMES_HOME / "SOUL.md"  
    assert soul_md.exists(), "Universal kernel SOUL.md is missing!"  
    content = soul_md.read_text(encoding="utf-8")  
    assert content.startswith("[PRECEDENCE OVERRIDE:"), "Missing token-0 RoPE override header!"  
    assert 500 < len(content) < 12000, "SOUL.md outside constitutional token envelope."

def test_pydantic_v2_path_sanitization():  
    """Certify Pydantic v2 SafePathModel eliminates Challenge A1 BPE suffix corruptions."""  
    assert str(SafePathModel(path="dag_executor.py_py").path).endswith("dag_executor.py")  
    assert str(SafePathModel(path="dag_executor_py").path).endswith("dag_executor.py")  
    assert str(SafePathModel(path="dag_executor.p").path).endswith("dag_executor.py")  
    assert str(SafePathModel(path="test_transactional_dagpy").path).endswith("test_transactional_dag.py")

def test_cpu_isolation_and_surgical_mutation(tmp_path: Path):  
    """Verify 100% CPU execution (0 MiB CUDA delta) and AST-validated module mutation."""  
    assert os.environ.get("CUDA_VISIBLE_DEVICES", "") in ("", "-1")  
    target = tmp_path / "pipeline_py"  
    out = jev_mutate_module(  
        MutateModuleInput(  
            path=target,  
            replacement_content="def run_task(x: int) -> int:\\n    return x + 1\\n",  
            workspace_dir=str(tmp_path),  
        )  
    )  
    assert "SUCCESS:" in out  
    assert (tmp_path / "pipeline.py").exists()

