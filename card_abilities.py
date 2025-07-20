from __future__ import annotations
from typing import TYPE_CHECKING, Any
import random
from status_effects import (
    StunEffect, HealEffect, DamageBuffEffect, ShieldEffect, 
    DamageReductionEffect, PoisonEffect
)

if TYPE_CHECKING:
    from entities.player import Player
    from entities.enemy import Enemy


class CombatContext:
    """Simple combat context for tarot card effects."""
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy
        self.last_hand = ''


def apply_card_combination_abilities(hand_name: str, player: 'Player', enemy: 'Enemy', base_damage: int) -> dict:
    """
    Apply special abilities based on the poker hand combination.
    Returns a dictionary with information about what effects were applied.
    """
    effects_applied = []
    
    # Get the status effect managers
    player_effects = getattr(player, 'status_effects', None)
    enemy_effects = getattr(enemy, 'status_effects', None)
    
    # Check for Fortune Teller joker (increases chances by 50%)
    chance_multiplier = 1.0
    if hasattr(player, 'jokers') and 'fortune_teller' in player.jokers:
        chance_multiplier = 1.5
    
    if hand_name == "High Card":
        # 30% chance of stunning enemy (affected by Fortune Teller)
        stun_chance = min(0.3 * chance_multiplier, 1.0)
        if random.random() < stun_chance:
            if enemy_effects:
                enemy_effects.add_effect(StunEffect(), enemy)
                effects_applied.append("Enemy stunned!")
    
    elif hand_name == "Pair":
        # Heal player
        heal_amount = base_damage // 2  # Heal for half the damage dealt
        if player_effects:
            player_effects.add_effect(HealEffect(heal_amount), player)
            effects_applied.append(f"Healed for {heal_amount} HP!")
    
    elif hand_name == "Two Pair":
        # 50% chance of twice the damage (affected by Fortune Teller)
        double_chance = min(0.5 * chance_multiplier, 1.0)
        if random.random() < double_chance:
            # This is handled by returning a damage multiplier
            effects_applied.append("Double damage!")
            return {"effects": effects_applied, "damage_multiplier": 2.0}
    
    elif hand_name == "Three of a Kind":
        # Tick damage every turn for both enemy and player
        poison_damage = max(3, base_damage // 10)  # At least 3 damage per turn
        if enemy_effects:
            enemy_effects.add_effect(PoisonEffect(poison_damage, 3), enemy)
        if player_effects:
            player_effects.add_effect(PoisonEffect(poison_damage // 2, 3), player)  # Less self-damage
        effects_applied.append(f"Poison applied! ({poison_damage} damage/turn to enemy, {poison_damage//2} to self)")
    
    elif hand_name == "Straight":
        # 30% damage increase buff for next attack
        if player_effects:
            player_effects.add_effect(DamageBuffEffect(1.3), player)
            effects_applied.append("Damage buff for next attack!")
    
    elif hand_name == "Flush":
        # Guard (30 health shield)
        shield_amount = 30
        if player_effects:
            player_effects.add_effect(ShieldEffect(shield_amount), player)
            effects_applied.append(f"Shield gained ({shield_amount} HP)!")
    
    elif hand_name == "Full House":
        # 30% damage reduction
        if player_effects:
            player_effects.add_effect(DamageReductionEffect(0.3), player)
            effects_applied.append("Damage reduction active!")
    
    elif hand_name == "Four of a Kind":
        # Activate all tarot card abilities on hand
        activated_items = []
        if hasattr(player, 'items'):
            for item in player.items[:]:  # Copy list to avoid modification issues
                if hasattr(item, 'on_use'):
                    try:
                        context = CombatContext(player, enemy)
                        item.on_use(context)
                        activated_items.append(str(item))
                        player.items.remove(item)  # Consume the item
                    except Exception as e:
                        print(f"Error applying {item} effect: {e}")
        if activated_items:
            effects_applied.append(f"Activated items: {', '.join(activated_items)}")
        else:
            effects_applied.append("No items to activate!")
    
    elif hand_name == "Straight Flush":
        # Discard +1 (increase discard limit)
        if hasattr(player, 'max_discards'):
            player.max_discards += 1
            effects_applied.append("Discard limit increased by 1!")
    
    elif hand_name == "Royal Flush":
        # Multiply attack by 4
        effects_applied.append("Attack multiplied by 4!")
        return {"effects": effects_applied, "damage_multiplier": 4.0}
    
    # New combinations
    elif hand_name == "Five of a Kind":
        # All pair, three of a kind, four of a kind abilities combined
        # Heal (from Pair)
        heal_amount = base_damage // 2
        if player_effects:
            player_effects.add_effect(HealEffect(heal_amount), player)
        
        # Poison (from Three of a Kind)
        poison_damage = max(3, base_damage // 10)
        if enemy_effects:
            enemy_effects.add_effect(PoisonEffect(poison_damage, 3), enemy)
        if player_effects:
            player_effects.add_effect(PoisonEffect(poison_damage // 2, 3), player)
        
        # Activate all items (from Four of a Kind)
        activated_items = []
        if hasattr(player, 'items'):
            for item in player.items[:]:
                if hasattr(item, 'on_use'):
                    try:
                        # Create a simple combat context for the tarot card
                        class CombatContext:
                            def __init__(self, p, e):
                                self.player = p
                                self.enemy = e
                                self.last_hand = ''
                        
                        context = CombatContext(player, enemy)
                        item.on_use(context)
                        activated_items.append(str(item))
                        player.items.remove(item)
                    except Exception as e:
                        print(f"Error applying {item} effect: {e}")
        
        effects_applied.append(f"Combined abilities: Heal ({heal_amount}), Poison ({poison_damage}), Items activated")
    
    elif hand_name == "Flush House":
        # Flush and Full House abilities combined
        # Shield (from Flush)
        shield_amount = 30
        if player_effects:
            player_effects.add_effect(ShieldEffect(shield_amount), player)
        
        # Damage reduction (from Full House)
        if player_effects:
            player_effects.add_effect(DamageReductionEffect(0.3), player)
        
        effects_applied.append(f"Combined abilities: Shield ({shield_amount}) + Damage Reduction (30%)")
    
    elif hand_name == "Flush Five":
        # Random max health percent damage to enemy (0-20%)
        if enemy and hasattr(enemy, 'max_hp'):
            damage_percent = random.uniform(0, 0.20)  # 0-20%
            bonus_damage = int(enemy.max_hp * damage_percent)
            enemy.take_damage(bonus_damage)
            effects_applied.append(f"Bonus max HP damage: {bonus_damage} ({damage_percent*100:.1f}% of max HP)")
    
    return {"effects": effects_applied, "damage_multiplier": 1.0}


def get_ability_description(hand_name: str) -> str:
    """Get a description of what ability a hand combination provides."""
    descriptions = {
        "High Card": "30% chance to stun enemy",
        "Pair": "Heal for half damage dealt",
        "Two Pair": "50% chance for double damage",
        "Three of a Kind": "Poison both players",
        "Straight": "30% damage buff next attack",
        "Flush": "30 HP shield",
        "Full House": "30% damage reduction",
        "Four of a Kind": "Activate all tarot cards",
        "Straight Flush": "Discard +1",
        "Royal Flush": "4x damage multiplier",
        "Five of a Kind": "Pair + Three of a Kind + Four of a Kind abilities",
        "Flush House": "Flush + Full House abilities",
        "Flush Five": "0-20% max HP damage to enemy"
    }
    return descriptions.get(hand_name, "No special ability") 