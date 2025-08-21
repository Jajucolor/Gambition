"""Command-line demo loop for Gambition.
This is an MVP extracted from the original prototype, refactored to use
modular core classes. It runs a single fight between the Player and one
Enemy for quick iterative testing.
"""
from __future__ import annotations

import random
from typing import List

from entities.player import Player
from entities.enemy import Enemy
from poker import get_poker_hand
from encounter import EncounterManager
from meta import load_meta, save_meta, record_run, add_permanent_hp
from shop import open_shop



def choose_indices(prompt: str, hand_len: int, expect: int | None = None) -> List[int]:
    """Helper to ask the user for comma-separated indices."""
    while True:
        indices_str = input(prompt).strip()
        if not indices_str:
            return []
        try:
            indices = [int(x.strip()) for x in indices_str.split(',') if x.strip()]
        except ValueError:
            print("Please enter only numbers.")
            continue
        if any(i < 0 or i >= hand_len for i in indices):
            print("One or more indices out of range – try again.")
            continue
        if expect is not None and len(indices) != expect:
            print(f"You must select exactly {expect} cards.")
            continue
        return indices


def play_game() -> None:
    player = Player()
    encounters = EncounterManager(stages=5)
    enemy = encounters.next_enemy()

    player.add_joker('joker')  # Starter joker

    print("Welcome to Gambition!")

    while player.is_alive() and enemy and enemy.is_alive():
        print("\n--- Player Turn ---")
        player.draw_cards()

        action_taken = False
        while not action_taken:
            print("\nYour hand:")
            for i, card in enumerate(player.hand):
                print(f"{i}: {card}")

            print("\nActions:")
            print("1) Form hand & attack")
            print("2) Discard and redraw")
            print("3) End turn")
            if 'magician' in player.jokers:
                print("4) Magician swap a card")
            if 'necromancer' in player.jokers and player.discard_pile:
                print("5) Necromancer retrieve from discard")
            choice = input("Choose action: ")

            if choice == '1':
                if len(player.hand) < 5:
                    print("Need at least 5 cards.")
                    continue
                indices = choose_indices("Select 5 card indices (comma-sep): ", len(player.hand), expect=5)
                dmg, hand_type = player.form_hand_and_attack(indices)
                if hand_type:
                    enemy.take_damage(dmg)
                    action_taken = True
            elif choice == '2':
                indices = choose_indices("Indices to discard (comma-sep, blank=none): ", len(player.hand))
                player.discard_cards(indices)
            elif choice == '3':
                action_taken = True
            elif choice == '4' and 'magician' in player.jokers:
                if not player.hand:
                    print("Hand empty.")
                    continue
                idx_list = choose_indices("Select ONE card index to swap: ", len(player.hand), expect=1)
                if idx_list:
                    player.magician_swap(idx_list[0])
            elif choice == '5' and 'necromancer' in player.jokers and player.discard_pile:
                for i, card in enumerate(player.discard_pile):
                    print(f"{i}: {card}")
                idx_list = choose_indices("Select ONE discard card to retrieve: ", len(player.discard_pile), expect=1)
                if idx_list:
                    player.necromancer_retrieve(idx_list[0])
            else:
                print("Invalid choice.")

        if not enemy.is_alive():
            print(f"\nYou defeated the {enemy.name}!")
            if encounters.has_more():
                enemy = encounters.next_enemy()
                print(f"\n--- A new enemy approaches: {enemy.name}! ---")

                # After each victory, chance for shop or event
                roll = random.random()
                if roll < 0.5:
                    open_shop(player)
                else:
                    print("You explore the area but find nothing of interest.")
                continue
            else:
                break

        # Enemy turn ------------------------------------------------------
        print("\n--- Enemy Turn ---")
        enemy.attack_player(player)

    # End of combat ---------------------------------------------------------
    meta = load_meta()
    if player.is_alive():
        won = not enemy or not encounters.has_more()
        if won:
            print("\nCongratulations! You survived all encounters.")
            # reward permanent HP every victory threshold
            add_permanent_hp(meta, 5)
            print("Permanent HP increased by 5!")
        else:
            print("\nYou retreated before finishing all encounters.")
        record_run(meta, won, player.gold)
    else:
        record_run(meta, False, player.gold)

    save_meta(meta)
    if not player.is_alive():
        print("\nGame Over. You were defeated.")


if __name__ == "__main__":
    play_game() 