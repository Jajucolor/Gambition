from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import random
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from dataclasses import dataclass


class DistrictType(Enum):
    """Enumeration of all districts in Aethelburg."""
    GRAND_TERMINAL = "grand_terminal"
    CASINO_DISTRICT = "casino_district" 
    PRINTING_PRESS_QUARTER = "printing_press_quarter"
    THE_UNDERDECK = "the_underdeck"
    GILDED_PROMENADE = "gilded_promenade"
    QUARANTINE_ZONE = "quarantine_zone"
    SYNDICATE_HEADQUARTERS = "syndicate_headquarters"


class District:
    """Represents a district in Aethelburg with unique characteristics."""
    
    def __init__(self, 
                 district_type: DistrictType,
                 name: str,
                 description: str,
                 unlocked: bool = False,
                 corruption_level: float = 0.0):
        self.district_type = district_type
        self.name = name
        self.description = description
        self.unlocked = unlocked
        self.corruption_level = corruption_level  # 0.0 = normal, 1.0 = fully corrupted
        
        # District-specific properties
        self.ambient_sounds: List[str] = []
        self.visual_effects: List[str] = []
        self.npcs: List[Dict] = []
        self.encounters: List[Dict] = []
        self.shops: List[Dict] = []
        self.secrets: List[Dict] = []
        
        # District geometry and layout
        self.bounds: Tuple[Vec3, Vec3] = (Vec3(-50, 0, -50), Vec3(50, 20, 50))
        self.spawn_points: List[Vec3] = []
        self.transition_points: List[Dict] = []
        
    def get_corruption_effects(self) -> Dict[str, Any]:
        """Get visual and audio effects based on corruption level."""
        effects = {
            'fog_density': self.corruption_level * 0.8,
            'light_intensity': 1.0 - (self.corruption_level * 0.5),
            'color_tint': (1.0, 1.0 - self.corruption_level * 0.3, 1.0 - self.corruption_level * 0.3),
            'ambient_sound_pitch': 1.0 + (self.corruption_level * 0.5)
        }
        return effects


