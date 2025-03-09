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
import json



# using default address 0x3C
i2c = SoftI2C(sda=Pin(48), scl=Pin(47))
display = ssd1306.SSD1306_I2C(128, 64, i2c)
TOPIC_TEST = f'{TOPIC_PREFIX}/test'
TOPIC_SMALLBLIND = f'{TOPIC_PREFIX}/smallblind'
TOPIC_BIGBLIND = f'{TOPIC_PREFIX}/bigblind'
TOPIC_MONEY = f'{TOPIC_PREFIX}/money'
TOPIC_PLAYER = f'{TOPIC_PREFIX}/player'
TOPIC_POT = f'{TOPIC_PREFIX}/pot'
TOPIC_PLAYER_REMAIN = f'{TOPIC_PREFIX}/players_remain'
TOPIC_MONEY_ROUND = f'{TOPIC_PREFIX}/players_bet'
TOPIC_SETTINGTABLE = f'{TOPIC_PREFIX}/setting_table'
TOPIC_MONEYRESULT = f'{TOPIC_PREFIX}/awards'
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
    mqtt.subscribe(TOPIC_PLAYER)
    mqtt.subscribe(TOPIC_POT)
    mqtt.subscribe(TOPIC_PLAYER_REMAIN)
    mqtt.subscribe(TOPIC_MONEY_ROUND)
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
    
def arrangesidepot(playerremain,moneyremain,mnot):
    playernew = list()
    amountnew = list()
    mnotnew = list()
    pod = min(moneyremain)
    for i in range(len(playerremain)):
        new = moneyremain[i] -pod
        if new != 0:
            playernew.append(playerremain[i])
            amountnew.append(new)
    for i in mnot:
        check = i - pod
        if check > 0:
            mnotnew.append(check)
            
    return playernew,amountnew,mnotnew

def potamount(playerremain,moneyremain,mnot):
    rule = min(moneyremain)
    pod = rule*len(playerremain)
    for i in mnot:
        print(i)
        print(rule)
        check = i - rule
        print(check)
        if check <= 0:
            pod = pod+i
        else:
            pod = pod+rule
    return pod
            
            
    

def whoremain(playlst):
    anslst =[]
    for i in playlst:
        if i !=0:
            anslst.append(i)
    return anslst

def monremain(playlst,moneylst):
    anslst =[]
    mnot =[]
    for i in range(len(playlst)):
        if playlst[i] !=0:
            anslst.append(moneylst[i])
        if playlst[i] ==0:
            mnot.append(moneylst[i])
    return anslst,mnot    
        
def whowin():
    check =True
    player=eval(player_remain_get)
    amount=eval(money_round_get)
    money_result=list()
    for i in player:
        money_result.append(0)
    playerremain=whoremain(player)
    moneyremain,mnot = monremain(player,amount)
    anslist=list()
    anskey = ''
    different_count = len(set(moneyremain))
    
    for i in range(different_count):
        check =True
        display.fill(0)
        pod = potamount(playerremain,moneyremain,mnot)
        display.text('Who win pod('+str(i+1)+ "):" , 0, 0, 1)
        display.text("pod size: "+str(pod) , 0, 10, 1)
        for j in range(len(playerremain)):
            display.text(str(j+1)+" Player"+str(playerremain[j]) , 0, 10*(j+2), 1)
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
                money_result[playerremain[int(anskey)-1]-1] += pod
                playerremain,moneyremain,mnot = arrangesidepot(playerremain,moneyremain,mnot)
                print(playerremain,moneyremain,mnot)
                check =False
                anslist = []
    mqtt.publish(TOPIC_MONEYRESULT, str(money_result))


def games_start():
    pokerchippage()
    sleep(1)
    text =[' Enter bigblind',' Enter money',' Enter player']
    i=-1
    while any(x == 0 for x in listgamestart):
        i+=1
        display.fill(0)
        ans =""
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
                            ans =""
                            listgamestart[0] =0
                            listgamestart[1] =0
                            continue
                    check = False
                    print(i)
        listgamestart[i] = ans
        print('round done')
    display.fill(0)
    pokerchippage()

player_get=''
pot_get =''
player_remain_get=''
money_round_get=''

def mqtt_callback(topic, payload):
    global player_remain_get,money_round_get,player_get,pot_get
    payload_str = payload.decode().strip()
    if topic.decode() == TOPIC_PLAYER:
            player_get=payload_str
    if topic.decode() == TOPIC_PLAYER_REMAIN:
            player_remain_get=payload_str
    if topic.decode() == TOPIC_POT:
            pot_get=payload_str
    if topic.decode() == TOPIC_MONEY_ROUND:
            money_round_get=payload_str

wifi = network.WLAN(network.STA_IF)
mqtt = MQTTClient(client_id='',
                  server=MQTT_BROKER,
                  user=MQTT_USER,
                  password=MQTT_PASS)
connect_wifi()
connect_mqtt()
last_publish = 0
textt = "1000,ongame,smallblind"
mqtt.publish(TOPIC_TEST, textt)

games_start()
mqtt.publish(TOPIC_BIGBLIND, str(int(listgamestart[0])))
mqtt.publish(TOPIC_SMALLBLIND, str(int(int(listgamestart[0])/2)))
mqtt.publish(TOPIC_MONEY, str(int(listgamestart[1])))
mqtt.publish(TOPIC_SETTINGTABLE, "["+str(int(listgamestart[0]))+","+str(int(listgamestart[1]))+"]")
while True:
    while money_round_get == '' or player_remain_get=='':
        mqtt.check_msg()
    whowin()  
    money_round_get = ''
    player_remain_get=''

    
