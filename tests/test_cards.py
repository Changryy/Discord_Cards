import cards
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

