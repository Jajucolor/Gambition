# Card Combination Abilities & New Jokers

## Card Combination Abilities

All abilities preserve the original damage values and add special effects:

### Standard Combinations
- **High Card**: 30% chance of stunning enemy (enemy cannot move for one turn)
- **Pair**: Heal for half the damage dealt
- **Two Pair**: 50% chance of twice the damage
- **Three of a Kind**: Poison damage over time for both enemy and player (3 turns)
- **Straight**: 30% damage increase buff for next attack
- **Flush**: Guard (30 health shield)
- **Full House**: 30% damage reduction
- **Four of a Kind**: Activate all tarot card abilities in inventory
- **Straight Flush**: Discard +1 (increases discard limit by 1)
- **Royal Flush**: Multiply attack by 4

### New Combinations
- **Five of a Kind** (five same rank cards): Combines Pair + Three of a Kind + Four of a Kind abilities
- **Flush House** (full house with same suit): Combines Flush + Full House abilities  
- **Flush Five** (5 cards same rank and suit): Random max health percent damage to enemy (0-20%)

## New Jokers (Companions)

### Fortune Teller
- **Effect**: Increases all probability-based effects by 50%
- **Description**: Boosts the chances of High Card stun (30% → 45%) and Two Pair double damage (50% → 75%)

### Berserker  
- **Effect**: Damage increases by 2 each turn in combat
- **Description**: Turn 1: +0, Turn 2: +2, Turn 3: +4, etc.

### Echo Mage
- **Effect**: When you discard exactly one card, add a copy to your hand
- **Description**: Allows strategic card duplication through single-card discards

## Technical Implementation

### Status Effects System
- **StunEffect**: Prevents enemy from acting for one turn
- **HealEffect**: Instant healing
- **DamageBuffEffect**: Increases damage for next attack
- **ShieldEffect**: Absorbs incoming damage until depleted
- **DamageReductionEffect**: Reduces incoming damage by percentage
- **PoisonEffect**: Deals damage over time

### Integration Points
- Player and Enemy classes now have `status_effects` managers
- Combat system processes status effects each turn
- Card abilities apply effects based on poker hand combinations
- Jokers modify probability chances and provide passive benefits

### New Poker Hands
Updated `poker.py` and `constants.py` with:
- Five of a Kind (multiplier: 40)
- Flush House (multiplier: 35) 
- Flush Five (multiplier: 100)

### Enhanced Combat Flow
1. Player starts turn (status effects tick, combat turn increments)
2. Player attacks (abilities apply, joker effects activate)
3. Enemy starts turn (status effects tick)
4. Enemy attacks (stun check, damage modifiers apply)
5. Repeat until combat ends

All abilities work together to create strategic depth while maintaining the core poker-based combat system. 