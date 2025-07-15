from typing import Callable, Dict, Any, List

from card import Card

# Type aliases --------------------------------------------------------------
JokerEffect = Callable[[List[Card], float, str | None], float]


# Helper wrappers -----------------------------------------------------------

def _simple_add_per_card(add_amount: float) -> JokerEffect:
    def _effect(hand: List[Card], base_damage: float, hand_type: str | None) -> float:
        return base_damage + add_amount * len(hand)
    return _effect


def _multiplier_by_card_count() -> JokerEffect:
    def _effect(hand: List[Card], base_damage: float, hand_type: str | None) -> float:
        return base_damage * len(hand)
    return _effect


def _conditional_multiplier(valid_hands: List[str], factor: float) -> JokerEffect:
    def _effect(hand: List[Card], base_damage: float, hand_type: str | None) -> float:
        if hand_type in valid_hands:
            return base_damage * factor
        return base_damage
    return _effect


# ----------------------------------------------------------------------------
# Joker catalogue
# ----------------------------------------------------------------------------
JOKER_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    'blank': {
        'name': 'The Blank',
        'description': 'No inherent effect, but can be used as a base for other Jokers.',
        'effect': lambda hand, dmg, ht: dmg,
    },
    'joker': {
        'name': 'The Joker',
        'description': 'Adds +1 damage per card in the hand.',
        'effect': _simple_add_per_card(1),
    },
    'archon': {
        'name': 'The Archon',
        'description': 'Multiplies damage based on the number of cards played in the hand.',
        'effect': _multiplier_by_card_count(),
    },
    'ruse': {
        'name': 'The Ruse',
        'description': 'Increases the damage of Pairs and Three of a Kind by 50%.',
        'effect': _conditional_multiplier(['Pair', 'Three of a Kind'], 1.5),
    },
    'emperor': {
        'name': 'The Emperor',
        'description': 'Increases the damage of Straights and Flushes by 50%.',
        'effect': _conditional_multiplier(['Straight', 'Flush'], 1.5),
    },
    'hierophant': {
        'name': 'The Hierophant',
        'description': 'Increases the damage of Four of a Kind and Straight Flushes by 50%.',
        'effect': _conditional_multiplier(['Four of a Kind', 'Straight Flush'], 1.5),
    },
    'fool': {
        'name': 'The Fool',
        'description': 'Draw +1 card each draw phase.',
        'effect': lambda hand, dmg, ht: dmg,  # passive, handled elsewhere
        'per_turn_extra_draw': 1,
    },
    'magician': {
        'name': 'The Magician',
        'description': 'Once per turn, swap a card in hand with top of deck.',
        'effect': lambda hand, dmg, ht: dmg,  # active ability
    },
    'business_card': {
        'name': 'The Businessman',
        'description': 'Single-use: triples final damage of a hand.',
        'effect': lambda hand, dmg, ht: dmg * 3,
        'single_use': True,
    },
    'gemini': {
        'name': 'The Gemini',
        'description': 'Duplicates the effects of two other Jokers.',
        'effect': lambda hand, dmg, ht: dmg,  # handled specially in apply_jokers
    },
    'necromancer': {
        'name': 'The Necromancer',
        'description': 'Lets you retrieve a card from the discard pile once per turn.',
        'effect': lambda hand, dmg, ht: dmg,  # active ability handled elsewhere
    },
    # More jokers can be added here
}


def apply_jokers(hand: List[Card], base_damage: float, hand_type: str, jokers: List[str]) -> float:
    """Apply joker effects sequentially and return updated damage.

    Jokers marked as single_use will be consumed (removed from *jokers* list)
    after their effect is applied.
    """
    damage = base_damage
    consumed: List[str] = []
    for jtype in jokers:
        definition = JOKER_DEFINITIONS.get(jtype)
        if not definition:
            continue
        effect = definition['effect']
        damage = effect(hand, damage, hand_type)
        if definition.get('single_use'):
            consumed.append(jtype)

    # Gemini duplication: apply effects of two other jokers again (per Gemini)
    if 'gemini' in jokers:
        # gather list of other joker types (in order)
        other_jokers = [j for j in jokers if j != 'gemini']
        duplicate_targets = other_jokers[:2]  # first two
        for _ in range(jokers.count('gemini')):
            for target in duplicate_targets:
                defn = JOKER_DEFINITIONS[target]
                damage = defn['effect'](hand, damage, hand_type)

    # Remove consumed jokers
    for j in consumed:
        jokers.remove(j)
        print(f"{JOKER_DEFINITIONS[j]['name']} was consumed!")

    return damage 