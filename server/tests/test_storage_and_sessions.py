from pathlib import Path

from storage.session_manager import SessionManager
from storage.storage_manager import Storage


def test_storage_writes_and_reads_json(tmp_path):
    store = Storage(tmp_path)
    store.write_json("data/sample.json", {"value": 1})

    assert store.read_json("data/sample.json") == {"value": 1}
    assert (tmp_path / "data" / "sample.json").exists()


def test_storage_returns_default_and_persists(tmp_path):
    store = Storage(tmp_path)
    result = store.read_json("missing.json", default={"sessions": []})

    assert result == {"sessions": []}
    assert store.read_json("missing.json") == {"sessions": []}


def test_storage_handles_text_and_namespaces(tmp_path):
    store = Storage(tmp_path)
    namespaced = store.namespace("child")
    namespaced.write_text("hello.txt", "hi")

    assert namespaced.read_text("hello.txt") == "hi"
    assert (tmp_path / "child" / "hello.txt").exists()


def test_session_manager_cleans_and_persists(tmp_path):
    store = Storage(tmp_path)
    sessions_file = "sessions.json"
    store.write_json(sessions_file, {"sessions": [1, {"uuid": 2}, "ignored"]})

    manager = SessionManager()
    manager.init(sessions_file=sessions_file, store=store)

    assert manager.list_sessions() == [1, 2]
    assert store.read_json(sessions_file)["sessions"] == [1, 2]


def test_session_manager_adds_sessions_once(tmp_path):
    store = Storage(tmp_path)
    manager = SessionManager()
    manager.init(sessions_file="other.json", store=store)

    assert manager.get_free_session_id() == 0
    manager.add_session(3)
    manager.add_session(3)

    assert manager.list_sessions() == [3]
    assert store.read_json("other.json")["sessions"] == [3]
    assert manager.get_free_session_id() == 4
