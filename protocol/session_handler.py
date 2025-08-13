import logging
from protocol.messages.MessageBase import RequestType
from protocol.mqtt import MQTT
from protocol.messages.SubscribeMessage import SubscribeMessage, SubscribeReply
from protocol.rpc_handler import RPCHandler
from storage.models.Sessions import Session
from storage.session_manager import SessionManager

class SessionHandler:
    def __init__(self, client: MQTT):
        SessionManager().init()
        self.client = client
        self.client.subscribe("espdisplay/subscribe", self.on_subscribe, SubscribeMessage)
    
    def on_subscribe(self, msg: SubscribeMessage):
        uuid = SessionManager().get_free_session_id()
        logging.debug(f"Device asking to subscribe, handing out uuid {uuid}")
        SessionManager().add_session(Session(uuid=uuid))
        self.client.publish("espdisplay/broadcast", SubscribeReply(request_id=msg.request_id, request_type=RequestType.SUBSCRIBE_REPLY, uuid=uuid))
        RPCHandler().update_subscriptions()
        