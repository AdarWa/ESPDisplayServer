import logging
import os
import time
from dotenv import load_dotenv
from protocol.mqtt import MQTT
from rpc.rpc_handler import RPCHandler
from protocol.session_handler import SessionHandler

load_dotenv()

MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")

logging.basicConfig(
    level=logging.DEBUG,  # Minimum log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    datefmt="%Y-%m-%d %H:%M:%S"  # Timestamp format
)

def main():
    logging.info("Starting ESP Display Server")
    client = MQTT("192.168.1.32", 1883, MQTT_USER, MQTT_PASSWORD)
    logging.info("Started MQTT client")
    SessionHandler(client)
    RPCHandler().init(client)
    RPCHandler().update_subscriptions()
    logging.info("Started Session Handler")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info("Shutting Down...")
        client.stop()

if __name__ == "__main__":
    main()