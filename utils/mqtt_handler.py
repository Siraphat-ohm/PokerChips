import time

from umqtt.simple import MQTTClient


class MQTTHandler:

    def __init__(self, broker: str, user: str, password: str, client_id="", ssl=False):
        self.broker = broker
        self.user = user
        self.password = password
        self.client_id = client_id
        self.ssl = ssl
        self.client = None
        self.topics = []
        self.connected = False

    def connect(self, callback=None):
        print(f"Connecting to MQTT broker at {self.broker}...")
        self.client = MQTTClient(
            self.client_id,
            self.broker,
            user=self.user,
            password=self.password,
            ssl=self.ssl,
        )
        self.client.connect()
        self.connected = True
        print("MQTT connected.\n")

        if callback:
            self.client.set_callback(callback)

    def subscribe(self, topic: str):
        if not self.connected:
            raise RuntimeError("You must connect to MQTT before subscribing.")
        self.client.subscribe(topic)
        self.topics.append(topic)
        print(f"Subscribed to topic: {topic}")

    def subscribe_multiple(self, topics: list):
        for t in topics:
            self.subscribe(t)

    def check_messages(self):
        if self.connected:
            self.client.check_msg()

    def publish(self, topic: str, message: str):
        if self.connected:
            self.client.publish(topic, message)

    def disconnect(self):
        if self.connected:
            self.client.disconnect()
            self.connected = False
            print("MQTT disconnected.")


def mqtt_callback(topic_bytes, payload_bytes):
    topic_str = topic_bytes.decode().strip()
    payload_str = payload_bytes.decode().strip()

    if topic_str.endswith("bigblind"):
        print(f"[Callback] Big Blind value received: {payload_str}")

    elif topic_str.endswith("money"):
        print(f"[Callback] Money value received: {payload_str}")

    elif topic_str.endswith("player"):
        print(f"[Callback] Player info received: {payload_str}")

    else:
        print(f"[Callback] Unknown topic {topic_str} with payload: {payload_str}")
