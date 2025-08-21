from __future__ import annotations
from typing import Dict, List, Optional, Any, Union
from world_map import WorldMap, DistrictType, DistrictRenderer, EnvironmentalStorytelling
from quest_system import QuestManager, StoryManager, ActType
from npc_system import DialogueManager, DialogueUI
from boss_encounters import BossManager
from final_choice import EndingManager, EndingType
from entities.player import Player
from entities.enemy import Enemy, create_enemy
from ursina import *
import time


class GameState:
    """Manages the overall state of the game."""
    
    def __init__(self):
        # Core systems
        self.world_map = WorldMap()
        self.story_manager = StoryManager(self.world_map)
        self.quest_manager = QuestManager(self.world_map, self.story_manager)
        self.dialogue_manager = DialogueManager(self.quest_manager, self.world_map)
        self.boss_manager = BossManager(self.world_map)
        
        # Environmental storytelling
        self.environmental_storytelling = EnvironmentalStorytelling(self.world_map)
        
        # Player
        self.player = Player()
        
        # Ending system
        self.ending_manager = EndingManager(self.world_map, self.player)
        
        # Current state
        self.current_district = DistrictType.GRAND_TERMINAL
        self.game_started = False
        self.game_completed = False
        
        # UI state
        self.current_ui = "world"  # world, combat, dialogue, inventory, etc.
        self.ui_data: Dict[str, Any] = {}
        
        # Event tracking
        self.events_triggered: List[str] = []
        self.combat_encounters: List[str] = []
        self.quests_completed: List[str] = []
        self.discovered_content: List[str] = []
        
        # Environmental tracking
        self.visual_cues_triggered: List[str] = []
        self.world_events_triggered: List[str] = []
    
    def start_game(self) -> bool:
        """Start the game and initialize the first quest."""
        if self.game_started:
            return False
        
        self.game_started = True
        self.current_ui = "world"
        
        # Start the arrival quest
        self.quest_manager.start_quest("arrival")
        
        # Trigger initial environmental content
        self._trigger_initial_content()
        
        print("=== GAMBITON: A TALE OF FORTUNA ===")
        print("Welcome to Aethelburg, traveler. Your journey begins...")
        
        return True
    
    def _trigger_initial_content(self):
        """Trigger initial environmental content for the starting area."""
        # Trigger visual corruption cues
        self.environmental_storytelling.trigger_visual_cue("corruption_wisps")
        
        print("You notice strange purple wisps floating through the air...")
    
    def explore_district(self, district: DistrictType) -> bool:
        """Explore a district and discover environmental content."""
        if district not in self.world_map.unlocked_districts:
            print(f"District {district.value} is not unlocked yet.")
            return False
        
        self.current_district = district
        
        # Get discoverable content for this district
        content = self.environmental_storytelling.get_discoverable_content(district)
        
        if content:
            print(f"\nExploring {district.value}...")
            print("You discover:")
            
            for item in content:
                content_type, content_id = item.split(":", 1)
                
                if content_type == "visual_cue":
                    self.environmental_storytelling.trigger_visual_cue(content_id)
                    self.visual_cues_triggered.append(content_id)
                
                elif content_type == "world_event":
                    self.environmental_storytelling.trigger_world_event(content_id)
                    self.world_events_triggered.append(content_id)
        
        return True
    
    def trigger_story_event(self, event_id: str) -> bool:
        """Trigger a story event and related environmental content."""
        if event_id in self.events_triggered:
            return False
        
        self.events_triggered.append(event_id)
        
        # Trigger related environmental content
        if event_id == "truth_revealed":
            self.environmental_storytelling.trigger_world_event("twisted_outbreak")
        
        return True
    
    def get_environmental_progress(self) -> Dict[str, Any]:
        """Get environmental storytelling progress."""
        return {
            'visual_cues_triggered': len(self.visual_cues_triggered),
            'world_events_triggered': len(self.world_events_triggered),
            'total_discoverable': len(self.environmental_storytelling.visual_cues) + 
                                len(self.environmental_storytelling.world_events)
        }
    
    def get_discovery_log(self) -> List[str]:
        """Get a log of all discovered environmental content."""
        log = []
        
        for cue_id in self.visual_cues_triggered:
            visual_cue = self.environmental_storytelling.visual_cues[cue_id]
            log.append(f"👁️ {visual_cue.description}")
        
        for event_id in self.world_events_triggered:
            world_event = self.environmental_storytelling.world_events[event_id]
            log.append(f"🌍 {world_event.title}")
        
        return log
    
    def change_district(self, new_district: DistrictType) -> bool:
        """Change to a new district."""
        if not self.world_map.change_district(new_district):
            return False
        
        self.current_district = new_district
        
        # Check for district-specific events
        self._trigger_district_events(new_district)
        
        return True
    
    def _trigger_district_events(self, district: DistrictType):
        """Trigger events specific to entering a district."""
        if district == DistrictType.CASINO_DISTRICT:
            if "first_casino_visit" not in self.events_triggered:
                self.events_triggered.append("first_casino_visit")
                print("You enter the glittering Casino District. The air is thick with Fortuna.")
        
        elif district == DistrictType.PRINTING_PRESS_QUARTER:
            if "first_press_visit" not in self.events_triggered:
                self.events_triggered.append("first_press_visit")
                print("The Printing Press Quarter is alive with the sound of rebellion.")
        
        elif district == DistrictType.THE_UNDERDECK:
            if "first_underdeck_visit" not in self.events_triggered:
                self.events_triggered.append("first_underdeck_visit")
                print("You descend into The Underdeck, a hidden world beneath the city.")
    
    def start_combat(self, enemy_type: str = "Twisted Guard") -> bool:
        """Start a combat encounter."""
        enemy = create_enemy(enemy_type)
        
        print(f"\n=== COMBAT: {enemy.name} ===")
        print(f"Enemy HP: {enemy.hp}/{enemy.max_hp}")
        print(f"Enemy Attack: {enemy.attack_value}")
        
        # Start combat turn
        self.player.start_turn()
        
        return True
    
    def start_boss_encounter(self, boss_id: str) -> bool:
        """Start a boss encounter."""
        encounter = self.boss_manager.start_boss_encounter(boss_id, self.player)
        
        if encounter:
            self.current_ui = "boss_combat"
            self.ui_data["boss_encounter"] = encounter
            return True
        
        return False
    
    def start_dialogue(self, npc_id: str) -> bool:
        """Start dialogue with an NPC."""
        dialogue_ui = DialogueUI(self.dialogue_manager)
        dialogue_ui.start_dialogue(npc_id)
        
        self.current_ui = "dialogue"
        self.ui_data["dialogue_ui"] = dialogue_ui
        self.ui_data["current_npc"] = npc_id
        
        return True
    
    def update_quest_progress(self, quest_id: str, objective_id: str, progress: int = 1) -> bool:
        """Update quest progress."""
        return self.quest_manager.update_quest_progress(quest_id, objective_id, progress)
    
    def get_available_quests(self) -> List[Any]:
        """Get all available quests."""
        return self.quest_manager.get_available_quests()
    
    def get_active_quests(self) -> List[Any]:
        """Get all active quests."""
        return self.quest_manager.get_active_quests()
    
    def get_current_district_info(self) -> Dict[str, Any]:
        """Get information about the current district."""
        district = self.world_map.get_current_district()
        if not district:
            return {}
        
        return {
            'name': district.name,
            'description': district.description,
            'corruption_level': district.corruption_level,
            'unlocked': district.unlocked,
            'ambient_sounds': district.ambient_sounds,
            'available_transitions': self.world_map.get_available_transitions()
        }
    
    def get_player_status(self) -> Dict[str, Any]:
        """Get current player status."""
        return {
            'hp': self.player.hp,
            'max_hp': self.player.max_hp,
            'gold': self.player.gold,
            'hand_size': len(self.player.hand),
            'jokers': self.player.jokers,
            'items': [str(item) for item in self.player.items],
            'combat_turn': self.player.combat_turn,
            'discards_left': self.player.discards_left
        }
    
    def get_game_progress(self) -> Dict[str, Any]:
        """Get overall game progress."""
        quest_progress = self.quest_manager.get_quest_progress()
        story_progress = {
            'current_act': self.story_manager.current_act.value,
            'act_description': self.story_manager.get_act_description(self.story_manager.current_act)
        }
        
        return {
            'quest_progress': quest_progress,
            'story_progress': story_progress,
            'districts_unlocked': len(self.world_map.unlocked_districts),
            'bosses_defeated': len(self.boss_manager.defeated_bosses),
            'events_triggered': len(self.events_triggered)
        }
    
    def trigger_final_choice(self) -> bool:
        """Trigger the final choice sequence."""
        if self.game_completed:
            return False
        
        final_choice = self.ending_manager.start_final_choice()
        
        # Start the ending sequence
        final_choice.start_ending_sequence()
        final_choice.reveal_truth()
        final_choice.present_choice()
        
        self.current_ui = "final_choice"
        self.ui_data["final_choice"] = final_choice
        
        return True
    
    def make_final_choice(self, choice: EndingType) -> bool:
        """Make the final choice."""
        if self.current_ui != "final_choice":
            return False
        
        if self.ending_manager.complete_ending(choice):
            self.game_completed = True
            self.current_ui = "ending"
            return True
        
        return False

