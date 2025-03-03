import time

import const
from machine import Pin
from player import I2CMultiplexer, Player
from poker import PokerGame

multiplexer = I2CMultiplexer(const.SCL_PIN, const.SDA_PIN)


game = PokerGame(money=10000, multiplexer=multiplexer, sb=10, bb=20)

for conf in const.PLAYER_CONFIG:
    print(conf)
    game.add_player(Player(multiplexer, conf['channel'], conf['joystick_pins']))
    
game.run_full_game()
