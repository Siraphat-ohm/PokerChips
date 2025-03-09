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

def detect_player(multiplexer):

    players = []
    for config in const.PLAYER_CONFIG:
        channel = config["channel"]
        joystick_pins = config["joystick_pins"]

        multiplexer.select_channel(channel)
        time.sleep(0.01)  

        devices = multiplexer.i2c.scan()

        if const.I2C_ADDR in devices:
            devices.remove(const.I2C_ADDR)

        if devices:
            player = Player(multiplexer, channel, joystick_pins)
            players.append(player)
    return players

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

    client = shared_mqtt.init_mqtt()

    for t in TOPICS:
        topic = TOPIC_PREFIX + t  
        shared_mqtt.subscribe_to_topic(topic)

    try:
#         data = wait_for_setting_table()
#         bb = data[0]
#         sb, money =   bb // 2, data[1]
        bb, sb, money = 50, 25, 500
        print("[SETTINGS]","Big blind:", bb, "Small blind:", sb, "Money:", money)
        multiplexer = I2CMultiplexer(const.SCL_PIN, const.SDA_PIN)
        game = PokerGame(money=money, multiplexer=multiplexer, sb=sb, bb=bb)
        players = detect_player(multiplexer)
        for p in players:
            game.add_player(p)
#         for conf in const.PLAYER_CONFIG:
#             print(conf)
#             game.add_player(Player(multiplexer, conf['channel'], conf['joystick_pins']))
        shared_mqtt.publish_message(TOPIC_PREFIX+f"/player",str(len(game.players)))
        game.give_money()
        game.clear_screen_players()
        while len([p for p in game.players if p.money > 0 ]) > 1:
            print("\nStarting a new hand...")
            game.run_full_game()
            game.clean_up_for_next_hand()
            game.players = [p for p in game.players if p.money > 0]
            print("Remaining players:", len(game.players))
            time.sleep(2)
            
        if game.players:
            winner = game.players[0]
            print(f"\nTournament Winner: Player on channel {winner.channel} ({winner.position}) with ${winner.money}")
    except KeyboardInterrupt:
        pass

    finally:
        shared_mqtt.disconnect_mqtt()
        print("Finished.")
