ENV_FILE = "local.env"

import json
import logging
import os
import threading
from dotenv import load_dotenv
import uuid
from typing import Any, Callable, Dict, Optional

from protocol.mqtt import MQTT
from rpc.rpc_protocol import make_error, make_request, make_response, deserialize
from rpc.rpc_models import JSONRPCRequest, JSONRPCMessage


class TestClient:
    """
    Minimal test client that acts like a device.
    - Performs the subscribe handshake to get a uuid
    - Calls server RPC methods via espdisplay/{uuid}/client
    - Registers simple device methods the server can invoke
    """

    def __init__(
        self,
        address: str = "localhost",
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        handshake_timeout: float = 5.0,
        default_timeout: float = 5.0,
        uuid: int = -1,
    ) -> None:
        self.default_timeout = default_timeout
        self._pending_events: Dict[str, threading.Event] = {}
        self._pending_results: Dict[str, Any] = {}
        self._methods: Dict[str, Callable[[Any], Any]] = {}

        self.client = MQTT(address, port, username, password)
        if uuid > -1:
            self.uuid = uuid
        else:
            self.uuid = self._handshake(handshake_timeout)

        # listen for responses and server->device calls
        self.client.subscribe(f"espdisplay/{self.uuid}/server", self._on_message)
        self.register_method("echo", self._echo)
        logging.info(f"[TestClient {self.uuid}] Ready")

    # -------- public helpers --------
    def call_server(
        self, method: str, params: Any, timeout: Optional[float] = None
    ) -> Any:
        logging.debug(
            f"[TestClient {self.uuid}] Calling server method {method} with params={params}"
        )
        req = make_request(method, params)
        event = threading.Event()
        self._pending_events[req.id] = event

        self.client.publish(f"espdisplay/{self.uuid}/client", req)
        wait_for = timeout if timeout is not None else self.default_timeout
        if not event.wait(wait_for):
            self._cleanup_pending(req.id)
            raise TimeoutError(f"RPC call={method} timed out after {wait_for} seconds")

        result = self._pending_results.pop(req.id, None)
        self._pending_events.pop(req.id, None)
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(f"JSON-RPC error {result['error']}")
        return result

    def register_method(self, name: str, func: Callable[[Any], Any]) -> None:
        logging.debug(f"[TestClient {self.uuid}] Registering device method {name}")
        self._methods[name] = func

    def stop(self) -> None:
        logging.info(f"[TestClient {self.uuid}] Stopping client")
        self.client.stop()

    # -------- MQTT callbacks --------
    def _on_message(self, payload: Any) -> None:
        try:
            msg: JSONRPCMessage = deserialize(payload)
        except Exception as exc:
            logging.error(f"[TestClient {self.uuid}] Invalid JSON-RPC payload: {exc}")
            return

        if msg.request:
            self._handle_request(msg.request)
        elif msg.result:
            event = self._pending_events.get(msg.result.id)
            if event:
                self._pending_results[msg.result.id] = msg.result.result
                event.set()
            else:
                logging.warning(
                    f"[TestClient {self.uuid}] Received response for unknown id {msg.result.id}"
                )
        elif msg.error:
            err = msg.error
            event = self._pending_events.get(err.id) if err.id else None
            if event and err.id is not None:
                self._pending_results[err.id] = {"error": err.error.model_dump()}
                event.set()
            else:
                logging.error(f"[TestClient {self.uuid}] Unhandled error: {err.error}")

    def _handle_request(self, req: JSONRPCRequest) -> None:
        logging.debug(f"[TestClient {self.uuid}] Handling server request {req.method}")
        if req.method not in self._methods:
            resp = make_error(f"Unknown method {req.method}", id=req.id, code=-32601)
        else:
            try:
                result = self._methods[req.method](req.params)
                resp = make_response(result, id=req.id)
            except Exception as exc:
                resp = make_error(
                    "Internal error", id=req.id, code=-32603, data=str(exc)
                )
        self.client.publish(f"espdisplay/{self.uuid}/client", resp)

    # -------- handshake --------
    def _handshake(self, timeout: float) -> int:
        request_id = f"req-{uuid.uuid4()}"
        event = threading.Event()
        assigned_uuid: Optional[int] = None

        def on_broadcast(payload: Any) -> None:
            nonlocal assigned_uuid
            try:
                data = payload if isinstance(payload, dict) else json.loads(payload)
                if (
                    data.get("request_id") == request_id
                    and data.get("type") == "subscribe_reply"
                ):
                    assigned_uuid = int(data["uuid"])
                    event.set()
            except Exception as exc:
                logging.error(f"Failed to parse broadcast payload: {exc}")

        self.client.subscribe("espdisplay/broadcast", on_broadcast, json_payload=True)
        self.client.publish("espdisplay/subscribe", {"request_id": request_id})

        if not event.wait(timeout):
            raise TimeoutError("Timed out waiting for subscribe_reply from server")
        logging.info(f"[TestClient] Received uuid {assigned_uuid} from server")
        return int(assigned_uuid) if assigned_uuid is not None else -1

    # -------- default device methods --------
    @staticmethod
    def _echo(params: Any) -> Any:
        return {"echo": params}

    def _cleanup_pending(self, req_id: str) -> None:
        self._pending_events.pop(req_id, None)
        self._pending_results.pop(req_id, None)


