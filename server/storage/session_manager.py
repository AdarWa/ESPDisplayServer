import logging
from typing import List
from utils.utils import singleton
from storage.storage_manager import storage, Storage


@singleton
class SessionManager:
    def init(
        self, sessions_file: str = "sessions.json", store: Storage | None = None
    ) -> None:
        self.sessions_file = sessions_file
        self.storage = store or storage
        self.sessions: List[int] = []
        self._load_sessions()

    def _persist(self) -> None:
        try:
            self.storage.write_json(self.sessions_file, {"sessions": self.sessions})
        except PermissionError as exc:
            logging.warning(
                f"Failed to persist sessions to {self.sessions_file}: {exc}"
            )

    def _load_sessions(self) -> None:
        data = self.storage.read_json(self.sessions_file, default={"sessions": []})
        raw_sessions = data.get("sessions", [])
        cleaned: List[int] = []
        for entry in raw_sessions:
            if isinstance(entry, dict) and "uuid" in entry:
                cleaned.append(int(entry["uuid"]))
            elif isinstance(entry, int):
                cleaned.append(entry)
        self.sessions = cleaned
        if raw_sessions != cleaned:
            self._persist()

    def list_sessions(self) -> List[int]:
        return list(self.sessions)

    def add_session(self, uuid: int) -> None:
        if uuid not in self.sessions:
            self.sessions.append(uuid)
            self._persist()

    def get_free_session_id(self) -> int:
        return (max(self.sessions) + 1) if self.sessions else 0
