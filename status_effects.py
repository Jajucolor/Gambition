from __future__ import annotations
from typing import Dict, List, Any
import random


class StatusEffect:
    """Base class for status effects that can be applied to players or enemies."""
    
    def __init__(self, name: str, duration: int = 1):
        self.name = name
        self.duration = duration
        self.active = True
    
    def apply(self, target: Any) -> None:
        """Apply the effect to the target."""
        pass
    
    def tick(self, target: Any) -> None:
        """Called each turn while the effect is active."""
        pass
    
    def expire(self, target: Any) -> None:
        """Called when the effect expires."""
        pass
    
    def reduce_duration(self) -> bool:
        """Reduce duration by 1. Returns True if effect should be removed."""
        self.duration -= 1
        if self.duration <= 0:
            self.active = False
            return True
        return False


class StunEffect(StatusEffect):
    """Prevents the target from taking actions."""
    
    def __init__(self):
        super().__init__("Stunned", 1)
    
    def apply(self, target: Any) -> None:
        print(f"{getattr(target, 'name', 'Target')} is stunned and cannot act!")


class HealEffect(StatusEffect):
    """Instantly heals the target."""
    
    def __init__(self, amount: int):
        super().__init__("Heal", 0)  # Instant effect
        self.amount = amount
    
    def apply(self, target: Any) -> None:
        if hasattr(target, 'hp') and hasattr(target, 'max_hp'):
            old_hp = target.hp
            target.hp = min(target.max_hp, target.hp + self.amount)
            healed = target.hp - old_hp
            print(f"{getattr(target, 'name', 'Target')} healed for {healed} HP! ({target.hp}/{target.max_hp})")


class DamageBuffEffect(StatusEffect):
    """Increases damage for next attack."""
    
    def __init__(self, multiplier: float):
        super().__init__("Damage Buff", 1)
        self.multiplier = multiplier
    
    def apply(self, target: Any) -> None:
        print(f"{getattr(target, 'name', 'Target')} gains a {int((self.multiplier - 1) * 100)}% damage buff!")


class ShieldEffect(StatusEffect):
    """Provides temporary HP shield."""
    
    def __init__(self, amount: int):
        super().__init__("Shield", 999)  # Lasts until depleted
        self.amount = amount
        self.original_amount = amount
    
    def apply(self, target: Any) -> None:
        print(f"{getattr(target, 'name', 'Target')} gains a {self.amount} HP shield!")
    
    def absorb_damage(self, damage: int) -> int:
        """Absorb damage and return remaining damage."""
        absorbed = min(self.amount, damage)
        self.amount -= absorbed
        remaining = damage - absorbed
        
        if self.amount <= 0:
            self.active = False
            print(f"Shield depleted!")
        else:
            print(f"Shield absorbed {absorbed} damage! ({self.amount} shield remaining)")
        
        return remaining


class DamageReductionEffect(StatusEffect):
    """Reduces incoming damage by a percentage."""
    
    def __init__(self, reduction: float, duration: int = 999):
        super().__init__("Damage Reduction", duration)
        self.reduction = reduction
    
    def apply(self, target: Any) -> None:
        print(f"{getattr(target, 'name', 'Target')} gains {int(self.reduction * 100)}% damage reduction!")
    
    def reduce_damage(self, damage: int) -> int:
        """Reduce damage and return the reduced amount."""
        reduced = int(damage * (1 - self.reduction))
        print(f"Damage reduced from {damage} to {reduced}!")
        return reduced


class PoisonEffect(StatusEffect):
    """Deals damage over time to the target."""
    
    def __init__(self, damage_per_turn: int, duration: int = 3):
        super().__init__("Poison", duration)
        self.damage_per_turn = damage_per_turn
    
    def apply(self, target: Any) -> None:
        print(f"{getattr(target, 'name', 'Target')} is poisoned!")
    
    def tick(self, target: Any) -> None:
        if hasattr(target, 'hp'):
            target.hp = max(0, target.hp - self.damage_per_turn)
            print(f"{getattr(target, 'name', 'Target')} takes {self.damage_per_turn} poison damage! ({target.hp} HP remaining)")


class StatusEffectManager:
    """Manages status effects for a character."""
    
    def __init__(self):
        self.effects: List[StatusEffect] = []
    
    def add_effect(self, effect: StatusEffect, target: Any) -> None:
        """Add a status effect and apply it immediately."""
        # Remove existing effects of the same type (except stackable ones)
        if not isinstance(effect, (PoisonEffect,)):  # Poison can stack
            self.effects = [e for e in self.effects if type(e) != type(effect)]
        
        self.effects.append(effect)
        effect.apply(target)
    
    def tick_effects(self, target: Any) -> None:
        """Process all effects for one turn."""
        expired = []
        for effect in self.effects:
            if effect.active:
                effect.tick(target)
                if effect.reduce_duration():
                    effect.expire(target)
                    expired.append(effect)
        
        # Remove expired effects
        for effect in expired:
            self.effects.remove(effect)
    
    def has_effect(self, effect_type: type) -> bool:
        """Check if target has a specific type of effect."""
        return any(isinstance(e, effect_type) and e.active for e in self.effects)
    
    def get_effect(self, effect_type: type) -> StatusEffect | None:
        """Get the first active effect of a specific type."""
        for effect in self.effects:
            if isinstance(effect, effect_type) and effect.active:
                return effect
        return None
    
    def clear_all_effects(self) -> None:
        """Remove all status effects."""
        self.effects.clear()
    
    def modify_outgoing_damage(self, damage: int) -> int:
        """Apply damage buffs to outgoing damage."""
        modified = damage
        for effect in self.effects:
            if isinstance(effect, DamageBuffEffect) and effect.active:
                modified = int(modified * effect.multiplier)
                effect.active = False  # Consume the buff
        return modified
    
    def modify_incoming_damage(self, damage: int) -> int:
        """Apply shields and damage reduction to incoming damage."""
        modified = damage
        
        # Apply damage reduction first
        for effect in self.effects:
            if isinstance(effect, DamageReductionEffect) and effect.active:
                modified = effect.reduce_damage(modified)
        
        # Then apply shields
        for effect in self.effects:
            if isinstance(effect, ShieldEffect) and effect.active:
                modified = effect.absorb_damage(modified)
                if not effect.active:
                    self.effects.remove(effect)
        
        return modified 