import time
import const

from player1 import Player,I2CMultiplexer

def get_poker_positions(num_players):
    if num_players < 2 or num_players > 10:
        raise ValueError("Poker requires 2-10 players.")

    positions = ["SB", "BB"] 

    if num_players >= 3:
        positions.append("UTG") 

    if num_players >= 4:
        positions.append("MP1")
    
    if num_players >= 5:
        positions.append("MP2") 
    
    if num_players >= 6:
        positions.append("HJ")  
    
    if num_players >= 7:
        positions.append("CO") 
    
    positions.append("BTN")

    seat_positions = {}
    for i in range(num_players):
        seat_positions[i] = positions[i % len(positions)]

    return seat_positions


if __name__ == "__main__":
    multiplexer = I2CMultiplexer(scl_pin=9, sda_pin=8)
    num_players = 3
    positions = get_poker_positions(num_players)
    players = [
        Player(multiplexer, channel=0, joystick_pins=(14, 13, 12), position=positions[0]),
        Player(multiplexer, channel=1, joystick_pins=(15, 16, 17), position=positions[1]),
    ]

    
    while True:
        for player in players:
            player.update_action()
            player.draw_screen(100)