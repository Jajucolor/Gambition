from __future__ import annotations
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from dataclasses import dataclass
from world_map import WorldMap, DistrictType
from entities.enemy import Enemy, create_enemy
from entities.player import Player
from status_effects import StatusEffectManager, StunEffect, PoisonEffect, ShieldEffect
import random


class BossType(Enum):
    """Types of boss encounters."""
    TWISTED_BOSS = "twisted_boss"
    STORY_BOSS = "story_boss"
    FINAL_BOSS = "final_boss"


class BossPhase(Enum):
    """Phases of a boss fight."""
    INTRO = "intro"
    PHASE_1 = "phase_1"
    PHASE_2 = "phase_2"
    PHASE_3 = "phase_3"
    DEFEATED = "defeated"


@dataclass
class BossAbility:
    """A special ability that a boss can use."""
    name: str
    description: str
    damage: int
    effects: List[str] = None
    cooldown: int = 0
    current_cooldown: int = 0
    
    def __post_init__(self):
        if self.effects is None:
            self.effects = []
    
    def can_use(self) -> bool:
        """Check if the ability can be used."""
        return self.current_cooldown <= 0
    
    def use(self) -> Dict[str, Any]:
        """Use the ability and return its effects."""
        if not self.can_use():
            return {}
        
        self.current_cooldown = self.cooldown
        
        return {
            'damage': self.damage,
            'effects': self.effects.copy()
        }
    
    def update_cooldown(self):
        """Update cooldown timer."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


class Boss:
    """Represents a boss enemy with special abilities and phases."""
    
    def __init__(self,
                 boss_id: str,
                 name: str,
                 boss_type: BossType,
                 district: DistrictType,
                 position: tuple,
                 base_stats: Dict[str, int],
                 abilities: List[BossAbility],
                 phases: List[BossPhase],
                 cutscene_intro: str = "",
                 cutscene_defeat: str = "",
                 on_defeat: Optional[Callable] = None):
        
        self.boss_id = boss_id
        self.name = name
        self.boss_type = boss_type
        self.district = district
        self.position = position
        self.base_stats = base_stats
        self.abilities = abilities
        self.phases = phases
        self.cutscene_intro = cutscene_intro
        self.cutscene_defeat = cutscene_defeat
        self.on_defeat = on_defeat
        
        # Boss state
        self.current_phase = BossPhase.INTRO
        self.phase_health_thresholds = {
            BossPhase.PHASE_1: 0.8,
            BossPhase.PHASE_2: 0.5,
            BossPhase.PHASE_3: 0.2
        }
        
        # Create the underlying enemy
        self.enemy = Enemy(
            name=name,
            hp=base_stats.get('hp', 100),
            attack=base_stats.get('attack', 10),
            defense=base_stats.get('defense', 0)
        )
        
        # Boss-specific status effects
        self.boss_effects = StatusEffectManager()
        
        # Combat state
        self.turn_count = 0
        self.special_abilities_used = []
    
    def get_health_percentage(self) -> float:
        """Get current health as a percentage."""
        return self.enemy.hp / self.enemy.max_hp
    
    def update_phase(self):
        """Update boss phase based on health."""
        health_pct = self.get_health_percentage()
        
        if health_pct <= 0.2 and BossPhase.PHASE_3 in self.phases:
            self.current_phase = BossPhase.PHASE_3
        elif health_pct <= 0.5 and BossPhase.PHASE_2 in self.phases:
            self.current_phase = BossPhase.PHASE_2
        elif health_pct <= 0.8 and BossPhase.PHASE_1 in self.phases:
            self.current_phase = BossPhase.PHASE_1
    
    def get_phase_abilities(self) -> List[BossAbility]:
        """Get abilities available in the current phase."""
        # In a real implementation, different phases would have different abilities
        return self.abilities
    
    def choose_ability(self) -> Optional[BossAbility]:
        """Choose which ability to use this turn."""
        available_abilities = [ability for ability in self.get_phase_abilities() if ability.can_use()]
        
        if not available_abilities:
            return None
        
        # Boss AI: prefer abilities that haven't been used recently
        unused_abilities = [ability for ability in available_abilities if ability.name not in self.special_abilities_used]
        
        if unused_abilities:
            return random.choice(unused_abilities)
        else:
            return random.choice(available_abilities)
    
    def take_turn(self, player: Player) -> Dict[str, Any]:
        """Take the boss's turn. Returns action details."""
        self.turn_count += 1
        
        # Update cooldowns
        for ability in self.abilities:
            ability.update_cooldown()
        
        # Choose ability
        chosen_ability = self.choose_ability()
        
        if chosen_ability:
            action = chosen_ability.use()
            self.special_abilities_used.append(chosen_ability.name)
            
            # Apply ability effects
            damage = action['damage']
            effects = action['effects']
            
            # Apply damage with any phase multipliers
            if self.current_phase == BossPhase.PHASE_2:
                damage = int(damage * 1.5)
            elif self.current_phase == BossPhase.PHASE_3:
                damage = int(damage * 2.0)
            
            # Apply effects
            for effect in effects:
                if effect == "stun":
                    player.status_effects.add_effect(StunEffect(), player)
                elif effect == "poison":
                    player.status_effects.add_effect(PoisonEffect(5, 3), player)
                elif effect == "shield":
                    self.boss_effects.add_effect(ShieldEffect(20), self.enemy)
            
            return {
                'ability': chosen_ability.name,
                'damage': damage,
                'effects': effects,
                'phase': self.current_phase.value
            }
        else:
            # Basic attack
            damage = self.enemy.attack_value
            if self.current_phase == BossPhase.PHASE_2:
                damage = int(damage * 1.3)
            elif self.current_phase == BossPhase.PHASE_3:
                damage = int(damage * 1.6)
            
            return {
                'ability': 'basic_attack',
                'damage': damage,
                'effects': [],
                'phase': self.current_phase.value
            }
    
    def is_defeated(self) -> bool:
        """Check if the boss is defeated."""
        return self.enemy.hp <= 0
    
    def get_phase_description(self) -> str:
        """Get description of current phase."""
        descriptions = {
            BossPhase.INTRO: "The boss is sizing you up...",
            BossPhase.PHASE_1: "The boss is taking you seriously!",
            BossPhase.PHASE_2: "The boss is enraged!",
            BossPhase.PHASE_3: "The boss is desperate and dangerous!"
        }
        return descriptions.get(self.current_phase, "Unknown phase")


