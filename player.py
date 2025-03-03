import time

import const
from joystick import Joystick
from machine import Pin, SoftI2C

import ssd1306


class I2CMultiplexer:
    def __init__(self, scl_pin, sda_pin, i2c_addr=0x70):
        self.i2c = SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.i2c_addr = i2c_addr
        self.current_channel = None

    def select_channel(self, channel):
        if self.current_channel != channel:
            self.i2c.writeto(self.i2c_addr, bytes([1 << channel]))
            time.sleep_ms(10)
            self.current_channel = channel


class Player:
    def __init__(self, multiplexer, channel, joystick_pins):
        self.multiplexer = multiplexer
        self.channel = channel
        self.fold = False
        self.joystick = Joystick(*joystick_pins)
        self.money = 0
        self.pot = 0
        self.bet = 0
        self.actions = []

        self.multiplexer.select_channel(channel)
        self.oled = ssd1306.SSD1306_I2C(
            const.SCREEN_WIDTH, const.SCREEN_HEIGHT, self.multiplexer.i2c
        )

    def set_position(self, pos):
        self.position = pos

    def set_money(self, money):
        self.money = money

    def draw_screen(self, pot, highest_bet=0, active=False):
        time.sleep(0.2)
        self.pot = pot
        self.multiplexer.select_channel(self.channel)
        if self.fold:
            self.draw_fold()
            return "Fold",0

        if active:
            if highest_bet == 0:
                self.actions = ["Bet", "Check", "Fold"]
            elif self.bet < highest_bet:
                self.actions = ["Raise", "Call", "Fold"]
            else:
                self.actions = ["Raise", "Check", "Fold"]

            selected = 0

            while active:
                time.sleep(0.1)
                self.oled.fill(0)
                self.oled.text(f"{self.position}: ${self.money}", 0, 0)
                self.oled.text(f"Pot: ${pot}", 0, 10)
                self.oled.text(f"Bet: ${self.bet}", 0, 20)
                self.oled.hline(0, 30, 128, 1)

                for i, action in enumerate(self.actions):
                    prefix = "> " if i == selected else "  "
                    self.oled.text(prefix + action, 0, 35 + (i * 10))

                self.oled.show()
                _, y_dir, sw_val = self.joystick.read_direction()

                if sw_val == 0:
                    if self.actions[selected] in ( "Bet" , "Raise"):
                        self.draw_bet(highest_bet)
                        return self.actions[selected], self.bet
                    elif self.actions[selected] == "Raise":
                        self.draw_bet(highest_bet)
                        return self.actions[selected], self.bet
                    elif self.actions[selected] == "Call":
                        call_amount = highest_bet - self.bet
                        if call_amount > 0:
                            call_amount = min(call_amount, self.money)
                            self.money -= call_amount
                            self.bet += call_amount
                            self.pot += call_amount
                        return "Call", call_amount
                    elif self.actions[selected] == "Check":
                        return self.actions[selected],0
                    else:
                        if self.draw_confirm():
                            self.draw_fold()
                            return self.actions[selected], 0
                            # break

                elif y_dir == -1:
                    selected = (selected - 1) % len(self.actions)
                elif y_dir == 1:
                    selected = (selected + 1) % len(self.actions)
        else:
            self.oled.fill(0)
            self.oled.text(f"{self.position}: ${self.money}", 0, 0)
            self.oled.text(f"Pot: ${pot}", 0, 10)
            self.oled.text(f"Bet: ${self.bet}", 0, 20)
            self.oled.hline(0, 30, 128, 1)
            self.oled.text("Waiting...", 0, 50)
            self.oled.show()

    def draw_fold(self):
        time.sleep(0.1)
        self.multiplexer.select_channel(self.channel)
        self.oled.fill(0)
        self.oled.text("YOU HAVE", 30, 20)
        self.oled.text("FOLDED", 35, 40)
        self.oled.show()
        self.fold = True

    def draw_confirm(self, message="Are You Sure?"):
        time.sleep(0.1)
        selected = 0
        options = ["Confirm", "Cancel"]

        while True:
            time.sleep(0.1)
            self.oled.fill(0)
            self.multiplexer.select_channel(self.channel)
            self.oled.text(message, 0, 0)

            for i, option in enumerate(options):
                prefix = "> " if i == selected else "  "
                self.oled.text(prefix + option, 10, (i + 1) * 12)
            self.oled.show()

            _, y_dir, sw_val = self.joystick.read_direction()
            if sw_val == 0:
                return selected == 0
            selected = (selected + y_dir) % 2

    def draw_bet(self, min_raise=0):
        time.sleep(0.1)
        self.multiplexer.select_channel(self.channel)

        current_bet = min(max(min_raise, 0), self.money)

        speed = 10
        max_speed = 100
        acceleration = 1.1
        decay = 0.9

        hold_time = 0
        last_time = time.ticks_ms()

        while True:
            time.sleep(0.1)
            x_dir, _, sw_val = self.joystick.read_direction()
            current_time = time.ticks_ms()
            elapsed = time.ticks_diff(current_time, last_time)
            last_time = current_time

            if x_dir == 1:
                hold_time += elapsed
                speed = min(speed * acceleration, max_speed)
                increment = int(speed * hold_time / 1000)
                current_bet += increment

            elif x_dir == -1 and current_bet > 0:
                hold_time += elapsed
                speed = min(speed * acceleration, max_speed)
                decrement = int(speed * hold_time / 1500)
                current_bet -= decrement

            else:
                speed = max(speed * decay, 10)
                hold_time = 0

            current_bet = round(current_bet / 10) * 10

            current_bet = max(min_raise, min(current_bet, self.money))

            self.oled.fill(0)
            self.oled.text(f"Bet: {current_bet}", 30, 20)

            bar_length = 100
            fill_length = int(current_bet / self.money * bar_length)
            self.oled.rect(10, 40, bar_length, 10, 1)
            self.oled.fill_rect(10, 40, fill_length, 10, 1)

            self.oled.show()
            time.sleep(0.05)

            if sw_val == 0:
                if self.draw_confirm(
                    "Confirm Raise?" if min_raise > 0 else "Confirm Bet?"
                ):
                    self.money -= current_bet
                    self.bet += current_bet
                    self.pot += current_bet
                    break
                    

        self.draw_screen(self.pot)


if __name__ == "__main__":
    multiplexer = I2CMultiplexer(const.SCL_PIN, const.SDA_PIN)
    player = Player(multiplexer, 0, (14, 13, 12))
    player.set_position("SB")
    player.set_money(1000)
    while True:
        player.draw_screen(40, highest_bet=20, active=True)

