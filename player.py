import time

from machine import Pin, SoftI2C

import const
import ssd1306
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
        self.fold = False

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
        self.multiplexer.select_channel(self.channel)
        self.oled.fill(0)

        self.oled.text(f"{self.position}: ${self.money}", 0, 0)
        self.oled.text(f"Pot: ${pot}", 0, 10)
        self.oled.text(f"Bet: ${self.bet}", 0, 20)
        self.oled.hline(0, 30, 128, 1)

        if betting_stage == "pre_bet":
            left_action = "Bet"
            center_action = "Check"
        else:
            left_action = "Raise"
            center_action = "Call"
        right_action = "Fold"
        actions = [left_action, center_action, right_action]

        def text_width(text):
            return len(text) * 6

        x_left = 5
        offset = 10
        x_center = (128 - text_width(center_action)) // 2 - offset
        x_right = 128 - text_width(right_action) - 5
        x_positions = [x_left, x_center, x_right]

        for i, action in enumerate(actions):
            display_text = f"[{action}]" if i == self.selected_action else action
            self.oled.text(
                display_text,
                x_positions[i] - (2 if i == self.selected_action else 0),
                42,
            )

        self.oled.show()

    def draw_Bet_menu(self, selected):
        time.sleep(0.2)
        self.multiplexer.select_channel(self.channel)
        Bet_menu_fraction = ["1/2", "1/4", "1/8", "Amount"]
        self.oled.fill(0)
        self.oled.text(f"Bet: ${self.bet_turn}", 0, 0)
        for i, item in enumerate(Bet_menu_fraction):
            if i == selected:
                self.oled.text("> " + item, 10, (i + 1) * 12)  # Highlighted item
            else:
                self.oled.text("  " + item, 10, (i + 1) * 12)  # Normal item
        self.oled.show()

    def draw_fold(self):
        self.oled.fill(0)
        self.multiplexer.select_channel(self.channel)
        self.oled.text("YOU HAVE", 30, 20)
        self.oled.text("FOLDED", 45, 40)
        self.oled.show()
        time.sleep(0.2)
        while True:
            x_dir, y_dir, sw_val = self.joystick.read_direction()
            if sw_val == 0:
                break
        self.draw_screen(self.pot)

    def draw_confirm(self, message="Are You Sure"):
        selected = 0
        while True:
            time.sleep(0.2)
            self.oled.fill(0)
            self.multiplexer.select_channel(self.channel)
            self.oled.text(message, 0, 0)
            options = ["Confirm", "Cancel"]
            for i, option in enumerate(options):
                prefix = "> " if i == selected else "  "
                self.oled.text(prefix + option, 10, (i + 1) * 12)
            self.oled.show()

            x_dir, y_dir, sw_val = self.joystick.read_direction()
            if sw_val == 0:
                break
            elif y_dir == 1:
                selected = (selected + 1) % 2
            elif y_dir == -1:
                selected = (selected - 1) % 2
        return selected == 0

    def draw_Bet(self):
        selected = 0
        time.sleep(0.2)
        self.bet_turn = 0
        self.draw_Bet_menu(selected)
        while True:
            x_dir, y_dir, sw_val = self.joystick.read_direction()
            if sw_val == 0:
                break
            elif y_dir == -1:
                selected = (selected - 1) % 4
            elif y_dir == 1:
                selected = (selected + 1) % 4

            # Update bet_turn based on the current selection
            if selected == 0:
                self.bet_turn = self.money / 2
            elif selected == 1:
                self.bet_turn = self.money / 4
            elif selected == 2:
                self.bet_turn = self.money / 8
            elif selected == 3:
                self.bet_turn = 0

            self.draw_Bet_menu(selected)
            time.sleep(0.2)

        # For fractional bets, ask for confirmation before applying the bet.
        if selected in (0, 1, 2):
            if self.draw_confirm("Confirm Bet?"):
                self.money -= self.bet_turn
                self.bet += self.bet_turn
                self.pot += self.bet_turn  # (Assuming 'pot' is the correct variable.)
            self.draw_screen(self.pot)
        elif selected == 3:
            # "Amount" option selected
            self.draw_Amount_Bar()

    def draw_Amount_Bar(self):
        time.sleep(0.2)
        self.multiplexer.select_channel(self.channel)
        self.bet_turn = 0
        speed = 10  # Starting speed
        max_speed = 100  # Maximum bet increase per second
        acceleration = 1.1  # Smooth acceleration
        decay = 0.9  # Slow down when joystick is neutral
        hold_time = 0  # Tracks how long joystick is held
        last_time = time.ticks_ms()

        while True:
            x_dir, y_dir, sw_val = self.joystick.read_direction()
            current_time = time.ticks_ms()
            elapsed = time.ticks_diff(current_time, last_time)
            last_time = current_time

            if x_dir == 1:
                hold_time += elapsed
                speed = min(speed * acceleration, max_speed)
                self.bet_turn += int(speed * hold_time / 1000)
            elif x_dir == -1 and self.bet_turn > 0:
                hold_time += elapsed
                speed = min(speed * acceleration, max_speed)
                self.bet_turn -= int(speed * hold_time / 1500)
            else:
                speed = max(speed * decay, 10)
                hold_time = 0

            # Round bet_turn to nearest 10 and clamp it within [0, money]
            self.bet_turn = round(self.bet_turn / 10) * 10
            self.bet_turn = max(0, min(self.bet_turn, self.money))

            # Draw the bet amount UI and a progress bar
            self.oled.fill(0)
            self.oled.text("Set Bet Amount", 20, 5)
            self.oled.text(f"Bet: {self.bet_turn}", 40, 20)
            bar_length = int(self.bet_turn / self.money * 100)
            self.oled.rect(10, 40, 100, 10, 1)
            self.oled.fill_rect(10, 40, bar_length, 10, 1)
            self.oled.show()
            time.sleep(0.05)

            if sw_val == 0:
                if self.draw_confirm("Confirm Bet Amount?"):
                    self.money -= self.bet_turn
                    self.bet += self.bet_turn
                    self.pot += self.bet_turn
                    break
            if y_dir == -1:
                break

        self.draw_screen(self.pot)

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
            if selected_action == "Bet":
                if self.draw_confirm("Confirm Bet?"):
                    self.draw_Bet()
                else:
                    self.draw_screen(self.pot)
            elif selected_action == "Call":
                if self.draw_confirm("Confirm Call?"):
                    print(f"{self.position} calls.")
                    self.draw_screen(self.pot)
                else:
                    self.draw_screen(self.pot)
            elif selected_action == "Fold":
                if self.draw_confirm("Confirm Fold ?"):
                    self.draw_fold()
                    self.fold = True
            return selected_action

        return None
