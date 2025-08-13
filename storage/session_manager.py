from storage.storage_manager import storage
from storage.models.Sessions import Session, Sessions
from typing import cast

from utils.utils import singleton

@singleton
class SessionManager:
    def init(self, sessions_file = "sessions.json", load=True) -> None:
        self.sessions = Sessions()
        self.sessions_file = sessions_file
        if load:
            self.load_sessions()

    def get_sessions(self) -> Sessions:
        return cast(Sessions,self.sessions)

    def load_sessions(self) -> None:
        if not storage.exists(self.sessions_file):
            self.write_sessions(Sessions())
        self.sessions = storage.read_file(self.sessions_file, Sessions)
    
    def write_sessions(self, sessions: Sessions | None = None) -> None:
        if not sessions:
            sessions = cast(Sessions, self.sessions)
        assert sessions is not None
        storage.write_file(self.sessions_file, sessions)

    def add_session(self, session: Session, write=True) -> None:
        cast(Sessions,self.sessions).sessions.append(session)
        if write:
            self.write_sessions()
    
    def get_free_session_id(self) -> int:
        return max([session.uuid for session in cast(Sessions,self.sessions).sessions]+[-1])+1



