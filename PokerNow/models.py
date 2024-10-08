from enum import Enum, auto

class Card:
    @staticmethod
    def parse_card_class(card_class):
        parts = card_class.split()
        suit = None
        rank = None
        for part in parts:
            if part.startswith("card-s-"):
                rank = part.split("-")[-1].upper()
                rank_dict = {'2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9', 'T': '10', 'J': 'Jack', 'Q': 'Queen', 'K': 'King', 'A': 'Ace'}
                rank = rank_dict.get(rank, rank)
            elif part in ["card-c", "card-d", "card-h", "card-s"]:
                suit_dict = {"card-c": "Clubs", "card-d": "Diamonds", "card-h": "Hearts", "card-s": "Spades"}
                suit = suit_dict.get(part)
        return f'{rank} of {suit}' if rank and suit else 'Unknown Card'
        
class GameState:
    def __init__(self, game_type, pot_size, community_cards, players, dealer_position, current_player, blinds, winners=None, is_your_turn=False):
        self.game_type = game_type
        self.pot_size = pot_size
        self.community_cards = community_cards
        self.players = players
        self.dealer_position = dealer_position
        self.current_player = current_player
        self.blinds = blinds
        self.winners = winners
        self.is_your_turn = is_your_turn

POSITION_NAMES = {
    0: "SB",
    1: "BB",
    2: "UTG",
    3: "UTG+1",
    4: "LJ",
    5: "HJ",
    6: "CO",
    7: "BTN"
}

#removed cards

class PlayerInfo:
    def __init__(self, name, stack, bet_value, status, position, position_name):
        self.name = name
        self.stack = stack
        self.bet_value = bet_value
        self.status = status
        self.position = position
        self.position_name = position_name
        self.position_number = [k for k, v in POSITION_NAMES.items() if v == position_name][0]

class PlayerState(Enum):
    CURRENT = auto()
    ACTIVE = auto()
    FOLDED = auto()
    OFFLINE = auto()


