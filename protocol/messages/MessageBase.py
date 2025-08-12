from pydantic import BaseModel
from enum import Enum

class RequestType(str, Enum):
    SUBSCRIBE = "subscribe"
    CLOCK_SYNC = "clock_sync"
    

class MessageBase(BaseModel):
    request_id: str
    request_type: RequestType
    