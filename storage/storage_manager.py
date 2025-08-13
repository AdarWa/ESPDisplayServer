from pathlib import Path
from typing import Type
from pydantic import BaseModel

class StorageManager:
    def __init__(self, path: Path = Path("./esp_storage")):
        self.path = path
        path.mkdir(exist_ok=True)
    
    def write_file(self, file_name: str, model: BaseModel, mode="w"):
        self.write_file_str(file_name, model.model_dump_json(), mode)

    def write_file_str(self, file_name: str, data: str, mode="w"):
        with open(self.path / file_name, mode) as f:
            f.write(data)

    def read_file_str(self, file_name: str, mode="r"):
        with open(self.path / file_name, mode) as f:
            return f.read()
    
    def read_file(self, file_name: str, model_type: Type[BaseModel], mode="r"):
        return model_type.model_validate_json(self.read_file_str(file_name,mode))
    
    def exists(self, file_name: str) -> bool:
        return (self.path / file_name).exists()
    
storage = StorageManager()