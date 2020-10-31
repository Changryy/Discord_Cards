import sys
sys.path.append('..')
import cards
import asyncio
from nose.tools import assert_raises
import random

def test_build_deck():
    deck = cards.build_deck("Durak", 1)
    assert(len(deck) == 36)

def test_create_durak_game():
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    assert(game['owner_id'] == 33)
    assert(len(game['players']) == 1)

def test_double_join():
    """
    attempts to join a game twice should raise a UserError
    """
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    assert_raises(cards.UserError, cards.join_player, game, 34, 'trump')
    assert_raises(cards.UserError, cards.join_player, game, 33, 'tobixen')

def test_start_game():
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.start_game(game)
    ## there should be no duplicated cards in the deck
    assert(len([x.display() for x in game['deck']]) == len(set([x.display() for x in game['deck']])))

def test_join_started():
    """
    attempts to join a game that has already started should fail
    """
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.start_game(game)
    assert_raises(cards.UserError, cards.join_player, game, 35, 'biden')

def test_use_first_card():
    """
    The game creator should start attacking
    """
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.start_game(game)
    first_card=game['players'][0]['hand'][0]
    asyncio.run(game.use_card(first_card))

def test_wrong_order():
    """
    Attempts to play out of order should fail
    """
    random.seed(2)
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.start_game(game)
    first_card=game['players'][0]['hand'][0]
    second_card=game['players'][1]['hand'][0]
    ## Second card belongs to second player, first player has to start the turn
    assert_raises(cards.UserError, asyncio.run, game.use_card(second_card))
    ## This is OK
    asyncio.run(game.use_card(first_card))
    ## This is not OK, defender should play, and card has already been played
    assert_raises(cards.UserError, asyncio.run, game.use_card(first_card))
    ## With the given random seed, this works fine
    asyncio.run(game.use_card(second_card))
    ## card has already been played, an error should be raised
    assert_raises(cards.UserError, asyncio.run, game.use_card(first_card))

def test_wrong_defence():
    """
    The card played has to be higher and of the same order or trump
    """
    random.seed(1)
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.start_game(game)
    first_card=game['players'][0]['hand'][0] ## King of diamond (trump)
    second_card=game['players'][1]['hand'][0] ## Queen of diamond
    asyncio.run(game.use_card(first_card))
    assert_raises(cards.UserError, asyncio.run, game.use_card(second_card))

def test_skip():
    """
    Game on, attacker skips to continue attacking
    """
    random.seed(2)
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.start_game(game)
    first_card=game['players'][0]['hand'][0]
    second_card=game['players'][1]['hand'][0]
    assert_raises(cards.UserError, asyncio.run, game.use_card(second_card))
    asyncio.run(game.use_card(first_card))
    asyncio.run(game.use_card(second_card))
    asyncio.run(game.skip([33]))
    
def test_pick_up():
    """
    Game on, attacker plays second attack and defender draws
    """
    random.seed(2)
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.start_game(game)
    first_card=game['players'][0]['hand'][0] ## JD
    second_card=game['players'][1]['hand'][0] ## AD
    third_card=game['players'][0]['hand'][3] ## JC
    fourth_card=game['players'][0]['hand'][1]
    fifth_card=game['players'][1]['hand'][1]
    assert_raises(cards.UserError, asyncio.run, game.use_card(second_card))
    asyncio.run(game.use_card(first_card))
    asyncio.run(game.use_card(second_card))
    asyncio.run(game.use_card(third_card))
    asyncio.run(game.pick_up(34))

def test_game_on():
    """
    Game on ... round #2 after pick_up
    """
    random.seed(2)
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.start_game(game)
    first_card=game['players'][0]['hand'][0] ## JD
    second_card=game['players'][1]['hand'][0] ## AD
    third_card=game['players'][0]['hand'][3] ## JC
    fourth_card=game['players'][0]['hand'][1]
    fifth_card=game['players'][1]['hand'][1]
    assert_raises(cards.UserError, asyncio.run, game.use_card(second_card))
    asyncio.run(game.use_card(first_card))
    asyncio.run(game.use_card(second_card))
    asyncio.run(game.use_card(third_card))
    asyncio.run(game.pick_up(34))
    ## should fail - card has already been played
    assert_raises(cards.UserError, asyncio.run, game.use_card(first_card))
    ## should fail - defender is still defender after picking
    assert_raises(cards.UserError, asyncio.run, game.use_card(fifth_card))
    asyncio.run(game.use_card(fourth_card))
    asyncio.run(game.use_card(fifth_card))
    asyncio.run(game.skip([33]))

def test_longer_game():
    random.seed(8)
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.join_player(game, 35, 'biden')
    cards.start_game(game)

    print(f"trump is {game['trump'].display()}")

    hands = [game['players'][x]['hand'] for x in range(3)]

    ## The king of clubs is in trumps hand.  It should not be in the deck. (observed bug 2020-10-29
    assert(not 'KC' in [x.display() for x in game['deck']])
    assert(    'KC' in [x.display() for x in hands[1]])

    
    def print_hands():
        for i in range(3):
            print(f"Player {game['players'][i]['player_name']} has this hand:")
            print(" ".join([x.display() for x in hands[i]]))
        print(f"Cards on the table:")
        print(" ".join([x.display() for x in game['cards']]))

    print_hands()

    asyncio.run(game.use_card(hands[0][1]))
    asyncio.run(game.use_card(hands[1][3]))
    asyncio.run(game.use_card(hands[2][3]))
    asyncio.run(game.use_card(hands[1][3]))
    asyncio.run(game.skip([33]))
    asyncio.run(game.use_card(hands[2][2]))
    asyncio.run(game.use_card(hands[1][3]))
    print_hands()
    assert(not 'KC' in [x.display() for x in game['deck']])
    asyncio.run(game.skip([33,35]))
    
    ## Card KC has been thrown and should be nowhere to be found
    assert(not 'KC' in [x.display() for x in game['deck']])
    assert(not 'KC' in [x.display() for x in hands[0]])
    assert(not 'KC' in [x.display() for x in hands[1]])
    assert(not 'KC' in [x.display() for x in hands[2]])

    ## All players should have six cards
    assert(len(hands[0])==6)
    assert(len(hands[1])==6)
    assert(len(hands[2])==6)

    print_hands()
