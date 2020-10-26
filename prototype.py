import discord
from random import shuffle
import re
import emoji
import sys
import json
import string
from copy import deepcopy
from datetime import datetime

SUITS = ["Diamonds","Hearts","Clubs","Spades"]
CARDS = ["0","Ace","2","3","4","5","6","7","8","9","10","Jack","Queen","King","Ace"]

class card:
    def __init__(self, val, suit):
        self.val = val
        self.suit = suit
        self.name = CARDS[val]

    def __str__(self):
        return "card"
    
    def value(self):
        return (self.val, self.suit, self.name)
    
    def display(self):
        return self.name + " of " + self.suit

    def __getitem__(self, key):
        return self.value()[key]

    def __gt__(self, other):
        if type(other) is card: return self.val > other.val
        else: return self.val > other
    
    def __ls__(self, other):
        if type(other) is card: return self.val < other.val
        else: return self.val < other

    def __eq__(self, other):
        if type(other) is card: return self.val == other.val
        else: return self.val == other
    
    def __ne__(self, other):
        if type(other) is card: return self.val != other.val
        else: return self.val != other





def build_deck(game):
    deck = []
    if game == "durak" or game == "standard":
        for suit in ["Clubs","Diamonds","Hearts","Spades"]:
            for value in range(1 if game == "standard" else 6, 14):
                new_card = card(value, suit)
                deck.append(new_card)
    shuffle(deck)
    return deck


game = {}
game["owner_id"] = 123
game["channel_id"] = 456
game["game_type"] = "durak"
game["start_time"] = datetime.utcnow().__str__() + " UTC"
game["deck"] = build_deck("durak")
game["data"] = {"attacker_id":321,"defender_id":123,"board":[]}


