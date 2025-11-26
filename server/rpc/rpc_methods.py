from internal_states.internal_state_handler import (
    SyncInternalStateHandler,
)
from utils.utils import register_rpc, set_value_by_string
from storage.config_manager import ConfigManager, ConfigError


@register_rpc()
def get_config(params, handler):
    try:
        config = ConfigManager().get()
    except ConfigError as exc:
        return {"error": str(exc)}
    return config.model_dump()


@register_rpc()
def reload_config(params, handler):
    try:
        config = ConfigManager().reload()
    except ConfigError as exc:
        return {"error": str(exc)}
    return config.model_dump()


@register_rpc()
def set_state(params, handler):
    name = params["state"]
    value = params["value"]
    state = ConfigManager().get().internal_states.find_state_by_name(name)
    assert state
    SyncInternalStateHandler().set(set_value_by_string(value, state))