class BossEncounter:
    """Manages a boss encounter with cutscenes and special rules."""
    
    def __init__(self, boss: Boss, player: Player, world_map: WorldMap):
        self.boss = boss
        self.player = player
        self.world_map = world_map
        
        # Encounter state
        self.encounter_started = False
        self.encounter_completed = False
        self.cutscene_active = False
        self.special_rules: List[str] = []
        
        # Combat tracking
        self.turn_number = 0
        self.boss_actions: List[Dict] = []
        self.player_actions: List[Dict] = []
    
    def start_encounter(self) -> bool:
        """Start the boss encounter. Returns True if successful."""
        if self.encounter_started:
            return False
        
        self.encounter_started = True
        self.cutscene_active = True
        
        print(f"\n=== BOSS ENCOUNTER: {self.boss.name} ===")
        
        # Play intro cutscene
        if self.boss.cutscene_intro:
            self._play_cutscene(self.boss.cutscene_intro)
        
        # Apply special rules
        self._apply_special_rules()
        
        self.cutscene_active = False
        print(f"Combat begins! {self.boss.get_phase_description()}")
        
        return True
    
    def _play_cutscene(self, cutscene_text: str):
        """Play a cutscene."""
        print(f"\n[CUTSCENE]")
        print(cutscene_text)
        print("[Press Enter to continue...]")
        # In a real implementation, this would wait for user input
    
    def _apply_special_rules(self):
        """Apply special combat rules for this boss."""
        if self.boss.boss_type == BossType.TWISTED_BOSS:
            self.special_rules.append("twisted_aura")
            print("Special Rule: Twisted Aura - Boss gains random buffs each turn")
        
        elif self.boss.boss_type == BossType.STORY_BOSS:
            self.special_rules.append("story_immunity")
            print("Special Rule: Story Immunity - Boss is immune to certain status effects")
        
        elif self.boss.boss_type == BossType.FINAL_BOSS:
            self.special_rules.append("reality_warp")
            print("Special Rule: Reality Warp - Boss can change combat rules mid-fight")
    
    def take_player_turn(self, player_action: Dict) -> Dict[str, Any]:
        """Process the player's turn and return boss response."""
        self.turn_number += 1
        self.player_actions.append(player_action)
        
        # Apply player action to boss
        damage = player_action.get('damage', 0)
        self.boss.enemy.take_damage(damage)
        
        # Update boss phase
        self.boss.update_phase()
        
        # Boss takes turn
        boss_action = self.boss.take_turn(self.player)
        self.boss_actions.append(boss_action)
        
        # Apply boss action to player
        boss_damage = boss_action['damage']
        self.player.take_damage(boss_damage)
        
        # Apply special rules
        self._apply_turn_special_rules()
        
        # Check for defeat
        if self.boss.is_defeated():
            return self._handle_boss_defeat()
        
        return {
            'boss_action': boss_action,
            'boss_health': self.boss.enemy.hp,
            'boss_health_percentage': self.boss.get_health_percentage(),
            'phase': self.boss.current_phase.value,
            'turn_number': self.turn_number
        }
    
    def _apply_turn_special_rules(self):
        """Apply special rules that happen each turn."""
        for rule in self.special_rules:
            if rule == "twisted_aura":
                # Random buff for boss
                buffs = ["damage_up", "defense_up", "speed_up"]
                buff = random.choice(buffs)
                print(f"Twisted Aura: Boss gains {buff}!")
            
            elif rule == "reality_warp":
                # Change combat rules
                if self.turn_number % 5 == 0:
                    rule_changes = [
                        "All red cards are wild",
                        "Straights are worthless",
                        "Pairs deal double damage",
                        "Flushes heal the caster"
                    ]
                    change = random.choice(rule_changes)
                    print(f"Reality Warp: {change}")
    
    def _handle_boss_defeat(self) -> Dict[str, Any]:
        """Handle boss defeat."""
        self.encounter_completed = True
        self.cutscene_active = True
        
        print(f"\n=== {self.boss.name} DEFEATED ===")
        
        # Play defeat cutscene
        if self.boss.cutscene_defeat:
            self._play_cutscene(self.boss.cutscene_defeat)
        
        # Call defeat callback
        if self.boss.on_defeat:
            self.boss.on_defeat()
        
        self.cutscene_active = False
        
        return {
            'result': 'victory',
            'boss_defeated': True,
            'loot': self._generate_loot()
        }
    
    def _generate_loot(self) -> Dict[str, Any]:
        """Generate loot from boss defeat."""
        loot = {
            'gold': random.randint(50, 200),
            'fortunas': random.randint(10, 50),
            'items': [],
            'companions': []
        }
        
        # Boss-specific loot
        if self.boss.boss_type == BossType.TWISTED_BOSS:
            loot['items'].append('twisted_essence')
        elif self.boss.boss_type == BossType.STORY_BOSS:
            loot['items'].append('memory_fragment')
        elif self.boss.boss_type == BossType.FINAL_BOSS:
            loot['items'].extend(['ascendancy_core', 'valerius_memory'])
        
        return loot
    
    def get_encounter_status(self) -> Dict[str, Any]:
        """Get current encounter status."""
        return {
            'encounter_started': self.encounter_started,
            'encounter_completed': self.encounter_completed,
            'cutscene_active': self.cutscene_active,
            'turn_number': self.turn_number,
            'boss_health': self.boss.enemy.hp,
            'boss_health_percentage': self.boss.get_health_percentage(),
            'current_phase': self.boss.current_phase.value,
            'special_rules': self.special_rules.copy()
        }


