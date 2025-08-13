import logging
import time

from protocol.mqtt import MQTT
from protocol.rpc_handler import RPCHandler
from protocol.session_handler import SessionHandler
logging.basicConfig(
    level=logging.DEBUG,  # Minimum log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    datefmt="%Y-%m-%d %H:%M:%S"  # Timestamp format
)

def main():
    logging.info("Starting ESP Display Server")
    client = MQTT("mosquitto", 1883)
    logging.info("Started MQTT client")
    sessions = SessionHandler(client)
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