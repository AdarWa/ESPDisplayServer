from __future__ import annotations
from typing import Dict, Any
from pydantic import BaseModel


class States(BaseModel):
    # Mapping: component_id -> state(dict)
    states: Dict[str, Dict[str, Any]] = {}

