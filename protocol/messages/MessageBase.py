from pydantic import BaseModel
from enum import Enum

class RequestType(str, Enum):
    SUBSCRIBE = "subscribe"
    SUBSCRIBE_REPLY = "subscribe_reply"
    

class MessageBase(BaseModel):
    request_id: str
    request_type: RequestType
    