def main():
    load_dotenv(ENV_FILE)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    mqtt_server = os.environ.get("MQTT_SERVER", "localhost")
    mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))
    mqtt_user = os.environ.get("MQTT_USER")
    mqtt_password = os.environ.get("MQTT_PASSWORD")
    uuid = input("input uuid to use(leave empty to handshake): ")
    if uuid:
        uuid = int(uuid)
    else:
        uuid = -1
    client = TestClient(
        address=mqtt_server,
        port=mqtt_port,
        username=mqtt_user,
        password=mqtt_password,
        uuid=uuid,
    )

    try:
        _interactive_shell(client)
    except KeyboardInterrupt:
        logging.info("Exiting...")
    finally:
        client.stop()


def _interactive_shell(client: TestClient) -> None:
    print("Interactive RPC test client")
    print("Commands:")
    print(
        '  call <method> <json_params>   - Call server method, e.g. call ping {"hello":"world"}'
    )
    print(
        "  register <name> <json_reply>  - Register device method that returns given JSON reply"
    )
    print("  list                          - List registered device methods")
    print("  help                          - Show this help")
    print("  quit/exit                     - Stop client")
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if not line:
            continue

        if line.lower() in {"quit", "exit"}:
            break
        if line.lower() in {"help", "h", "?"}:
            print("call <method> <json_params>")
            print("register <name> <json_reply>")
            print("list")
            print("quit/exit")
            continue
        if line.startswith("call "):
            parts = line.split(" ", 2)
            if len(parts) < 3:
                print("Usage: call <method> <json_params>")
                continue
            method, raw_params = parts[1], parts[2]
            try:
                params = json.loads(raw_params)
            except json.JSONDecodeError as exc:
                print(f"Invalid JSON for params: {exc}")
                continue
            try:
                result = client.call_server(method, params)
                print(f"Result: {result}")
            except Exception as exc:
                print(f"Error: {exc}")
            continue
        if line.startswith("register "):
            parts = line.split(" ", 2)
            if len(parts) < 3:
                print("Usage: register <name> <json_reply>")
                continue
            name, raw_reply = parts[1], parts[2]
            try:
                reply_data = json.loads(raw_reply)
            except json.JSONDecodeError as exc:
                print(f"Invalid JSON for reply: {exc}")
                continue

            def handler(params, data=reply_data):
                return data

            client.register_method(name, handler)
            print(f"Registered device method '{name}' returning: {reply_data}")
            continue
        if line == "list":
            if not client._methods:
                print("No device methods registered")
            else:
                print("Device methods:")
                for key in client._methods:
                    print(f"  - {key}")
            continue

        print("Unknown command. Type 'help' for options.")


if __name__ == "__main__":
    main()
