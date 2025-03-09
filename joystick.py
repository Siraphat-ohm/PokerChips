import time

from machine import ADC, Pin


class Joystick:

    def __init__(self, x_pin, y_pin, sw_pin, attenuation=ADC.ATTN_11DB):
        self.select_pins = [Pin(45, Pin.OUT), Pin(48, Pin.OUT), Pin(47, Pin.OUT)]
        self.adc_x = x_pin
        self.z_pin = ADC(Pin(6))
        self.z_pin.atten(ADC.ATTN_11DB)
        self.adc_y = y_pin
        self.pin_list = [self.adc_x, self.adc_y]
        self.sw_pin = Pin(sw_pin, Pin.IN, Pin.PULL_UP)
        self.e_pin = Pin(14, Pin.OUT)

    def set_channel(self, channel):
        for i in range(3):
            self.select_pins[i].value((channel >> i) & 1)

    def read_raw(self):
        self.e_pin.value(1)
        time.sleep_ms(10)
        x_y_val = [0, 0]
        self.e_pin.value(0)
        sw_val = self.sw_pin.value()
        for i, j in enumerate(self.pin_list):
            self.set_channel(j)
            time.sleep_ms(10)  # Allow MUX to stabilize
            x_y_val[i] = self.z_pin.read()

        return (x_y_val[0], x_y_val[1], sw_val)

    def calibrate(self):
        xs, ys = [], []
        for _ in range(20):
            x_val, y_val, _ = self.read_raw()
            time.sleep(0.1)
            xs.append(x_val)
            ys.append(y_val)
        center = (sum(xs) / len(xs) + sum(ys) / len(ys)) / 2
        deadzone = center * 0.85

        return center, deadzone

    def read_direction(self, center=1900, deadzone=300):
        x_val, y_val, sw_val = self.read_raw()

        if x_val < center - deadzone:
            x_dir = -1
        elif x_val > center + deadzone:
            x_dir = +1
        else:
            x_dir = 0

        if y_val < center - deadzone:
            y_dir = +1
        elif y_val > center + deadzone:
            y_dir = -1
        else:
            y_dir = 0

        return (x_dir, y_dir, sw_val)


if __name__ == "__main__":
    e = Pin(14, Pin.OUT)
    e.value(1)
    joystick1 = Joystick(x_pin=0, y_pin=1, sw_pin=3)
    # center, deadzone = joystick1.calibrate()
    e.value(0)
    while True:
        # x_dir, y_dir, sw_dir = joystick1.read_direction(center, deadzone)
        print(joystick1.read_raw())
    #         dir_msg = []
    #         dir_msg.append("Left" if x_dir < 0 else ("Right" if x_dir > 0 else "CenterX"))
    #         dir_msg.append("Up" if y_dir < 0 else ("Down" if y_dir > 0 else "CenterY"))
    #         dir_msg.append("Pressed" if sw_dir == 0 else "NotPressed")
    #         print("Direction:", dir_msg)
    time.sleep(0.3)
