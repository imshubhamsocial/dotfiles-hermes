"""
Hermes Orchestrator Engine (OpenAI Swarm + Claude Code Execution Loop)
=====================================================================
Executes the native loop:
  1. Calls llama-server on port 8138 with OpenAI tool calling schema.
  2. Parses tool_calls, invokes Python callables, updates context_variables.
  3. Supports dynamic agent transfers via Result(agent=next_agent).
  4. Truncates context dynamically (Claude Code MessageHistory pattern).
"""

import os
import json
import copy
import inspect
from collections import defaultdict
from typing import List, Dict, Any, Optional
from openai import OpenAI

from .agent import Agent, Response, Result, AgentFunction


def function_to_schema(func: AgentFunction) -> Dict[str, Any]:
    """Convert a Python function with docstrings/type annotations into OpenAI Tool JSON Schema."""
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name == "context_variables":
            continue
            
        p_type = "string"
        if param.annotation == int:
            p_type = "integer"
        elif param.annotation == float:
            p_type = "number"
        elif param.annotation == bool:
            p_type = "boolean"
        elif param.annotation == dict or param.annotation == Dict:
            p_type = "object"
        elif param.annotation == list or param.annotation == List:
            p_type = "array"
            
        properties[param_name] = {
            "type": p_type,
            "description": f"Parameter {param_name}"
        }
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
            
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": doc.split("\n\n")[0] if doc else f"Execute {func.__name__}",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }


