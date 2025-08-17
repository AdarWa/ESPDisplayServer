from __future__ import annotations
from typing import List
from pydantic import BaseModel
from enum import Enum

class ComponentType(str, Enum):
    LIGHT = "light"

class Config(BaseModel):
    screens: List[Screen]

class Screen(BaseModel):
    scr_id: str
    name: str
    back_screen: str
    components: List[Component]

class Component(BaseModel):
    comp_id: str
    type: ComponentType
    params: dict
