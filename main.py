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

TOPICS = ["/setting_table"]

def wait_for_setting_table():
    print("Waiting for 'setting_table' data...")

    while True:
        shared_mqtt.check_messages()
        if "setting_table" in shared_data:
            try:
                data = ujson.loads(shared_data["setting_table"])
                shared_data["setting_table"] = data 
                return data
            except ValueError:
                print("Invalid JSON for setting_table. Ignoring this message.")
                del shared_data["setting_table"]
        time.sleep(0.25)

if __name__ == "__main__":
    wifi = WiFiHandler(WIFI_SSID, WIFI_PASS)
    wifi.connect()
    sb,bb = 0, 0
    money = 0

    client = shared_mqtt.init_mqtt()

    for t in TOPICS:
        topic = TOPIC_PREFIX + t  
        shared_mqtt.subscribe_to_topic(topic)

    try:
        data = wait_for_setting_table()

        bb = data[0]
        sb = bb // 2
        money = data[1]
        print("Big blind:", bb, "Small blind:", sb, "Money:", money)
        multiplexer = I2CMultiplexer(const.SCL_PIN, const.SDA_PIN)
        game = PokerGame(money=money, multiplexer=multiplexer, sb=sb, bb=bb)
        shared_mqtt.publish_message(TOPIC_PREFIX+f"/player","2")
        for conf in const.PLAYER_CONFIG:
            print(conf)
            game.add_player(Player(multiplexer, conf['channel'], conf['joystick_pins']))
        
        game.run_full_game()

    except KeyboardInterrupt:
        pass

    finally:
        shared_mqtt.disconnect_mqtt()
        print("Finished.")

