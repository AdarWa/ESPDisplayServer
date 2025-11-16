import logging
from protocol.mqtt import MQTT
from rpc.rpc_handler import RPCHandler
from storage.session_manager import SessionManager


class SessionHandler:
    """
    Minimal session handshake. Devices publish a JSON message to
    `espdisplay/subscribe` and get back a `subscribe_reply` with a new uuid.
    """

    def __init__(self, client: MQTT):
        SessionManager().init()
        self.client = client
        self.client.subscribe("espdisplay/subscribe", self.on_subscribe, json_payload=True)
    
    def on_subscribe(self, payload):
        if not isinstance(payload, dict):
            logging.warning("Subscribe payload was not JSON, ignoring")
            return
        uuid = SessionManager().get_free_session_id()
        logging.debug(f"Device asking to subscribe, handing out uuid {uuid}")
        SessionManager().add_session(uuid)
        reply = {
            "request_id": payload.get("request_id"),
            "type": "subscribe_reply",
            "uuid": uuid,
        }
        self.client.publish("espdisplay/broadcast", reply)
        RPCHandler().update_subscriptions()
