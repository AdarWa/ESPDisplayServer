from mqtt import MQTT

class SessionHandler:
    def __init__(client: MQTT):
        client.subscribe("/espdisplay/subscribe", )