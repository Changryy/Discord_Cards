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
    def __init__(self, value, suit, game_id):
        self.value = value
        self.suit = suit
        self.name = CARDS[value]
        self.game_id = game_id
        self.deck = None
        self.wielder = None

    def __str__(self):
        return "card"
        
    def display(self):
        return self.name + " of " + self.suit

    def __gt__(self, other):
        if type(other) is Card: return self.value > other.value
        else: return self.value > other
    
    def __ls__(self, other):
        if type(other) is Card: return self.value < other.value
        else: return self.value < other

    def __eq__(self, other):
        if type(other) is Card: return self.value == other.value
        else: return self.value == other
    
    def __ne__(self, other):
        if type(other) is Card: return self.value != other.value
        else: return self.value != other

# --------------------------------------------------------------------

games = []

EMOJI = {
    "use":"⤴️",
    "skip":"⏩"
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
        new_game = {
            "owner_id" : user.id,
            "channel_id" : message.channel.id,
            "game_type" : "Durak",
            "start_time" : None,
            "deck" : build_deck("Durak", game_id),
            "trump" : None,
            "trump_in_deck": True,
            "attacker" : 0,
            "cards" : [],
            "attack_card" : None,
            "players" : [{"player_id":user.id,"player_name":user.display_name,"hand":[],"skipped":False}]
        }
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
        if True in [True if user.id == x["player_id"] else False for x in game["players"]]:
            await message.channel.send("You are already in the game.")
            return
        # errors #

        game["players"].append({"player_id":user.id,"player_name":user.display_name,"hand":[],"skipped":False})
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
            # errors #
            if len(game["players"]) == 1:
                await message.channel.send("Game requires a minimum of 2 players.")
                return
            if len(game["players"]) > 5:
                await message.channel.send("Game cannot exceed the player limit of 5.")
                return
            # errors #

            trump = game["deck"].pop() # assign trump
            game["trump"] = trump
            await message.channel.send(f"{trump.suit} is trump!\n{trump.display()}")
            for p in game["players"]: # deal cards
                draw(game["deck"], p["hand"], 6, p["player_id"])
                await user.create_dm()
                sort(p["hand"])
                for card in [x for x in p["hand"]]:
                    await send_card(card,user.dm_channel,[EMOJI["use"]])
            
            await message.channel.send(durak_turn_msg(game)[1:])

    if msg in ["s",".s","sort",".sort"] and msgtype == "private":
        for x in games:
            for p in x["players"]:
                if p["player_id"] == user.id:
                    async for msg_item in message.channel.history(limit=len(p["hand"])+1):
                        if msg_item.author == client.user:
                            await msg_item.delete()
                    sort(p["hand"])
                    for card in p["hand"]:
                        await send_card(card,message.channel,[EMOJI["use"]])



# --------------------------------------------------------------------

@client.event
async def on_reaction_add(reaction, user):
    global games
    global cards_by_id
    command = get_key(reaction.emoji, EMOJI)
    channel = reaction.message.channel
    if user == client.user: return


    # COMMANDS #

    if command == "use":
        try:
            card = cards_by_id[reaction.message.id]
            game = games[card.game_id]
        except: return
    
        await reaction.message.delete()
        
        if game["game_type"] == "Durak":
            defender = game["players"][ (game["attacker"]+1) % len(game["players"]) ]["player_id"]


            if len(game["cards"])%2 == 0 and card.wielder != defender: # attacker code
                
                if len(game["cards"]) >= 11: # send error if an attacker tries to attack with a 7th card
                    await channel.send("Cannot attack with more than 6 cards in a bout.")
                    return

                if card.wielder == game["players"][game["attacker"]]["player_id"] and len(game["cards"]) == 0: # main attack
                    insert(card, game["cards"])
                    await send_card(card,client.get_channel(game["channel_id"]),[EMOJI["skip"]])
                    game["attack_card"] = card
                
                elif len(game["cards"]) > 0: # other attacks
                    insert(card, game["cards"])
                    await send_card(card,client.get_channel(game["channel_id"]),[EMOJI["skip"]])
                    game["attack_card"] = card
    

            elif len(game["cards"])%2 == 1 and card.wielder == defender: # defender code
                
                if card.suit == game["cards"][-1].suit and card > game["cards"][-1]: # defend if same suit and card is greater
                    insert(card, game["cards"])
                    await send_card(card,client.get_channel(game["channel_id"]),[EMOJI["skip"]])

                elif card.suit == game["trump"].suit and card > game["cards"][-1]: # defend if trump and card is greater 
                    insert(card, game["cards"])
                    await send_card(card,client.get_channel(game["channel_id"]),[EMOJI["skip"]])

                else:
                    await channel.send("Invalid card.")
                
                if next_durak_bout(game): # NEXT TURN
                    await client.get_channel(game["channel_id"]).send("*Attackers gave up.*"+durak_turn_msg(game))
                    for p in game["players"]:
                        if True in [True if card.wielder == None else False for card in p["hand"]]:
                            card.wielder = p["player_id"]
                            await send_card(card,client.get_channel(game["channel_id"]),[EMOJI["skip"]])
            


    elif command == "skip":
        try:
            game = list(filter(lambda a: a != None, [x if x["channel_id"] == channel.id else None for x in games] ))[0]
        except: return
        if not user.id in [x["player_id"] for x in game["players"]]: return

        
        if game["game_type"] == "Durak":
            defender_index = (game["attacker"]+1) % len(game["players"])
            defender = game["players"][defender_index]["player_id"]


            if user.id == defender: # if defender skips he gets all the cards  # NEXT TURN
                draw(game["cards"], game["players"][defender_index]["hand"], len(game["cards"]), user.id)
                game["attacker"] = (defender_index+1) % len(game["players"])
                
                durak_replenish(game, (defender_index-1) % len(game["players"]))
                await channel.send("*"+user.display_name+"picked up all the cards.*"+durak_turn_msg(game))
                for p in game["players"]:
                    if True in [True if card.wielder == None else False for card in p["hand"]]:
                        card.wielder = p["player_id"]
                        bot_msg = await client.get_user(p["player_id"]).dm_channel.send(card.display())
                        await bot_msg.add_reaction(EMOJI["use"])

            else: # player skip recognition
                skipped_users = []
                async for u in reaction.users(): skipped_users.append(u.id)
                for p in game["players"]:
                    if p["player_id"] == user.id: p["skipped"] = True
                    elif p["skipped"] and p["player_id"] in skipped_users: p["skipped"] = False

                if next_durak_bout(game): # NEXT TURN
                    await channel.send("*Attackers gave up.*"+durak_turn_msg(game))
                    for p in game["players"]:
                        if True in [True if card.wielder == None else False for card in p["hand"]]:
                            card.wielder = p["player_id"]
                            send_card(card,client.get_user(p["player_id"]).dm_channel,[EMOJI["use"]])

                
        
# --------------------------------------------------------------------

def next_durak_bout(game): # next bout if everybody skipped and defender defended
    if (not False in [x["skipped"] for x in game["players"]]) and len(game["cards"]) % 2 == 0:
        attacker = game["attacker"]
        game["cards"] = []
        game["attacker"] = (attacker+1) % len(game["players"])
        durak_replenish(game, attacker)
    return (not False in [x["skipped"] for x in game["players"]]) and len(game["cards"]) % 2 == 0

def durak_replenish(game, attacker): # replenish cards
    d_cards = len(game["deck"])
    if d_cards == 0: return
    p_count = len(game["players"])
    players = [game["players"][attacker]] # attacker
    players += [game["players"][(x+attacker+2)%p_count] for x in range(p_count-2)] # other attackers
    players.append(game["players"][(attacker-1)%p_count]) # defender

    for p in players:
        p_cards = len(p["hand"])
        if 6-p_cards > d_cards: # if player needs more cards than the deck can offer
            draw(game["deck"], p["hand"], d_cards, None)
            draw([deepcopy(game["trump"])], p["hand"], 1, None)
            game["trump_in_deck"] = False
            break
        else: # normal refill
            draw(game["deck"], p["hand"], 6-p_cards, None)
    
def durak_turn_msg(game): # message at the end of the turn
    a = game["players"][game["attacker"]]["player_name"]
    d = game["players"][(game["attacker"]+1)%len(game["players"])]["player_name"]
    d_cards = len(game["deck"])

    msg = "\nThere " # talon cards
    if game["trump_in_deck"]:
        if d_cards > 0:
            msg += "are "+str(d_cards+1)+" cards left in the talon.\n"
        else:
            msg += "is only the trump left of the talon.\n"
    
    else: # player cards
        msg += "are no cards left in the talon.\n__Cards left in each players hand:__\n"
        for p in game["players"]:
            p["player_name"] +" - "+ str(len(p["hand"])) + "\n"
    
    return msg + "**" + a + "'s turn to attack" + d + "!**"


# --------------------------------------------------------------------

get_key = lambda value, dictionary : list(filter(lambda a: a != None, [x if dictionary[x] == value else None for x in dictionary] ))[0]

def sort(cards):
    cards.sort(key=lambda x: SUITS.index(x.suit)*100 - x.value)

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
    global cards_by_id
    for _ in range(amount):
        card = from_deck.pop()
        card.deck = to_deck
        card.wielder = player_id
        to_deck.append(card)

def insert(card, deck):
    card.deck.remove(card)
    card.deck = deck
    deck.append(card)

async def send_card(card, channel, reactions):
    global cards_by_id
    bot_msg = await channel.send(card.display())
    card.discord_id = bot_msg.id
    cards_by_id[card.discord_id] = card
    for emoji in reactions:
        await bot_msg.add_reaction(emoji)

# --------------------------------------------------------------------

client.run(token)