class HermesOrchestrator:
    """Production Multi-Agent Orchestrator connecting Hermes to local llama-server."""

    def __init__(self, base_url: str = "http://127.0.0.1:8138/v1", api_key: str = "local"):
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def run(
        self,
        agent: Agent,
        messages: List[Dict[str, Any]],
        context_variables: Optional[Dict[str, Any]] = None,
        max_turns: int = 25,
        verbose: bool = True,
        preset: Optional[str] = None
    ) -> Response:
        # U9 Minimal Mode Benchmark Preset: strip auxiliary tools down to
        # persistent bash + atomic patch editor (<350-token system prompt).
        if preset is not None:
            from .presets import PRESETS, build_minimal_agent
            if preset not in PRESETS:
                raise ValueError(f"Unknown preset '{preset}'. Available: {sorted(PRESETS)}")
            active_agent = build_minimal_agent(agent) if preset == "minimal" else agent
        else:
            active_agent = agent
        ctx = copy.deepcopy(context_variables or {})
        history = copy.deepcopy(messages)
        init_len = len(messages)
        turns = 0

        # U6: hash-chained append-only trajectory stream (RAMDisk-active).
        from .trajectory import TrajectoryRecorder
        recorder = getattr(self, "_u6_recorder", None) or TrajectoryRecorder()
        self._u6_recorder = recorder

        def _trace(**fields):
            try:
                return recorder.append(**fields)
            except Exception:
                return None

        while turns < max_turns and active_agent:
            turns += 1
            from .middleware import MythosCognitiveGovernor, FableMiddleware
            from .hypothesis_tree import HypothesisTree
            from .working_memory import WorkingMemoryAnchor

            # ── U8 Byte-Static Prefix Cache Alignment ──────────────────────
            # System prompt = fixed-order STATIC segments only (governor law
            # block + agent instructions). Dynamic context (working-memory
            # anchor, boundary constraints) is injected at the TAIL of the
            # latest USER turn so llama-server KV prefix reuse stays intact.
            from .prefix_cache import (
                assert_byte_static,
                build_static_system_prompt,
                inject_dynamic_into_last_user_turn,
                static_prefix_hash,
            )

            static_system = build_static_system_prompt(
                MythosCognitiveGovernor.wrap_instructions(
                    active_agent.get_instructions(ctx),
                    coder=(active_agent.name == "coder"),
                )
            )

            # U8 Trap-1 lint: register the prefix on first sight of an agent,
            # then fail LOUD if any later turn mutates a single byte of it.
            reg_key = f"{active_agent.name}:{active_agent.model}"
            if not hasattr(self, "_u8_prefix_registry"):
                self._u8_prefix_registry = {}
            if reg_key in self._u8_prefix_registry:
                assert_byte_static(static_system, self._u8_prefix_registry[reg_key])
            else:
                self._u8_prefix_registry[reg_key] = static_prefix_hash(static_system)

            dynamic_blocks = []
            anchor = WorkingMemoryAnchor.load_state()
            if anchor.active_contract_summary or anchor.pinned_symbols:
                dynamic_blocks.append(anchor.format_prompt_block())
            tree = HypothesisTree.load_state()
            neg_constraints = tree.get_accumulated_negative_constraints()
            if neg_constraints:
                dynamic_blocks.append(
                    "\n[FRONTIER BOUNDARY CONSTRAINTS - DO NOT REPEAT FAILED APPROACHES]:\n"
                    + "\n".join(f"- {c}" for c in neg_constraints[:4])
                )

            call_messages = (
                [{"role": "system", "content": static_system}]
                + inject_dynamic_into_last_user_turn(history, "\n\n".join(dynamic_blocks))
            )

            # U6 trajectory: turn start with prompt footprint estimate.
            from .presets import estimate_prompt_tokens
            _trace(event="turn_start", turn=turns, role=active_agent.name,
                   prompt_tokens=estimate_prompt_tokens(static_system))


            
            # U3 Schema-Level Capability Masks: masked tools are never even
            # advertised to the model (violation becomes physically impossible).
            from .capability_masks import mask_functions, resolve_role
            role = resolve_role(active_agent)
            visible_functions = mask_functions(active_agent.functions, role)

            # Build tools schema from agent's registered functions
            tool_schemas = [function_to_schema(f) for f in visible_functions] if visible_functions else None
            
            if verbose:
                print(f"\n🤖 [{active_agent.name}] Calling model (Turn {turns}/{max_turns})...")
            
            create_params: Dict[str, Any] = {
                "model": active_agent.model,
                "messages": call_messages,
                "temperature": active_agent.temperature,
                "max_tokens": active_agent.max_tokens,
            }
            if tool_schemas:
                create_params["tools"] = tool_schemas
                if active_agent.tool_choice:
                    create_params["tool_choice"] = active_agent.tool_choice

            completion = self.client.chat.completions.create(**create_params)
            msg = completion.choices[0].message
            
            # Append model message to history
            assistant_msg = {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in (msg.tool_calls or [])
                ] if msg.tool_calls else None
            }
            history.append(assistant_msg)
            
            if verbose and msg.content:
                print(f"📝 [{active_agent.name}]:\n{msg.content[:400]}..." if len(msg.content) > 400 else f"📝 [{active_agent.name}]:\n{msg.content}")

            # If no tools called, we have reached a response state for this agent
            if not msg.tool_calls:
                if verbose:
                    print(f"✅ [{active_agent.name}] Finished turn without tool calls.")
                _trace(event="response", turn=turns, role=active_agent.name,
                       content_head=(msg.content or "")[:200])
                _trace(event="turn_end", turn=turns)
                break

            # Execute tool calls
            # U2/U3: dispatch map is the MASKED surface only; hooks gate mutations.
            from .hooks import LifecycleHookEngine
            if "hook_engine" not in dir(self):
                self.hook_engine = LifecycleHookEngine()
            function_map = {f.__name__: f for f in visible_functions}
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args_raw = tc.function.arguments

                if verbose:
                    print(f"🔧 [{active_agent.name}] Tool Call: {fn_name}({fn_args_raw[:150]}...)")

                _trace(event="tool_call", turn=turns, role=active_agent.name,
                       tool=fn_name, args_head=fn_args_raw)

                if fn_name not in function_map:
                    _trace(event="gate_check", turn=turns, tool=fn_name,
                           gate_status="REJECT",
                           reason=f"capability_mask_backstop:{active_agent.name}")
                    err_msg = f"Error: Tool '{fn_name}' not available for agent '{active_agent.name}'."
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": err_msg
                    })
                    continue

                try:
                    args = json.loads(fn_args_raw) if fn_args_raw else {}
                except Exception as e:
                    args = {}

                # Fable Middleware Pre-Flight Tool Payload Validation
                valid_payload, validation_msg = FableMiddleware.filter_tool_payload(fn_name, args)
                if not valid_payload:
                    if verbose:
                        print(f"   🛡️  [Fable Middleware Interception]: {validation_msg}")
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": validation_msg
                    })
                    continue

                # U2 pre_tool_call hook: mutating payloads validated BEFORE disk.
                hook_ok, hook_msg = self.hook_engine.pre_tool_call(role, fn_name, args)
                _trace(event="gate_check", turn=turns, tool=fn_name,
                       gate_status="PASS" if hook_ok else "REJECT",
                       reason=hook_msg.splitlines()[0] if hook_msg else "")
                if not hook_ok:
                    if verbose:
                        print(f"   🪝 [pre_tool_call REJECTED]: {hook_msg.splitlines()[0]}")
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": hook_msg
                    })
                    continue

                func = function_map[fn_name]
                if "context_variables" in inspect.signature(func).parameters:
                    args["context_variables"] = ctx

                try:
                    raw_result = func(**args)
                except Exception as e:
                    raw_result = f"Error executing tool {fn_name}: {str(e)}"


                # Handle Swarm Result objects or dynamic agent handoffs
                if isinstance(raw_result, Result):
                    tool_content = raw_result.value
                    ctx.update(raw_result.context_variables)
                    if raw_result.agent:
                        if verbose:
                            print(f"🔀 Handoff: [{active_agent.name}] ➔ [{raw_result.agent.name}]")
                        _trace(event="handoff", turn=turns, from_role=active_agent.name,
                               to_role=raw_result.agent.name)
                        active_agent = raw_result.agent
                elif isinstance(raw_result, Agent):
                    tool_content = f"Transferred to @{raw_result.name}."
                    if verbose:
                        print(f"🔀 Handoff: [{active_agent.name}] ➔ [{raw_result.name}]")
                    _trace(event="handoff", turn=turns, from_role=active_agent.name,
                           to_role=raw_result.name)
                    active_agent = raw_result
                else:
                    tool_content = str(raw_result)

                # U2 post_tool_call hook: shadow snapshot + trajectory event.
                self.hook_engine.post_tool_call(fn_name, args, str(tool_content))

                # U6/U7: record the actual outcome so replay can diff it later.
                _trace(event="tool_result", turn=turns, tool=fn_name,
                       result_ok=not str(tool_content).startswith("Error"),
                       result_head=str(tool_content)[:200])

                if verbose:
                    print(f"   ↳ Result: {tool_content[:200]}...")

                history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": fn_name,
                    "content": tool_content
                })

            # U15 Differential State Compaction (Codex Token Economy pattern)
            # Prunes resolved intermediate tool turns while preserving the goal
            # anchor head and the active reasoning window.
            from .token_engine import DifferentialStateCompactor
            history = DifferentialStateCompactor(keep_recent=6).compact(history)

        return Response(
            messages=history[init_len:],
            agent=active_agent,
            context_variables=ctx
        )

