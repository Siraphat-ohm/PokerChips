import time
import ujson
from machine import Pin
from mqtt_handler import MQTTHandler, mqtt_callback, shared_data
from wifi_handler import WiFiHandler
from player import I2CMultiplexer, Player
import shared_mqtt
import const
from poker import PokerGame
from config import MQTT_BROKER, MQTT_PASS, MQTT_USER, TOPIC_PREFIX, WIFI_PASS, WIFI_SSID

TOPICS = ["/setting_table","/awards"]
players = []

def awards(timeout=300):
    print("Waiting for 'awards' data...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        shared_mqtt.check_messages()
        if "awards" in shared_data:
            try:
                data = ujson.loads(shared_data["awards"])
                for p, m in zip(players, data):
                    if m > 0:
                        print(f"Player {p.channel} wins +{m}")
                        p.money += m
                del shared_data["awards"]
                return
            except ValueError:
                print("Invalid JSON for awards. Ignoring this message.")
                del shared_data["awards"]
        time.sleep(0.25)
    print("No awards message received within the timeout.")


if __name__ == "__main__":
    wifi = WiFiHandler(WIFI_SSID, WIFI_PASS)
    wifi.connect()

    client = shared_mqtt.init_mqtt()
    multiplexer = I2CMultiplexer(const.SCL_PIN, const.SDA_PIN)
    player_remain = [1,2,3,4]
    print("Remaining Players:", player_remain)
    shared_mqtt.publish_message(TOPIC_PREFIX + "/players_remain", str(player_remain))
    player_bet = [1000,1000,1000,1000]
    print("Players Bet:", player_bet)
    shared_mqtt.publish_message(TOPIC_PREFIX + "/players_bet", str(player_bet))

    for t in TOPICS:
        topic = TOPIC_PREFIX + t  
        shared_mqtt.subscribe_to_topic(topic)

    try:
        for conf in const.PLAYER_CONFIG:
            print(conf)
            players.append(Player(multiplexer, conf['channel'], conf['joystick_pins']))
        awards()
    except KeyboardInterrupt:
        pass

    finally:
        shared_mqtt.disconnect_mqtt()
        print("Finished.")