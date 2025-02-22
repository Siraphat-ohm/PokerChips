import time

import ssd1306
from machine import ADC, Pin, SoftI2C

# OLED Setup
i2c = SoftI2C(scl=Pin(47), sda=Pin(48))
# Change for Pico: I2C(0, scl=Pin(5), sda=Pin(4))


# Joystick Setup
joystick_x = ADC(Pin(13))  # X-axis
joystick_y = ADC(Pin(12))  # Y-axis
button = Pin(14, Pin.IN, Pin.PULL_UP)  # Button (active LOW)

# ADC Range (ESP32: 0-4095, Pico: 0-65535)
joystick_x.atten(ADC.ATTN_11DB)  # Full range 0-3.3V
joystick_y.atten(ADC.ATTN_11DB)

# Menu options
Action_menu = ["Check/Call", "Bet/Raise", "Fold", "Cancel"]
Confirm_menu = ["YES", "NO"]
selected = 0  # Current selection
chip = 1000

channel = 1
i2c.writeto(0x70, bytes([1 << channel]))
print(f"Channel {channel} selected.")
time.sleep(0.1)  # Short delay for stability

i2c_channel = SoftI2C(scl=Pin(47), sda=Pin(48))
devices = i2c_channel.scan()
print(f"Devices on channel {channel}: {[hex(d) for d in devices]}")

if 0x3C not in devices and 0x3D not in devices:
    raise OSError(f"No SSD1306 display found on channel {channel}!")
oled = ssd1306.SSD1306_I2C(128, 64, i2c_channel)


Balance = 1000
Position = "None"
Pod = 0
Player_Bet = 0


def draw_Action_menu(selected):
    oled.fill(0)
    for i, item in enumerate(Action_menu):
        if i == selected:
            oled.text("> " + item, 10, (i) * 12)  # Highlighted item
        else:
            oled.text("  " + item, 10, (i) * 12)  # Normal item
    oled.show()


def draw_Confirm_menu(selected):
    oled.fill(0)
    oled.text("Confirm", 0, 0)
    for i, item in enumerate(Confirm_menu):
        if i == selected:
            oled.text("> " + item, 10, (i + 1) * 12)  # Highlighted item
        else:
            oled.text("  " + item, 10, (i + 1) * 12)  # Normal item
    oled.show()


def draw_Confirm():
    time.sleep(0.2)
    selected = 0
    draw_Confirm_menu(selected)
    while True:
        y_val = joystick_y.read()
        btn_state = button.value()
        if btn_state == 0 and selected == 0:
            pass
            # Ccc
        elif btn_state == 0 and selected == 1:
            draw_Action()
        elif y_val > 3000:
            selected = (selected - 1) % len(Confirm_menu)
            draw_Confirm_menu(selected)
            time.sleep(0.2)  # Prevent rapid scrolling
            # Move DOWN (Y < 1000)
        elif y_val < 1000:
            selected = (selected + 1) % len(Confirm_menu)
            draw_Confirm_menu(selected)
            time.sleep(0.2)
        else:
            time.sleep(0.2)


def draw_Action():
    time.sleep(0.2)
    selected = 0

    draw_Action_menu(selected)
    while True:
        y_val = joystick_y.read()
        btn_state = button.value()
        print(f"y_val {y_val}")
        print(f"btn_state {btn_state}")
        print(selected)
        if btn_state == 0 and selected == 3:
            draw_idle()
        elif btn_state == 0 and selected == 2:
            draw_Confirm()
        elif btn_state == 0:
            oled.fill(0)
            oled.text("Choices:", 10, 20)
            oled.text(Action_menu[selected], 10, 40)
            oled.show()
            time.sleep(2)  # Show selection for a moment
            draw_Action_menu(selected)
        elif y_val > 3000:
            selected = (selected - 1) % len(Action_menu)
            draw_Action_menu(selected)
            time.sleep(0.2)  # Prevent rapid scrolling
        # Move DOWN (Y < 1000)
        elif y_val < 1000:
            selected = (selected + 1) % len(Action_menu)
            draw_Action_menu(selected)
            time.sleep(0.2)
        else:
            time.sleep(0.2)


def draw_idle():
    time.sleep(0.2)
    oled.fill(0)
    oled.text("Balance:" + str(Balance), 0, 0)
    oled.text("Position: " + Position, 0, 10)
    oled.text("Pod:   " + str(Pod), 0, 20)
    oled.text("Bet:   " + str(Player_Bet), 0, 30)
    oled.text("Action", 0, 40)
    oled.show()
    btn_state = button.value()
    while btn_state != 0:
        btn_state = button.value()
        print(btn_state)
        time.sleep(0.1)
    else:
        draw_Action()


draw_idle()


# while True:
#
#     y_val = joystick_y.read()
#     btn_state = button.value()
#     print(f"y_val {y_val}")
#     print(f"btn_state {btn_state}")
#     if btn_state == 0:
#         oled.fill(0)
#         oled.text("Choices:", 10, 20)
#         oled.text(menu[selected], 10, 40)
#         #select_confirm= [menu[selected],'Cancel']
#         #for i , j in enumerate(select_confirm):
#         #if i == selected:
#         #    oled.text("> " + item, 10,( i+1) * 12)  # Highlighted item
#         #else:
#         #    oled.text("  " + item, 10, (i+1) * 12)  # Normal item
#         oled.show()
#         time.sleep(2)  # Show selection for a moment
#         draw_menu()
#     elif y_val > 3000:
#         selected = (selected - 1) % len(menu)
#         draw_menu()
#         time.sleep(0.2)  # Prevent rapid scrolling
#     # Move DOWN (Y < 1000)
#     elif y_val < 1000:
#         selected = (selected + 1) % len(menu)
#         draw_menu()
#         time.sleep(0.2)
#     else:
#         time.sleep(0.2)  # Show selection for a moment
# Select option (Button Pressoled.fill(0)
