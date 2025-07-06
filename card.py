from __future__ import annotations

from dataclasses import dataclass

from constants import CARD_VALUES, SUITS, RANKS


@dataclass(frozen=True)
class Card:
    """Represents a single playing card."""

    suit: str
    rank: str

    def __post_init__(self):
        if self.suit not in SUITS:
            raise ValueError(f"Invalid suit: {self.suit}")
        if self.rank not in RANKS:
            raise ValueError(f"Invalid rank: {self.rank}")

    @property
    def value(self) -> int:
        """Numerical value used for comparisons (2..14)."""
        return CARD_VALUES[self.rank]

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.rank} of {self.suit}" 