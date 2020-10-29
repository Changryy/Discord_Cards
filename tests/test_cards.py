import cards
import asyncio
from nose.tools import assert_raises

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

def test_join_started():
    """
    attempts to join a game that has already started should fail
    """
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.start_game(game)
    assert_raises(cards.UserError, cards.join_player, game, 35, 'biden')

def test_use_card():
    """
    first player should use a card
    """
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    cards.join_player(game, 34, 'trump')
    cards.start_game(game)
    first_card=game['players'][0]['hand'][0]
    first_player=game['players'][0]['player_id']
    asyncio.run(game.use_card(first_card, first_player))
