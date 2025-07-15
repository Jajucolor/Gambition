from __future__ import annotations

from dataclasses import dataclass
from typing import List, Callable, Dict, Any, Optional
import random

from entities.player import Player
from tarot import TAROT_DEFINITIONS, TarotCard
from card import Card
from constants import SUITS, RANKS


@dataclass
class DialogueChoice:
    text: str
    action: Callable[[Player, 'NPC'], str]  # returns next dialogue key or 'END'
    requirement: Optional[Callable[[Player], bool]] = None  # condition to show choice


@dataclass
class DialogueNode:
    text: str
    choices: List[DialogueChoice]


class NPC:
    def __init__(self, name: str, npc_type: str, dialogue_tree: Dict[str, DialogueNode]):
        self.name = name
        self.npc_type = npc_type  # 'quest_giver', 'merchant', 'intruder'
        self.dialogue_tree = dialogue_tree
        self.current_state = 'start'
        self.quest_completed = False
        self.has_traded = False
        self.is_hostile = False

    def get_current_dialogue(self) -> DialogueNode:
        return self.dialogue_tree.get(self.current_state, self.dialogue_tree['start'])

    def process_choice(self, choice_idx: int, player: Player) -> str:
        current = self.get_current_dialogue()
        if 0 <= choice_idx < len(current.choices):
            choice = current.choices[choice_idx]
            if choice.requirement is None or choice.requirement(player):
                next_state = choice.action(player, self)
                if next_state != 'END':
                    self.current_state = next_state
                return next_state
        return 'INVALID'


# ---------------------------------------------------------------------------
# NPC Action Functions
# ---------------------------------------------------------------------------

def _give_quest_reward(player: Player, npc: NPC) -> str:
    """Quest completion reward."""
    if not npc.quest_completed:
        player.gold += 25
        # Give random tarot
        tarot_key = random.choice(list(TAROT_DEFINITIONS.keys()))
        player.add_item(TAROT_DEFINITIONS[tarot_key])
        npc.quest_completed = True
        print(f"Quest completed! Gained 25 gold and {TAROT_DEFINITIONS[tarot_key].name}")
    return 'quest_complete'

def _accept_quest(player: Player, npc: NPC) -> str:
    """Accept a quest."""
    print("Quest accepted: Defeat 3 enemies and return!")
    # In a full implementation, this would set quest flags
    return 'quest_active'

def _decline_quest(player: Player, npc: NPC) -> str:
    """Decline quest."""
    return 'quest_declined'

def _merchant_trade(player: Player, npc: NPC) -> str:
    """Special merchant trade."""
    if player.gold >= 20 and not npc.has_traded:
        player.gold -= 20
        # Give special card
        special_card = Card('Spades', 'A')  # Ace of Spades
        player.deck.cards.append(special_card)
        npc.has_traded = True
        print("Traded 20 gold for Ace of Spades!")
        return 'trade_complete'
    elif npc.has_traded:
        return 'already_traded'
    else:
        return 'insufficient_gold'

def _provoke_intruder(player: Player, npc: NPC) -> str:
    """Trigger combat with intruder."""
    npc.is_hostile = True
    print("The stranger draws a weapon! Combat begins!")
    return 'combat_triggered'

def _peaceful_resolution(player: Player, npc: NPC) -> str:
    """Avoid conflict."""
    player.gold += 5
    print("The stranger calms down and gives you 5 gold as apology.")
    return 'peaceful_end'

def _simple_goodbye(player: Player, npc: NPC) -> str:
    """End conversation."""
    return 'END'


# ---------------------------------------------------------------------------
# NPC Definitions
# ---------------------------------------------------------------------------

