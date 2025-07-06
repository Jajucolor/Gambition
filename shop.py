from typing import List, Dict, Callable

from jokers import JOKER_DEFINITIONS
from entities.player import Player


class ShopItem:
    def __init__(self, name: str, cost: int, purchase_fn: Callable[[Player], None]):
        self.name = name
        self.cost = cost
        self.purchase_fn = purchase_fn

    def buy(self, player: Player):
        if player.gold < self.cost:
            print("Not enough gold.")
            return False
        player.gold -= self.cost
        self.purchase_fn(player)
        print(f"Purchased {self.name} for {self.cost} gold.")
        return True


# ---------------------------------------------------------------------------
# Shop generator
# ---------------------------------------------------------------------------

def generate_shop_items() -> List[ShopItem]:
    items: List[ShopItem] = []

    # Random 3 joker offers
    import random

    joker_keys = list(JOKER_DEFINITIONS.keys())
    random.shuffle(joker_keys)
    for key in joker_keys[:3]:
        def make_purchase_fn(k):
            return lambda p: p.add_joker(k)

        items.append(ShopItem(JOKER_DEFINITIONS[key]['name'], cost=15, purchase_fn=make_purchase_fn(key)))

    # HP upgrade
    items.append(ShopItem("Increase Max HP by 10", cost=25, purchase_fn=lambda p: (
        setattr(p, 'max_hp', p.max_hp + 10), setattr(p, 'hp', p.max_hp))))

    return items


# ---------------------------------------------------------------------------
# CLI shop interaction
# ---------------------------------------------------------------------------

def open_shop(player: Player):
    items = generate_shop_items()
    print("\n=== Merchant's Caravan ===")
    print(f"You have {player.gold} gold.")

    while True:
        print("\nItems:")
        for idx, it in enumerate(items):
            print(f"{idx}: {it.name} (Cost {it.cost})")
        print("X: Leave shop")

        choice = input("Choose item to buy: ").strip().lower()
        if choice == 'x':
            break
        try:
            idx = int(choice)
            if 0 <= idx < len(items):
                success = items[idx].buy(player)
                if success:
                    items.pop(idx)
            else:
                print("Invalid item.")
        except ValueError:
            print("Enter a number or X to exit.")

    print("Leaving shop.\n") 