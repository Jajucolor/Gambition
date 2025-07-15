from __future__ import annotations

import random
from typing import List, Callable, Union

from card import Card
from constants import SUITS, RANKS
from tarot import TAROT_DEFINITIONS, TarotCard
from entities.player import Player


class ShopOffer:
    """Generic shop offer for a Card or TarotCard."""

    def __init__(self, obj: Union[Card, TarotCard], cost: int, on_buy: Callable[[Player], None]):
        self.obj = obj
        self.cost = cost
        self.on_buy = on_buy

    @property
    def name(self) -> str:  # for display
        if isinstance(self.obj, Card):
            return f"{self.obj} (Card)"
        return f"{self.obj.name} (Tarot)"

    def buy(self, player: Player) -> bool:
        if player.gold < self.cost:
            print("Not enough gold.")
            return False
        player.gold -= self.cost
        self.on_buy(player)
        print(f"Purchased {self.name} for {self.cost} gold.")
        return True


# ---------------------------------------------------------------------------
# Offer generation helpers
# ---------------------------------------------------------------------------

def _random_card() -> Card:
    suit = random.choice(SUITS)
    rank = random.choice(RANKS)
    return Card(suit, rank)


def generate_shop_offers() -> List[ShopOffer]:
    offers: List[ShopOffer] = []

    # Three normal cards (cheap)
    for _ in range(3):
        card_obj = _random_card()
        def _make_fn(c: Card):
            return lambda p: p.deck.cards.append(c)
        offers.append(ShopOffer(card_obj, cost=3, on_buy=_make_fn(card_obj)))

    # Two random tarot cards (expensive)
    tarot_keys = list(TAROT_DEFINITIONS.keys())
    random.shuffle(tarot_keys)
    for key in tarot_keys[:2]:
        tarot_obj = TAROT_DEFINITIONS[key]
        def _make_tarot(t: TarotCard):
            return lambda p: p.add_item(t)
        offers.append(ShopOffer(tarot_obj, cost=12, on_buy=_make_tarot(tarot_obj)))

    return offers


# ---------------------------------------------------------------------------
# CLI shop (for quick testing)
# ---------------------------------------------------------------------------

def open_card_shop(player: Player):
    offers = generate_shop_offers()
    while True:
        print("\n=== Card Emporium ===")
        print(f"Gold: {player.gold}\n")
        for idx, off in enumerate(offers):
            print(f"{idx}: {off.name} (Cost {off.cost})")
        print("X: leave")
        choice = input("Buy which? ").strip().lower()
        if choice == 'x':
            break
        try:
            idx = int(choice)
            if 0 <= idx < len(offers):
                if offers[idx].buy(player):
                    offers.pop(idx)
            else:
                print("Invalid index")
        except ValueError:
            print("Enter number or X")

    print("Leaving emporium.\n") 