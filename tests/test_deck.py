import unittest

from deck import Deck


class DeckTest(unittest.TestCase):
    def test_initial_deck_size_unique(self):
        deck = Deck(auto_shuffle=False)
        self.assertEqual(len(deck), 52)
        self.assertEqual(len({repr(card) for card in deck.cards}), 52)

    def test_draw_reduces_size(self):
        deck = Deck()
        drawn = deck.draw(5)
        self.assertEqual(len(drawn), 5)
        self.assertEqual(len(deck), 47)

    def test_draw_triggers_new_deck(self):
        deck = Deck(auto_shuffle=True)
        _ = deck.draw(52)
        self.assertEqual(len(deck), 0)
        # Drawing again should recreate a full deck internally
        drawn = deck.draw(10)
        self.assertEqual(len(drawn), 10)
        self.assertEqual(len(deck), 42)


if __name__ == '__main__':  # pragma: no cover
    unittest.main() 