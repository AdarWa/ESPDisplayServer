from utils.utils import register_rpc
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
