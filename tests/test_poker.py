import unittest

from card import Card
from poker import get_poker_hand


def build_cards(specs):
    """Helper taking list of (rank, suit) tuples and returning Card objects."""
    return [Card(suit, rank) for rank, suit in specs]


class PokerHandTest(unittest.TestCase):
    def test_royal_flush(self):
        cards = build_cards([('10', 'Hearts'), ('J', 'Hearts'), ('Q', 'Hearts'), ('K', 'Hearts'), ('A', 'Hearts')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Royal Flush')

    def test_straight_flush(self):
        cards = build_cards([('6', 'Diamonds'), ('7', 'Diamonds'), ('8', 'Diamonds'), ('9', 'Diamonds'), ('10', 'Diamonds')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Straight Flush')

    def test_four_kind(self):
        cards = build_cards([('5', 'Clubs'), ('5', 'Diamonds'), ('5', 'Hearts'), ('5', 'Spades'), ('K', 'Hearts')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Four of a Kind')

    def test_full_house(self):
        cards = build_cards([('9', 'Clubs'), ('9', 'Diamonds'), ('9', 'Hearts'), ('Q', 'Spades'), ('Q', 'Hearts')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Full House')

    def test_flush(self):
        cards = build_cards([('2', 'Spades'), ('6', 'Spades'), ('9', 'Spades'), ('J', 'Spades'), ('K', 'Spades')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Flush')

    def test_straight(self):
        cards = build_cards([('3', 'Hearts'), ('4', 'Clubs'), ('5', 'Diamonds'), ('6', 'Spades'), ('7', 'Hearts')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Straight')

    def test_wheel_straight(self):
        cards = build_cards([('A', 'Clubs'), ('2', 'Diamonds'), ('3', 'Hearts'), ('4', 'Spades'), ('5', 'Clubs')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Straight')

    def test_three_kind(self):
        cards = build_cards([('8', 'Clubs'), ('8', 'Diamonds'), ('8', 'Spades'), ('2', 'Hearts'), ('K', 'Clubs')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Three of a Kind')

    def test_two_pair(self):
        cards = build_cards([('4', 'Hearts'), ('4', 'Clubs'), ('J', 'Spades'), ('J', 'Diamonds'), ('9', 'Hearts')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Two Pair')

    def test_pair(self):
        cards = build_cards([('7', 'Hearts'), ('7', 'Diamonds'), ('2', 'Clubs'), ('5', 'Spades'), ('Q', 'Hearts')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Pair')

    def test_high_card(self):
        cards = build_cards([('2', 'Hearts'), ('4', 'Diamonds'), ('6', 'Clubs'), ('9', 'Spades'), ('K', 'Hearts')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'High Card')

    def test_invalid_hand(self):
        cards = build_cards([('A', 'Hearts'), ('K', 'Hearts')])
        hand, _ = get_poker_hand(cards)
        self.assertEqual(hand, 'Invalid Hand')


if __name__ == '__main__':  # pragma: no cover
    unittest.main() 