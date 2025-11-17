import json
from pathlib import Path
from typing import Any, Optional


class Storage:
    """
    Lightweight storage helper for reading/writing JSON or text files under a
    configurable root directory. Namespaces can be created for easy separation
    of concerns (e.g. sessions/, configs/).
    """

    def __init__(self, root: Path = Path("./esp_storage")):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def namespace(self, name: str) -> "Storage":
        """Return a new Storage rooted at a child directory."""
        return Storage(self.root / name)

    def _resolve(self, filename: str | Path) -> Path:
        path = self.root / Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def write_json(self, filename: str | Path, data: Any) -> None:
        path = self._resolve(filename)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def read_json(self, filename: str | Path, default: Optional[Any] = None) -> Any:
        path = self._resolve(filename)
        if not path.exists():
            if default is not None:
                self.write_json(filename, default)
                return default
            raise FileNotFoundError(f"Missing file: {path}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def write_text(self, filename: str | Path, data: str) -> None:
        path = self._resolve(filename)
        with path.open("w", encoding="utf-8") as f:
            f.write(data)

    def read_text(self, filename: str | Path, default: Optional[str] = None) -> str:
        path = self._resolve(filename)
        if not path.exists():
            if default is not None:
                self.write_text(filename, default)
                return default
            raise FileNotFoundError(f"Missing file: {path}")
        with path.open("r", encoding="utf-8") as f:
            return f.read()


storage = Storage()