class WorldMap:
    """Manages the entire world of Aethelburg and district transitions."""
    
    def __init__(self):
        self.districts: Dict[DistrictType, District] = {}
        self.current_district: Optional[DistrictType] = None
        self.player_position: Vec3 = Vec3(0, 1, 0)
        self.player_rotation: float = 0.0
        
        # World state
        self.story_progress: int = 0  # 0 = Act I, 1 = Act II, 2 = Act III
        self.unlocked_districts: List[DistrictType] = [DistrictType.GRAND_TERMINAL]
        self.completed_quests: List[str] = []
        self.world_events: Dict[str, bool] = {}
        
        # Initialize all districts
        self._initialize_districts()
        
    def _initialize_districts(self):
        """Create all districts with their unique characteristics."""
        
        # Grand Terminal - Starting area
        self.districts[DistrictType.GRAND_TERMINAL] = District(
            DistrictType.GRAND_TERMINAL,
            "Grand Terminal",
            "The ornate train station where your journey begins. Marble columns and gilded clocks, now in chaos.",
            unlocked=True,
            corruption_level=0.1
        )
        gt = self.districts[DistrictType.GRAND_TERMINAL]
        gt.ambient_sounds = ["steam_whistle", "crowd_murmur", "clock_chimes"]
        gt.spawn_points = [Vec3(0, 1, 0), Vec3(10, 1, 5), Vec3(-5, 1, -10)]
        gt.transition_points = [
            {"position": Vec3(25, 1, 0), "target": DistrictType.CASINO_DISTRICT, "name": "Casino District Gate"}
        ]
        
        # Casino District - Glittering wealth and danger
        self.districts[DistrictType.CASINO_DISTRICT] = District(
            DistrictType.CASINO_DISTRICT,
            "Casino District", 
            "A glittering maze of casinos and luxury shops. Fortuna-powered automatons serve the elite.",
            unlocked=False,
            corruption_level=0.3
        )
        cd = self.districts[DistrictType.CASINO_DISTRICT]
        cd.ambient_sounds = ["slot_machines", "orchestra", "champagne_corks"]
        cd.spawn_points = [Vec3(0, 1, 0), Vec3(15, 1, 20), Vec3(-20, 1, 15)]
        cd.transition_points = [
            {"position": Vec3(-25, 1, 0), "target": DistrictType.GRAND_TERMINAL, "name": "Terminal Gate"},
            {"position": Vec3(0, 1, 25), "target": DistrictType.PRINTING_PRESS_QUARTER, "name": "Press Quarter Gate"},
            {"position": Vec3(25, 1, 0), "target": DistrictType.GILDED_PROMENADE, "name": "Promenade Gate"}
        ]
        
        # Printing Press Quarter - Gritty and revolutionary
        self.districts[DistrictType.PRINTING_PRESS_QUARTER] = District(
            DistrictType.PRINTING_PRESS_QUARTER,
            "Printing Press Quarter",
            "A maze of narrow streets and towering presses. The air is thick with ink and rebellion.",
            unlocked=False,
            corruption_level=0.5
        )
        ppq = self.districts[DistrictType.PRINTING_PRESS_QUARTER]
        ppq.ambient_sounds = ["printing_presses", "steam_engines", "whispers"]
        ppq.spawn_points = [Vec3(0, 1, 0), Vec3(10, 1, -15), Vec3(-10, 1, 10)]
        ppq.transition_points = [
            {"position": Vec3(0, 1, -25), "target": DistrictType.CASINO_DISTRICT, "name": "Casino Gate"},
            {"position": Vec3(25, 1, 0), "target": DistrictType.THE_UNDERDECK, "name": "Underdeck Entrance"}
        ]
        
        # The Underdeck - Hidden guild and black market
        self.districts[DistrictType.THE_UNDERDECK] = District(
            DistrictType.THE_UNDERDECK,
            "The Underdeck",
            "A hidden labyrinth beneath the city. Home to Jokers, smugglers, and those who live by their own rules.",
            unlocked=False,
            corruption_level=0.2
        )
        ud = self.districts[DistrictType.THE_UNDERDECK]
        ud.ambient_sounds = ["dripping_water", "distant_voices", "creaking_wood"]
        ud.spawn_points = [Vec3(0, -5, 0), Vec3(15, -5, 10), Vec3(-10, -5, -15)]
        ud.transition_points = [
            {"position": Vec3(-25, -5, 0), "target": DistrictType.PRINTING_PRESS_QUARTER, "name": "Surface Exit"}
        ]
        
        # Gilded Promenade - Luxury and the Cartomancer
        self.districts[DistrictType.GILDED_PROMENADE] = District(
            DistrictType.GILDED_PROMENADE,
            "Gilded Promenade",
            "A wide boulevard lined with theaters, boutiques, and the Cartomancer's mysterious shop.",
            unlocked=False,
            corruption_level=0.4
        )
        gp = self.districts[DistrictType.GILDED_PROMENADE]
        gp.ambient_sounds = ["string_quartet", "fountain_splash", "carriage_wheels"]
        gp.spawn_points = [Vec3(0, 1, 0), Vec3(20, 1, 10), Vec3(-15, 1, 20)]
        gp.transition_points = [
            {"position": Vec3(-25, 1, 0), "target": DistrictType.CASINO_DISTRICT, "name": "Casino Gate"},
            {"position": Vec3(0, 1, 25), "target": DistrictType.QUARANTINE_ZONE, "name": "Quarantine Gate"}
        ]
        
        # Quarantine Zone - High danger and corruption
        self.districts[DistrictType.QUARANTINE_ZONE] = District(
            DistrictType.QUARANTINE_ZONE,
            "Quarantine Zone",
            "A district sealed off by the Syndicate. Twisted roam freely, and reality itself seems to crack.",
            unlocked=False,
            corruption_level=0.8
        )
        qz = self.districts[DistrictType.QUARANTINE_ZONE]
        qz.ambient_sounds = ["distant_screams", "reality_cracks", "twisted_growls"]
        qz.spawn_points = [Vec3(0, 1, 0), Vec3(30, 1, -20), Vec3(-25, 1, 30)]
        qz.transition_points = [
            {"position": Vec3(0, 1, -25), "target": DistrictType.GILDED_PROMENADE, "name": "Promenade Gate"},
            {"position": Vec3(25, 1, 0), "target": DistrictType.SYNDICATE_HEADQUARTERS, "name": "Syndicate Gate"}
        ]
        
        # Syndicate Headquarters - Final area
        self.districts[DistrictType.SYNDICATE_HEADQUARTERS] = District(
            DistrictType.SYNDICATE_HEADQUARTERS,
            "Syndicate Headquarters",
            "A palace of luck and power. The Ascendancy Engine pulses beneath, and Chairman Valerius awaits.",
            unlocked=False,
            corruption_level=0.9
        )
        sh = self.districts[DistrictType.SYNDICATE_HEADQUARTERS]
        sh.ambient_sounds = ["engine_hum", "fortuna_pulse", "clockwork_ticks"]
        sh.spawn_points = [Vec3(0, 1, 0), Vec3(40, 1, 0), Vec3(-40, 1, 0)]
        sh.transition_points = [
            {"position": Vec3(-25, 1, 0), "target": DistrictType.QUARANTINE_ZONE, "name": "Quarantine Gate"}
        ]
    
    def get_current_district(self) -> Optional[District]:
        """Get the currently active district."""
        if self.current_district:
            return self.districts[self.current_district]
        return None
    
    def change_district(self, new_district: DistrictType, spawn_point: Optional[Vec3] = None) -> bool:
        """Change to a new district. Returns True if successful."""
        if new_district not in self.districts:
            print(f"District {new_district} not found!")
            return False
            
        district = self.districts[new_district]
        if not district.unlocked:
            print(f"District {district.name} is not unlocked!")
            return False
        
        # Update current district
        old_district = self.current_district
        self.current_district = new_district
        
        # Set spawn position
        if spawn_point:
            self.player_position = spawn_point
        else:
            # Use first spawn point
            self.player_position = district.spawn_points[0] if district.spawn_points else Vec3(0, 1, 0)
        
        print(f"Entering {district.name}...")
        print(f"Corruption Level: {district.corruption_level:.1%}")
        
        # Apply district-specific effects
        self._apply_district_effects(district)
        
        return True
    
    def _apply_district_effects(self, district: District):
        """Apply visual and audio effects for the district."""
        effects = district.get_corruption_effects()
        
        # Apply fog based on corruption
        if hasattr(self, 'fog'):
            self.fog.density = effects['fog_density']
        
        # Apply lighting effects
        if hasattr(self, 'ambient_light'):
            self.ambient_light.color = effects['color_tint']
            self.ambient_light.intensity = effects['light_intensity']
        
        # Play ambient sounds
        if district.ambient_sounds:
            # In a real implementation, you'd play the sounds here
            print(f"Ambient sounds: {', '.join(district.ambient_sounds)}")
    
    def unlock_district(self, district_type: DistrictType) -> bool:
        """Unlock a district for travel."""
        if district_type in self.districts:
            self.districts[district_type].unlocked = True
            if district_type not in self.unlocked_districts:
                self.unlocked_districts.append(district_type)
            print(f"District {self.districts[district_type].name} unlocked!")
            return True
        return False
    
    def get_available_transitions(self) -> List[Dict]:
        """Get available transition points from current district."""
        if not self.current_district:
            return []
        
        district = self.districts[self.current_district]
        available = []
        
        for transition in district.transition_points:
            target_district = transition["target"]
            if target_district in self.unlocked_districts:
                available.append(transition)
        
        return available
    
    def is_near_transition(self, player_pos: Vec3, threshold: float = 3.0) -> Optional[Dict]:
        """Check if player is near a transition point."""
        if not self.current_district:
            return None
        
        district = self.districts[self.current_district]
        
        for transition in district.transition_points:
            distance = (player_pos - transition["position"]).length()
            if distance <= threshold:
                return transition
        
        return None


