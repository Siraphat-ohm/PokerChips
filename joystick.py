import machine


class Joystick:
    def __init__(self, x_pin: int, y_pin: int, sw_pin: int):
        self.x_adc = machine.ADC(machine.Pin(x_pin))
        self.y_adc = machine.ADC(machine.Pin(y_pin))

        self.x_adc.atten(machine.ADC.ATTN_11DB)  # Full range 0-3.3V
        self.y_adc.atten(machine.ADC.ATTN_11DB)

        self.sw_pin = machine.Pin(sw_pin, machine.Pin.IN)

    def read(self):
        return (self.x_adc.read(), self.y_adc.read(), self.sw_pin.value())
