from typing import List
from protocol.mqtt import MQTT
from storage.session_manager import SessionManager
from utils.utils import singleton
from rpc.rpc_session_handler import RPCSessionHandler

@singleton
class RPCHandler:
    def init(self, client: MQTT, default_timeout: float = 5.0):
        self.client = client
        self.default_timeout = default_timeout
        self.handlers: List[RPCSessionHandler] = []

    def update_subscriptions(self):
        # make sure every session has a handler
        for uuid in SessionManager().list_sessions():
            if not self.handler_exists(uuid):
                handler = RPCSessionHandler(uuid, self.client, default_timeout=self.default_timeout)
                self.handlers.append(handler)

    def handler_exists(self, uuid: int) -> bool:
        return any(h.uuid == uuid for h in self.handlers)

    def get_handler(self, uuid: int) -> RPCSessionHandler:
        for h in self.handlers:
            if h.uuid == uuid:
                return h
        raise ValueError(f"No RPC handler for uuid {uuid}")