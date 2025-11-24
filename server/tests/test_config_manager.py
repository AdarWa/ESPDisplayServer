import yaml
import pytest

from models.models import FullConfig
from storage.config_manager import ConfigError, ConfigManager


@pytest.fixture
def reset_config_manager():
    manager = ConfigManager()
    original_path = manager.path
    manager._config = None
    yield manager
    manager.path = original_path
    manager._config = None


def _valid_config():
    return {
        "screens": [
            {
                "id": "main",
                "template": "simple",
                "state_bindings": {"field": "temperature"},
            }
        ],
        "internal_states": {
            "states": [
                {
                    "name": "temperature",
                    "definition": {"type": "number", "default": 20, "min": 0},
                    "bind": "ha:climate.living_room",
                }
            ]
        },
        "actions": {
            "actions": [
                {
                    "id": "adjust_temp",
                    "update_state": {"target": "temperature", "value": 21},
                }
            ]
        },
        "modules": [
            {"id": "timer", "timer": {"callback": "cb", "time_state": "temperature"}}
        ],
    }


def test_loads_valid_config(tmp_path, reset_config_manager):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(_valid_config()))

    config = reset_config_manager.init(path)

    assert isinstance(config, FullConfig)
    assert reset_config_manager.as_dict()["screens"][0]["id"] == "main"
    assert config.internal_states.states[0].name == "temperature"


def test_missing_file_raises(tmp_path, reset_config_manager):
    with pytest.raises(ConfigError):
        reset_config_manager.init(tmp_path / "missing.yaml")


def test_invalid_references_raise(tmp_path, reset_config_manager):
    data = _valid_config()
    data["screens"][0]["state_bindings"]["field"] = "missing"
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))

    with pytest.raises(ConfigError):
        reset_config_manager.init(path)


def test_duplicate_bind_raises(tmp_path, reset_config_manager):
    data = _valid_config()
    data["internal_states"]["states"].append(
        {
            "name": "dup",
            "definition": {"type": "number", "default": 10},
            "bind": "ha:climate.living_room",
        }
    )
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))

    with pytest.raises(ConfigError):
        reset_config_manager.init(path)
