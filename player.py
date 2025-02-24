import time

import ssd1306
from machine import Pin, SoftI2C

import const
from joystick import Joystick


class I2CMultiplexer:
    def __init__(self, scl_pin, sda_pin, i2c_addr=0x70):
        self.i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.i2c_addr = i2c_addr

    def select_channel(self, channel):
        self.i2c.writeto(self.i2c_addr, bytes([1 << channel]))
        time.sleep_ms(10)


class Player:
    def __init__(self, multiplexer, channel, joystick_pins, position, money=1000):
        self.multiplexer = multiplexer
        self.channel = channel

        self.joystick = Joystick(*joystick_pins)

        self.money = money
        self.position = position
        self.pot = 500
        self.bet = 50
        self.selected_action = 0

        self.multiplexer.select_channel(channel)
        self.oled = ssd1306.SSD1306_I2C(
            const.SCREEN_WIDTH, const.SCREEN_HEIGHT, self.multiplexer.i2c
        )

    def draw_screen(self, pot, betting_stage="pre_bet"):
        """Display player stats and a row of actions on a 128x64 OLED."""
        self.multiplexer.select_channel(self.channel)
        self.oled.fill(0)

        # Display player information
        self.oled.text(f"{self.position}: ${self.money}", 0, 0)
        self.oled.text(f"Pot: ${pot}", 0, 10)
        self.oled.text(f"Bet: ${self.bet}", 0, 20)
        self.oled.hline(0, 30, 128, 1)

        # Define actions based on betting stage:
        # Left: Bet or Raise; Center: Check or Call; Right: Fold (always)
        if betting_stage == "pre_bet":
            left_action = "Bet"
            center_action = "Check"
        else:
            left_action = "Raise"
            center_action = "Call"
        right_action = "Fold"
        actions = [left_action, center_action, right_action]

        # Helper function to estimate text width (6 pixels per character)
        def text_width(text):
            return len(text) * 6

        # Calculate x positions for each action
        # Left action: fixed margin (5 pixels)
        x_left = 5
        # Center action: centered then shifted to left by an offset (e.g., 10 pixels)
        offset = 10
        x_center = (128 - text_width(center_action)) // 2 - offset
        # Right action: right aligned with a margin of 5 pixels
        x_right = 128 - text_width(right_action) - 5
        x_positions = [x_left, x_center, x_right]

        # Draw each action. If selected, wrap it in brackets.
        for i, action in enumerate(actions):
            display_text = f"[{action}]" if i == self.selected_action else action
            self.oled.text(
                display_text,
                x_positions[i] - (2 if i == self.selected_action else 0),
                42,
            )

        self.oled.show()

    def update_action(self):
        x_dir, _, sw_val = self.joystick.read_direction()

        if x_dir == -1:
            self.selected_action = (self.selected_action - 1) % 3
            time.sleep(0.2)

        elif x_dir == 1:
            self.selected_action = (self.selected_action + 1) % 3
            time.sleep(0.2)

        if sw_val == 0:
            actions = ["Bet", "Call", "Fold"]
            selected_action = actions[self.selected_action]
            print(f"{self.position} selected: {selected_action}")
            time.sleep(0.3)
            return selected_action

        return None
