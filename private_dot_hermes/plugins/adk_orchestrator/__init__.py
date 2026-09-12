from .agent import Agent, Response, Result, AgentFunction
from .swarm_engine import HermesOrchestrator, function_to_schema
from .adk_custom_agent import HermesADKCustomAgent, adk_content_to_str, hermes_response_to_adk_event

def register(ctx=None):
    """
    Registers Google ADK Orchestrator components into Hermes runtime.
    """
    if not ctx:
        return True

    # 1. Native CLI command: hermes adk [status | run]
    if hasattr(ctx, "register_cli_command"):
        def setup_adk(parser):
            parser.description = "Google ADK Multi-Agent Orchestrator and Swarm Engine"
            subparsers = parser.add_subparsers(dest="subcommand", help="ADK actions")
            subparsers.add_parser("status", help="Show Google ADK integration status")
            run_p = subparsers.add_parser("run", help="Run a prompt through Hermes ADK orchestrator")
            run_p.add_argument("prompt", help="Prompt to execute")

        def handle_adk(args):
            subcmd = getattr(args, "subcommand", None) or "status"
            if subcmd == "status":
                from .adk_custom_agent import ADK_AVAILABLE
                print("Google ADK Orchestrator Status:")
                print(f"  ADK Library Available: {ADK_AVAILABLE}")
                print("  Engine: HermesOrchestrator (Local OpenAI-compatible Port 8138)")
                print("  Adapter: HermesADKCustomAgent (BaseAgent wrapper)")
            elif subcmd == "run":
                orch = HermesOrchestrator()
                ag = Agent(name="adk-worker", instructions="You are a helpful Hermes ADK agent.")
                resp = orch.run(ag, [{"role": "user", "content": args.prompt}])
                last_msg = resp.messages[-1] if resp.messages else {"content": "No response"}
                print(last_msg.get("content", ""))

        ctx.register_cli_command("adk", setup_adk, handle_adk)

    # 2. Slash command: /adk
    if hasattr(ctx, "register_command"):
        def slash_adk(arg_str: str = ""):
            from .adk_custom_agent import ADK_AVAILABLE
            if not arg_str.strip():
                return f"Google ADK Orchestrator: Active (ADK_AVAILABLE={ADK_AVAILABLE}). Use `/adk <prompt>` to run."
            orch = HermesOrchestrator()
            ag = Agent(name="adk-worker", instructions="You are a helpful Hermes ADK agent.")
            resp = orch.run(ag, [{"role": "user", "content": arg_str.strip()}])
            last_msg = resp.messages[-1] if resp.messages else {"content": "No response"}
            return str(last_msg.get("content", ""))

        ctx.register_command("adk", slash_adk, "Run prompt via Google ADK orchestrator", "<prompt>")

    return True