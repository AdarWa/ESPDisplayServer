from typing import Dict, List, Optional
from homeassistant_api import WebsocketClient
from internal_states.internal_state_handler import InternalStateHandler
from models.models import Action, InternalState, StoredInternalState
from state_scheduler.ha_listener import AsyncWrapperHAListener
from storage.config_manager import ConfigManager
from utils.utils import compare, set_value_by_string
import asyncio
from typing import Callable

type TriggerCallback = Callable[[str, str], None]
type ActionKey = str


def states_to_stored_states(states: List[InternalState]) -> List[StoredInternalState]:
    return [state.to_stored_internal_state() for state in states]


def get_ha_bind_dict(states: List[InternalState]) -> Dict[str, str]:
    return {
        state.name: state.bind.removeprefix("ha:")
        for state in states
        if state.bind and state.bind.startswith("ha:")
    }


def bulk_add_trigger(
    entity_ids: List[str],
    listener: AsyncWrapperHAListener,
    callback: TriggerCallback,
    type: str = "state",
) -> None:
    for entity_id in entity_ids:
        listener.add_trigger(type, callback, entity_id=entity_id)
        


class StateScheduler:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.client = WebsocketClient(base_url, token)

        config = ConfigManager().get()

        asyncio.get_running_loop().create_task(
            InternalStateHandler().bulk_set_if_not_exists(
                states_to_stored_states(config.internal_states.states)
            )
        )

        self.ha_listener = AsyncWrapperHAListener(self.client)

        self.bind_dict = get_ha_bind_dict(config.internal_states.states)  # internal:ha
        self.bind_list = list(self.bind_dict.values())

        bulk_add_trigger(self.bind_list, self.ha_listener, self.handle_new_state)
        
        self.actions = self._get_all_actions()

    def _get_bound_state_by_entity_id(self, entity_id: str) -> Optional[InternalState]:
        for key, value in self.bind_dict.items():
            if value.removeprefix("ha:") == entity_id:
                return ConfigManager().get().internal_states.find_state_by_name(key)
        return None

    def handle_new_state(self, entity_id: str, new_state: str):
        internal_state = self._get_bound_state_by_entity_id(entity_id)
        assert internal_state
        asyncio.get_running_loop().create_task(
            InternalStateHandler().set(set_value_by_string(new_state, internal_state))
        )

    def _get_all_actions(self) -> Dict[str, Action]:
        config = ConfigManager().get()
        return {action.id:action for action in config.actions.actions}
    
    def _find_action(self, action_id: ActionKey) -> Action:
        action = self.actions.get(action_id)
        if not action:
            raise KeyError(f"Action {action_id} not found")
        return action
        
    
    def call_action(self, action_id: ActionKey):
        action = self._find_action(action_id)
        if action.call_script:
            raise NotImplementedError()
        elif action.on_callback:
            actions = action.on_callback.actions
            for _action in actions:
                self.call_action(_action)
        elif action.compare:
            cmp = action.compare
            left_value = asyncio.run_coroutine_threadsafe(InternalStateHandler().get(cmp.left), asyncio.get_running_loop()).result()
            assert left_value
            left_value = left_value.value
            op = cmp.operator
            right_value = cmp.right
            if isinstance(cmp.right, str):
                right_value = asyncio.run_coroutine_threadsafe(InternalStateHandler().get(cmp.right), asyncio.get_running_loop()).result()
                assert right_value
                right_value = right_value.value
            assert left_value
            assert right_value
            result = compare(float(left_value), float(right_value), op)
            if result:
                if cmp.on_true:
                    self.call_action(cmp.on_true)
            else:
                if cmp.on_false:
                    self.call_action(cmp.on_false)
        elif action.update_state:
            raise NotImplementedError()
            
            
                
