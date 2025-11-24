import asyncio

import pytest

from models.models import (
    BooleanState,
    CallbackState,
    EnumState,
    InternalState,
    NumberState,
)
from utils.utils import AsyncLoopBase, is_json, set_value_by_string, singleton


def test_is_json_handles_valid_and_invalid_strings():
    assert is_json('{"valid": true}')
    assert not is_json("this is not json")


def test_singleton_decorator_returns_same_instance():
    calls = []

    @singleton
    class Example:
        def __init__(self, value: int):
            calls.append(value)
            self.value = value

    first = Example(1)
    second = Example(2)

    assert first is second
    assert first.value == 1
    assert calls == [1]


def test_set_value_by_string_converts_types():
    bool_state = InternalState(name="switch", definition=BooleanState(default=False))
    num_state = InternalState(name="temperature", definition=NumberState(default=20))
    enum_state = InternalState(
        name="mode",
        definition=EnumState(default="auto", options=["auto", "cool", "heat"]),
    )
    callback_state = InternalState(
        name="callback", definition=CallbackState(callback_id="cb")
    )

    assert set_value_by_string("on", bool_state).value is True
    assert set_value_by_string("true", bool_state).value is True
    assert set_value_by_string("off", bool_state).value is False
    assert set_value_by_string("21.5", num_state).value == 21.5
    assert set_value_by_string("cool", enum_state).value == "cool"
    assert set_value_by_string("anything", callback_state).value == ""


class CounterLoop(AsyncLoopBase):
    def __init__(self, interval: float = 0.01):
        super().__init__(interval)
        self.iterations = 0

    def on_iteration(self):
        self.iterations += 1


def test_async_loop_base_runs_iterations(monkeypatch):
    async def inline_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", inline_to_thread)

    async def runner():
        loop = CounterLoop(interval=0.01)
        loop.start()
        await asyncio.sleep(0.02)
        await loop.stop()
        return loop.iterations

    iterations = asyncio.run(runner())

    assert iterations >= 1
