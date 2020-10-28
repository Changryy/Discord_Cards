import cards

def test_build_deck():
    deck = cards.build_deck("Durak", 1)
    assert(len(deck) == 36)
