import logging
from typing import List
from protocol.mqtt import MQTT
from storage.session_manager import SessionManager
from utils.utils import singleton

class RPCSessionHandler:
    def __init__(self, uuid: int) -> None:
        self.uuid = uuid
    
    def callback(self, msg):
        logging.debug(f"RPC Session Handler with uuid {self.uuid} received {msg}")
    
    

@singleton
class RPCHandler:
    instance = None

    def init(self,client: MQTT):
        self.client = client
        self.handlers: List[RPCSessionHandler] = []

    def update_subscriptions(self):
        for session in SessionManager().get_sessions().sessions:
            uuid = session.uuid
            handler = self.find_handler(uuid)
            self.client.subscribe(f"espdisplay/{uuid}/client", handler.callback)
    
    def handler_exists(self, uuid: int) -> bool:
        return uuid in [handler.uuid for handler in self.handlers]
    
    def find_handler(self, uuid: int) -> RPCSessionHandler:
        for handler in self.handlers:
            if handler.uuid == uuid:
                return handler
        return RPCSessionHandler(uuid)


