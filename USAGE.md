# ESP Display Server - Quick Usage

## Start the server
- Install deps: `pip install -e .`
- Set MQTT env vars (optional): `MQTT_SERVER`, `MQTT_PORT`, `MQTT_USER`, `MQTT_PASSWORD`
- Run: `python main.py`

## Device session handshake
- Publish to `espdisplay/subscribe` with JSON:
  ```json
  { "request_id": "req-1" }
  ```
- Server replies on `espdisplay/broadcast`:
  ```json
  { "request_id": "req-1", "type": "subscribe_reply", "uuid": 0 }
  ```
- Use the returned `uuid` for all RPC topics below.

## JSON-RPC over MQTT topics
- Server → Device requests: publish to `espdisplay/{uuid}/server`
- Device → Server requests: publish to `espdisplay/{uuid}/client`
- Both sides listen on their opposite topic for responses/errors.

### Example: device calling server `ping`
- Device publishes to `espdisplay/{uuid}/client`:
  ```json
  { "jsonrpc": "2.0", "method": "ping", "params": { "hello": "world" }, "id": "1" }
  ```
- Server responds on `espdisplay/{uuid}/server`:
  ```json
  { "jsonrpc": "2.0", "result": { "pong": { "hello": "world" } }, "id": "1" }
  ```

## Storage layout
- Files live under `esp_storage/` (created automatically).
- Sessions are stored in `esp_storage/sessions.json` as a list of UUIDs.

## Using the modules directly
- Bootstrap (server-side):
  ```python
  from protocol.mqtt import MQTT
  from protocol.session_handler import SessionHandler
  from rpc.rpc_handler import RPCHandler

  client = MQTT("localhost", 1883)
  SessionHandler(client)
  RPCHandler().init(client)
  RPCHandler().update_subscriptions()
  ```
- Publish/subscribe with MQTT helper:
  ```python
  client.subscribe("espdisplay/subscribe", lambda payload: print(payload), json_payload=True)
  client.publish("espdisplay/broadcast", {"hello": "world"})
  ```
- JSON-RPC from server to device:
  ```python
  handler = RPCHandler().get_handler(uuid)
  result = handler.call("ping", {"hello": "world"})
  print(result)  # {"pong": {"hello": "world"}}
  ```
- Storage helper:
  ```python
  from storage.storage_manager import storage

  storage.write_json("sessions.json", {"sessions": [0, 1]})
  sessions = storage.read_json("sessions.json")
  ```
