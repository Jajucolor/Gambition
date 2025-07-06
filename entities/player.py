from __future__ import annotations

from typing import List

from deck import Deck
from card import Card
from constants import HAND_MULTIPLIERS
from poker import get_poker_hand, hand_multiplier
from jokers import apply_jokers
from meta import load_meta  # local import to avoid circular in UI


class Player:
    """Represents the player and their combat resources."""

    def __init__(self):
        meta = load_meta()
        bonus = meta.get('permanent_hp_bonus', 0)
        self.max_hp: int = 100 + bonus
        self.hp: int = self.max_hp
        self.gold: int = 0

        self.deck: Deck = Deck()
        self.discard_pile: List[Card] = []
        self.hand: List[Card] = []
        self.hand_size: int = 8

        # Jokers held represented by their type key (matching jokers.JOKER_DEFINITIONS)
        self.jokers: List[str] = []

    # ------------------------------------------------------------------
    # Card management
    # ------------------------------------------------------------------
    def draw_cards(self, count: int | None = None) -> None:
        """Draw cards into hand.

        If *count* is None we top-up the hand so that its final size equals
        `hand_size` (+ any extras from "The Fool" jokers) instead of always
        adding a full hand_size every time. This prevents hand overflow after
        consecutive draw phases in the same turn cycle (issue observed in
        Ursina/Pygame UI where hand exceeded 8 cards)."""

        if count is None:
            # Extra draws from "The Fool" jokers
            extra = self.jokers.count('fool') * 1  # each Fool gives +1
            desired = self.hand_size + extra
            count = max(0, desired - len(self.hand))
            if count == 0:
                return  # already full

        if count <= 0:
            return

        drawn = self.deck.draw(count)
        self.hand.extend(drawn)
        print(f"Player drew {len(drawn)} cards. Hand now: {self.hand}")

    def discard_cards(self, indices: List[int]) -> None:
        # Sort descending to avoid index shifts
        indices = sorted(set(indices), reverse=True)
        discarded = []
        for idx in indices:
            if 0 <= idx < len(self.hand):
                discarded.append(self.hand.pop(idx))
        self.discard_pile.extend(discarded)
        print(f"Discarded {len(discarded)} cards → {discarded}")

        # Draw replacements
        self.draw_cards(len(discarded))

    # ------------------------------------------------------------------
    # Combat actions
    # ------------------------------------------------------------------
    def form_hand_and_attack(self, indices: List[int]) -> tuple[float, str | None]:
        if not indices:
            print("No cards selected.")
            return 0.0, None
        if any(i >= len(self.hand) or i < 0 for i in indices):
            print("Invalid card index in selection.")
            return 0.0, None

        selected = [self.hand[i] for i in indices]
        if len(indices) == 5:
            hand_type, _ = get_poker_hand(selected)
            if hand_type == "Invalid Hand":
                hand_type = "Strike"
                mult = 1
            else:
                mult = hand_multiplier(hand_type)
        else:
            # Detect partial combinations for 2–4 card selections
            values = [c.value for c in selected]
            rank_counts: dict[int, int] = {}
            for v in values:
                rank_counts[v] = rank_counts.get(v, 0) + 1
            counts = sorted(rank_counts.values(), reverse=True)

            if counts == [4]:
                hand_type = "Four of a Kind"
            elif counts == [3, 1]:
                hand_type = "Three of a Kind"
            elif counts == [2, 2]:
                hand_type = "Two Pair"
            elif counts == [2, 1] or counts == [2]:
                hand_type = "Pair"
            else:
                hand_type = "Strike"

            mult = HAND_MULTIPLIERS.get(hand_type, 1)

        base_damage = sum(card.value for card in selected) * mult
        total_damage = apply_jokers(selected, base_damage, hand_type, self.jokers)

        # Remove played cards from hand to discard pile
        for idx in sorted(indices, reverse=True):
            self.discard_pile.append(self.hand.pop(idx))

        # Refill hand to maintain hand_size
        self.draw_cards(len(indices))

        print(f"Attack using {len(selected)} card(s) as {hand_type}: base {base_damage} → total {total_damage}")
        return total_damage, hand_type

    # ------------------------------------------------------------------
    # Stat adjustments
    # ------------------------------------------------------------------
    def take_damage(self, dmg: float) -> None:
        self.hp = max(0, self.hp - int(dmg))
        print(f"Player took {dmg} damage. HP {self.hp}/{self.max_hp}")

    def add_joker(self, jtype: str) -> None:
        self.jokers.append(jtype)
        print(f"Acquired joker: {jtype}")

    # Utility ----------------------------------------------------------------
    def is_alive(self) -> bool:
        return self.hp > 0

    # ------------------------------------------------------------------
    # Joker active abilities
    # ------------------------------------------------------------------
    def magician_swap(self, hand_idx: int) -> bool:
        """Swap a card in hand with top of deck. Returns True if success."""
        if 'magician' not in self.jokers:
            print("No Magician joker available.")
            return False
        if not (0 <= hand_idx < len(self.hand)):
            print("Hand index out of range.")
            return False

        # Draw top card from deck (1) and swap
        new_card = self.deck.draw(1)[0]
        old_card = self.hand[hand_idx]
        self.hand[hand_idx] = new_card
        self.discard_pile.append(old_card)
        print(f"Magician swapped {old_card} → {new_card}")
        return True

    def necromancer_retrieve(self, discard_idx: int) -> bool:
        """Move a card from discard pile back to hand once per turn."""
        if 'necromancer' not in self.jokers:
            print("No Necromancer joker available.")
            return False
        if not (0 <= discard_idx < len(self.discard_pile)):
            print("Discard index out of range.")
            return False
        card = self.discard_pile.pop(discard_idx)
        self.hand.append(card)
        print(f"Necromancer retrieved {card} from discard into hand.")
        return True 