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
        if len(player.jokers) >= 5:
            print("Cannot recruit more companions - maximum of 5 companions allowed!")
            return False
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
    print(f"Current companions: {len(player.jokers)}/5")

    while True:
        print("\n--- Current Companions ---")
        if player.jokers:
            for idx, joker_key in enumerate(player.jokers):
                joker_name = JOKER_DEFINITIONS[joker_key]["name"]
                print(f"F{idx}: Farewell {joker_name}")
        else:
            print("No companions currently in your party.")
        
        print("\n--- Available Companions ---")
        if len(player.jokers) >= 5:
            print("Companion limit reached! Farewell a companion to recruit new ones.")
        else:
            for idx, off in enumerate(offers):
                print(f"{idx}: {off.name} (Recruit Cost {off.cost})")
        
        print("X: Leave guild hall")

        choice = input("Enter choice: ").strip().lower()
        if choice == 'x':
            break
        elif choice.startswith('f'):
            try:
                idx = int(choice[1:])
                if 0 <= idx < len(player.jokers):
                    joker_key = player.jokers[idx]
                    player.remove_joker(joker_key)
                else:
                    print("Invalid companion selection.")
            except ValueError:
                print("Enter F followed by a number to farewell a companion.")
        else:
            if len(player.jokers) >= 5:
                print("Cannot recruit - companion limit reached!")
                continue
            try:
                idx = int(choice)
                if 0 <= idx < len(offers):
                    success = offers[idx].recruit(player)
                    if success:
                        offers.pop(idx)
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Enter a number, F+number, or X to exit.")

    print("You leave the guild hall.\n") 