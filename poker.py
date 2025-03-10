import time

import shared_mqtt
import ujson
from logs import log
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
        player.total += amount
        shared_mqtt.publish_message(TOPIC_PREFIX + "/pot", str(self.pot))

    def place_blind_bet(self, player, amount):
        amount = min(amount, player.money)
        player.money -= amount
        player.bet += amount
        self.pot += amount
        player.total += amount
        shared_mqtt.publish_message(TOPIC_PREFIX + "/pot", str(self.pot))

    def _handle_bet_raise(self, player, amount):

        self.pot += amount
        self.highest_bet = player.bet
        print(f"[{player.position}] {player.bet}")
        player.total += amount
        shared_mqtt.publish_message(TOPIC_PREFIX + "/pot", str(self.pot))

    def post_blinds(self):
        sb_player = self.players[(self.d_pos + 1) % self.num_player]
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

    def awards(self, timeout=300):
        log("[shared_mqtt] Waiting for 'awards' data...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            shared_mqtt.check_messages()
            if "awards" in shared_data:
                try:
                    data = ujson.loads(shared_data["awards"])
                    for p, m in zip(self.players, data):
                        if m > 0:
                            log(f"Player {p.channel} wins +{m}")
                            p.draw_text(f"+ ${m}")
                            p.money += m
                    del shared_data["awards"]
                    return
                except ValueError:
                    log("Invalid JSON for awards. Ignoring this message.")
                    del shared_data["awards"]
            time.sleep(0.25)
        log("No awards message received within the timeout.")

    def give_money(self):
        for player in self.players:
            player.set_money(self.money)

    def clear_screen_players(self):
        for p in self.players:
            p.oled.fill(0)

    def clean_up_for_next_hand(self):
        log("Cleaning for next hand")
        self.pot = 0
        self.side_pots = []
        self.highest_bet = 0
        for p in self.players:
            p.bet = 0
            p.fold = False
            p.allin = False
            p.total = 0
        players = []
        for p in self.players:
            if p.money > 0:
                players.append(p)
            else:
                p.draw_text("BROKE ASS")

        self.players = players
        self.num_player = len(self.players)
        self.d_pos = (self.d_pos + 1) % self.num_player

    def betting_round(self, start_index=0, round_name=""):
        for p in self.players:
            p.draw_screen(self.pot)
        active_players = [p for p in self.players if not p.fold and not p.allin]

        for p in self.players:
            status = "ALL-IN" if p.allin else ("active" if not p.fold else "fold")
            shared_mqtt.publish_message(
                TOPIC_PREFIX + f"/player{p.channel}",
                f"{p.money},{status},{p.position},None",
            )

        num_active = len(active_players)
        if num_active <= 1:
            return active_players

        shared_mqtt.publish_message(TOPIC_PREFIX + f"/round_name", round_name)
        if round_name:
            log(f"\n===== {round_name.upper()} ROUND =====")
            log(f"Starting {round_name} with {num_active} players active.")

        current_index = start_index
        players_to_act = num_active

        while players_to_act > 0:
            if len([p for p in self.players if not p.fold]) <= 1:
                break

            while self.players[current_index].fold or self.players[current_index].allin:
                current_index = (current_index + 1) % len(self.players)

            player = self.players[current_index]
            self._display_inactive_players(active_players, current_index)
            # log("players to act:", players_to_act)

            action, amount = player.draw_screen(
                pot=self.pot, highest_bet=self.highest_bet, active=True
            )

            status = (
                "ALL-IN" if player.allin else ("active" if not player.fold else "fold")
            )
            shared_mqtt.publish_message(
                TOPIC_PREFIX + f"/player{player.channel}",
                f"{player.money},{status},{player.position},{action}",
            )
            log(f"[{player.position}] => {action}, Amount: {amount}")

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
                active_players = [p for p in self.players if not p.fold and not p.allin]
                if not player.allin:
                    players_to_act = len(active_players) - 1
                else:
                    players_to_act = len(active_players)

            if len([p for p in self.players if not p.fold]) <= 1 or players_to_act <= 0:
                break
            player_bet = [p.total for p in self.players]
            # log("Players Bet:", player_bet)
            current_index = (current_index + 1) % len(self.players)

        self.highest_bet = 0
        for p in self.players:
            p.bet = 0
        active_players = [p for p in self.players if not p.fold]
        return active_players

    def run_full_game(self):
        self.assign_position()
        self.post_blinds()
        print("SUM", sum([p.money for p in self.players]) + self.pot)
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
            active_players = self.betting_round(
                start_index=start_index, round_name=round_name
            )
            remaining = [p for p in self.players if not p.fold]
            if len(remaining) == 1:
                winner = remaining[0]
                winner.money += self.pot
                winner.draw_text(f"+ ${self.pot}")
                log(f"Player {winner.channel} wins the pot of {self.pot} by default!")
                self.clean_up_for_next_hand()
                return

        player_remain = [p.channel if not p.fold else 0 for p in self.players]
        while len(player_remain) < 4:
            player_remain.append(0)

        # log("Remaining Players:", player_remain)
        shared_mqtt.publish_message(
            TOPIC_PREFIX + "/players_remain", str(player_remain)
        )

        player_money = [p.total for p in self.players]
        while len(player_money) < 4:
            player_money.append(0)

        # log("Players Money:", player_money)
        shared_mqtt.publish_message(TOPIC_PREFIX + "/players_bet", str(player_money))

        self.awards()
        self.clean_up_for_next_hand()
