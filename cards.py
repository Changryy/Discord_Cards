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

def assert_(cond):
    if not cond:
        import pdb; pdb.set_trace()
    assert(cond)

class UserError(Exception):
    pass

class Game(dict):
    async def client_delete_cards(self):
        pass

    async def delete_card_at_client_side(self, comm):
        pass
    
    async def send_card(self, card, reactions, private=False, channel=None):
        print(f"sending card {card.display()} ... possible reactions: " + " ".join(reactions))

    async def use_card(self, card, comm=None):
        if self["game_type"] == "Durak":
            defender = self["players"][ (self["attacker"]+1) % len(self["players"]) ]["player_id"]

            if not card.wielder:
                raise UserError("Card has already been played")
            if bool(len(self["cards"])%2) != bool(card.wielder == defender):
                raise UserError("It's not your turn to play")
            
            if len(self["cards"])%2 == 0 and card.wielder != defender: # attacker code

                if len(self["cards"]) >= 11: # send error if an attacker tries to attack with a 7th card
                    raise UserError("Cannot attack with more than 6 cards in a bout.")

                if card.wielder == self["players"][self["attacker"]]["player_id"] and len(self["cards"]) == 0: # main attack
                    await self.client_delete_cards()
                    insert(card, self["cards"])
                    await self.send_card(card,[EMOJI["pick_up"]])
                    self["attack_card"] = card

                elif len(self["cards"]) > 0 and card.value in [x.value for x in self["cards"]]: # other attacks
                    await self.delete_card_at_client_side(comm)
                    insert(card, self["cards"])
                    await self.send_card(card,[EMOJI["pick_up"]])
                    self["attack_card"] = card

            elif len(self["cards"])%2 == 1 and card.wielder == defender: # defender code

                if card.suit == self["cards"][-1].suit and card > self["cards"][-1]: # defend if same suit and card is greater
                    await self.delete_card_at_client_side(comm)
                    insert(card, self["cards"])
                    await self.send_card(card,[EMOJI["skip"]])

                elif card.suit == self["trump"].suit: # defend if trump 
                    await self.delete_card_at_client_side(comm)
                    insert(card, self["cards"])
                    await self.send_card(card,[EMOJI["skip"]])

                else:
                    raise UserError("Invalid card.")

                if self.durak_skip(): # NEXT TURN
                    await self.next_durak_bout()
                    await self.durak_push_cards()
                    await self.status_msg("*Attackers gave up.*"+durak_turn_msg(self))
            else:
                ## we should not be here?
                assert(False)

    async def pick_up(self, user_id, card):
        if self["game_type"] == "Durak":
            defender_index = (self["attacker"]+1) % len(self["players"])
            defender = self["players"][defender_index]["player_id"]

            #                                                     # NEXT TURN
            if user_id == defender and len(self["cards"])%2 == 1: # defender picks up all the cards
                self.client_delete_cards()

                draw(self["cards"], self["players"][defender_index]["hand"], len(self["cards"]))
                self["attacker"] = (defender_index+1) % len(self["players"])
                
                await self.durak_replenish((defender_index-1) % len(self["players"]))
                await self.durak_push_cards()
                await self.status_msg("*"+user.display_name+" picked up all the cards.*"+self.durak_turn_msg())

    async def skip(self, user_id):
        if self["game_type"] == "Durak":
            # player skip recognition
            skipped_users = []
            async for u in reaction.users(): skipped_users.append(u.id)
            for p in self["players"]:
                if p["player_id"] == user.id: p["skipped"] = True
                elif p["skipped"] and (p["player_id"] not in skipped_users): p["skipped"] = False

            if durak_skip(self): # NEXT TURN
                await self.next_durak_bout()
                await self.durak_push_cards()
                await self.status_msg("*Attackers gave up.*"+self.durak_turn_msg())

    async def durak_push_cards(self):
        for p in self["players"]:
            for card in [x if x.wielder == None else None for x in p["hand"]]:
                if card is None: continue
                card.wielder = p["player_id"]
                await self.send_card(card,[EMOJI["use"]], private=p["player_id"])
                    
    async def next_durak_bout(self): # next bout if everybody skipped and defender defended
        attacker = self["attacker"]
        defender = (attacker+1) % len(self["players"])
        await self.client_next_durak_bout()
        self["cards"] = []
        self["attacker"] = defender
        self.durak_replenish(attacker)
                    
    def durak_skip(self):
        attacker = self["attacker"]
        defender = (attacker+1) % len(self["players"])
        return (not False in [True if self["players"].index(x) == defender else x["skipped"] for x in self["players"]]) and len(game["cards"]) % 2 == 0

    def durak_replenish(self, attacker): # replenish cards
        d_cards = len(self["deck"])
        if d_cards == 0: return
        p_count = len(self["players"])
        players = [self["players"][attacker]] # attacker
        players += [self["players"][(x+attacker+2)%p_count] for x in range(p_count-2)] # other attackers
        players.append(self["players"][(attacker-1)%p_count]) # defender

        for p in players:
            p_cards = len(p["hand"])
            if 6-p_cards > d_cards: # if player needs more cards than the deck can offer
                draw(self["deck"], p["hand"], d_cards)
                draw([deepcopy(self["trump"])], p["hand"], 1)
                self["trump_in_deck"] = False
                break
            else: # normal refill
                draw(self["deck"], p["hand"], 6-p_cards)
    
    def durak_turn_msg(self): # message at the end of the turn
        a = self["players"][self["attacker"]]["player_name"]
        d = self["players"][(self["attacker"]+1)%len(self["players"])]["player_name"]
        d_cards = len(self["deck"])

        msg = "\nThere " # talon cards
        if self["trump_in_deck"]:
            if d_cards > 0:
                msg += "are "+str(d_cards+1)+" cards left in the talon.\n"
            else:
                msg += "is only the trump left of the talon.\n"
    
        else: # player cards
            msg += "are no cards left in the talon.\n__Cards left in each players hand:__\n"
            for p in self["players"]:
                p["player_name"] +" - "+ str(len(p["hand"])) + "\n"
    
        return msg + "**" + a + "'s turn to attack " + d + "!**"

