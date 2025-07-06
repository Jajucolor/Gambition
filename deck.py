import random
from typing import List

from card import Card
from constants import SUITS, RANKS


class Deck:
    """Standard 52-card deck with simple draw/shuffle logic."""

    def __init__(self, *, auto_shuffle: bool = True):
        self.cards: List[Card] = [Card(s, r) for s in SUITS for r in RANKS]
        if auto_shuffle:
            self.shuffle()

    # ---------------------------------------------------------------------
    # Deck operations
    # ---------------------------------------------------------------------
    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def draw(self, count: int = 1) -> List[Card]:
        """Draw up to *count* cards; reshuffle the discard pile if needed.
        Currently this deck is infinite (reshuffles its own remaining cards).
        """
        if count <= 0:
            return []
        actual = min(count, len(self.cards))
        if actual == 0:
            return []
        drawn = self.cards[-actual:]
        self.cards = self.cards[:-actual]
        return drawn

    # ------------------------------------------------------------------
    # Utility dunder methods
    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self.cards)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Deck({len(self.cards)} cards remaining)" 