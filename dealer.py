from machine import Pin, ADC
import time
from time import sleep
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



# using default address 0x3C
i2c = SoftI2C(sda=Pin(48), scl=Pin(47))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
TOPIC_BIGBLIND = f'{TOPIC_PREFIX}/bigblind'
TOPIC_MONEY = f'{TOPIC_PREFIX}/money'
TOPIC_PLAYER = f'{TOPIC_PREFIX}/player'
keypad = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]
listgamestart=[0,0,0]

# Define row and column pins
row_pins = [Pin(15, Pin.OUT),Pin(16, Pin.OUT),Pin(17, Pin.OUT),Pin(18, Pin.OUT)]
col_pins = [Pin(8, Pin.IN, Pin.PULL_DOWN),Pin(3, Pin.IN, Pin.PULL_DOWN),Pin(46, Pin.IN, Pin.PULL_DOWN),Pin(9, Pin.IN, Pin.PULL_DOWN)]

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
    #mqtt.set_callback(mqtt_callback)
    print('MQTT broker connected.')
    
def pokerchippage():
    display.text("POKERCHIP", 25, 25,1)
    display.text("dealer", 35, 40, 1)
    display.show()
    
def noanspage():
    display.fill(0)
    display.text("NO ANSWER", 25, 25,1)
    display.show()
    sleep(1)
    display.fill(0)
    display.show()

def blankpage():
    display.fill(0)
    display.text("NOT ENOUGH MONEY FOR BIG BLIND", 0, 25,1)
    display.show()
    sleep(1)
    display.fill(0)
    display.show()

def games_start():
    pokerchippage()
    sleep(1.5)
    text =[' Enter bigblind',' Enter money',' Enter player']
    i=-1
    ll = False
    lastlist =[0,0,0]
    while any(x == 0 for x in listgamestart):
        i+=1
        display.fill(0)
        ans =""
        amount =""
        charlist =['A','B','C','D','#','*']
        check = True
        while check == True:
            amount =""
            display.text(str(i+1)+text[i], 0, 0, 1)
            display.text(">>"+ans, 0, 15, 1)
            display.text('D:Enter C:delete', 0, 55, 1)
            display.show()
            for row_index, row in enumerate(row_pins):
                row.value(1)  # Set current row HIGH
                for col_index, col in enumerate(col_pins):
                    if col.value() == 1:  # If column is HIGH, key is pressed
                        amount = keypad[row_index][col_index]
                        sleep(0.3)  # Debounce delay
                row.value(0)  # Reset row to LOW
            if amount not in charlist:
                ans = ans + amount
            if amount == "C":
                if ans =="":
                    if i >1:
                        i -=1
                ans = ans[0:len(ans)-1]
                display.fill(0)
            if amount == "D":
                sleep(0.5)
                try:
                    if int(ans) <=0:
                        ans =""
                        noanspage()
                except:
                    pass
                if ans == '':
                    ans =""
                    noanspage()
                else:
                    if i == 1:
                        if int(ans) < int(listgamestart[0]):
                            blankpage()
                            i=0
                            lastlist = [listgamestart[0],listgamestart[1],ans]
                            ans =""
                            ll =True
                            listgamestart[0] =0
                            listgamestart[1] =0
                            continue
                    check = False
                    print(i)
        listgamestart[i] = ans
        print('round done')
    display.fill(0)
    pokerchippage()
               
games_start()
    
def mqtt_callback(topic, payload):
    if topic.decode() == TOPIC_LED_RED:
        try:
            red.value(int(payload))
        except ValueError:
            pass

wifi = network.WLAN(network.STA_IF)
mqtt = MQTTClient(client_id='',
                  server=MQTT_BROKER,
                  user=MQTT_USER,
                  password=MQTT_PASS)
connect_wifi()
connect_mqtt()
last_publish = 0

mqtt.publish(TOPIC_BIGBLIND, str(int(listgamestart[0])))
mqtt.publish(TOPIC_MONEY, str(int(listgamestart[1])))
mqtt.publish(TOPIC_PLAYER, str(int(listgamestart[2])))



#while True:
#    mqtt.check_msg()
#if ans playerlastround player = [sd,sd,s,ds,] amount=[sd,sd,sd,sd,sd]

def arrangesidepot(amount,player):
    playernew = list()
    amountnew = list()
    pod = min(amount)
    for i in range(len(player)):
        new = amount[i] -pod
        if new != 0:
            playernew.append(player[i])
            amountnew.append(new)
    return playernew,amountnew
    
        
def whowin():
    check =True
    player=[1,2,4,5]
    amount=[100,200,200,300]
    anslist=list()
    anskey = ''
    different_count = len(set(amount))
    
    for i in range(different_count):
        check =True
        pod = min(amount)*len(player)
        display.fill(0)
        display.text('Who win pod('+str(i+1)+ "):" , 0, 0, 1)
        display.text("pod size: 202"+str(pod) , 0, 10, 1)
        for j in range(len(player)):
            display.text(str(j+1)+" Player"+str(player[j]) , 0, 10*(j+2), 1)
            anslist.append(str(j+1))
        display.show()
        while check == True:
            anskey = ''
            for row_index, row in enumerate(row_pins):
                row.value(1)  # Set current row HIGH
                for col_index, col in enumerate(col_pins):
                    if col.value() == 1:  # If column is HIGH, key is pressed
                        anskey = keypad[row_index][col_index]
                        sleep(0.3)  # Debounce delay
                row.value(0)  # Reset row to LOW
            if anskey !="" and anskey in anslist:
                print(anskey)
                player,amount = arrangesidepot(amount,player)
                check =False
                anslist = []
                

                
whowin()  

    

    
