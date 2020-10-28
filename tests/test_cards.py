import cards

def test_build_deck():
    deck = cards.build_deck("Durak", 1)
    assert(len(deck) == 36)

def test_create_durak_game():
    game = cards.create_durak_game(user_id=33, user_name='tobixen', channel_id=34)
    assert(game['owner_id'] == 33)
    assert(len(game['players']) == 1)
