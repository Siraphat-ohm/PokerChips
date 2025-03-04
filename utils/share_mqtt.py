import time

from mqtt_handler import MQTTHandler, mqtt_callback

from config import MQTT_BROKER, MQTT_PASS, MQTT_USER, TOPIC_PREFIX

mqtt_client = None


def init_mqtt():
    global mqtt_client

    if mqtt_client is not None:
        return mqtt_client

    mqtt_client = MQTTHandler(
        broker=MQTT_BROKER,
        user=MQTT_USER,
        password=MQTT_PASS,
        client_id="shared_mqtt_client",
    )
    mqtt_client.connect(callback=mqtt_callback)

    print("[shared_mqtt] MQTT client connected and ready.")
    return mqtt_client


def subscribe_to_topic(topic_suffix):
    global mqtt_client
    if mqtt_client is None:
        raise RuntimeError("MQTT client not initialized. Call init_mqtt() first.")
    full_topic = f"{TOPIC_PREFIX}{topic_suffix}"
    mqtt_client.subscribe(full_topic)


def publish_message(topic_suffix, message):
    global mqtt_client
    if mqtt_client is None:
        raise RuntimeError("MQTT client not initialized. Call init_mqtt() first.")
    full_topic = f"{TOPIC_PREFIX}{topic_suffix}"
    mqtt_client.publish(full_topic, message)


def check_messages():
    global mqtt_client
    if mqtt_client:
        mqtt_client.check_messages()


def disconnect_mqtt():
    global mqtt_client
    if mqtt_client:
        mqtt_client.disconnect()
        mqtt_client = None
        print("[shared_mqtt] MQTT client disconnected.")
