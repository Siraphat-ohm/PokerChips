import time

import const
from player import Player

if __name__ == "__main__":
    p = []
    for i, v in const.JOYSTICKS.items():
        p.append(
            Player(
                const.I2C_SCL_PIN,
                const.I2C_SDA_PIN,
                1,
                x_pin=v["x_pin"],
                y_pin=v["y_pin"],
                sw_pin=v["sw_pin"],
            )
        )
    while True:
        p[0].draw_screen()
        p[0].handle_joystick()
