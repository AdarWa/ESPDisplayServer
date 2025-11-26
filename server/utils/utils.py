import json
import asyncio
from typing import Literal

from models.models import InternalState, StoredInternalState


def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


rpc_functions: dict = {}


def register_rpc(name: str = ""):
    def decorator(func):
        key = name or func.__name__
        rpc_functions[key] = func

        def error_handler(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return {"error": str(e)}

        return error_handler

    return decorator


def set_value_by_string(value: str, state: InternalState) -> StoredInternalState:
    if state.definition.type == "boolean":
        return state.to_stored_internal_state(value == "true" or value == "on")
    if state.definition.type == "number":
        return state.to_stored_internal_state(float(value))
    if state.definition.type == "enum":
        return state.to_stored_internal_state(value)
    return state.to_stored_internal_state()


class AsyncLoopBase:
    def __init__(self, interval):
        self.interval = interval
        self._task = None
        self._stop = asyncio.Event()

    def on_iteration(self):
        raise NotImplementedError

    async def _runner(self):
        try:
            while not self._stop.is_set():
                # run sync code in a thread
                await asyncio.to_thread(self.on_iteration)
                await asyncio.wait_for(self._stop.wait(), timeout=self.interval)
        except asyncio.TimeoutError:
            pass

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._runner())

    async def stop(self):
        self._stop.set()
        if self._task:
            await self._task


def compare(
    a: float | int, b: float | int, op: Literal["eq", "ne", "lt", "gt", "le", "ge"]
) -> bool:
    if op == "eq":
        return a == b
    elif op == "ge":
        return a >= b
    elif op == "gt":
        return a > b
    elif op == "le":
        return a <= b
    elif op == "lt":
        return a < b
    elif op == "ne":
        return a != b
