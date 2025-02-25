import time

import machine
from machine import ADC, Pin, SoftI2C

import const
import ssd1306


class I2CMultiplexer:
    def __init__(self, scl_pin, sda_pin, i2c_addr=0x70):
        self.i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.i2c_addr = i2c_addr

    def select_channel(self, channel):
        self.i2c.writeto(self.i2c_addr, bytes([1 << channel]))
        time.sleep_ms(10)


class Joystick:

    def __init__(self, x_pin, y_pin, sw_pin, attenuation=machine.ADC.ATTN_11DB):
        self.adc_x = machine.ADC(machine.Pin(x_pin))
        self.adc_x.atten(attenuation)

        self.adc_y = machine.ADC(machine.Pin(y_pin))
        self.adc_y.atten(attenuation)

        self.sw_pin = machine.Pin(sw_pin, machine.Pin.IN, machine.Pin.PULL_UP)

    def read_raw(self):
        x_val = self.adc_x.read()
        y_val = self.adc_y.read()
        sw_val = self.sw_pin.value()
        return (x_val, y_val, sw_val)

    def read_direction(self, center=2048, deadzone=300):
        x_val, y_val, sw_val = self.read_raw()

        if x_val < center - deadzone:
            x_dir = -1
        elif x_val > center + deadzone:
            x_dir = +1
        else:
            x_dir = 0

        if y_val < center - deadzone:
            y_dir = -1
        elif y_val > center + deadzone:
            y_dir = +1
        else:
            y_dir = 0

        return (x_dir, y_dir, sw_val)


