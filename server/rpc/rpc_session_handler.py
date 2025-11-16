from __future__ import annotations
import logging
import threading
from typing import Dict, Callable, Any, Optional

from protocol.mqtt import MQTT
from rpc.rpc_protocol import (
    make_request, make_response, make_error, deserialize
)
from rpc.rpc_models import JSONRPCRequest, JSONRPCResult, JSONRPCErrorResponse, JSONRPCMessage

rpc_functions: dict = {}
def register_rpc(name: str = ""): 
    def decorator(func):
        key = name or func.__name__
        rpc_functions[key] = func
        return func
    return decorator

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
        self.logging_prefix = f"[RPC {self.uuid}] "

        # server subscribes to client topic (incoming requests and responses)
        logging.debug(f"{self.logging_prefix}Subscribing to espdisplay/{uuid}/client")
        self.client.subscribe(f"espdisplay/{uuid}/client", self._on_message)
        self.register_method("ping", self._ping)
        for key,func in rpc_functions.items():
            self.register_method(key, func)
            logging.debug(f"{self.logging_prefix}Registed method {key}")
        logging.debug(f"{self.logging_prefix}Registered default handler methods")

    # -------- outgoing call --------
    def call(self, method: str, params: Any, timeout: Optional[float] = None) -> Any:
        logging.debug(f"{self.logging_prefix}Making call: {method} with params: {params}")
        req = make_request(method, params)
        event = threading.Event()
        self._pending_events[req.id] = event

        # publish to server topic (device will receive)
        logging.debug(f"{self.logging_prefix}Publishing request to espdisplay/{self.uuid}/server: {req}")
        self.client.publish(f"espdisplay/{self.uuid}/server", req)

        wait_for = timeout if timeout is not None else self.default_timeout
        if not event.wait(wait_for):
            logging.debug(f"{self.logging_prefix}Timeout waiting for response to request {req.id}")
            self._pending_events.pop(req.id, None)
            self._pending_results.pop(req.id, None)
            raise TimeoutError(f"RPC call={method} in device={self.uuid} timed out after {wait_for} seconds")

        result = self._pending_results.pop(req.id, None)
        self._pending_events.pop(req.id, None)
        logging.debug(f"{self.logging_prefix}Received result for request {req.id}: {result}")

        if isinstance(result, dict) and "error" in result:
            err = result["error"]
            code = err.get("code", -32000)
            msg = err.get("message", "Unknown JSON-RPC error")
            data = err.get("data")
            logging.debug(f"{self.logging_prefix}JSON-RPC error received: {err}")
            raise RuntimeError(f"JSON-RPC error {code}: {msg}, data={data}")

        return result

    # -------- incoming request from device --------
    def _handle_request(self, req: JSONRPCRequest) -> None:
        logging.debug(f"{self.logging_prefix}Handling incoming request: {req}")
        method = req.method
        params = req.params
        req_id = req.id

        if method not in self._methods:
            logging.debug(f"{self.logging_prefix}Unknown method: {method}")
            resp = make_error(f"Unknown method {method}", id=req_id, code=-32601)
        else:
            try:
                result = self._methods[method](params, self)
                logging.debug(f"{self.logging_prefix}Method {method} returned: {result}")
                resp = make_response(result, id=req_id)
            except Exception as e:
                logging.debug(f"{self.logging_prefix}Error in method {method}: {e}")
                resp = make_error("Internal error", id=req_id, code=-32603, data=str(e))

        # reply on server topic (device is listening)
        logging.debug(f"{self.logging_prefix}Publishing response to espdisplay/{self.uuid}/server: {resp}")
        self.client.publish(f"espdisplay/{self.uuid}/server", resp)

    # -------- handle incoming messages --------
    def _on_message(self, payload: Any) -> None:
        logging.debug(f"{self.logging_prefix}Received message payload: {payload}")
        try:
            msg: JSONRPCMessage = deserialize(payload)
            logging.debug(f"{self.logging_prefix}Deserialized message: {msg}")
        except Exception as e:
            logging.error(f"{self.logging_prefix}Invalid JSON-RPC payload: {e}")
            return

        if msg.request is not None:
            logging.debug(f"{self.logging_prefix}Message is a request")
            self._handle_request(msg.request)
        elif msg.result is not None:
            logging.debug(f"{self.logging_prefix}Message is a result for request {msg.result.id}")
            event = self._pending_events.get(msg.result.id)
            if event:
                self._pending_results[msg.result.id] = msg.result.result
                event.set()
            else:
                logging.warning(f"{self.logging_prefix}Received result for unknown request id {msg.result.id}")
        elif msg.error is not None:
            logging.debug(f"{self.logging_prefix}Message is an error: {msg.error}")
            err = msg.error
            event = self._pending_events.get(err.id) if err.id else None
            if event and err.id is not None:
                self._pending_results[err.id] = {"error": err.error.model_dump()}
                event.set()
            else:
                logging.error(f"{self.logging_prefix}Unhandled JSON-RPC error: {err.error}")
            
    def register_method(self, name: str, func: Callable[[Any, RPCSessionHandler], Any]) -> None:
        logging.debug(f"{self.logging_prefix}Registering method: {name}")
        self._methods[name] = func

    def unregister_method(self, name: str) -> None:
        logging.debug(f"{self.logging_prefix}Unregistering method: {name}")
        self._methods.pop(name, None)

    @staticmethod
    def _ping(params: Any, handler: "RPCSessionHandler") -> Any:
        """Simple health check method."""
        return {"pong": params}
