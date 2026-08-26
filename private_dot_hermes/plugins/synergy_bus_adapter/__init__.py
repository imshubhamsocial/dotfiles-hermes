"""
Synergy Bus Adapter Plugin for Upstream Hermes Agent.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from hermes_core.synergy_bus import SynergyBus, SynergyEvent, create_synergy_bus

logger = logging.getLogger(__name__)
_bus = create_synergy_bus()


def register(ctx: Any) -> None:
    if hasattr(ctx, "register_hook"):
        ctx.register_hook("on_session_start", on_session_start)
        ctx.register_hook("on_session_end", on_session_end)
        logger.info("Synergy Bus Adapter Plugin registered successfully.")


def on_session_start(**kwargs: Any) -> None:
    _bus.publish(SynergyEvent(event_type="session_start", payload=kwargs))


def on_session_end(**kwargs: Any) -> None:
    _bus.publish(SynergyEvent(event_type="session_end", payload=kwargs))
