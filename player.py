import time

import ssd1306
from machine import Pin, SoftI2C

import const
from joystick import Joystick


class Player:
    def __init__(self, scl_pin, sda_pin, channel, x_pin, y_pin, sw_pin):
        self.i2c_channel = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.channel = channel

        self.joystick = Joystick(x_pin, y_pin, sw_pin)

        self.devices = self.i2c_channel.scan()
        print(f"Devices on channel {channel}: {[hex(d) for d in self.devices]}")

        if 0x3C not in self.devices and 0x3D not in self.devices:
            raise OSError(f"No SSD1306 display found on channel {channel}!")

        self.oled = ssd1306.SSD1306_I2C(
            const.SCREEN_WIDTH, const.SCREEN_HEIGHT, self.i2c_channel
        )

        self.money = 1000
        self.position = "SB"
        self.pot = 500
        self.bet = 50
        self.selected_action = 0

    def select_channel(self):
        """Switch I2C multiplexer to the correct channel before using OLED."""
        self.i2c_channel.writeto(const.I2C_ADDR, bytes([1 << self.channel]))
        time.sleep_ms(10)

    def draw_screen(self):
        """Display poker player stats and action choices."""
        self.select_channel()
        self.oled.fill(0)

        self.oled.text(f"${self.money} P:{self.position}", 0, 0)
        self.oled.text(f"Pot: ${self.pot}", 0, 10)
        self.oled.text(f"Bet: ${self.bet}", 0, 20)

        self.oled.hline(0, 30, 128, 1)

        actions = ["Bet", "Call", "Fold"]
        for i, action in enumerate(actions):
            if i == self.selected_action:
                self.oled.fill_rect(5, 40 + i * 10, 40, 8, 1)
                self.oled.text(action, 7, 42 + i * 10, 0)
            else:
                self.oled.text(action, 7, 42 + i * 10, 1)

        self.oled.show()

    def update_selection(self, direction):
        self.selected_action = (self.selected_action + direction) % 3
        self.draw_screen()

    def idle_screen(self):
        self.select_channel()
        self.oled.fill(0)
        self.oled.text(f"Poker game {self.channel + 1}", 0, 0, 1)
        self.oled.show()

    def handle_joystick(self):
        x_dir, y_dir, sw_state = self.joystick.read_direction()

        if y_dir == -1:
            self.update_selection(-1)
            time.sleep(0.2)
        elif y_dir == 1:
            self.update_selection(1)
            time.sleep(0.2)

        if sw_state == 0:
            self.confirm_action()
            time.sleep(0.3)

    def confirm_action(self):
        actions = ["Bet", "Call", "Fold"]
        print(f"Player {self.channel + 1} selected: {actions[self.selected_action]}")

        if self.selected_action == 0:  # Bet
            self.bet += 50
            self.money -= 50
        elif self.selected_action == 1:  # Call
            self.money -= self.bet
        elif self.selected_action == 2:  # Fold
            print(f"Player {self.channel + 1} folded!")

        self.draw_screen()
