import unittest

from card import Card
from constants import CARD_VALUES


class CardTest(unittest.TestCase):
    def test_value_mapping(self):
        for rank, value in CARD_VALUES.items():
            card = Card('Hearts', rank)
            self.assertEqual(card.value, value)

    def test_invalid_suit_raises(self):
        with self.assertRaises(ValueError):
            Card('Stars', '2')

    def test_invalid_rank_raises(self):
        with self.assertRaises(ValueError):
            Card('Hearts', '1')


if __name__ == '__main__':  # pragma: no cover
    unittest.main() 