def create_quest_giver() -> NPC:
    """Village elder with a quest."""
    tree = {
        'start': DialogueNode(
            "Greetings, traveler! Our village is plagued by monsters. Will you help us?",
            [
                DialogueChoice("I'll help you.", _accept_quest),
                DialogueChoice("Not interested.", _decline_quest),
                DialogueChoice("What's the reward?", lambda p, n: 'reward_info')
            ]
        ),
        'reward_info': DialogueNode(
            "I can offer 25 gold and a powerful Tarot card for your services.",
            [
                DialogueChoice("Sounds fair, I accept.", _accept_quest),
                DialogueChoice("Still not interested.", _decline_quest)
            ]
        ),
        'quest_active': DialogueNode(
            "Good luck on your quest! Return when you've defeated 3 enemies.",
            [
                DialogueChoice("I've completed the quest!", _give_quest_reward, 
                             lambda p: True),  # In real game: check quest completion
                DialogueChoice("Still working on it.", _simple_goodbye)
            ]
        ),
        'quest_complete': DialogueNode(
            "Thank you, hero! The village is safe thanks to you.",
            [DialogueChoice("Farewell.", _simple_goodbye)]
        ),
        'quest_declined': DialogueNode(
            "I understand. Safe travels, stranger.",
            [DialogueChoice("Actually, I changed my mind.", _accept_quest),
             DialogueChoice("Goodbye.", _simple_goodbye)]
        )
    }
    return NPC("Village Elder", "quest_giver", tree)


def create_wandering_merchant() -> NPC:
    """Merchant with special items."""
    tree = {
        'start': DialogueNode(
            "Welcome, traveler! I have rare wares from distant lands.",
            [
                DialogueChoice("What do you sell?", lambda p, n: 'show_wares'),
                DialogueChoice("I'm not buying.", _simple_goodbye)
            ]
        ),
        'show_wares': DialogueNode(
            "I have a legendary Ace of Spades for 20 gold. Interested?",
            [
                DialogueChoice("Yes, I'll buy it.", _merchant_trade),
                DialogueChoice("Too expensive.", _simple_goodbye)
            ]
        ),
        'trade_complete': DialogueNode(
            "Excellent! That card will serve you well in battle.",
            [DialogueChoice("Thank you.", _simple_goodbye)]
        ),
        'already_traded': DialogueNode(
            "I've already sold you my best item! Come back another time.",
            [DialogueChoice("Farewell.", _simple_goodbye)]
        ),
        'insufficient_gold': DialogueNode(
            "You don't have enough gold, friend. Come back when you do!",
            [DialogueChoice("I'll return later.", _simple_goodbye)]
        )
    }
    return NPC("Wandering Merchant", "merchant", tree)


def create_suspicious_intruder() -> NPC:
    """Hostile NPC that can be fought or pacified."""
    tree = {
        'start': DialogueNode(
            "You there! Hand over your gold or face the consequences!",
            [
                DialogueChoice("Never! Prepare to fight!", _provoke_intruder),
                DialogueChoice("Calm down, let's talk.", lambda p, n: 'negotiate'),
                DialogueChoice("Here, take 10 gold.", lambda p, n: 'bribe' if p.gold >= 10 else 'no_gold')
            ]
        ),
        'negotiate': DialogueNode(
            "Talk? Ha! You think words will save you?",
            [
                DialogueChoice("I'm not your enemy.", _peaceful_resolution),
                DialogueChoice("Fine, let's fight!", _provoke_intruder)
            ]
        ),
        'bribe': DialogueNode(
            "Smart choice. Now get out of my sight!",
            [DialogueChoice("Gladly...", lambda p, n: (setattr(p, 'gold', p.gold - 10), 'END')[1])]
        ),
        'no_gold': DialogueNode(
            "You're broke? Then you're worthless to me. Fight or flee!",
            [
                DialogueChoice("I'll fight!", _provoke_intruder),
                DialogueChoice("I'm leaving!", _simple_goodbye)
            ]
        ),
        'combat_triggered': DialogueNode(
            "Draw your cards, fool!",
            [DialogueChoice("Let's do this!", _simple_goodbye)]
        ),
        'peaceful_end': DialogueNode(
            "Perhaps I was too hasty. Safe travels.",
            [DialogueChoice("Thank you.", _simple_goodbye)]
        )
    }
    return NPC("Suspicious Stranger", "intruder", tree)


# ---------------------------------------------------------------------------
# NPC Registry
# ---------------------------------------------------------------------------

NPC_TYPES = {
    'quest_giver': create_quest_giver,
    'merchant': create_wandering_merchant,
    'intruder': create_suspicious_intruder
}

def create_random_npc() -> NPC:
    """Create a random NPC."""
    npc_type = random.choice(list(NPC_TYPES.keys()))
    return NPC_TYPES[npc_type]() 