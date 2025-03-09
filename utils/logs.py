import shared_mqtt
from config import MQTT_BROKER, MQTT_PASS, MQTT_USER, TOPIC_PREFIX, WIFI_PASS, WIFI_SSID

client = shared_mqtt.init_mqtt()
def log(text, TOPIC="/logs"):
    print(text)
    shared_mqtt.publish_message(TOPIC_PREFIX + TOPIC, text)