class DiscordGame(Game):
    def __init__(self, client):
        self.client = client

    async def client_delete_cards(self):
        await delete_client_messages(self.client.get_channel(self["channel_id"]), len(self["cards"])+1)

    async def status_msg(self, message):
        self.client.get_channel(self["channel_id"]).send(message)

    async def delete_card_at_client_side(self, comm):
        await comm.message.delete()

    async def send_card(self, card, reactions, private=False, channel=None):
        global cards_by_id
        if private and not channel:
            channel = client.get_user(private).dm_channel
        elif not channel:
            channel = self.client.get_channel(games['channel_id'])
        bot_msg = await channel.send(file=discord.File(f"PNG/{card.display()}.png"))
        card.discord_id = bot_msg.id
        cards_by_id[card.discord_id] = card
        for emoji in reactions:
            await bot_msg.add_reaction(emoji)

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
        if self.value == 10: return "10" + self.suit[0]
        else: return self.name[0] + self.suit[0]

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
    "skip":"⏩",
    "pick_up":"↩️"
}

# --------------------------------------------------------------------

### ON READY
@client.event
async def on_ready():
    pass

# --------------------------------------------------------------------


@client.event
async def on_message(message):
    try:
        await _on_message(message)
    except UserError as err:
        await message.channel.send(str(err))

async def _on_message(message):
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
        if not game is None:
            raise UserError("A game has already been started in this channel.")

        game = create_durak_game(user_id=user.id, user_name=user.display_name, channel_id=message.channel.id)
        await message.channel.send(f"**Starting a game of Durak!**\nGame owner: {user.display_name}\nJoin with `.join`")

    if msg == ".join":
        # errors #
        if game is None:
            raise UserError("There are no ongoing games in this channel.")
        
        join_player(game, user.id, user.display_name)
        await message.channel.send(f"{user.display_name} joined the game!")

    if msg == ".start":
        # errors #
        if game is None:
            raise UserError("There are no pending games in this channel.")
        if game["owner_id"] != user.id:
            raise UserError("You are not the owner of this game.")

        start_game(game)

        if game["game_type"] == "Durak":
            trump = game['trump']
            await message.channel.send(f"{trump.suit} is trump!",file=discord.File(f"PNG/{trump.display()}.png"))
            for p in game["players"]: # show cards dealt
                await client.get_user(p["player_id"]).create_dm()
                for card in [x for x in p["hand"]]:
                    await game.send_card(card,[EMOJI["use"]], private=p["player_id"])

            await message.channel.send(game.durak_turn_msg()[1:])

    if msg in ["s",".s","sort",".sort"] and msgtype == "private":
        for x in games:
            for p in x["players"]:
                if p["player_id"] == user.id:
                    await delete_client_messages(message.channel, len(p["hand"])+1)
                    sort(p["hand"])
                    for card in p["hand"]:
                        await game.send_card(card, [EMOJI["use"]], channel=message.channel)



