from pydantic import BaseModel
from typing import List


class Session(BaseModel):
    uuid: int


class Sessions(BaseModel):
    sessions: List[Session] = []

