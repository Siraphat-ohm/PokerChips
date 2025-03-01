import time

from machine import ADC, Pin, SoftI2C

import ssd1306

i2c = SoftI2C(scl=Pin(9), sda=Pin(8))


def select_channel(channel):
    """Select the I2C channel on the multiplexer."""
    if 0 <= channel <= 7:
        i2c.writeto(0x70, bytes([1 << channel]))
        print(f"Channel {channel} selected.")
        time.sleep(0.1)
    else:
        raise ValueError("Channel must be between 0 and 7")


def test_oled(channel, message):
    """Test the OLED display on the specified channel with a custom message."""
    try:
        select_channel(channel)

        i2c_channel = SoftI2C(scl=Pin(9), sda=Pin(8))
        devices = i2c_channel.scan()
        print(f"Devices on channel {channel}: {[hex(d) for d in devices]}")

        if 0x3C not in devices and 0x3D not in devices:
            raise OSError(f"No SSD1306 display found on channel {channel}!")

        oled = ssd1306.SSD1306_I2C(128, 64, i2c_channel)

        oled.fill(0)
        oled.text(f"{message}", 0, 0, 1)
        oled.text(f"Channel {channel}", 0, 16, 1)
        oled.text("I2C Working!", 0, 32, 1)
        oled.show()

        print(f"Display on channel {channel} tested successfully.")
        return oled

    except Exception as e:
        print(f"Failed to test OLED on channel {channel}: {e}")
        return None


oled = test_oled(1, "Poker Game")

if not oled:
    print("OLED initialization failed. Exiting.")