class Player:
    def __init__(self, multiplexer, channel, joystick_pins, position, money=1000):
        self.multiplexer = multiplexer
        self.channel = channel

        self.joystick = Joystick(*joystick_pins)
        self.stage = "pre_bet"
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
        time.sleep(0.2)
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
                if selected == 0:
                    self.bet_turn = self.money / 2
                if selected == 1:
                    self.bet_turn = self.money / 4
                if selected == 2:
                    self.bet_turn = self.money / 8
                if selected == 3:
                    self.bet_turn = 0
                self.draw_Bet_menu(selected)
                time.sleep(0.2)  # Prevent rapid scrolling
            # Move DOWN (Y < 1000)
            elif y_dir == 1:
                selected = (selected + 1) % 4
                if selected == 0:
                    self.bet_turn = self.money / 2
                if selected == 1:
                    self.bet_turn = self.money / 4
                if selected == 2:
                    self.bet_turn = self.money / 8
                if selected == 3:
                    self.bet_turn = 0
                self.draw_Bet_menu(selected)
                time.sleep(0.2)
            else:
                time.sleep(0.2)
        if selected == 0:
            self.money -= self.bet_turn
            self.bet += self.bet_turn
            self.pod += self.bet_turn
            self.draw_screen(self.pot)

        elif selected == 1:
            self.money -= self.bet_turn
            self.bet += self.bet_turn
            self.pod += self.bet_turn
            self.draw_screen(self.pot)

        elif selected == 2:
            self.money -= self.bet_turn
            self.bet += self.bet_turn
            self.pod += self.bet_turn
            self.draw_screen(self.pot)

        elif selected == 3:
            self.draw_Amount_Bar()

    def draw_Amount_Bar(self):
        selected = 0
        time.sleep(0.2)
        self.multiplexer.select_channel(self.channel)
        self.bet_turn = 0
        speed = 10  # Start slow
        max_speed = 100  # Maximum bet increase per second
        acceleration = 1.1  # Smooth acceleration
        decay = 0.9  # Slow down when joystick is neutral
        hold_time = 0  # Tracks how long joystick is held
        last_time = time.ticks_ms()

        while True:
            x_dir, y_dir, sw_val = self.joystick.read_direction()
            # This returns only -1, 0, or 1

            current_time = time.ticks_ms()
            elapsed = time.ticks_diff(current_time, last_time)
            last_time = current_time

            # Joystick moved RIGHT (increase bet)
            if x_dir == 1:
                hold_time += elapsed
                speed = min(speed * acceleration, max_speed)  # Gradual speed increase
                self.bet_turn += int(speed * hold_time / 1000)  # Increase bet over time

            # Joystick moved LEFT (decrease bet)
            elif x_dir == -1 and self.bet_turn > 0:
                hold_time += elapsed
                speed = min(speed * acceleration, max_speed)
                self.bet_turn -= int(speed * hold_time / 1500)  # Decrease bet over time

            # Joystick NEUTRAL (reset acceleration)
            else:
                speed = max(speed * decay, 10)  # Slow down naturally
                hold_time = 0  # Reset hold time

            # Round bet_turn to nearest 10
            self.bet_turn = round(self.bet_turn / 10) * 10

            # Clamp bet amount within valid range
            self.bet_turn = max(0, min(self.bet_turn, self.money))

            # Draw UI
            self.oled.fill(0)
            self.oled.text("Set Bet Amount", 20, 5)
            self.oled.text(f"Bet: {self.bet_turn}", 40, 20)

            # Draw progress bar
            bar_length = int(self.bet_turn / self.money * 100)
            self.oled.rect(10, 40, 100, 10, 1)  # Outline of bar
            self.oled.fill_rect(10, 40, bar_length, 10, 1)  # Fill bar

            self.oled.show()
            time.sleep(0.05)  # Smooth animation

            # Confirm bet with joystick button
            if sw_val == 0:
                self.money -= self.bet_turn
                self.bet += self.bet_turn
                self.pod += self.bet_turn
                break
            if y_dir == -1:
                break
        self.draw_screen(self.pot)

    def draw_confirm_fold_menu(self, selected):
        time.sleep(0.2)
        self.oled.fill(0)
        self.multiplexer.select_channel(self.channel)
        fold_options = ["Confirm", "Cancel"]
        self.oled.text(f"Are You Sure", 0, 0)
        for i, item in enumerate(fold_options):
            if i == selected:
                self.oled.text("> " + item, 10, (i + 1) * 12)  # Highlighted item
            else:
                self.oled.text("  " + item, 10, (i + 1) * 12)  # Normal item
        self.oled.show()

    def draw_fold(self):
        time.sleep(0.2)
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

    def draw_confirm_fold(self):
        time.sleep(0.2)
        self.oled.fill(0)
        selected = 0
        self.multiplexer.select_channel(self.channel)
        self.draw_confirm_fold_menu(selected)
        while True:

            x_dir, y_dir, sw_val = self.joystick.read_direction()
            print(self.joystick.read_direction())
            if sw_val == 0:
                break
            elif y_dir == 1:
                selected = (selected + 1) % 2
                self.draw_confirm_fold_menu(selected)
            elif y_dir == -1:
                selected = (selected - 1) % 2
                self.draw_confirm_fold_menu(selected)
            else:
                time.sleep(0.2)
        if selected == 0:
            self.draw_fold()
        if selected == 1:
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
                self.draw_Bet()
            elif selected_action == "Fold":
                self.draw_confirm_fold()
            return selected_action

        return None


def get_poker_positions(num_players):
    if num_players < 2 or num_players > 10:
        raise ValueError("Poker requires 2-10 players.")

    positions = ["SB", "BB"]

    if num_players >= 3:
        positions.append("UTG")

    if num_players >= 4:
        positions.append("MP1")

    if num_players >= 5:
        positions.append("MP2")

    if num_players >= 6:
        positions.append("HJ")

    if num_players >= 7:
        positions.append("CO")

    positions.append("BTN")

    seat_positions = {}
    for i in range(num_players):
        seat_positions[i] = positions[i % len(positions)]

    return seat_positions


if __name__ == "__main__":
    multiplexer = I2CMultiplexer(scl_pin=9, sda_pin=8)
    num_players = 4
    positions = get_poker_positions(num_players)
    players = [
        Player(
            multiplexer, channel=0, joystick_pins=(14, 13, 12), position=positions[0]
        ),
        Player(
            multiplexer, channel=1, joystick_pins=(15, 16, 17), position=positions[1]
        ),
        Player(
            multiplexer, channel=2, joystick_pins=(15, 16, 17), position=positions[2]
        ),
        Player(
            multiplexer, channel=3, joystick_pins=(15, 16, 17), position=positions[3]
        ),
    ]

    while True:
        for player in players:
            player.update_action()
            player.draw_screen(100)