class EnvironmentalStorytelling:
    """Manages environmental storytelling elements like audio logs, visual cues, and world events."""
    
    def __init__(self, world_map: WorldMap):
        self.world_map = world_map
        self.visual_cues: Dict[str, VisualCue] = {}
        self.world_events: Dict[str, WorldEvent] = {}
        self.discovered_content: List[str] = []
        
        # Initialize environmental content
        self._initialize_visual_cues()
        self._initialize_world_events()
    

    
    def _initialize_visual_cues(self):
        """Initialize visual cues that show the Dissonance's effects."""
        
        # Corruption indicators
        self.visual_cues["corruption_wisps"] = VisualCue(
            "corruption_wisps",
            "Purple energy wisps float through the air",
            DistrictType.CASINO_DISTRICT,
            Vec3(10, 2, 10),
            "purple_particles"
        )
        
        self.visual_cues["twisted_remains"] = VisualCue(
            "twisted_remains",
            "Piles of twisted, corrupted Fortuna crystals",
            DistrictType.PRINTING_PRESS_QUARTER,
            Vec3(-5, 0, 5),
            "crystal_piles"
        )
        
        self.visual_cues["ascendancy_leak"] = VisualCue(
            "ascendancy_leak",
            "Raw Fortuna energy leaks from the ground",
            DistrictType.QUARANTINE_ZONE,
            Vec3(0, 0, 15),
            "energy_leak"
        )
        
        self.visual_cues["syndicate_control"] = VisualCue(
            "syndicate_control",
            "Syndicate surveillance equipment monitors the area",
            DistrictType.SYNDICATE_HEADQUARTERS,
            Vec3(5, 3, 5),
            "surveillance_gear"
        )
    
    def _initialize_world_events(self):
        """Initialize dynamic world events that occur based on story progress."""
        
        # Fortuna surges
        self.world_events["fortuna_surge"] = WorldEvent(
            "fortuna_surge",
            "A surge of Fortuna energy ripples through the district",
            "The air crackles with raw probability energy. Cards in your deck feel more powerful...",
            ["boost_card_power", "increase_corruption"],
            DistrictType.CASINO_DISTRICT
        )
        
        # Twisted outbreaks
        self.world_events["twisted_outbreak"] = WorldEvent(
            "twisted_outbreak",
            "Twisted creatures emerge from the shadows",
            "The Dissonance has corrupted more citizens. They lurch toward you with malicious intent...",
            ["spawn_enemies", "increase_difficulty"],
            DistrictType.PRINTING_PRESS_QUARTER
        )
        
        # Syndicate crackdown
        self.world_events["syndicate_crackdown"] = WorldEvent(
            "syndicate_crackdown",
            "Syndicate enforcers patrol the area",
            "The Syndicate has increased security. They're looking for someone...",
            ["spawn_guards", "restrict_movement"],
            DistrictType.GILDED_PROMENADE
        )
    

    
    def trigger_visual_cue(self, cue_id: str) -> bool:
        """Trigger a visual cue. Returns True if successful."""
        if cue_id not in self.visual_cues:
            return False
        
        cue = self.visual_cues[cue_id]
        
        print(f"\n=== VISUAL CUE: {cue.description} ===")
        print(f"[{cue.visual_effect}] {cue.description}")
        print("=== END CUE ===\n")
        
        return True
    
    def trigger_world_event(self, event_id: str) -> bool:
        """Trigger a world event. Returns True if successful."""
        if event_id not in self.world_events:
            return False
        
        event = self.world_events[event_id]
        
        print(f"\n=== WORLD EVENT: {event.title} ===")
        print(event.description)
        print("=== END EVENT ===\n")
        
        return True
    
    def get_discoverable_content(self, district: DistrictType) -> List[str]:
        """Get all discoverable content in a district."""
        content = []
        
        for cue_id, cue in self.visual_cues.items():
            if cue.district == district:
                content.append(f"visual_cue:{cue_id}")
        
        for event_id, event in self.world_events.items():
            if event.district == district:
                content.append(f"world_event:{event_id}")
        
        return content


