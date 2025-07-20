from __future__ import annotations

from typing import List, TYPE_CHECKING

from deck import Deck
from card import Card
from constants import HAND_MULTIPLIERS
from poker import get_poker_hand, hand_multiplier
from jokers import apply_jokers
from meta import load_meta  # local import to avoid circular in UI
from status_effects import StatusEffectManager

if TYPE_CHECKING:
    from tarot import TarotCard


class Player:
    """Represents the player and their combat resources."""

    def __init__(self):
        meta = load_meta()
        bonus = meta.get('permanent_hp_bonus', 0)
        self.max_hp: int = 100 + bonus
        self.hp: int = self.max_hp
        self.gold: int = 20

        self.deck: Deck = Deck()
        self.discard_pile: List[Card] = []
        self.hand: List[Card] = []
        self.hand_size: int = 8
        
        # Discard system
        self.max_discards: int = 3
        self.discards_left: int = self.max_discards

        # Jokers held represented by their type key (matching jokers.JOKER_DEFINITIONS)
        self.jokers: List[str] = []

        # Inventory of single-use Tarot cards or other consumables
        self.items: List['TarotCard'] = []
        
        # Status effects manager
        self.status_effects: StatusEffectManager = StatusEffectManager()
        
        # Combat tracking
        self.combat_turn: int = 0  # For Berserker joker

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

        new_cards = self.deck.draw(count)
        self.hand.extend(new_cards)

    def discard_cards(self, indices: List[int]) -> List[Card]:
        """Discard cards at given indices, return the discarded cards."""
        if self.discards_left <= 0:
            print("No discards remaining!")
            return []
        
        if len(indices) == 0:
            print("No cards selected for discard.")
            return []
        
        self.discards_left -= 1
        discarded = []
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(self.hand):
                card = self.hand.pop(idx)
                self.discard_pile.append(card)
                discarded.append(card)
        
        # Echo Mage joker: if discarding exactly one card, add a copy to hand
        if len(discarded) == 1 and 'echo_mage' in self.jokers:
            cloned_card = discarded[0]  # Create a reference to the same card
            self.hand.append(cloned_card)
            print(f"Echo Mage cloned {cloned_card}!")
            # Refill hand with one less card since we added a clone
            self.draw_cards(len(discarded) - 1)
        else:
            # Refill hand normally
            self.draw_cards(len(discarded))
        
        print(f"Discarded {len(discarded)} card(s). {self.discards_left} discards left.")
        return discarded

    def reset_discards(self) -> None:
        """Reset discards for a new combat."""
        self.discards_left = self.max_discards

    # ------------------------------------------------------------------
    # Combat actions
    # ------------------------------------------------------------------
    def form_hand_and_attack(self, indices: List[int], enemy=None) -> tuple[float, str | None, List[str]]:
        """Form a hand and attack, applying card abilities. Returns (damage, hand_type, effects)."""
        if not indices:
            print("No cards selected.")
            return 0.0, None, []
        if any(i >= len(self.hand) or i < 0 for i in indices):
            print("Invalid card index in selection.")
            return 0.0, None, []

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
        
        # Apply joker effects
        total_damage = apply_jokers(selected, base_damage, hand_type, self.jokers)
        
        # Apply Berserker joker damage bonus
        if 'berserker' in self.jokers:
            berserker_bonus = self.combat_turn * 2  # +2 damage per turn
            total_damage += berserker_bonus
            if berserker_bonus > 0:
                print(f"Berserker bonus: +{berserker_bonus} damage!")
        
        # Apply status effect damage buffs
        total_damage = self.status_effects.modify_outgoing_damage(int(total_damage))
        
        # Apply card combination abilities
        abilities_result = {"effects": [], "damage_multiplier": 1.0}
        if enemy and hand_type != "Strike":
            from card_abilities import apply_card_combination_abilities
            abilities_result = apply_card_combination_abilities(hand_type, self, enemy, int(base_damage))
        
        # Apply damage multiplier from abilities
        total_damage = int(total_damage * abilities_result["damage_multiplier"])

        # Remove played cards from hand to discard pile
        for idx in sorted(indices, reverse=True):
            self.discard_pile.append(self.hand.pop(idx))

        # Refill hand to maintain hand_size
        self.draw_cards(len(indices))

        print(f"Attack using {len(selected)} card(s) as {hand_type}: base {base_damage} → total {total_damage}")
        return float(total_damage), hand_type, abilities_result["effects"]

    # ------------------------------------------------------------------
    # Stat adjustments
    # ------------------------------------------------------------------
    def take_damage(self, dmg: float) -> None:
        # Apply status effect damage reduction and shields
        actual_damage = self.status_effects.modify_incoming_damage(int(dmg))
        self.hp = max(0, self.hp - actual_damage)
        print(f"Player took {actual_damage} damage. HP {self.hp}/{self.max_hp}")
    
    def start_turn(self) -> None:
        """Called at the start of the player's turn to process status effects."""
        self.combat_turn += 1
        self.status_effects.tick_effects(self)
    
    def end_turn(self) -> None:
        """Called at the end of the player's turn."""
        pass
    
    def start_combat(self) -> None:
        """Called when combat begins."""
        self.combat_turn = 0
        self.reset_discards()
        self.status_effects.clear_all_effects()
    
    def end_combat(self) -> None:
        """Called when combat ends."""
        self.combat_turn = 0
        self.status_effects.clear_all_effects()

    def add_joker(self, jtype: str) -> None:
        if len(self.jokers) >= 5:
            print("Cannot recruit more companions - maximum of 5 companions allowed!")
            return
        self.jokers.append(jtype)
        print(f"Acquired companion: {jtype}")

    def remove_joker(self, jtype: str) -> bool:
        """Remove a companion from the player's collection. Returns True if successful."""
        if jtype in self.jokers:
            self.jokers.remove(jtype)
            print(f"Farewelled companion: {jtype}")
            return True
        return False

    # ------------------------------------------------------------------
    # Item management
    # ------------------------------------------------------------------
    def add_item(self, item: 'TarotCard') -> None:
        """Add a consumable (e.g., TarotCard) to inventory."""
        self.items.append(item)
        print(f"Obtained item: {item}")

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