from __future__ import annotations
from typing import List
from pydantic import BaseModel
from enum import Enum

class ComponentType(str, Enum):
    LIGHT = "light"

    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return self.__str__()
    

class Config(BaseModel):
    screens: List[Screen]

class Screen(BaseModel):
    scr_id: str
    name: str
    back_screen: str
    components: List[Component]

class Component(BaseModel):
    comp_id: str
    type: str
    params: dict


def get_default_config():
    comp = Component(comp_id="light", type=ComponentType.LIGHT, params={})
    scr = Screen(scr_id="scr1", name="TestScreen", back_screen="", components=[comp])
    return Config(screens=[scr])