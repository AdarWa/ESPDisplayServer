from typing import Dict, List, Optional
from homeassistant_api import WebsocketClient
from internal_states.internal_state_handler import (
    SyncInternalStateHandler,
)
from models.models import Action, InternalState, StoredInternalState
from state_scheduler.ha_listener import AsyncWrapperHAListener
from storage.config_manager import ConfigManager
from utils.utils import compare, set_value_by_string
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

        SyncInternalStateHandler().bulk_set_if_not_exists(
            states_to_stored_states(config.internal_states.states)
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
        SyncInternalStateHandler().set(set_value_by_string(new_state, internal_state))

    def _get_all_actions(self) -> Dict[str, Action]:
        config = ConfigManager().get()
        return {action.id: action for action in config.actions.actions}

    def _find_action(self, action_id: ActionKey) -> Action:
        action = self.actions.get(action_id)
        if not action:
            raise KeyError(f"Action {action_id} not found")
        return action
    
    def _handle_call_script(self, action: Action) -> None:
        act = action.call_script
        assert act
        
        if act.script_name.startswith("ha:"):
            pass
        else:
            raise NotImplementedError()
        
    def _handle_on_callback(self, action: Action) -> None:
        act = action.on_callback
        assert act
        
        actions = act.actions
        for _action in actions:
            self.call_action(_action)
            
    def _handle_compare(self, action: Action) -> None:
        cmp = action.compare
        assert cmp
        
        left_value = SyncInternalStateHandler().get(cmp.left)
        assert left_value
        left_value = left_value.value
        op = cmp.operator
        right_value = cmp.right
        if isinstance(cmp.right, str):
            right_value = SyncInternalStateHandler().get(cmp.right)
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
    
    def _handle_update_state(self, action: Action) -> None:
        act = action.update_state
        assert act
        
        target = act.target
        value = act.value
            
        config = ConfigManager().get()
        state = config.internal_states.find_state_by_name(target)
        assert state
            
        SyncInternalStateHandler().set(state.to_stored_internal_state(value))


    def call_action(self, action_id: ActionKey) -> None:
        action = self._find_action(action_id)
        if action.call_script:
            self._handle_call_script(action)
        elif action.on_callback:
            self._handle_on_callback(action)
        elif action.compare:
            self._handle_compare(action)
        elif action.update_state:
            self._handle_update_state(action)
