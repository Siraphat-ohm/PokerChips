import time

import const
from machine import Pin
from player import I2CMultiplexer, Player
from poker import PokerGame

multiplexer = I2CMultiplexer(const.SCL_PIN, const.SDA_PIN)


game = PokerGame(money=1000, multiplexer=multiplexer, sb=10, bb=20)
