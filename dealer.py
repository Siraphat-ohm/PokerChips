from machine import Pin, ADC
import time
import network
from config import (
    WIFI_SSID, WIFI_PASS,
    MQTT_BROKER, MQTT_USER, MQTT_PASS,
    TOPIC_PREFIX
)
from umqtt.simple import MQTTClient
import ssd1306
from machine import SoftI2C
import ssd1306
from time import sleep

# using default address 0x3C
i2c = SoftI2C(sda=Pin(48), scl=Pin(47))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
RED_GPIO = 42
YELLOW_GPIO = 41
GREEN_GPIO = 40
LDR_GPIO = 4
TOPIC_LIGHT = f'{TOPIC_PREFIX}/light'
TOPIC_LED_RED = f'{TOPIC_PREFIX}/led/red'
TOPIC_BIGBLIND = f'{TOPIC_PREFIX}/bigblind'
TOPIC_POD = f'{TOPIC_PREFIX}/pod'
keypad = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]
listgamestart=[0,0]

# Define row and column pins
row_pins = [Pin(15, Pin.OUT),Pin(16, Pin.OUT),Pin(17, Pin.OUT),Pin(18, Pin.OUT)]
col_pins = [Pin(8, Pin.IN, Pin.PULL_DOWN),Pin(3, Pin.IN, Pin.PULL_DOWN),Pin(46, Pin.IN, Pin.PULL_DOWN),Pin(9, Pin.IN, Pin.PULL_DOWN)]

def scan_keypad():
    ans =""
    while amount != "D":
        for row_index, row in enumerate(row_pins):
            row.value(1)  # Set current row HIGH
            for col_index, col in enumerate(col_pins):
                if col.value() == 1:  # If column is HIGH, key is pressed
                    amount = keypad[row_index][col_index]
                    sleep(0.3)  # Debounce delay
            row.value(0)  # Reset row to LOW
        ans = ans + amount
    return ans
        
        

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
    mqtt.subscribe(TOPIC_LED_RED)
    print('MQTT broker connected.')


def games_start():
    text =['Enter big blind amount','Enter pod']
    for i in range (2):
        display.fill(0)
        display.show()
        ans =""
        amount =""
        while amount != "D":
            amount =""
            display.text(text[i], 0, 0, 1)
            display.text(ans, 10, 10, 1)
            display.show()
            for row_index, row in enumerate(row_pins):
                row.value(1)  # Set current row HIGH
                for col_index, col in enumerate(col_pins):
                    if col.value() == 1:  # If column is HIGH, key is pressed
                        amount = keypad[row_index][col_index]
                        sleep(0.3)  # Debounce delay
                row.value(0)  # Reset row to LOW
            ans = ans + amount
        listgamestart[i] = ans
        print('round done')
        

        
games_start()
    

def mqtt_callback(topic, payload):
    if topic.decode() == TOPIC_LED_RED:
        try:
            red.value(int(payload))
        except ValueError:
            pass


red = Pin(RED_GPIO, Pin.OUT)
ldr = ADC(Pin(LDR_GPIO), atten=ADC.ATTN_11DB)
wifi = network.WLAN(network.STA_IF)
mqtt = MQTTClient(client_id='',
                  server=MQTT_BROKER,
                  user=MQTT_USER,
                  password=MQTT_PASS)
connect_wifi()
connect_mqtt()
last_publish = 0



while True:
    # check for incoming subscribed topics
    mqtt.check_msg()
    mqtt.publish(TOPIC_BIGBLIND, listgamestart[0])
    mqtt.publish(TOPIC_POD, listgamestart[1])

    # publish light value periodically (without using sleep)
    now = time.ticks_ms()
    if now - last_publish >= 2000:
        level = 100 - int(ldr.read()*100/4095)
        print(f'Publishing light value: {level}')
        mqtt.publish(TOPIC_LIGHT, str(level))
        last_publish = now
