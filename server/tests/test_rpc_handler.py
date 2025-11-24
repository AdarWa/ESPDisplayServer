import pytest

import rpc.rpc_handler as rh
from rpc.rpc_handler import RPCHandler
from storage.session_manager import SessionManager
from storage.storage_manager import Storage


@pytest.fixture
def reset_rpc(monkeypatch, tmp_path):
    handler = RPCHandler()
    handler.handlers = []
    handler.client = None
    SessionManager().init(sessions_file="rpc_sessions.json", store=Storage(tmp_path))
    yield handler
    handler.handlers = []
    handler.client = None


def test_update_subscriptions_creates_handlers(monkeypatch, tmp_path, reset_rpc):
    created = []

    class FakeHandler:
        def __init__(self, uuid, client, default_timeout):
            created.append((uuid, client, default_timeout))
            self.uuid = uuid

    monkeypatch.setattr(rh, "RPCSessionHandler", FakeHandler)

    reset_rpc.init(client="client", default_timeout=3.0)
    session_manager = SessionManager()
    session_manager.sessions = [1, 2]
    reset_rpc.handlers = []

    reset_rpc.update_subscriptions()

    assert created == [(1, "client", 3.0), (2, "client", 3.0)]
    assert reset_rpc.handler_exists(1)
    assert reset_rpc.handler_exists(2)


def test_get_handler_errors_when_missing(reset_rpc):
    reset_rpc.handlers = []
    with pytest.raises(ValueError):
        reset_rpc.get_handler(99)
