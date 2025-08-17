from pathlib import Path
from storage.models.Config import Config
from storage.storage_manager import storage

from utils.utils import singleton

@singleton
class ConfigManager:
    def init(self, configs_folder = "configs") -> None:
        self.configs_folder = configs_folder

    def get_config_path(self, uuid: int):
        filename = str(uuid)+".yaml"
        return str(Path(self.configs_folder) / filename)

    def get_config(self,uuid: int):
        path = self.get_config_path(uuid)
        if storage.exists(path):
            return storage.read_file_yaml(path, Config)
        else:
            storage.write_file_yaml(path, Config(screens=[]))
            return storage.read_file_yaml(path, Config)

    def write_config(self, uuid: int, config: Config):
        storage.write_file_yaml(self.get_config_path(uuid), config)




