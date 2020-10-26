import discord
from random import shuffle
import re
import emoji
import sys
import json
import string
from copy import deepcopy
from datetime import datetime

token = "NDM2OTMyMTc2MjM2MzgwMTYw.WtoazA.npoZRpWrFSQLLAlay90Vz70L57Q"
client = discord.Client()

VERSION = "0.0.0"

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
    "players":[],
    "deck":[]
}

def search(games, owner_id, channel_id):
    mylist = [x for x in games if x['owner_id']==owner_id and x['channel_id']==channel_id]
    assert(len(mylist)==1)
    return mylist[0]

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

    if message.content.lower() == "start durak":
        new_game = {}
        new_game["owner_id"] = user.id
        new_game["channel_id"] = message.channel.id
        new_game["game_type"] = "durak"
        new_game["start_time"] = datetime.utcnow().__str__() + " UTC"
        new_game["deck"] = build_deck("durak")
        new_game["data"] = {"attacker_id":0,"defender_id":0,}
        new_game["player"]
        games.append(new_game)
        await message.channel.send(f"**__Starting a game of Durak!__**\nGame owner: {user.display_name}\n*Join with* `.join (game owner)`")

    if message.content.lower() == ".join":
        mention = re.findall(r"<@[!&]\d+>(?=\W*?\w)", message.content)[0]
        mention = int(mention[3:len(mention)-1])

        for game in games:
            if game["channel_id"] == message.channel.id and game["owner_id"] == mention:
                {"player_id":0,"hand":[]}



def build_deck(game):
    deck = []
    if game == "durak" or game == "standard":
        for suit in ["Clubs","Diamonds","Hearts","Spades"]:
            for value in range(1 if game == "standard" else 6, 14):
                new_card = card(value, suit)
                deck.append(new_card)
    shuffle(deck)
    return deck

def draw(deck, amount):
    cards = []
    for i in range(amount):
        cards.append(deck.pop())
    return cards

client.run(token)
