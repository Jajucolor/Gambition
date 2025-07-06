from typing import List, Callable
import random

from jokers import JOKER_DEFINITIONS
from entities.player import Player


class CompanionOffer:
    """Represents a single recruitable companion (formerly Joker)."""

    def __init__(self, key: str, cost: int, recruit_fn: Callable[[Player], None]):
        self.key = key
        self.name = JOKER_DEFINITIONS[key]["name"]
        self.cost = cost
        self.recruit_fn = recruit_fn

    def recruit(self, player: Player) -> bool:
        if player.gold < self.cost:
            print("Not enough gold to recruit.")
            return False
        player.gold -= self.cost
        self.recruit_fn(player)
        print(f"{self.name} has joined your party for {self.cost} gold!")
        return True


# ---------------------------------------------------------------------------
# Guild (shop) helpers
# ---------------------------------------------------------------------------

def generate_guild_offers() -> List[CompanionOffer]:
    """Return a list of 3 random companion offers."""
    keys = list(JOKER_DEFINITIONS.keys())
    random.shuffle(keys)
    offers: List[CompanionOffer] = []
    for key in keys[:3]:
        def make_fn(k):
            return lambda p: p.add_joker(k)
        offers.append(CompanionOffer(key, cost=20, recruit_fn=make_fn(key)))
    return offers


def open_guild(player: Player):
    """CLI interaction for recruiting companions. Mirrors shop.open_shop."""
    offers = generate_guild_offers()
    print("\n=== Adventurer\'s Guild ===")
    print(f"You have {player.gold} gold.")

    while True:
        print("\nAvailable Companions:")
        for idx, off in enumerate(offers):
            print(f"{idx}: {off.name} (Recruit Cost {off.cost})")
        print("X: Leave guild hall")

        choice = input("Recruit which companion? ").strip().lower()
        if choice == 'x':
            break
        try:
            idx = int(choice)
            if 0 <= idx < len(offers):
                success = offers[idx].recruit(player)
                if success:
                    offers.pop(idx)
            else:
                print("Invalid selection.")
        except ValueError:
            print("Enter a number or X to exit.")

    print("You leave the guild hall.\n") 