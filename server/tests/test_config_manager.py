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
    with open("config.yaml", 'r') as f:
        return yaml.safe_load(f)


def test_loads_valid_config(tmp_path, reset_config_manager):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(_valid_config()))

    config = reset_config_manager.init(path)

    assert isinstance(config, FullConfig)


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
            "bind": "ha:climate.living_room.hvac_mode",
        }
    )
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))

    with pytest.raises(ConfigError):
        reset_config_manager.init(path)