# --------------------------------------------------------------------

@client.event
async def on_reaction_add(reaction, user):
    try:
        on_reaction_add_(reaction, user)
    except UserError as err:
        await message.channel.send(str(err))

async def on_reaction_add_(reaction, user):
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
        except KeyError: return
    
        await game.use_card(card, reaction)

    elif command == "pick_up":
        try:
            card = cards_by_id[reaction.message.id]
            game = list(filter(lambda a: a != None, [x if x["channel_id"] == channel.id else None for x in games] ))[0]
        except KeyError: return
        if not user.id in [x["player_id"] for x in game["players"]]: return # return if user not in game

        await game.pick_up(user.id, card)

    elif command == "skip":
        try:
            game = list(filter(lambda a: a != None, [x if x["channel_id"] == channel.id else None for x in games] ))[0]
        except: return
        if not user.id in [x["player_id"] for x in game["players"]]: return # return if user not in game

        await game.skip(user_id)
        

                
        
# --------------------------------------------------------------------

async def delete_client_messages(channel, amount):
    async for msg_item in channel.history(limit=amount):
        if msg_item.author == client.user:
            await msg_item.delete()


# --------------------------------------------------------------------

get_key = lambda value, dictionary : list(filter(lambda a: a != None, [x if dictionary[x] == value else None for x in dictionary] ))[0]

def sort(cards):
    cards.sort(key=lambda x: SUITS.index(x.suit)*100 - x.value)

def create_durak_game(user_id, user_name, channel_id, game_class=Game):
    global games
    
    game_id = len(games)
    new_game = game_class()
    new_game.update({
        "owner_id" : user_id,
        "channel_id" : channel_id,
        "game_type" : "Durak",
        "start_time" : None,
        "deck" : build_deck("Durak", game_id),
        "trump" : None,
        "trump_in_deck": True,
        "attacker" : 0,
        "cards" : [],
        "attack_card" : None,
        "players" : []
    })
    games.append(new_game)
    join_player(new_game, user_id=user_id, user_name=user_name)
    return new_game

def start_game(game):
    if not game["start_time"] is None: # return error if game has already started
        raise UserError("Game has already started.")
    if game["game_type"] == "Durak":
        # errors #
        if len(game["players"]) == 1:
            raise UserError("Game requires a minimum of 2 players.")
        if len(game["players"]) > 5:
            raise UserError("Game cannot exceed the player limit of 5.")

        trump = game["deck"].pop() # assign trump
        game["trump"] = trump
        for p in game["players"]: # show cards dealt
            draw(game["deck"], p["hand"], 6, p["player_id"])
            sort(p["hand"])

    game["start_time"] = datetime.utcnow().__str__() + " UTC" # set start time

def join_player(game, user_id, user_name):
    if game["start_time"] is not None:
        raise UserError("You cannot join to a game that has already started")
    if user_id in [x["player_id"] for x in game["players"]]:
        raise UserError("You are already in the game")
    game["players"].append({"player_id":user_id,"player_name":user_name,"hand":[],"skipped":False})

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
        ## all cards in a deck should be owned by same player
        #assert_(not to_deck or len(set([x.wielder for x in to_deck]))==1)
        #assert_(not from_deck or len(set([x.wielder for x in from_deck]))==1)
        card = from_deck.pop()
        card.deck = to_deck
        card.wielder = player_id
        to_deck.append(card)
        ## all cards in a deck should be owned by same player
        #assert_(not to_deck or len(set([x.wielder for x in to_deck]))==1)
        #assert_(not from_deck or len(set([x.wielder for x in from_deck]))==1)

def insert(card, deck):
    card.deck.remove(card)
    card.deck = deck
    card.wielder = None
    deck.append(card)


# --------------------------------------------------------------------

if __name__ == '__main__':
    client.run(token)

