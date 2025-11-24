import yaml
import pytest

from storage.template_manager import TemplateError, TemplateManager


@pytest.fixture
def reset_template_manager():
    manager = TemplateManager()
    original_path = manager.path
    manager._config = None
    yield manager
    manager.path = original_path
    manager._config = None


def _valid_templates():
    return {
        "templates": [
            {
                "name": "card",
                "fields": [
                    {"name": "title", "bind_to_internal": "state"},
                    {"name": "action", "callback": "cb"},
                ],
            }
        ]
    }


def test_loads_valid_templates(tmp_path, reset_template_manager):
    path = tmp_path / "templates.yaml"
    path.write_text(yaml.safe_dump(_valid_templates()))

    config = reset_template_manager.init(path)

    assert config.templates[0].name == "card"
    assert reset_template_manager.as_dict()["templates"][0]["fields"][0]["name"] == (
        "title"
    )


def test_missing_template_file_raises(tmp_path, reset_template_manager):
    with pytest.raises(TemplateError):
        reset_template_manager.init(tmp_path / "missing.yaml")


def test_invalid_template_structure_raises(tmp_path, reset_template_manager):
    invalid = {"templates": [{"name": "broken", "fields": "not-a-list"}]}
    path = tmp_path / "templates.yaml"
    path.write_text(yaml.safe_dump(invalid))

    with pytest.raises(TemplateError):
        reset_template_manager.init(path)
