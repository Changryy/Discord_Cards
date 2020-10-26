import discord
from random import shuffle
import re
import emoji
import sys
import json
import string
from copy import deepcopy
from datetime import datetime

token = ""
client = discord.Client()

VERSION = "0.0.0"

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

games = []
GAME_TEMPLATE = {
    "owner_id":0,
    "channel_id":0,
    "game_type":"",
    "start_time":"",
    "players":[{"player_id":0,"player_name":"","hand":[]}],
    "data":{},
    "deck":[]
}

EMOJI = {
    "use":"⤴️"
}


### ON READY
@client.event
async def on_ready():
    pass


@client.event
async def on_message(message):
    #info
    global games
    user = message.author
    msgtype = str(message.channel.type)
    #info

    if user == client.user: return

    game = None
    for x in games:
        if x["channel_id"] == message.channel.id:
            game = x


    # COMMANDS #

    if message.content.lower() == ".durak":
        # errors #
        if not game is None:
            await message.channel.send("A game has already started in this channel.")
            return
        # errors #

        new_game = {}
        new_game["owner_id"] = user.id
        new_game["channel_id"] = message.channel.id
        new_game["game_type"] = "Durak"
        new_game["start_time"] = ""
        new_game["deck"] = build_deck("Durak")
        new_game["data"] = {"trump":"","attacker":0,"cards":[],"attack_card":None}
        new_game["players"] = [{"player_id":user.id,"player_name":user.display_name,"hand":[]}]
        games.append(new_game)
        await message.channel.send(f"**Starting a game of Durak!**\nGame owner: {user.display_name}\nJoin with `.join`")

    if message.content.lower() == ".join":
        # errors #
        if game is None:
            await message.channel.send("There are no ongoing games in this channel.")
            return
        if game["start_time"] != "": # return error if game has already started
            await message.channel.send("Game has already started.")
            return
        # errors #

        game["players"].append({"player_id":user.id,"player_name":user.display_name,"hand":[]})
        await message.channel.send(f"{user.display_name} joined the game!")
    
    if message.content.lower() == ".start":
        # errors #
        if game is None:
            await message.channel.send("There are no pending games in this channel.")
            return
        if game["start_time"] != "": # return error if game has already started
            await message.channel.send("Game has already started.")
            return
        if game["owner_id"] != user.id:
            await message.channel.send("You are not the owner of this game.")
            return
        # errors #

        game["start_time"] = datetime.utcnow().__str__() + " UTC" # set start time

        if game["game_type"] == "Durak":
            
            trump = game["deck"].pop() # assign trump
            game["data"]["trump"] = trump.suit
            await message.channel.send(f"{trump.suit} is trump!\n{trump.display()}")
            for p in range(len(game["players"])): # deal cards
                draw(game["deck"], game["players"][p]["hand"], 6)
                await user.create_dm()
                sort(game["players"][p]["hand"])
                for card_name in [x.display() for x in game["players"][p]["hand"]]:
                    bot_msg = await user.dm_channel.send(card_name)
                    await bot_msg.add_reaction(EMOJI["use"])



def sort(cards):
    cards.sort(key=lambda x: SUITS.index(x.suit)*100 - x.val)


def build_deck(game):
    deck = []
    if game == "Durak" or game == "standard":
        for suit in SUITS:
            for value in range(1 if game == "standard" else 6, 15):
                new_card = card(value, suit)
                deck.append(new_card)
    shuffle(deck)
    return deck

def draw(from_deck, to_deck, amount):
    for _ in range(amount): to_deck.append(from_deck.pop())

client.run(token)
