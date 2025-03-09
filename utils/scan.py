import time

from machine import Pin, SoftI2C

import const


def i2c_scan(i2c):
    for channel in range(8):
        i2c.writeto(const.I2C_ADDR, bytes([1 << channel]))
        time.sleep_ms(10)
        devices = i2c.scan()
        if devices and len(devices) > 1:
            print(f"Channel {channel}: found devices -> {[hex(d) for d in devices]}")


if __name__ == "__main__":
    i2c = SoftI2C(scl=Pin(const.SCL_PIN), sda=Pin(const.SDA_PIN))
    i2c_scan(i2c)