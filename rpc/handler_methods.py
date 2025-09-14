from __future__ import annotations
from typing import TYPE_CHECKING
from storage.config_manager import ConfigManager
from storage.state_manager import StateManager

if TYPE_CHECKING:
    from rpc.rpc_session_handler import RPCSessionHandler  # type-only import

def add_methods(handler: RPCSessionHandler):
    handler.register_method("get_config", get_config)
    handler.register_method("get_states", get_states)
    handler.register_method("update_state", update_state)

def get_config(params: dict, handler: RPCSessionHandler):
    return ConfigManager().get_config(handler.uuid).model_dump()

def get_states(params: dict, handler: RPCSessionHandler):
    return StateManager().get_states(handler.uuid).model_dump()

def update_state(params: dict, handler: RPCSessionHandler):
    if not isinstance(params, dict):
        raise ValueError("params must be an object with comp_id, and state")
    comp_id = params.get("comp_id")
    state = params.get("state")
    if not isinstance(comp_id, str) or not isinstance(state, dict):
        raise ValueError("Invalid params: expected comp_id(str), state(object)")
    updated = StateManager().update_component_state(handler.uuid, comp_id, state)
    return {"comp_id": comp_id, "state": updated}
