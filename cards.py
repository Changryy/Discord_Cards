import discord
from random import shuffle
import re
import emoji
import sys
import json
import string
from copy import deepcopy
from datetime import datetime

# --------------------------------------------------------------------

token = ""
client = discord.Client()

VERSION = "0.0.0"

# --------------------------------------------------------------------

SUITS = ["Diamonds","Hearts","Clubs","Spades"]
CARDS = ["0","Ace","2","3","4","5","6","7","8","9","10","Jack","Queen","King","Ace"]

cards_by_id = {}

class Card:
    def __init__(self, val, suit, game_id):
        self.val = val
        self.suit = suit
        self.name = CARDS[val]
        self.game_id = game_id
        self.deck = None
        self.wielder = None

    def __str__(self):
        return "card"
    
    def value(self):
        return (self.val, self.suit, self.name)
    
    def display(self):
        return self.name + " of " + self.suit

    def __getitem__(self, key):
        return self.value()[key]

    def __gt__(self, other):
        if type(other) is Card: return self.val > other.val
        else: return self.val > other
    
    def __ls__(self, other):
        if type(other) is Card: return self.val < other.val
        else: return self.val < other

    def __eq__(self, other):
        if type(other) is Card: return self.val == other.val
        else: return self.val == other
    
    def __ne__(self, other):
        if type(other) is Card: return self.val != other.val
        else: return self.val != other

# --------------------------------------------------------------------

games = []
GAME_TEMPLATE = {
    "owner_id":0,
    "channel_id":0,
    "game_type":None,
    "start_time":None,
    "players":[{"player_id":0,"player_name":"","hand":[]}],
    "data":{},
    "deck":[]
}

EMOJI = {
    "use":"⤴️"
}

# --------------------------------------------------------------------

### ON READY
@client.event
async def on_ready():
    pass

# --------------------------------------------------------------------

@client.event
async def on_message(message):
    #info
    global games
    global cards_by_id
    user = message.author
    msg = message.content.lower()
    msgtype = str(message.channel.type)
    #info

    if user == client.user: return

    game = None
    for x in games:
        if x["channel_id"] == message.channel.id:
            game = x


    # COMMANDS #

    if msg == ".durak":
        # errors #
        if not game is None:
            await message.channel.send("A game has already started in this channel.")
            return
        # errors #

        game_id = len(games)
        new_game = deepcopy(GAME_TEMPLATE)
        new_game["owner_id"] = user.id
        new_game["channel_id"] = message.channel.id
        new_game["game_type"] = "Durak"
        new_game["deck"] = build_deck("Durak", game_id)
        new_game["data"] = {"trump":"","attacker":0,"cards":[],"attack_card":None}
        new_game["players"] = [{"player_id":user.id,"player_name":user.display_name,"hand":[]}]
        games.append(new_game)
        await message.channel.send(f"**Starting a game of Durak!**\nGame owner: {user.display_name}\nJoin with `.join`")

    if msg == ".join":
        # errors #
        if game is None:
            await message.channel.send("There are no ongoing games in this channel.")
            return
        if game["start_time"] != None: # return error if game has already started
            await message.channel.send("Game has already started.")
            return
        # errors #

        game["players"].append({"player_id":user.id,"player_name":user.display_name,"hand":[]})
        await message.channel.send(f"{user.display_name} joined the game!")
    
    if msg == ".start":
        # errors #
        if game is None:
            await message.channel.send("There are no pending games in this channel.")
            return
        if game["start_time"] != None: # return error if game has already started
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
                draw(game["deck"], game["players"][p]["hand"], 6, game["players"][p]["player_id"])
                await user.create_dm()
                sort(game["players"][p]["hand"])
                for card in [x for x in game["players"][p]["hand"]]:
                    bot_msg = await user.dm_channel.send(card.display())
                    card.discord_id = bot_msg.id
                    cards_by_id[card.discord_id] = card
                    await bot_msg.add_reaction(EMOJI["use"])

    if msg in ["s",".s","sort",".sort"] and msgtype == "private":
        for x in games:
            for p in x["players"]:
                if p["player_id"] == user.id:
                    async for msg_item in message.channel.history(limit=len(p["hand"])+1):
                        if msg_item.author == client.user:
                            await msg_item.delete()


# --------------------------------------------------------------------

@client.event
async def on_reaction_add(reaction, user):
    global games
    global cards_by_id
    command = get_key(reaction.emoji, EMOJI)
    if user == client.user: return

    if command == "use":
        card = cards_by_id[reaction.message.id]
        game = games[card.game_id]
        
        
        if game["game_type"] == "Durak":
            if game["data"]["attacker"] == card.wielder:
                pass

# --------------------------------------------------------------------

def get_key(value, dictionary): # gets key by its value
    for x in dictionary:
        if dictionary[x] == value:
            return x

def sort(cards):
    cards.sort(key=lambda x: SUITS.index(x.suit)*100 - x.val)

def build_deck(game_type, game_id):
    deck = []
    if game_type == "Durak" or game_type == "standard":
        for suit in SUITS:
            for value in range(1 if game_type == "standard" else 6, 15):
                new_card = Card(value, suit, game_id)
                deck.append(new_card)
    shuffle(deck)
    return deck

def draw(from_deck, to_deck, amount, player_id=None):
    for _ in range(amount):
        card = from_deck.pop()
        card.deck = to_deck
        card.wielder = player_id
        to_deck.append(card)




client.run(token)

