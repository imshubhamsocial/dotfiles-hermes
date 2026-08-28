"""COG Dual-Agent Verifier & Second Brain Plugin for Hermes."""
from hermes_core.cog_verifier import CogVerifier, create_cog_verifier
from hermes_core.cog_vault import CogVault, create_cog_vault

_verifier = create_cog_verifier()
_vault = create_cog_vault()

def register(ctx):
    if hasattr(ctx, "register_hook"):
        ctx.register_hook("pre_tool_call", on_pre_tool_call)

def on_pre_tool_call(tool_name, arguments):
    return None
