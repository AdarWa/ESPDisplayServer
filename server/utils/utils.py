import json
import asyncio

def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError as e:
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
        return func

    return decorator


class AsyncLoopBase:
    def __init__(self, interval):
        self.interval = interval
        self._task = None
        self._stop = asyncio.Event()

    async def on_iteration(self):
        raise NotImplementedError

    async def _runner(self):
        try:
            while not self._stop.is_set():
                await self.on_iteration()
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
