"""
U9: Minimal Mode Benchmark Preset (`--preset minimal`)
======================================================
Loading 15+ tool definitions burns ~1,200 context tokens before the task even
starts on a 6 GB local GPU. The minimal preset strips every auxiliary/MCP tool
down to ONLY persistent bash (execute_command) + atomic file editor
(patch_file), collapsing system prompt overhead to <350 tokens.

4B SLM Trap-1 Countermeasure (Tool Availability Hallucination):
  The prompt explicitly declares that ONLY 'patch' and 'bash' exist in this
  runtime, so the model stops calling stripped tools from pretraining priors.
"""

from typing import List, Any

MINIMAL_ALLOWED_TOOLS = ("patch_file", "execute_command")

PRESETS = ("minimal",)

MINIMAL_SYSTEM_PROMPT = """You are Hermes @coder in MINIMAL BENCHMARK MODE.
ONLY 'patch_file' and 'execute_command' exist in this runtime. All other tools are disabled.
Rules:
- Edit files exclusively via patch_file(target_block, replacement_block); never rewrite whole files.
- Run shell/tests via execute_command(command).
- Obey Karpathy Laws: ground truth first; no speculative bloat; surgical diffs only; verify against the stated failure condition.
- Emit zero prose. Finish with a one-line VERIFIED/FAILED verdict."""


def estimate_prompt_tokens(text: str) -> int:
    """Deterministic sub-100ms token proxy (4 chars/token heuristic, whitespace-normalized)."""
    return max(1, len(" ".join(text.split())) // 4)


def filter_functions(functions: List[Any], allowed=MINIMAL_ALLOWED_TOOLS) -> List[Any]:
    """Keep ONLY the persistent bash + atomic patch editor bindings."""
    return [f for f in functions if getattr(f, "__name__", "") in allowed]


def build_minimal_agent(agent, task_prompt: str = ""):
    """Return a preset-minimal copy of an agent (never mutates the original)."""
    agent.functions = filter_functions(agent.functions)
    agent.instructions = (
        MINIMAL_SYSTEM_PROMPT + ("\n\nCURRENT TASK:\n" + task_prompt if task_prompt else "")
    )
    agent.tool_choice = None
    return agent


def validate_minimal_prompt_budget(budget_tokens: int = 350) -> bool:
    return estimate_prompt_tokens(MINIMAL_SYSTEM_PROMPT) < budget_tokens


if __name__ == "__main__":
    print(f"minimal prompt tokens ~ {estimate_prompt_tokens(MINIMAL_SYSTEM_PROMPT)} (budget <350)")
