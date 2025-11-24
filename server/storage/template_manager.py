from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from models.models import TemplateConfig
from utils.utils import singleton


class TemplateError(RuntimeError):
    """Raised when configuration cannot be loaded or validated."""


@singleton
class TemplateManager:
    def __init__(self, path: str | Path = "templates.yaml") -> None:
        self.path = Path(path)
        self._config: Optional[TemplateConfig] = None

    def init(self, path: str | Path | None = None) -> TemplateConfig:
        """Initialise and load configuration from disk."""
        if path is not None:
            self.path = Path(path)
        return self.reload()

    def _read_raw(self) -> dict:
        if not self.path.exists():
            raise TemplateError(f"Config file not found at {self.path.resolve()}")
        try:
            return yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        except Exception as exc:  # pragma: no cover - defensive guard
            raise TemplateError(f"Failed to read config: {exc}") from exc

    def reload(self) -> TemplateConfig:
        """Force re-read of the file and validate via Pydantic models."""
        raw = self._read_raw()
        try:
            self._config = TemplateConfig.model_validate(raw)
        except ValidationError as exc:
            raise TemplateError(f"Invalid configuration: {exc}") from exc
        return self._config

    def get(self) -> TemplateConfig:
        """Return cached config, loading from disk if necessary."""
        if self._config is None:
            return self.reload()
        return self._config

    def as_dict(self) -> dict:
        """Return the validated configuration as a primitive dict."""
        return self.get().model_dump()
