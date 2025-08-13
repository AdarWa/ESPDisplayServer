import paho.mqtt.client as mqtt
import time
import logging
from pydantic import BaseModel, ValidationError

class MQTT:
    def __init__(self, address: str, port = 1883, username="", password="", timeout=5):
        self.client = mqtt.Client()
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
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
    
    def on_msg(self,client, userdata, msg):
        logging.debug(f"Got message on topic {msg.topic}, {msg.payload}")
        if msg.topic in self.subscribers.keys():
            callback, model_type = self.subscribers[msg.topic]
            logging.debug("Calling callback...")
            try:
                if model_type is None:
                    callback(msg.payload)
                else:
                    callback(model_type.model_validate_json(msg.payload))
            except ValidationError as e:
                logging.exception("Validation error in json model: " + str(e))
            
    
    def subscribe(self,topic, callback, model_type = None):
        logging.debug(f"Client subscribed on topic {topic} with model {model_type}")
        self.client.subscribe(topic)
        self.subscribers[topic] = (callback, model_type)
        
    def publish(self, topic, payload_model: BaseModel):
        logging.debug(f"client published on topic {topic}")
        self.client.publish(topic, payload_model.model_dump_json())