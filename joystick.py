import time

import machine


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


if __name__ == "__main__":
    joystick = Joystick(x_pin=10, y_pin=11, sw_pin=9)

    while True:
        x, y, sw = joystick.read_raw()
        print("Raw:", x, y, sw)

        x_dir, y_dir, sw_dir = joystick.read_direction()
        dir_msg = []
        dir_msg.append("Left" if x_dir < 0 else ("Right" if x_dir > 0 else "CenterX"))
        dir_msg.append("Up" if y_dir < 0 else ("Down" if y_dir > 0 else "CenterY"))
        dir_msg.append("Pressed" if sw_dir == 0 else "NotPressed")

        print("Direction:", dir_msg)
        time.sleep(0.3)
