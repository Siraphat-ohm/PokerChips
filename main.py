#setup MQTT =======================================================
import time
import const
from machine import Pin
from player import I2CMultiplexer, Player
from poker import PokerGame
import network
from config import (
    WIFI_SSID, WIFI_PASS,
    MQTT_BROKER, MQTT_USER, MQTT_PASS,
    TOPIC_PREFIX
)
from umqtt.simple import MQTTClient
TOPIC_BIGBLIND = f'{TOPIC_PREFIX}/bigblind'
TOPIC_MONEY = f'{TOPIC_PREFIX}/money'
TOPIC_PLAYER = f'{TOPIC_PREFIX}/player'

def connect_wifi():
    mac = ':'.join(f'{b:02X}' for b in wifi.config('mac'))
    print(f'WiFi MAC address is {mac}')
    wifi.active(True)
    print(f'Connecting to WiFi {WIFI_SSID}.')
    wifi.connect(WIFI_SSID, WIFI_PASS)
    while not wifi.isconnected():
        print('.', end='')
        time.sleep(0.5)
    print('\nWiFi connected.')

def connect_mqtt():
    print(f'Connecting to MQTT broker at {MQTT_BROKER}.')
    mqtt.connect()
    mqtt.set_callback(mqtt_callback)
    mqtt.subscribe(TOPIC_BIGBLIND)
    mqtt.subscribe(TOPIC_MONEY)
    mqtt.subscribe(TOPIC_PLAYER)
    print('MQTT broker connected.')

multiplexer = I2CMultiplexer(const.SCL_PIN, const.SDA_PIN)

bb,sb='',''
money =''

def mqtt_callback(topic, payload):
    global bb,money
    topic_str = topic.decode()
    payload_str = payload.decode().strip()
    if topic_str == TOPIC_BIGBLIND:
        try:
            bb = payload_str
            print(f"Big Blind value received: {bb}")
        except ValueError:
            print(f"Invalid Big Blind value received: {payload_str}")
    if topic_str == TOPIC_MONEY:
        try:
            money = payload_str
            print(f"Big Blind value received: {money}")
        except ValueError:
            print(f"Invalid Big Blind value received: {payload_str}")
            
wifi = network.WLAN(network.STA_IF)
mqtt = MQTTClient(client_id='',
                  server=MQTT_BROKER,
                  user=MQTT_USER,
                  password=MQTT_PASS)
connect_wifi()
connect_mqtt()
last_publish = 0

check = True
while check == True:
    mqtt.check_msg()
    if money:
        check = False

money=int(money)
bb=int(bb)
#=================================================================

multiplexer = I2CMultiplexer(const.SCL_PIN, const.SDA_PIN)
game = PokerGame(money=10000, multiplexer=multiplexer, sb=10, bb=20)

for conf in const.PLAYER_CONFIG:
    print(conf)
    game.add_player(Player(multiplexer, conf['channel'], conf['joystick_pins']))
    
game.run_full_game()


