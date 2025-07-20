from __future__ import annotations

from typing import List, Tuple

from card import Card
from constants import HAND_MULTIPLIERS


# ---------------------------------------------------------------------------
# Poker hand detection utilities
# ---------------------------------------------------------------------------

def get_poker_hand(cards: List[Card]) -> Tuple[str, List[int]]:
    """Detect the best poker hand from exactly 5 cards.

    Returns a tuple: (hand_name, sorted_card_values)
    If the hand is invalid (not 5 cards) returns ("Invalid Hand", []).
    """
    if len(cards) != 5:
        return "Invalid Hand", []

    values = sorted([card.value for card in cards])
    suits = [card.suit for card in cards]

    # Count occurrences of each rank value
    rank_counts = {}
    for v in values:
        rank_counts[v] = rank_counts.get(v, 0) + 1

    is_flush = len(set(suits)) == 1
    # Straight check (wheel straight included)
    is_sequential = all(values[i + 1] == values[i] + 1 for i in range(4))
    is_wheel_straight = values == [2, 3, 4, 5, 14]  # Ace acting low
    is_straight = is_sequential or is_wheel_straight

    counts = sorted(rank_counts.values(), reverse=True)

    # New combinations first (highest priority)
    if counts == [5]:  # Five of a Kind
        return "Five of a Kind", values
    
    # Check for Flush Five (5 cards same rank and suit)
    if counts == [5] and is_flush:
        return "Flush Five", values
    
    # Check for Royal Flush
    if is_straight and is_flush and values == [10, 11, 12, 13, 14]:
        return "Royal Flush", values
    
    # Check for Straight Flush
    if is_straight and is_flush:
        return "Straight Flush", values
    
    # Check for Flush House (Full House + Flush)
    if counts == [3, 2] and is_flush:
        return "Flush House", values
    
    # Standard combinations
    if counts == [4, 1]:
        return "Four of a Kind", values
    if counts == [3, 2]:
        return "Full House", values
    if is_flush:
        return "Flush", values
    if is_straight:
        return "Straight", values
    if counts == [3, 1, 1]:
        return "Three of a Kind", values
    if counts == [2, 2, 1]:
        return "Two Pair", values
    if counts == [2, 1, 1, 1]:
        return "Pair", values
    return "High Card", values


# Convenience function ------------------------------------------------------

def hand_multiplier(hand_name: str) -> int:
    """Return the base multiplier for a poker hand."""
    return HAND_MULTIPLIERS.get(hand_name, 0) 