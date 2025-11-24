from typing import List
from homeassistant_api import WebsocketClient
from internal_states.internal_state_handler import InternalStateHandler
from models.models import InternalState, StoredInternalState
from storage.config_manager import ConfigManager
from utils.utils import AsyncLoopBase
import asyncio


def state_to_stored_state(state: InternalState) -> StoredInternalState:
    if state.definition.type == "callback":
        return StoredInternalState(
            name=state.name, definition=state.definition, value=""
        )
    return StoredInternalState(
        name=state.name,
        definition=state.definition,
        bind=state.bind,
        value=state.definition.default,
    )


def states_to_stored_states(states: List[InternalState]) -> List[StoredInternalState]:
    return [state_to_stored_state(state) for state in states]


class StateScheduler(AsyncLoopBase):
    def __init__(self, interval, base_url, token):
        super().__init__(interval)
        self.base_url = base_url
        self.token = token
        self.client = WebsocketClient(base_url, token)
        config = ConfigManager().get()
        asyncio.run(
            InternalStateHandler().bulk_set(
                states_to_stored_states(config.internal_states.states)
            )
        )

    def on_iteration(self):
        pass

