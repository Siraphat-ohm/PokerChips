from machine import Pin
from time import sleep

# Define keypad matrix layout
keypad = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

# Define row and column pins
row_pins = [Pin(15, Pin.OUT),Pin(16, Pin.OUT),Pin(17, Pin.OUT),Pin(18, Pin.OUT)]
col_pins = [Pin(8, Pin.IN, Pin.PULL_DOWN),Pin(3, Pin.IN, Pin.PULL_DOWN),Pin(46, Pin.IN, Pin.PULL_DOWN),Pin(9, Pin.IN, Pin.PULL_DOWN)]

def scan_keypad():
    for row_index, row in enumerate(row_pins):
        row.value(1)  # Set current row HIGH
        for col_index, col in enumerate(col_pins):
            if col.value() == 1:  # If column is HIGH, key is pressed
                print("Key Pressed:", keypad[row_index][col_index])
                sleep(0.3)  # Debounce delay
        row.value(0)  # Reset row to LOW

while True:
    scan_keypad()
