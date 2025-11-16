from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from models.models import FullConfig
from utils.utils import singleton


class ConfigError(RuntimeError):
    """Raised when configuration cannot be loaded or validated."""


@singleton
class ConfigManager:
    def __init__(self, path: str | Path = "config.yaml") -> None:
        self.path = Path(path)
        self._config: Optional[FullConfig] = None

    def init(self, path: str | Path | None = None) -> FullConfig:
        """Initialise and load configuration from disk."""
        if path is not None:
            self.path = Path(path)
        return self.reload()

    def _read_raw(self) -> dict:
        if not self.path.exists():
            raise ConfigError(f"Config file not found at {self.path.resolve()}")
        try:
            return yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
        except Exception as exc:  # pragma: no cover - defensive guard
            raise ConfigError(f"Failed to read config: {exc}") from exc

    def reload(self) -> FullConfig:
        """Force re-read of the file and validate via Pydantic models."""
        raw = self._read_raw()
        try:
            self._config = FullConfig.model_validate(raw)
        except ValidationError as exc:
            raise ConfigError(f"Invalid configuration: {exc}") from exc
        return self._config

    def get(self) -> FullConfig:
        """Return cached config, loading from disk if necessary."""
        if self._config is None:
            return self.reload()
        return self._config

    def as_dict(self) -> dict:
        """Return the validated configuration as a primitive dict."""
        return self.get().model_dump()