class DistrictRenderer:
    """Handles the 3D rendering and geometry for each district."""
    
    def __init__(self, world_map: WorldMap):
        self.world_map = world_map
        self.current_scene: Optional[Entity] = None
        self.district_entities: Dict[DistrictType, Entity] = {}
        
    def load_district(self, district_type: DistrictType) -> Entity:
        """Load and render a district's 3D geometry."""
        district = self.world_map.districts[district_type]
        
        # Create the district scene
        scene = Entity(name=f"district_{district_type.value}")
        
        # Add ground plane
        ground = Entity(
            parent=scene,
            model='plane',
            scale=(100, 1, 100),
            texture='white_cube',
            color=color.gray
        )
        
        # Add district-specific buildings and props
        self._add_district_props(scene, district)
        
        # Add transition markers
        self._add_transition_markers(scene, district)
        
        # Store the scene
        self.district_entities[district_type] = scene
        
        return scene
    
    def _add_district_props(self, scene: Entity, district: District):
        """Add district-specific buildings and props."""
        if district.district_type == DistrictType.GRAND_TERMINAL:
            # Add train station elements
            self._add_terminal_props(scene)
        elif district.district_type == DistrictType.CASINO_DISTRICT:
            # Add casino buildings
            self._add_casino_props(scene)
        elif district.district_type == DistrictType.PRINTING_PRESS_QUARTER:
            # Add industrial buildings
            self._add_press_quarter_props(scene)
        elif district.district_type == DistrictType.THE_UNDERDECK:
            # Add underground elements
            self._add_underdeck_props(scene)
        elif district.district_type == DistrictType.GILDED_PROMENADE:
            # Add luxury buildings
            self._add_promenade_props(scene)
        elif district.district_type == DistrictType.QUARANTINE_ZONE:
            # Add corrupted buildings
            self._add_quarantine_props(scene)
        elif district.district_type == DistrictType.SYNDICATE_HEADQUARTERS:
            # Add palace elements
            self._add_syndicate_props(scene)
    
    def _add_terminal_props(self, scene: Entity):
        """Add Grand Terminal specific props."""
        # Train tracks
        for i in range(-3, 4):
            track = Entity(
                parent=scene,
                model='cube',
                scale=(80, 0.2, 0.5),
                position=(0, 0.1, i * 5),
                color=color.dark_gray,
                collider='box'
            )
        
        # Station building
        station = Entity(
            parent=scene,
            model='cube',
            scale=(20, 10, 15),
            position=(0, 5, -20),
            color=color.light_gray,
            collider='box'
        )
        
        # Clock tower
        clock = Entity(
            parent=scene,
            model='cube',
            scale=(3, 15, 3),
            position=(15, 7.5, -20),
            color=color.gold,
            collider='box'
        )
    
    def _add_casino_props(self, scene: Entity):
        """Add Casino District specific props."""
        # Casino buildings
        for i in range(3):
            casino = Entity(
                parent=scene,
                model='cube',
                scale=(15, 8, 12),
                position=(i * 20 - 20, 4, 0),
                color=color.gold,
            collider='box'
            )
        
        # Fortuna-powered lights
        for i in range(-4, 5):
            light = Entity(
                parent=scene,
                model='sphere',
                scale=0.5,
                position=(i * 10, 3, 10),
                color=color.cyan
            )
    
    def _add_press_quarter_props(self, scene: Entity):
        """Add Printing Press Quarter specific props."""
        # Industrial buildings
        for i in range(4):
            building = Entity(
                parent=scene,
                model='cube',
                scale=(8, 6, 8),
                position=(i * 15 - 20, 3, 0),
                color=color.brown,
                collider='box'
            )
        
        # Chimneys
        for i in range(2):
            chimney = Entity(
                parent=scene,
                model='cylinder',
                scale=(1, 8, 1),
                position=(i * 20 - 10, 4, 0),
                color=color.dark_gray
            )
    
    def _add_underdeck_props(self, scene: Entity):
        """Add The Underdeck specific props."""
        # Underground tunnels
        tunnel = Entity(
            parent=scene,
            model='cube',
            scale=(60, 4, 8),
            position=(0, 2, 0),
            color=color.dark_gray
        )
        
        # Support beams
        for i in range(-2, 3):
            beam = Entity(
                parent=scene,
                model='cube',
                scale=(1, 6, 1),
                position=(i * 15, 3, 0),
                color=color.brown
            )
    
    def _add_promenade_props(self, scene: Entity):
        """Add Gilded Promenade specific props."""
        # Luxury shops
        for i in range(5):
            shop = Entity(
                parent=scene,
                model='cube',
                scale=(6, 4, 6),
                position=(i * 12 - 24, 2, 0),
                color=color.white
            )
        
        # Fountain
        fountain = Entity(
            parent=scene,
            model='cylinder',
            scale=(3, 1, 3),
            position=(0, 0.5, 0),
            color=color.blue
        )
    
    def _add_quarantine_props(self, scene: Entity):
        """Add Quarantine Zone specific props."""
        # Corrupted buildings
        for i in range(3):
            building = Entity(
                parent=scene,
                model='cube',
                scale=(10, 5, 10),
                position=(i * 20 - 20, 2.5, 0),
                color=color.dark_red
            )
        
        # Reality cracks (visual effects)
        for i in range(5):
            crack = Entity(
                parent=scene,
                model='cube',
                scale=(0.2, 0.2, 10),
                position=(i * 8 - 16, 0.1, 0),
                color=color.purple
            )
    
    def _add_syndicate_props(self, scene: Entity):
        """Add Syndicate Headquarters specific props."""
        # Main palace
        palace = Entity(
            parent=scene,
            model='cube',
            scale=(30, 15, 20),
            position=(0, 7.5, 0),
            color=color.gold
        )
        
        # Ascendancy Engine (beneath)
        engine = Entity(
            parent=scene,
            model='sphere',
            scale=10,
            position=(0, -5, 0),
            color=color.cyan
        )
    
    def _add_transition_markers(self, scene: Entity, district: District):
        """Add visual markers for transition points."""
        for transition in district.transition_points:
            marker = Entity(
                parent=scene,
                model='cube',
                scale=(2, 3, 2),
                position=transition["position"],
                color=color.yellow
            )
            
            # Add text label
            Text(
                parent=marker,
                text=transition["name"],
                position=(0, 2, 0),
                scale=2,
                color=color.white
            )


@dataclass
class VisualCue:
    """Represents a visual cue in the world."""
    cue_id: str
    description: str
    district: DistrictType
    position: Vec3
    visual_effect: str


@dataclass
class WorldEvent:
    """Represents a dynamic world event."""
    event_id: str
    title: str
    description: str
    effects: List[str]
    district: DistrictType


# Example usage and testing
if __name__ == "__main__":
    # Create the world map
    world = WorldMap()
    
    # Start in Grand Terminal
    world.change_district(DistrictType.GRAND_TERMINAL)
    
    # Unlock some districts for testing
    world.unlock_district(DistrictType.CASINO_DISTRICT)
    world.unlock_district(DistrictType.PRINTING_PRESS_QUARTER)
    
    print(f"Current district: {world.get_current_district().name}")
    print(f"Available transitions: {[t['name'] for t in world.get_available_transitions()]}") 