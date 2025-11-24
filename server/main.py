import os
if os.path.exists("local.env"):
    ENV_FILE = "local.env"
elif os.path.exists("prod.env"):
    ENV_FILE = "prod.env"
elif os.path.exists(".env"):
    ENV_FILE = ".env"
else:
    ENV_FILE = None

import asyncio
import logging
import time
from dotenv import load_dotenv
from protocol.mqtt import MQTT
from rpc.rpc_handler import RPCHandler
from protocol.session_handler import SessionHandler
from state_scheduler.state_scheduler import StateScheduler

load_dotenv(ENV_FILE)

MQTT_SERVER = os.environ.get("MQTT_SERVER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("MQTT_USER")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")

BASE_API_URL = os.environ.get("BASE_API_URL")
LONG_LIVED_TOKEN = os.environ.get("LONG_LIVED_TOKEN")

assert BASE_API_URL, "BASE_API_URL is a required environment field!"
assert LONG_LIVED_TOKEN, "LONG_LIVED_TOKEN is a required environment field!"

BASE_LOGGING_LEVEL = os.environ.get("BASE_LOGGING_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, BASE_LOGGING_LEVEL),  # Minimum log level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    datefmt="%Y-%m-%d %H:%M:%S",  # Timestamp format
)


def main():
    logging.info(f"Starting ESP Display Server on MQTT({MQTT_SERVER}:{MQTT_PORT})")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = MQTT(MQTT_SERVER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD)
    logging.info("Started MQTT client")

    SessionHandler(client)
    RPCHandler().init(client)
    RPCHandler().update_subscriptions()
    logging.info("Started Session Handler")

    StateScheduler(BASE_API_URL, LONG_LIVED_TOKEN).start()
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info("Shutting Down...")
        client.stop()


if __name__ == "__main__":
    main()
