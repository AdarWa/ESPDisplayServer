import json
import uuid
from typing import Any, Union, Optional

from rpc.rpc_models import (
    JSONRPCRequest,
    JSONRPCResult,
    JSONRPCErrorResponse,
    JSONRPCError,
    JSONRPCMessage,
)


def make_id() -> str:
    return str(uuid.uuid4())


def make_request(method: str, params: Any, id: Optional[str] = None) -> JSONRPCRequest:
    return JSONRPCRequest(method=method, params=params, id=id or make_id())


def make_response(result: Any, id: str) -> JSONRPCResult:
    return JSONRPCResult(result=result, id=id)


def make_error(
    message: str, id: Optional[str] = None, code: int = -32000, data: Any = None
) -> JSONRPCErrorResponse:
    return JSONRPCErrorResponse(
        error=JSONRPCError(code=code, message=message, data=data), id=id
    )


def serialize(msg: Union[JSONRPCRequest, JSONRPCResult, JSONRPCErrorResponse]) -> str:
    return msg.model_dump_json()


def deserialize(raw: Union[str, bytes]) -> JSONRPCMessage:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    obj = json.loads(raw)
    return JSONRPCMessage(**obj)
