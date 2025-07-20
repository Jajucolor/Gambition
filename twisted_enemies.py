from __future__ import annotations
from typing import Dict, List, Optional
from dataclasses import dataclass
from entities.enemy import Enemy, ENEMY_TEMPLATES
from status_effects import StatusEffectManager, PoisonEffect, StunEffect
import random


@dataclass
class TwistedLore:
    """Background story for a Twisted enemy"""
    former_identity: str
    obsession: str
    transformation_story: str
    memory_echo: str  # Revealed when defeated


class TwistedEnemy(Enemy):
    """Enhanced enemy class for story-driven Twisted creatures"""
    
    def __init__(self, name: str, hp: int, attack: int, defense: int = 0, 
                 lore: Optional[TwistedLore] = None, special_abilities: Optional[List[str]] = None):
        super().__init__(name, hp, attack, defense)
        self.lore = lore
        self.special_abilities = special_abilities or []
        self.is_boss = False
        self.district_theme = ""
    
    def use_special_ability(self, player) -> str:
        """Use a special ability based on the Twisted's nature"""
        if not self.special_abilities:
            return ""
        
        ability = random.choice(self.special_abilities)
        
        if ability == "greed_drain":
            # Steals gold from player
            stolen = min(10, getattr(player, 'gold', 0))
            if hasattr(player, 'gold'):
                player.gold -= stolen
            return f"{self.name} drains {stolen} gold from you with its grasping claws!"
        
        elif ability == "vanity_reflect":
            # Reflects damage back to attacker
            return f"{self.name}'s crystalline surface gleams menacingly!"
        
        elif ability == "despair_weaken":
            # Reduces player's next attack
            return f"{self.name} emanates an aura of crushing despair!"
        
        elif ability == "rage_frenzy":
            # Increases own attack temporarily
            self.attack_value = int(self.attack_value * 1.5)
            return f"{self.name} enters a berserk frenzy!"
        
        elif ability == "ink_blind":
            # Chance to make player miss next attack
            return f"{self.name} sprays corrupted ink, obscuring your vision!"
        
        return f"{self.name} uses {ability}!"
    
    def get_memory_echo(self) -> str:
        """Return the memory echo revealed when defeated"""
        if self.lore:
            return self.lore.memory_echo
        return "The Twisted fades away, leaving only silence."


# Create the Twisted enemy catalog
TWISTED_ENEMIES = {}