class BossManager:
    """Manages all boss encounters in the game."""
    
    def __init__(self, world_map: WorldMap):
        self.world_map = world_map
        self.bosses: Dict[str, Boss] = {}
        self.defeated_bosses: List[str] = []
        self.current_encounter: Optional[BossEncounter] = None
        
        # Initialize all bosses
        self._initialize_bosses()
    
    def _initialize_bosses(self):
        """Initialize all boss encounters."""
        
        # Casino District Boss: Twisted Casino Manager
        casino_abilities = [
            BossAbility("slot_machine_spin", "Spins slot machine for random damage", 15, cooldown=3),
            BossAbility("lucky_charm", "Gains temporary shield", 0, effects=["shield"], cooldown=4),
            BossAbility("high_roller", "Deals massive damage if player has low gold", 25, cooldown=5)
        ]
        
        casino_boss = Boss(
            boss_id="casino_manager",
            name="Twisted Casino Manager",
            boss_type=BossType.TWISTED_BOSS,
            district=DistrictType.CASINO_DISTRICT,
            position=(0, 1, 0),
            base_stats={'hp': 120, 'attack': 15, 'defense': 2},
            abilities=casino_abilities,
            phases=[BossPhase.INTRO, BossPhase.PHASE_1, BossPhase.PHASE_2],
            cutscene_intro="The once-proud casino manager, now twisted by greed and the Dissonance, rises from behind his golden desk. His body is covered in spinning slot machine reels and his eyes glow with corrupted Fortuna.",
            cutscene_defeat="The Casino Manager collapses, the slot machine parts falling away. His final words echo: 'The house always wins... but at what cost?'",
            on_defeat=lambda: self._on_casino_boss_defeat()
        )
        self.bosses["casino_manager"] = casino_boss
        
        # Printing Press Quarter Boss: Twisted Press Foreman
        press_abilities = [
            BossAbility("ink_spray", "Sprays corrosive ink", 12, effects=["poison"], cooldown=2),
            BossAbility("press_crush", "Uses massive press to crush", 20, cooldown=4),
            BossAbility("propaganda_blast", "Shouts corrupted words", 18, effects=["stun"], cooldown=6)
        ]
        
        press_boss = Boss(
            boss_id="press_foreman",
            name="Twisted Press Foreman",
            boss_type=BossType.STORY_BOSS,
            district=DistrictType.PRINTING_PRESS_QUARTER,
            position=(0, 1, 0),
            base_stats={'hp': 150, 'attack': 18, 'defense': 3},
            abilities=press_abilities,
            phases=[BossPhase.INTRO, BossPhase.PHASE_1, BossPhase.PHASE_2, BossPhase.PHASE_3],
            cutscene_intro="The Press Foreman emerges from the shadows, his body fused with the massive printing presses. Ink flows from his pores, and his voice echoes with the sound of grinding machinery.",
            cutscene_defeat="The Press Foreman's machinery grinds to a halt. As he falls, he whispers: 'The truth... it's all in the Engine... Valerius... he's not what he seems...'",
            on_defeat=lambda: self._on_press_boss_defeat()
        )
        self.bosses["press_foreman"] = press_boss
        
        # Underdeck Boss: Guardian
        guardian_abilities = [
            BossAbility("shadow_step", "Teleports and attacks", 16, cooldown=2),
            BossAbility("guardian_shield", "Creates protective barrier", 0, effects=["shield"], cooldown=3),
            BossAbility("underground_rage", "Channeling the Underdeck's power", 22, cooldown=5)
        ]
        
        guardian_boss = Boss(
            boss_id="underdeck_guardian",
            name="Underdeck Guardian",
            boss_type=BossType.STORY_BOSS,
            district=DistrictType.THE_UNDERDECK,
            position=(0, -5, 0),
            base_stats={'hp': 180, 'attack': 20, 'defense': 4},
            abilities=guardian_abilities,
            phases=[BossPhase.INTRO, BossPhase.PHASE_1, BossPhase.PHASE_2],
            cutscene_intro="The Guardian materializes from the shadows of The Underdeck. His form shifts between human and shadow, and his voice carries the weight of countless secrets.",
            cutscene_defeat="The Guardian's form stabilizes as he falls. 'You have proven yourself worthy. The Jokers will join your cause. But beware... the truth about Maestro will shake you to your core.'",
            on_defeat=lambda: self._on_guardian_defeat()
        )
        self.bosses["underdeck_guardian"] = guardian_boss
        
        # Final Boss: Chairman Valerius
        valerius_abilities = [
            BossAbility("reality_warp", "Changes the rules of combat", 0, effects=["rule_change"], cooldown=3),
            BossAbility("ascendancy_blast", "Channels the Engine's power", 30, cooldown=4),
            BossAbility("fortuna_drain", "Drains player's Fortuna", 15, effects=["fortuna_loss"], cooldown=2),
            BossAbility("truth_reveal", "Reveals the truth about the player", 0, effects=["mind_break"], cooldown=8)
        ]
        
        valerius_boss = Boss(
            boss_id="chairman_valerius",
            name="Chairman Valerius",
            boss_type=BossType.FINAL_BOSS,
            district=DistrictType.SYNDICATE_HEADQUARTERS,
            position=(0, 1, 0),
            base_stats={'hp': 300, 'attack': 25, 'defense': 5},
            abilities=valerius_abilities,
            phases=[BossPhase.INTRO, BossPhase.PHASE_1, BossPhase.PHASE_2, BossPhase.PHASE_3],
            cutscene_intro="Chairman Valerius stands before the pulsing Ascendancy Engine, his form beginning to merge with the machine. 'Ah, my creation has returned. You are not human, you know. You are my greatest work - a Homunculus of pure Fortuna.'",
            cutscene_defeat="Valerius's form begins to break apart as the Engine destabilizes. 'You... you were supposed to be the final component... the perfect catalyst...'",
            on_defeat=lambda: self._on_valerius_defeat()
        )
        self.bosses["chairman_valerius"] = valerius_boss
    
    def _on_casino_boss_defeat(self):
        """Called when Casino Manager is defeated."""
        print("Casino District is now safer to explore.")
        self.defeated_bosses.append("casino_manager")
    
    def _on_press_boss_defeat(self):
        """Called when Press Foreman is defeated."""
        print("You've learned the truth about the Ascendancy Engine!")
        self.defeated_bosses.append("press_foreman")
    
    def _on_guardian_defeat(self):
        """Called when Underdeck Guardian is defeated."""
        print("The Jokers are now available for recruitment!")
        self.defeated_bosses.append("underdeck_guardian")
    
    def _on_valerius_defeat(self):
        """Called when Chairman Valerius is defeated."""
        print("The final choice awaits...")
        self.defeated_bosses.append("chairman_valerius")
    
    def start_boss_encounter(self, boss_id: str, player: Player) -> Optional[BossEncounter]:
        """Start a boss encounter. Returns the encounter object."""
        if boss_id not in self.bosses:
            return None
        
        boss = self.bosses[boss_id]
        
        # Check if boss is already defeated
        if boss_id in self.defeated_bosses:
            print(f"{boss.name} has already been defeated.")
            return None
        
        # Create encounter
        encounter = BossEncounter(boss, player, self.world_map)
        self.current_encounter = encounter
        
        # Start encounter
        if encounter.start_encounter():
            return encounter
        
        return None
    
    def get_boss_at_position(self, position: tuple, district: DistrictType) -> Optional[Boss]:
        """Get boss at a specific position in a district."""
        for boss in self.bosses.values():
            if boss.district == district and boss.position == position:
                return boss
        return None
    
    def get_bosses_in_district(self, district: DistrictType) -> List[Boss]:
        """Get all bosses in a specific district."""
        return [boss for boss in self.bosses.values() if boss.district == district]


# Example usage and testing
if __name__ == "__main__":
    # Create world map and player
    world_map = WorldMap()
    player = Player()
    
    # Create boss manager
    boss_manager = BossManager(world_map)
    
    # Test boss encounter
    print("Testing boss encounter...")
    encounter = boss_manager.start_boss_encounter("casino_manager", player)
    
    if encounter:
        print(f"Boss health: {encounter.boss.enemy.hp}")
        print(f"Current phase: {encounter.boss.current_phase.value}")
        
        # Simulate a player turn
        player_action = {'damage': 25, 'ability': 'straight_flush'}
        result = encounter.take_player_turn(player_action)
        
        print(f"Boss response: {result}")
        print(f"Boss health after attack: {encounter.boss.enemy.hp}") 