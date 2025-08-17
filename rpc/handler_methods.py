from __future__ import annotations
from typing import TYPE_CHECKING
from storage.config_manager import ConfigManager

if TYPE_CHECKING:
    from rpc.rpc_session_handler import RPCSessionHandler  # type-only import

def add_methods(handler: RPCSessionHandler):
    handler.register_method("get_config", get_config)

def get_config(params: dict, handler: RPCSessionHandler):
    return ConfigManager().get_config(handler.uuid).model_dump()
