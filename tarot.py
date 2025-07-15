from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Any

# Forward reference to avoid circular import
CombatUIType = Any  # will be refined when imported inside combat module

@dataclass
class TarotCard:
    key: str
    name: str
    description: str
    on_use: Callable[[CombatUIType], None]  # called when player uses the card

    def __repr__(self) -> str:  # pragma: no cover
        return self.name

# ---------------------------------------------------------------------------
# Example tarot definitions
# ---------------------------------------------------------------------------

def _sun_effect(ui):  # noqa: ANN001
    """Adds +5 bonus damage to the next attack."""
    setattr(ui, '_tarot_bonus', getattr(ui, '_tarot_bonus', 0) + 5)
    ui.last_hand = 'Sun Blessing'


def _moon_effect(ui):  # noqa: ANN001
    """Heal 10 HP instantly."""
    ui.player.hp = min(ui.player.max_hp, ui.player.hp + 10)
    ui.last_hand = 'Moonlight Heal'


def _tower_effect(ui):  # noqa: ANN001
    """Placeholder: prints message for future implementation."""
    print('The Tower shakes the battlefield! (effect TBD)')
    ui.last_hand = 'Tower Foresight'

TAROT_DEFINITIONS: Dict[str, TarotCard] = {
    'sun': TarotCard('sun', 'The Sun', '+5 dmg to next attack', _sun_effect),
    'moon': TarotCard('moon', 'The Moon', 'Heal 10 HP', _moon_effect),
    'tower': TarotCard('tower', 'The Tower', '???', _tower_effect),
} 