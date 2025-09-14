from pathlib import Path
from typing import Dict, Any, cast

from storage.config_manager import ConfigManager
from storage.models.Config import Config
from storage.models.States import States
from storage.storage_manager import storage
from utils.utils import singleton


@singleton
class StateManager:
    def init(self, states_folder: str = "states") -> None:
        self.states_folder = states_folder

    def get_state_path(self, uuid: int) -> str:
        filename = f"{uuid}.yaml"
        return str(Path(self.states_folder) / filename)

    def _default_states_from_config(self, config: Config) -> States:
        mapping: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for screen in config.screens:
            mapping[screen.scr_id] = {}
            for comp in screen.components:
                mapping[screen.scr_id][comp.comp_id] = {}
        return States(states=mapping)

    def get_states(self, uuid: int) -> States:
        path = self.get_state_path(uuid)
        if storage.exists(path):
            
            return cast(States, storage.read_file_yaml(path, States))
        # create default based on config
        cfg = ConfigManager().get_config(uuid)
        defaults = self._default_states_from_config(cast(Config, cfg))
        storage.write_file_yaml(path, defaults)
        return defaults

    def write_states(self, uuid: int, states: States) -> None:
        storage.write_file_yaml(self.get_state_path(uuid), states)

    def update_component_state(self, uuid: int, comp_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        states = self.get_states(uuid)
        if comp_id not in states.states:
            states.states[comp_id] = {}
        states.states[comp_id] = state
        self.write_states(uuid, states)
        return states.states[comp_id]

