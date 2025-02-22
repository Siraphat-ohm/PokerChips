import time

import ssd1306
from machine import ADC, Pin, SoftI2C

# I2C setup
i2c = SoftI2C(scl=Pin(47), sda=Pin(48))


# Function to select I2C channel on the multiplexer
def select_channel(channel):
    """Select the I2C channel on the multiplexer."""
    if 0 <= channel <= 7:
        i2c.writeto(0x70, bytes([1 << channel]))
        print(f"Channel {channel} selected.")
        time.sleep(0.1)  # Short delay for stability
    else:
        raise ValueError("Channel must be between 0 and 7")


# Function to test OLED on a specific channel
def test_oled(channel, message):
    """Test the OLED display on the specified channel with a custom message."""
    try:
        # Select the I2C channel
        select_channel(channel)

        # Initialize I2C for the specific channel
        i2c_channel = SoftI2C(scl=Pin(47), sda=Pin(48))
        devices = i2c_channel.scan()
        print(f"Devices on channel {channel}: {[hex(d) for d in devices]}")

        # Check if OLED is detected
        if 0x3C not in devices and 0x3D not in devices:
            raise OSError(f"No SSD1306 display found on channel {channel}!")

        # Initialize OLED display
        oled = ssd1306.SSD1306_I2C(128, 64, i2c_channel)

        # Display message
        oled.fill(0)
        oled.text(f"{message}", 0, 0, 1)
        oled.text(f"Channel {channel}", 0, 16, 1)
        oled.text("I2C Working!", 0, 32, 1)
        oled.show()

        print(f"Display on channel {channel} tested successfully.")
        return oled

    except Exception as e:
        print(f"Failed to test OLED on channel {channel}: {e}")
        return None


# Initialize joystick function
def readJoystick(x_pin, y_pin, sw_pin):
    x = ADC(Pin(x_pin))
    y = ADC(Pin(y_pin))
    sw = Pin(sw_pin, Pin.IN, Pin.PULL_UP)

    x.atten(ADC.ATTN_11DB)
    y.atten(ADC.ATTN_11DB)

    return x, y, sw


# Initialize Joystick
joystick_x, joystick_y, button = readJoystick(13, 12, 14)

# Menu options
Action_menu = ["Check/Call", "Bet/Raise", "Fold", "Cancel"]
Confirm_menu = ["YES", "NO"]
selected = 0
chip = 1000

# Test OLED on channel 1
oled = test_oled(1, "Poker Game")

# Game Variables
Balance = 1000
Position = "SB"
Pod = 0
Player_Bet = 0


# Display Action Menu
def draw_Action_menu(selected):
    oled.fill(0)
    for i, item in enumerate(Action_menu):
        oled.text("> " + item if i == selected else "  " + item, 10, i * 12)
    oled.show()


# Display Confirm Menu
def draw_Confirm_menu(selected):
    oled.fill(0)
    oled.text("Confirm", 0, 0)
    for i, item in enumerate(Confirm_menu):
        oled.text("> " + item if i == selected else "  " + item, 10, (i + 1) * 12)
    oled.show()


# Confirm Action
def draw_Confirm():
    time.sleep(0.2)
    selected = 0
    draw_Confirm_menu(selected)
    while True:
        y_val = joystick_y.read()
        btn_state = button.value()

        if btn_state == 0:
            if selected == 0:
                pass  # Confirm Yes Action
            elif selected == 1:
                draw_Action()
        elif y_val > 3000:
            selected = (selected - 1) % len(Confirm_menu)
            draw_Confirm_menu(selected)
            time.sleep(0.2)
        elif y_val < 1000:
            selected = (selected + 1) % len(Confirm_menu)
            draw_Confirm_menu(selected)
            time.sleep(0.2)
        else:
            time.sleep(0.2)


# Action Menu Navigation
def draw_Action():
    time.sleep(0.2)
    selected = 0
    draw_Action_menu(selected)

    while True:
        y_val = joystick_y.read()
        btn_state = button.value()

        if btn_state == 0:
            if selected == 3:
                draw_idle()
            elif selected == 2:
                draw_Confirm()
            else:
                oled.fill(0)
                oled.text("Choice:", 10, 20)
                oled.text(Action_menu[selected], 10, 40)
                oled.show()
                time.sleep(2)
                draw_Action_menu(selected)
        elif y_val > 3200:
            selected = (selected - 1) % len(Action_menu)
            draw_Action_menu(selected)
            time.sleep(0.2)
        elif y_val < 1000:
            selected = (selected + 1) % len(Action_menu)
            draw_Action_menu(selected)
            time.sleep(0.2)
        else:
            time.sleep(0.2)


# Idle Screen
def draw_idle():
    time.sleep(0.2)
    oled.fill(0)
    oled.text(f"$: {Balance}", 0, 0)
    oled.text(f"Pos: {Position}", 0, 10)
    oled.text(f"Pod: {Pod}", 0, 20)
    oled.text(f"Bet: {Player_Bet}", 0, 30)
    oled.text("Action", 0, 40)
    oled.show()

    while button.value() != 0:
        time.sleep(0.1)
    draw_Action()


# Start Program
if oled:
    draw_idle()
else:
    print("OLED initialization failed. Exiting.")
