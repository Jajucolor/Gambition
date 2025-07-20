from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import random


class ActProgress(Enum):
    """Story progression through the three acts"""
    ACT_1_ANTE = "act1"
    ACT_2_TURN = "act2" 
    ACT_3_RIVER = "act3"
    COMPLETED = "completed"


class DistrictState(Enum):
    """State of a district based on story progress"""
    LOCKED = "locked"
    ACCESSIBLE = "accessible"
    CLEARED = "cleared"
    CORRUPTED = "corrupted"


@dataclass
class Location:
    """A specific location within a district"""
    name: str
    description: str
    location_type: str  # "shop", "combat", "story", "npc"
    unlocked: bool = True
    special_requirements: Optional[str] = None
    npc_id: Optional[str] = None
    enemy_type: Optional[str] = None


@dataclass
class District:
    """A district of Aethelburg"""
    name: str
    description: str
    theme: str
    state: DistrictState
    locations: List[Location]
    unlock_requirement: Optional[str] = None
    boss_defeated: bool = False
    boss_name: Optional[str] = None


class WorldState:
    """Manages the overall world state and story progression"""
    
    def __init__(self):
        self.current_act: ActProgress = ActProgress.ACT_1_ANTE
        self.story_flags: Dict[str, bool] = {}
        self.districts: Dict[str, District] = {}
        self.player_location: str = "grand_terminal"
        self.maestro_clues_found: int = 0
        self.valerius_trust: int = 50  # 0-100, affects dialogue options
        self.dissonance_level: int = 25  # 0-100, affects world corruption
        
        # Initialize the world
        self._create_districts()
        self._set_initial_story_flags()
    
    def _create_districts(self):
        """Create all districts of Aethelburg"""
        
        # Grand Terminal - Starting area
        self.districts["grand_terminal"] = District(
            name="Grand Terminal",
            description="The ornate train station where you first arrived. Once a marvel of gilded architecture, now overrun with low-level Twisted.",
            theme="tutorial_combat",
            state=DistrictState.ACCESSIBLE,
            locations=[
                Location("Platform 7", "Your arrival platform, now twisted with corrupted Fortuna crystals", "combat", True, None, None, "Twisted Guard"),
                Location("Station Master's Office", "Contains clues about the city's current state", "story", True),
                Location("Ticket Booth", "An automated booth still selling tickets to nowhere", "shop", True, None, "ticket_vendor"),
            ]
        )
        
        # Syndicate Plaza - Where you meet Valerius
        self.districts["syndicate_plaza"] = District(
            name="Syndicate Plaza",
            description="The heart of the Syndicate's power. Gleaming towers of brass and crystal reach toward the sky, powered by Fortuna conduits.",
            theme="story_hub",
            state=DistrictState.ACCESSIBLE,
            locations=[
                Location("Valerius's Office", "The Chairman's opulent office overlooking the city", "story", True, None, "valerius"),
                Location("Syndicate Archives", "Records of the city's recent history", "story", False, "syndicate_clearance"),
                Location("Fortuna Observatory", "Monitors the city's luck flows", "story", True, None, "syndicate_scientist"),
            ]
        )
        
        # The Underdeck - Companion recruitment
        self.districts["underdeck"] = District(
            name="The Underdeck",
            description="A hidden underground district where rogues, outcasts, and survivors gather. The air hums with rebellious energy.",
            theme="companions",
            state=DistrictState.ACCESSIBLE,
            locations=[
                Location("The Lucky Seven Tavern", "Where companions gather to share stories and seek employment", "shop", True, None, "guild_master"),
                Location("Black Market", "Illegal goods and information", "shop", True, None, "fence"),
                Location("Fighting Pits", "Test your skills against other gamblers", "combat", True, None, "pit_fighter"),
            ]
        )
        
        # Casino District - Opulent but silent
        self.districts["casino_district"] = District(
            name="Casino District",
            description="Once the jewel of Aethelburg, now eerily quiet. Grand casinos stand empty, their Fortuna-powered games frozen mid-spin.",
            theme="wealth_corruption",
            state=DistrictState.LOCKED,
            unlock_requirement="meet_valerius",
            boss_name="The Dealer Supreme",
            locations=[
                Location("Golden Roulette Palace", "The grandest casino, now home to a powerful Twisted", "combat", True, None, None, "Twisted Croupier"),
                Location("Card Shark's Den", "A private gambling club for the elite", "story", True),
                Location("The Cartomancer's Shop", "Hidden tarot card shop", "shop", True, None, "cartomancer"),
                Location("High Roller's Suite", "Abandoned penthouse with valuable clues", "story", False, "casino_key"),
            ]
        )
        
        # Printing Press Quarter - Working class area
        self.districts["printing_quarter"] = District(
            name="Printing Press Quarter", 
            description="The industrial heart where newspapers and propaganda were produced. Now ink flows like blood through twisted machinery.",
            theme="information_control",
            state=DistrictState.LOCKED,
            unlock_requirement="casino_district_cleared",
            boss_name="The Editor-in-Chief",
            locations=[
                Location("The Daily Fortune Press", "Main newspaper building", "story", True),
                Location("Ink Foundry", "Where Fortuna-infused ink was created", "combat", True, None, None, "Ink Wraith"),
                Location("Underground Printing", "Secret press for resistance materials", "story", False, "resistance_contact"),
                Location("Typesetter's Workshop", "Contains evidence of Syndicate propaganda", "story", True),
            ]
        )
        
        # Residential Gardens - Middle class homes
        self.districts["residential_gardens"] = District(
            name="Residential Gardens",
            description="Elegant townhouses and manicured parks where the middle class lived. Now overgrown with crystalline Fortuna growths.",
            theme="domestic_horror",
            state=DistrictState.LOCKED,
            unlock_requirement="printing_quarter_cleared", 
            boss_name="The Perfect Housewife",
            locations=[
                Location("Maestro's Townhouse", "Your mentor's abandoned home", "story", True),
                Location("Fortuna Gardens", "Public park now twisted into crystal maze", "combat", True, None, None, "Crystal Gardener"),
                Location("Community Center", "Meeting place with important records", "story", True),
                Location("The Apothecary", "Sells healing items and information", "shop", True, None, "apothecary"),
            ]
        )
        
        # Factory District - Industrial corruption
        self.districts["factory_district"] = District(
            name="Factory District",
            description="Massive Fortuna refineries and processing plants. The machinery still runs, but produces only corruption and Twisted workers.",
            theme="industrial_nightmare",
            state=DistrictState.LOCKED,
            unlock_requirement="residential_gardens_cleared",
            boss_name="The Foreman",
            locations=[
                Location("Fortuna Refinery Alpha", "Main processing plant", "combat", True, None, None, "Twisted Worker"),
                Location("Quality Control Lab", "Contains research on Fortuna corruption", "story", True),
                Location("Worker's Union Hall", "Evidence of labor disputes", "story", True),
                Location("Maintenance Tunnels", "Secret paths to other districts", "story", False, "tunnel_map"),
            ]
        )
        
        # The Depths - Underground Ascendancy Engine
        self.districts["the_depths"] = District(
            name="The Depths",
            description="The hidden underground chamber containing the Ascendancy Engine. Reality itself bends around the massive clockwork machine.",
            theme="final_confrontation",
            state=DistrictState.LOCKED,
            unlock_requirement="all_districts_cleared",
            boss_name="Chairman Valerius",
            locations=[
                Location("Engine Chamber", "The heart of the conspiracy", "story", True, None, "valerius_final"),
                Location("Control Room", "Monitors and controls for the Engine", "story", True),
                Location("Maestro's Prison", "Where your mentor was held", "story", True),
                Location("Fortuna Core", "The source of all the city's power", "story", True),
            ]
        )
    
    def _set_initial_story_flags(self):
        """Set up initial story state"""
        self.story_flags = {
            "arrived_in_city": True,
            "met_valerius": False,
            "received_syndicate_deck": False,
            "learned_about_dissonance": False,
            "found_maestro_clue_1": False,
            "found_maestro_clue_2": False,
            "found_maestro_clue_3": False,
            "discovered_ascendancy_engine": False,
            "learned_player_origin": False,
            "confronted_valerius": False,
            "engine_destroyed": False,
            "became_warden": False,
        }
    
    def advance_story(self, event: str) -> List[str]:
        """Advance the story based on an event, return list of updates"""
        updates = []
        
        if event == "meet_valerius" and not self.story_flags["met_valerius"]:
            self.story_flags["met_valerius"] = True
            self.story_flags["learned_about_dissonance"] = True
            self.story_flags["received_syndicate_deck"] = True
            self.unlock_district("casino_district")
            updates.append("Met Chairman Valerius and learned about the Dissonance")
            updates.append("Received the Syndicate Standard deck")
            updates.append("Casino District is now accessible")
        
        elif event == "defeat_casino_boss":
            self.districts["casino_district"].boss_defeated = True
            self.unlock_district("printing_quarter")
            updates.append("Defeated The Dealer Supreme")
            updates.append("Printing Press Quarter is now accessible")
            
        elif event == "find_maestro_clue":
            self.maestro_clues_found += 1
            self.story_flags[f"found_maestro_clue_{self.maestro_clues_found}"] = True
            updates.append(f"Found clue about Maestro ({self.maestro_clues_found}/3)")
            
            if self.maestro_clues_found >= 3:
                updates.append("You've gathered enough clues about Maestro's investigation")
                if self.current_act == ActProgress.ACT_1_ANTE:
                    self.current_act = ActProgress.ACT_2_TURN
                    updates.append("--- ACT II: THE TURN ---")
        
        elif event == "discover_ascendancy_engine":
            self.story_flags["discovered_ascendancy_engine"] = True
            if self.current_act == ActProgress.ACT_2_TURN:
                self.current_act = ActProgress.ACT_3_RIVER
                updates.append("--- ACT III: THE RIVER ---")
            updates.append("Discovered the truth about the Ascendancy Engine!")
        
        elif event == "final_confrontation":
            self.story_flags["confronted_valerius"] = True
            self.story_flags["learned_player_origin"] = True
            updates.append("The truth about your origin has been revealed...")
        
        return updates
    
    def unlock_district(self, district_id: str):
        """Unlock a district for exploration"""
        if district_id in self.districts:
            self.districts[district_id].state = DistrictState.ACCESSIBLE
    
    def get_available_districts(self) -> List[District]:
        """Get all districts the player can currently access"""
        return [d for d in self.districts.values() if d.state == DistrictState.ACCESSIBLE]
    
    def get_district_locations(self, district_id: str) -> List[Location]:
        """Get all accessible locations in a district"""
        if district_id not in self.districts:
            return []
        
        district = self.districts[district_id]
        accessible_locations = []
        
        for location in district.locations:
            if location.unlocked:
                if location.special_requirements is None:
                    accessible_locations.append(location)
                elif location.special_requirements in self.story_flags and self.story_flags[location.special_requirements]:
                    accessible_locations.append(location)
        
        return accessible_locations
    
    def get_current_story_context(self) -> Dict[str, Any]:
        """Get current story context for dialogue and events"""
        return {
            "act": self.current_act,
            "maestro_clues": self.maestro_clues_found,
            "valerius_trust": self.valerius_trust,
            "dissonance_level": self.dissonance_level,
            "flags": self.story_flags.copy()
        }
    
    def modify_valerius_trust(self, change: int):
        """Modify trust level with Valerius (affects dialogue options)"""
        self.valerius_trust = max(0, min(100, self.valerius_trust + change))
    
    def modify_dissonance_level(self, change: int):
        """Modify the city's corruption level"""
        self.dissonance_level = max(0, min(100, self.dissonance_level + change))


# Global world state instance
world_state = WorldState() 