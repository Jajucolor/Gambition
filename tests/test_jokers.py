import unittest

from card import Card
from jokers import apply_jokers
from poker import hand_multiplier


def make_hand():
    return [Card('Hearts', '2'), Card('Diamonds', '2'), Card('Clubs', '2'), Card('Spades', '5'), Card('Hearts', '7')]


class JokerDamageTest(unittest.TestCase):
    def test_joker_add_damage(self):
        hand = make_hand()
        base = sum(c.value for c in hand) * hand_multiplier('Three of a Kind')
        final = apply_jokers(hand, base, 'Three of a Kind', ['joker'])
        self.assertEqual(final, base + len(hand))

    def test_archon_multiplier(self):
        hand = make_hand()
        base = 10.0
        final = apply_jokers(hand, base, 'High Card', ['archon'])
        self.assertEqual(final, base * len(hand))

    def test_business_card_consumed(self):
        hand = make_hand()
        jokers = ['business_card']
        base = 10
        final = apply_jokers(hand, base, 'Pair', jokers)
        self.assertEqual(final, base * 3)  # triple
        self.assertEqual(jokers, [])  # consumed

    def test_gemini_duplicates(self):
        hand = make_hand()
        jokers = ['joker', 'archon', 'gemini']
        base = 10
        # Effect order: joker (+5) -> archon (*5) = 75, then gemini duplicates first two effects again
        # duplicate joker (+5) => 80, duplicate archon (*5) => 400
        final = apply_jokers(hand, base, 'High Card', jokers)
        self.assertEqual(final, 400)


if __name__ == '__main__':  # pragma: no cover
    unittest.main() 