def create_twisted_enemy(enemy_type: str) -> TwistedEnemy:
    """Factory function to create Twisted enemies"""
    
    if enemy_type == "Twisted Guard":
        lore = TwistedLore(
            former_identity="Station Security Guard Marcus Webb",
            obsession="Absolute Order and Control",
            transformation_story="A guard who became obsessed with perfect security, his body fused with metal detectors and surveillance equipment.",
            memory_echo="'I just... I just wanted to keep everyone safe... Why won't they follow the rules?'"
        )
        return TwistedEnemy(
            name="Twisted Guard",
            hp=60, attack=12, defense=3,
            lore=lore,
            special_abilities=["stun_baton", "alarm_call"]
        )
    
    elif enemy_type == "Twisted Croupier":
        lore = TwistedLore(
            former_identity="Casino Dealer Elena Vasquez", 
            obsession="The Perfect Game",
            transformation_story="A croupier who became obsessed with controlling every outcome, her hands became roulette wheels and her eyes became dice.",
            memory_echo="'The house always wins... always... but what if it doesn't? What if I can't control the odds?'"
        )
        return TwistedEnemy(
            name="Twisted Croupier",
            hp=80, attack=15, defense=2,
            lore=lore,
            special_abilities=["rigged_game", "luck_steal"]
        )
    
    elif enemy_type == "The Dealer Supreme":
        # Boss of Casino District
        lore = TwistedLore(
            former_identity="High Roller Vincent Goldhand",
            obsession="Infinite Wealth",
            transformation_story="The richest gambler in the city, his greed transformed him into a living casino, cards and chips embedded in his flesh.",
            memory_echo="'Chairman Valerius promised me... promised me I could have it all... Why did the gold turn to ash in my mouth?'"
        )
        boss = TwistedEnemy(
            name="The Dealer Supreme",
            hp=200, attack=25, defense=5,
            lore=lore,
            special_abilities=["greed_drain", "golden_bind", "jackpot_explosion"]
        )
        boss.is_boss = True
        boss.district_theme = "wealth_corruption"
        return boss
    
    elif enemy_type == "Ink Wraith":
        lore = TwistedLore(
            former_identity="Journalist Sarah Blackwell",
            obsession="Exposing the Truth",
            transformation_story="A reporter who became obsessed with uncovering every secret, her body dissolved into living ink that seeks to absorb all information.",
            memory_echo="'The truth... I was so close to the truth about the Syndicate... but the ink... it burns...'"
        )
        return TwistedEnemy(
            name="Ink Wraith", 
            hp=50, attack=10, defense=1,
            lore=lore,
            special_abilities=["ink_blind", "truth_drain"]
        )
    
    elif enemy_type == "The Editor-in-Chief":
        # Boss of Printing Quarter
        lore = TwistedLore(
            former_identity="Newspaper Editor Thomas Blackwood",
            obsession="Controlling Information",
            transformation_story="The head of The Daily Fortune, his obsession with narrative control turned him into a creature of living text and headlines.",
            memory_echo="'I wrote the stories... I controlled what people knew... Valerius said I could write reality itself...'"
        )
        boss = TwistedEnemy(
            name="The Editor-in-Chief",
            hp=180, attack=20, defense=4,
            lore=lore,
            special_abilities=["rewrite_reality", "headline_attack", "censorship_silence"]
        )
        boss.is_boss = True
        boss.district_theme = "information_control"
        return boss
    
    elif enemy_type == "Crystal Gardener":
        lore = TwistedLore(
            former_identity="Groundskeeper Harold Moss",
            obsession="Perfect Beauty",
            transformation_story="A gardener who wanted to create the perfect garden, his body merged with Fortuna crystals to become a living topiary.",
            memory_echo="'The gardens... they were supposed to be beautiful forever... crystalline perfection... but nothing grows anymore...'"
        )
        return TwistedEnemy(
            name="Crystal Gardener",
            hp=70, attack=14, defense=6,
            lore=lore,
            special_abilities=["crystal_growth", "root_entangle"]
        )
    
    elif enemy_type == "The Perfect Housewife":
        # Boss of Residential Gardens
        lore = TwistedLore(
            former_identity="Margaret Hartwell, Community Leader",
            obsession="Perfect Domestic Life", 
            transformation_story="A housewife who became obsessed with maintaining perfect order in her home and community, her body became a fusion of household appliances and crystalline perfection.",
            memory_echo="'Everything had to be perfect... the Chairman promised me a perfect world... but perfection is so... cold...'"
        )
        boss = TwistedEnemy(
            name="The Perfect Housewife",
            hp=160, attack=18, defense=7,
            lore=lore,
            special_abilities=["domestic_fury", "crystal_prison", "perfect_order"]
        )
        boss.is_boss = True
        boss.district_theme = "domestic_horror"
        return boss
    
    elif enemy_type == "Twisted Worker":
        lore = TwistedLore(
            former_identity="Factory Worker Jim Patterson",
            obsession="Endless Productivity",
            transformation_story="A worker who became obsessed with meeting impossible quotas, his body fused with industrial machinery.",
            memory_echo="'Must work... must produce... the quota... never enough... never fast enough...'"
        )
        return TwistedEnemy(
            name="Twisted Worker",
            hp=65, attack=16, defense=4,
            lore=lore,
            special_abilities=["industrial_smash", "toxic_steam"]
        )
    
    elif enemy_type == "The Foreman":
        # Boss of Factory District
        lore = TwistedLore(
            former_identity="Factory Supervisor Big Bill Morrison",
            obsession="Total Control Over Production",
            transformation_story="The factory foreman who became obsessed with perfect efficiency, his body became a massive industrial complex of gears, pistons, and Fortuna conduits.",
            memory_echo="'Efficiency... productivity... the Chairman said we could automate everything... but the workers... they're all gone now...'"
        )
        boss = TwistedEnemy(
            name="The Foreman",
            hp=220, attack=22, defense=8,
            lore=lore,
            special_abilities=["industrial_rampage", "toxic_cloud", "assembly_line"]
        )
        boss.is_boss = True
        boss.district_theme = "industrial_nightmare"
        return boss
    
    # Default fallback
    else:
        return TwistedEnemy(
            name="Unknown Twisted",
            hp=40, attack=8, defense=0,
            special_abilities=["desperate_strike"]
        )


def get_district_enemies(district_id: str) -> List[str]:
    """Get appropriate enemies for a district"""
    district_enemies = {
        "grand_terminal": ["Twisted Guard"],
        "casino_district": ["Twisted Croupier", "The Dealer Supreme"],
        "printing_quarter": ["Ink Wraith", "The Editor-in-Chief"],
        "residential_gardens": ["Crystal Gardener", "The Perfect Housewife"],
        "factory_district": ["Twisted Worker", "The Foreman"],
        "the_depths": ["Valerius_Final_Form"]
    }
    
    return district_enemies.get(district_id, ["Twisted Guard"])


def get_memory_echo_rewards(enemy_name: str) -> Dict[str, int]:
    """Get rewards for defeating bosses and witnessing their memory echoes"""
    boss_rewards = {
        "The Dealer Supreme": {"gold": 100, "exp": 50},
        "The Editor-in-Chief": {"gold": 120, "exp": 60},
        "The Perfect Housewife": {"gold": 110, "exp": 55},
        "The Foreman": {"gold": 150, "exp": 70},
    }
    
    return boss_rewards.get(enemy_name, {"gold": 20, "exp": 10})


# Update the main enemy templates to include Twisted variants
ENEMY_TEMPLATES.update({
    'Twisted Guard': dict(hp=60, attack=12, defense=3),
    'Twisted Croupier': dict(hp=80, attack=15, defense=2),
    'The Dealer Supreme': dict(hp=200, attack=25, defense=5),
    'Ink Wraith': dict(hp=50, attack=10, defense=1),
    'The Editor-in-Chief': dict(hp=180, attack=20, defense=4),
    'Crystal Gardener': dict(hp=70, attack=14, defense=6),
    'The Perfect Housewife': dict(hp=160, attack=18, defense=7),
    'Twisted Worker': dict(hp=65, attack=16, defense=4),
    'The Foreman': dict(hp=220, attack=22, defense=8),
}) 