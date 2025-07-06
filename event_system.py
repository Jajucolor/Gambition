import random
from typing import Callable, List

from entities.player import Player
from jokers import JOKER_DEFINITIONS


class Event:
    def __init__(self, description: str, choices: List[tuple[str, Callable[[Player], None]]]):
        self.description = description
        self.choices = choices

    def trigger(self, player: Player):
        print("\n=== Mysterious Encounter ===")
        print(self.description)
        for idx, (text, _) in enumerate(self.choices):
            print(f"{idx}: {text}")
        choice = input("Choose: ")
        try:
            idx = int(choice)
            if 0 <= idx < len(self.choices):
                self.choices[idx][1](player)
            else:
                print("The opportunity fades...")
        except ValueError:
            print("The opportunity fades...")


# ---------------------------------------------------------------------------
# Event generator
# ---------------------------------------------------------------------------

def random_event() -> Event:
    events: List[Event] = []

    # Gain gold vs lose hp
    def gold_gain(p):
        amt = random.randint(10, 20)
        p.gold += amt
        print(f"You found a hidden stash of {amt} gold!")

    def lose_hp(p):
        dmg = random.randint(5, 15)
        p.take_damage(dmg)
        print(f"A trap springs! You lose {dmg} HP.")

    events.append(Event("You stumble upon an abandoned campsite.", [
        ("Search the camp", gold_gain),
        ("Leave it be", lambda p: print("You move on cautiously.")),
    ]))

    # Free joker versus nothing
    def free_joker(p):
        jk = random.choice(list(JOKER_DEFINITIONS.keys()))
        p.add_joker(jk)

    events.append(Event("A wandering jester offers you a gift.", [
        ("Accept the Joker", free_joker),
        ("Decline", lambda p: print("You politely refuse.")),
    ]))

    return random.choice(events) 