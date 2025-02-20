import time

import ssd1306
from machine import Pin, SoftI2C

i2c = SoftI2C(scl=Pin(47), sda=Pin(48))
print("I2C initialized.")


def select_channel(channel):
    if 0 <= channel <= 7:
        i2c.writeto(0x70, bytes([1 << channel]))
        print(f"Channel {channel} selected.")
        time.sleep(0.1)  # Short delay for stability
    else:
        raise ValueError("Channel must be between 0 and 7")


def test_oled(channel, message):
    try:
        select_channel(channel)
        i2c_channel = SoftI2C(scl=Pin(47), sda=Pin(48))
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

    except Exception as e:
        print(f"Failed to test OLED on channel {channel}: {e}")


# Test OLED on Channel 2
test_oled(2, "Hello Display 1")

# Test OLED on Channel 3
test_oled(3, "Hello Display 2")

# Test OLED on Channel 4
# test_oled(1, "Hello Display 3")

print("Two OLED displays test completed.")
