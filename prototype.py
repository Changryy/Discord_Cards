import discord
from random import shuffle
import re
import emoji
import sys
import json
import string
from copy import deepcopy
from datetime import datetime



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


