import paho.mqtt.client as mqtt
import time
import logging
from pydantic import BaseModel

class MQTT:
    def __init__(self, address, port, username="", password="", timeout=5):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if username and password:
            self.client.username_pw_set(username, password)
        self.client.on_message = self.on_msg
        self.subscribers = {}
        self.client.connect(address, port, 60)
        start = time.time()
        while not self.client.is_connected and time.time()-start > timeout:
            time.sleep(10)
        if time.time()-start > timeout:
            logging.warning("Timeout while connecting to MQTT")
            self.client.disconnect()
    
    def on_msg(self,client, userdata, msg):
        if msg.topic in self.subscribers.keys():
            callback, model_type = self.subscribers[msg.topic]
            callback(model_type.model_validate_json(msg.payload))
            
    
    def subscribe(self,topic, callback, model_type):
        self.client.subscribe(topic)
        self.subscribe[topic] = (callback, model_type)
        
    def publish(self, topic, payload_model: BaseModel):
        self.client.publish(topic, payload_model.model_dump_json())