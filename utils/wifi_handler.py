import time

import network


class WiFiHandler:

    def __init__(self, ssid: str, password: str):
        self.ssid = ssid
        self.password = password
        self.station = network.WLAN(network.STA_IF)

    def connect(self):
        if not self.station.active():
            self.station.active(True)

        # Print MAC address
        mac = ":".join(f"{b:02X}" for b in self.station.config("mac"))
        print(f"WiFi MAC address: {mac}")

        if self.station.isconnected():
            print("Already connected to Wi-Fi.")
            return

        print(f"Connecting to Wi-Fi: {self.ssid}")
        self.station.connect(self.ssid, self.password)

        while not self.station.isconnected():
            print(".", end="")
            time.sleep(0.5)
        print("\nConnected to Wi-Fi!\n")
