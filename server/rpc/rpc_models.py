from typing import Any, Optional, Literal
from pydantic import BaseModel, model_validator

JSONRPC_VERSION = "2.0"


class JSONRPCBase(BaseModel):
    jsonrpc: Literal["2.0"] = JSONRPC_VERSION


class JSONRPCRequest(JSONRPCBase):
    method: str
    params: Any = None
    id: str


class JSONRPCError(BaseModel):
    code: int = -32000
    message: str
    data: Any = None


class JSONRPCResult(JSONRPCBase):
    result: Any
    id: str


class JSONRPCErrorResponse(JSONRPCBase):
    error: JSONRPCError
    id: Optional[str] = None


class JSONRPCMessage(BaseModel):
    """Discriminated wrapper that can hold request or response."""
    request: Optional[JSONRPCRequest] = None
    result: Optional[JSONRPCResult] = None
    error: Optional[JSONRPCErrorResponse] = None

    @model_validator(mode="before")
    def pick_variant(cls, values):
        if values.get("method"):
            return {"request": JSONRPCRequest(**values)}
        if "result" in values:
            return {"result": JSONRPCResult(**values)}
        if "error" in values:
            return {"error": JSONRPCErrorResponse(**values)}
        raise ValueError("Not a valid JSON-RPC 2.0 message")



class JSONRPCException(Exception):
    def __init__(self, error: JSONRPCError):
        if not isinstance(error, JSONRPCError):
            raise TypeError("JSONRPCException requires a JSONRPCError instance")
        self.error = error
        super().__init__(self.error.message)

    def model_dump(self):
        return self.error.model_dump()

    def __str__(self):
        return str(self.error.model_dump())
