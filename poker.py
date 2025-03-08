import time

import shared_mqtt
import ujson
from mqtt_handler import shared_data

import const
from config import TOPIC_PREFIX
from player import I2CMultiplexer, Player


class PokerGame:
    POSITIONS = [
        "D",
        "SB",
        "BB",
        "UTG",
    ]

    def __init__(self, money, multiplexer: I2CMultiplexer, sb=10, bb=20):
        self.money = money
        self.multiplexer = multiplexer
        self.pot = 0
        self.players: list[Player] = []
        self.bb = bb
        self.sb = sb
        self.d_pos = 0
        self.num_player = 0
        self.highest_bet = 0
        shared_mqtt.init_mqtt()

    def _display_inactive_players(self, players, active_index):
        for idx, p in enumerate(players):
            if idx != active_index:
                p.draw_screen(self.pot, self.highest_bet, active=False)

    def _handle_fold(self, players, index):
        p = players.pop(index)
        p.fold = True

    def _handle_call(self, player, amount):
        self.pot += amount
        shared_mqtt.publish_message(TOPIC_PREFIX + "/pot", str(self.pot))
        player.total += amount

    def place_blind_bet(self, player, amount):
        amount = min(amount, player.money)
        player.money -= amount
        player.bet += amount
        self.pot += amount
        player.total += amount
        shared_mqtt.publish_message(TOPIC_PREFIX + "/pot", str(self.pot))

    def _handle_bet_raise(self, player, amount):
        diff = amount - self.highest_bet
        print(self.bb, self.sb, diff)
        if diff > 0:
            self.pot += diff
            shared_mqtt.publish_message(TOPIC_PREFIX + "/pot", str(self.pot))
            self.highest_bet = amount
            player.total += amount

    def post_blinds(self):
        sb_player = self.players[self.d_pos + 1 % self.num_player]
        bb_player = self.players[(self.d_pos + 2) % self.num_player]
        self.highest_bet = self.bb
        self.place_blind_bet(sb_player, self.sb)
        self.place_blind_bet(bb_player, self.bb)

    def add_player(self, player: Player):
        self.players.append(player)

    def assign_position(self):
        n = len(self.players)
        if n == 0:
            return

        if n > 4:
            raise ValueError("This game is configured for a maximum of 4 players.")

        self.num_player = n

        for offset in range(n):
            seat_index = (self.d_pos + offset) % n
            position_abbr = self.POSITIONS[offset]
            self.players[seat_index].position = position_abbr

    def give_money(self):
        for player in self.players:
            player.set_money(self.money)

    def check_if_one_player_left(self):
        active_players = [p for p in self.players if not p.fold]
        return len(active_players) <= 1

    def clean_up_for_next_hand(self):
        self.pot = 0
        self.side_pots = []
        self.highest_bet = 0
        for p in self.players:
            p.bet = 0
            p.fold = False
        self.d_pos = (self.d_pos + 1) % len(self.players)

    def betting_round(self, start_index=0, round_name=""):
        active_players = [p for p in self.players if not p.fold and not p.allin]

        for p in self.players:
            status = "ALL-IN" if p.allin else ("active" if not p.fold else "fold")
            shared_mqtt.publish_message(
                TOPIC_PREFIX + f"/player{p.channel}",
                f"{p.money},{status},{p.position},None",
            )

        num_players = len(active_players)
        if num_players <= 1:
            return

        shared_mqtt.publish_message(TOPIC_PREFIX + f"/round_name", round_name)
        if round_name:
            print(f"\n===== {round_name.upper()} ROUND =====")
            print(f"Starting {round_name} with {num_players} players active.")

        current_index = start_index
        players_to_act = num_players

        while players_to_act > 0:
            # Find the next active player
            while self.players[current_index].fold or self.players[current_index].allin:
                current_index = (current_index + 1) % len(self.players)

            player = self.players[current_index]

            self._display_inactive_players(active_players, current_index)
            print("players to act :", players_to_act)

            action, amount = player.draw_screen(
                pot=self.pot, highest_bet=self.highest_bet, active=True
            )

            # Send player action info:
            status = (
                "ALL-IN" if player.allin else ("active" if not player.fold else "fold")
            )
            shared_mqtt.publish_message(
                TOPIC_PREFIX + f"/player{player.channel}",
                f"{player.money},{status},{player.position},{action}",
            )
            print(f"[{player.position}] => {action}, Amount: {amount}")

            if action == "Fold":
                player.fold = True
                players_to_act -= 1

            elif action == "Call":
                self._handle_call(player, amount)
                players_to_act -= 1

            elif action == "Check":
                players_to_act -= 1

            elif action in ("Bet", "Raise"):
                self._handle_bet_raise(player, amount)
                players_to_act = num_players - 1  # Reset for a new betting round

            if num_players <= 1 or players_to_act <= 0:
                break

            # Move to the next player in turn order
            current_index = (current_index + 1) % len(self.players)

    def awards(self, timeout=300):
        print("Waiting for 'awards' data...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            shared_mqtt.check_messages()
            if "awards" in shared_data:
                try:
                    data = ujson.loads(shared_data["awards"])
                    for p, m in zip(self.players, data):
                        if m > 0:
                            print(f"Player {p.channel} wins +{m}")
                            p.money += m
                    del shared_data["awards"]
                    return
                except ValueError:
                    print("Invalid JSON for awards. Ignoring this message.")
                    del shared_data["awards"]
            time.sleep(0.25)
        print("No awards message received within the timeout.")

    def run_full_game(self):
        self.assign_position()
        self.post_blinds()

        rounds = [
            (
                "Pre-Flop",
                (
                    self.d_pos
                    if len(self.players) == 2
                    else (self.d_pos + 3) % len(self.players)
                ),
            ),
            ("Flop", (self.d_pos + 1) % len(self.players)),
            ("Turn", (self.d_pos + 1) % len(self.players)),
            ("River", (self.d_pos + 1) % len(self.players)),
        ]

        for round_name, start_index in rounds:
            self.betting_round(start_index=start_index, round_name=round_name)
            if self.check_if_one_player_left():
                self.clean_up_for_next_hand()
                return

        player_remain = [p.channel if not p.fold else 0 for p in self.players]
        print("Remaining Players:", player_remain)
        shared_mqtt.publish_message(
            TOPIC_PREFIX + "/players_remain", str(player_remain)
        )
        player_bet = [p.total for p in self.players]
        print("Players Bet:", player_bet)
        shared_mqtt.publish_message(TOPIC_PREFIX + "/players_bet", str(player_bet))

        self.awards()
        self.clean_up_for_next_hand()
