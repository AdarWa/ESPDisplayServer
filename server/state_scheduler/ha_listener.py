import asyncio
from typing import Callable, cast

from homeassistant_api import WebsocketClient


class AsyncWrapperHAListener:
    def __init__(self, client: WebsocketClient):
        self.client = client
        self.triggers = []

    def add_trigger(
        self, trigger_type: str, callback: Callable[[str, str], None], **kwargs
    ):
        self.triggers.append((trigger_type, kwargs, callback))

    async def _run_trigger(self, trigger_type: str, kwargs, callback):
        # Run the blocking generator in a thread
        def generator():
            with self.client.listen_trigger(trigger_type, **kwargs) as gen:
                for event in gen:
                    # Schedule the async callback in the main asyncio loop
                    asyncio.run_coroutine_threadsafe(
                        callback(
                            kwargs.get("entity_id"),
                            cast(dict, event["data"])["new_state"]["state"],
                        ),
                        asyncio.get_running_loop(),
                    )

        await asyncio.to_thread(generator)

    async def start(self):
        tasks = [
            asyncio.create_task(self._run_trigger(trigger_type, kwargs, callback))
            for trigger_type, kwargs, callback in self.triggers
        ]
        await asyncio.gather(*tasks)
