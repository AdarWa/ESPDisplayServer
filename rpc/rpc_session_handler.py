from __future__ import annotations
import logging
import threading
from typing import Dict, Callable, Any, Optional

from protocol.mqtt import MQTT
from rpc.rpc_protocol import (
    make_request, make_response, make_error, serialize, deserialize
)
from rpc.rpc_models import JSONRPCRequest, JSONRPCResult, JSONRPCErrorResponse, JSONRPCMessage, JSONRPCException
import rpc.handler_methods as handler_methods

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
        self._methods: Dict[str, Callable[[Any, RPCSessionHandler], Any]] = {}

        # server subscribes to client topic (incoming requests and responses)
        logging.debug(f"[RPC {self.uuid}] Subscribing to espdisplay/{uuid}/client")
        self.client.subscribe(f"espdisplay/{uuid}/client", self._on_message)
        handler_methods.add_methods(self)
        logging.debug(f"[RPC {self.uuid}] Registered default handler methods")

    # -------- outgoing call --------
    def call(self, method: str, params: Any, timeout: Optional[float] = None) -> Any:
        logging.debug(f"[RPC {self.uuid}] Making call: {method} with params: {params}")
        req = make_request(method, params)
        event = threading.Event()
        self._pending_events[req.id] = event

        # publish to server topic (device will receive)
        logging.debug(f"[RPC {self.uuid}] Publishing request to espdisplay/{self.uuid}/server: {req}")
        self.client.publish(f"espdisplay/{self.uuid}/server", req)

        wait_for = timeout if timeout is not None else self.default_timeout
        if not event.wait(wait_for):
            logging.debug(f"[RPC {self.uuid}] Timeout waiting for response to request {req.id}")
            self._pending_events.pop(req.id, None)
            self._pending_results.pop(req.id, None)
            raise TimeoutError(f"RPC call={method} in device={self.uuid} timed out after {wait_for} seconds")

        result = self._pending_results.pop(req.id, None)
        self._pending_events.pop(req.id, None)
        logging.debug(f"[RPC {self.uuid}] Received result for request {req.id}: {result}")

        if isinstance(result, dict) and "error" in result:
            err = result["error"]
            code = err.get("code", -32000)
            msg = err.get("message", "Unknown JSON-RPC error")
            data = err.get("data")
            logging.debug(f"[RPC {self.uuid}] JSON-RPC error received: {err}")
            raise RuntimeError(f"JSON-RPC error {code}: {msg}, data={data}")

        return result

    # -------- incoming request from device --------
    def _handle_request(self, req: JSONRPCRequest) -> None:
        logging.debug(f"[RPC {self.uuid}] Handling incoming request: {req}")
        method = req.method
        params = req.params
        req_id = req.id

        if method not in self._methods:
            logging.debug(f"[RPC {self.uuid}] Unknown method: {method}")
            resp = make_error(f"Unknown method {method}", id=req_id, code=-32601)
        else:
            try:
                result = self._methods[method](params, self)
                logging.debug(f"[RPC {self.uuid}] Method {method} returned: {result}")
                resp = make_response(result, id=req_id)
            except Exception as e:
                logging.debug(f"[RPC {self.uuid}] Error in method {method}: {e}")
                resp = make_error("Internal error", id=req_id, code=-32603, data=str(e))

        # reply on server topic (device is listening)
        logging.debug(f"[RPC {self.uuid}] Publishing response to espdisplay/{self.uuid}/server: {resp}")
        self.client.publish(f"espdisplay/{self.uuid}/server", resp)

    # -------- handle incoming messages --------
    def _on_message(self, payload: Any) -> None:
        logging.debug(f"[RPC {self.uuid}] Received message payload: {payload}")
        try:
            msg: JSONRPCMessage = deserialize(payload)
            logging.debug(f"[RPC {self.uuid}] Deserialized message: {msg}")
        except Exception as e:
            logging.error(f"[RPC {self.uuid}] Invalid JSON-RPC payload: {e}")
            return

        if msg.request is not None:
            logging.debug(f"[RPC {self.uuid}] Message is a request")
            self._handle_request(msg.request)
        elif msg.result is not None:
            logging.debug(f"[RPC {self.uuid}] Message is a result for request {msg.result.id}")
            self._pending_results[msg.result.id] = msg.result.result
            self._pending_events[msg.result.id].set()
        elif msg.error is not None:
            logging.debug(f"[RPC {self.uuid}] Message is an error: {msg.error}")
            raise JSONRPCException(msg.error.error)
            
    def register_method(self, name: str, func: Callable[[Any, RPCSessionHandler], Any]) -> None:
        logging.debug(f"[RPC {self.uuid}] Registering method: {name}")
        self._methods[name] = func

    def unregister_method(self, name: str) -> None:
        logging.debug(f"[RPC {self.uuid}] Unregistering method: {name}")
        self._methods.pop(name, None)
