import const
from player import I2CMultiplexer, Player


class PokerGame:
    POSITIONS = ["SB", "BB", "UTG", "MP1", "MP2", "HJ", "CO", "BTN"]

    def __init__(self, money, multiplexer: I2CMultiplexer, sb=10, bb=20):
        self.money = money
        self.multiplexer = multiplexer
        self.pot = 0
        self.players: list[Player] = []
        self.bb = bb
        self.sb = sb
        self.d_pos = 0
        self.num_player = len(self.players)
        self.side_pots = []
        self.highest_bet = 0

    def post_blinds(self):
        sb_player = self.players[self.d_pos % self.num_player]
        bb_player = self.players[(self.d_pos + 1) % self.num_player]
        self.highest_bet = self.bb
        self.place_bet(sb_player, self.sb)
        self.place_bet(bb_player, self.bb)

    def add_player(self, player: Player):
        self.players.append(player)

    def place_bet(self, player, amount):
        amount = min(amount, player.money)
        player.money -= amount
        player.bet += amount
        self.pot += amount

    def award_pots(self):
        active_players = [p for p in self.players if not p.fold]
        if active_players:
            winner = active_players[0]
            winner.money += self.pot
        self.pot = 0
        self.side_pots = []

    def reset_bets(self):
        for p in self.players:
            p.bet = 0

    def assign_position(self):
        self.num_player = len(self.players)
        for i in range(self.num_player):
            seat_index = (self.d_pos + i) % self.num_player
            self.players[seat_index].set_position(self.POSITIONS[i])

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
            # clear cards if you wish, e.g. p.hole_cards = []
        self.d_pos = (self.d_pos + 1) % len(self.players)

    def betting_round(self, start_index=0, round_name=""):
        active_players = [p for p in self.players if not p.fold]
        num_active = len(active_players)
        if num_active <= 1:
            return

        if round_name:
            print(f"\n===== {round_name.upper()} ROUND =====")
            print(f"Starting {round_name} with {num_active} players active.")

        current_index = start_index % num_active
        players_to_act = num_active

        while True:
            for i, pl in enumerate(active_players):
                if i != current_index:
                    pl.draw_screen(self.pot, self.highest_bet, active=False)

            player = active_players[current_index]
            action, amount = player.draw_screen(
                pot=self.pot, highest_bet=self.highest_bet, active=True
            )

            print(f"[{player.position}] => {action}, Amount: {amount}")

            if action == "Fold":
                player.fold = True
                active_players.remove(player)
                num_active = len(active_players)
                if num_active <= 1:
                    break

                players_to_act -= 1

                if current_index >= num_active:
                    current_index = 0

            elif action == "Call":
                self.pot += amount
                players_to_act -= 1

            elif action == "Check":
                players_to_act -= 1

            elif action in ("Bet", "Raise"):
                diff = amount - self.highest_bet
                if diff > 0:
                    self.pot += diff
                    self.highest_bet = amount

                last_raiser_index = current_index
                players_to_act = num_active - 1

            if num_active <= 1:
                break
            if players_to_act <= 0:
                break

            current_index = (current_index + 1) % num_active

    def run_full_game(self):
        self.assign_position()
        self.give_money()

        self.post_blinds()

        # ---------------- PRE-FLOP ----------------
        print("\n===== PRE-FLOP ROUND =====")
        self.betting_round(
            start_index=(self.d_pos + 2) % len(self.players), round_name="Pre-Flop"
        )
        if self.check_if_one_player_left():
            self.award_pots()
            self.clean_up_for_next_hand()
            return

        # ---------------- FLOP ----------------
        print("\n===== FLOP ROUND =====")
        self.betting_round(
            start_index=(self.d_pos + 1) % len(self.players), round_name="Flop"
        )
        if self.check_if_one_player_left():
            self.award_pots()
            self.clean_up_for_next_hand()
            return

        # ---------------- TURN ----------------
        print("\n===== TURN ROUND =====")
        self.betting_round(
            start_index=(self.d_pos + 1) % len(self.players), round_name="Turn"
        )
        if self.check_if_one_player_left():
            self.award_pots()
            self.clean_up_for_next_hand()
            return

        print("\n===== RIVER ROUND =====")
        self.betting_round(
            start_index=(self.d_pos + 1) % len(self.players), round_name="River"
        )
        if self.check_if_one_player_left():
            self.award_pots()
            self.clean_up_for_next_hand()
            return

        self.award_pots()

        self.clean_up_for_next_hand()
