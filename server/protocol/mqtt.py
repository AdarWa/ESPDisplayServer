import json
import logging
import time
from typing import Any, Callable, Dict, Tuple

import paho.mqtt.client as mqtt
from pydantic import BaseModel


class MQTT:
    def __init__(
        self, address: str, port=1883, username=None, password=None, timeout=5
    ):
        self.client = mqtt.Client()
        self.client.username_pw_set(username, password)
        self.client.on_message = self.on_msg
        self.subscribers: Dict[str, Tuple[Callable[[Any], None], bool]] = {}
        self.client.connect(address, port, 60)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()

    def on_msg(self, client, userdata, msg):
        logging.debug(f"Got message on topic {msg.topic}, {msg.payload}")
        if msg.topic not in self.subscribers:
            return

        callback, json_payload = self.subscribers[msg.topic]
        try:
            payload: Any = msg.payload
            if json_payload:
                payload = json.loads(msg.payload.decode("utf-8"))
            callback(payload)
        except Exception as e:
            logging.exception(
                f"Error in MQTT message callback for topic {msg.topic}: {e}"
            )

    def subscribe(
        self, topic: str, callback: Callable[[Any], None], json_payload: bool = False
    ):
        logging.debug(
            f"Client subscribed on topic {topic} with json_payload={json_payload}"
        )
        self.client.subscribe(topic)
        self.subscribers[topic] = (callback, json_payload)

    def publish(self, topic: str, payload: Any):
        logging.debug(f"client published on topic {topic}")
        formatted = self._format_payload(payload)
        self.client.publish(topic, formatted)

    def _format_payload(self, payload: Any) -> Any:
        if isinstance(payload, BaseModel):
            return payload.model_dump_json()
        if isinstance(payload, (dict, list)):
            return json.dumps(payload)
        if isinstance(payload, str):
            return payload
        if isinstance(payload, (bytes, bytearray)):
            return payload
        return str(payload)
