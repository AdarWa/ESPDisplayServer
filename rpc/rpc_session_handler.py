import logging
import threading
from typing import Dict, Callable, Any, Optional

from protocol.mqtt import MQTT
from rpc.rpc_protocol import (
    make_request, make_response, make_error, serialize, deserialize
)
from rpc.rpc_models import JSONRPCRequest, JSONRPCResult, JSONRPCErrorResponse, JSONRPCMessage, JSONRPCException

class RPCSessionHandler:
    """
    Handles JSON-RPC over MQTT for a single UUID.
    Topic flow:
      - Server publishes requests to /espdisplay/{uuid}/server
      - Server receives responses from /espdisplay/{uuid}/client
      - Device publishes requests to /espdisplay/{uuid}/client
      - Device receives responses from /espdisplay/{uuid}/server
    """

    def __init__(self, uuid: int, client: MQTT, default_timeout: float = 5.0) -> None:
        self.uuid = uuid
        self.client = client
        self.default_timeout = default_timeout

        self._pending_events: Dict[str, threading.Event] = {}
        self._pending_results: Dict[str, Any] = {}
        self._methods: Dict[str, Callable[[Any], Any]] = {}

        # server subscribes to client topic (incoming requests and responses)
        self.client.subscribe(f"espdisplay/{uuid}/client", self._on_message)
        logging.debug(self.call("add", {"a": 1, "b": 2}))

    # -------- outgoing call --------
    def call(self, method: str, params: Any, timeout: Optional[float] = None) -> Any:
        req = make_request(method, params)
        event = threading.Event()
        self._pending_events[req.id] = event

        # publish to server topic (device will receive)
        self.client.publish(f"espdisplay/{self.uuid}/server", req)

        wait_for = timeout if timeout is not None else self.default_timeout
        if not event.wait(wait_for):
            self._pending_events.pop(req.id, None)
            self._pending_results.pop(req.id, None)
            raise TimeoutError(f"RPC call={method} in device={self.uuid} timed out after {wait_for} seconds")

        result = self._pending_results.pop(req.id, None)
        self._pending_events.pop(req.id, None)

        if isinstance(result, dict) and "error" in result:
            err = result["error"]
            code = err.get("code", -32000)
            msg = err.get("message", "Unknown JSON-RPC error")
            data = err.get("data")
            raise RuntimeError(f"JSON-RPC error {code}: {msg}, data={data}")

        return result

    # -------- incoming request from device --------
    def _handle_request(self, req: JSONRPCRequest) -> None:
        method = req.method
        params = req.params
        req_id = req.id

        if method not in self._methods:
            resp = make_error(f"Unknown method {method}", id=req_id, code=-32601)
        else:
            try:
                result = self._methods[method](params)
                resp = make_response(result, id=req_id)
            except Exception as e:
                resp = make_error("Internal error", id=req_id, code=-32603, data=str(e))

        # reply on server topic (device is listening)
        self.client.publish(f"espdisplay/{self.uuid}/server", serialize(resp))

    # -------- handle incoming messages --------
    def _on_message(self, payload: Any) -> None:
        try:
            msg: JSONRPCMessage = deserialize(payload)
        except Exception as e:
            logging.error(f"[RPC {self.uuid}] invalid JSON-RPC payload: {e}")
            return

        if msg.request is not None:
            self._handle_request(msg.request)
        elif msg.result is not None:
            self._pending_results[msg.result.id] = msg.result.result
            self._pending_events[msg.result.id].set()
        elif msg.error is not None:
            raise JSONRPCException(msg.error)
            
    
    def register_method(self, name: str, func: Callable[[Any], Any]) -> None:
        """Register a callable. It receives params and returns a result."""
        self._methods[name] = func

    def unregister_method(self, name: str) -> None:
        self._methods.pop(name, None)
