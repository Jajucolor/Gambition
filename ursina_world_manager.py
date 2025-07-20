from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from ursina import *
from world_system import world_state, District, Location
from story_npcs import STORY_NPCS, get_npc_dialogue, process_npc_choice
from twisted_enemies import create_twisted_enemy, get_district_enemies
import random
import math


class WorldManager:
    """Manages the 3D world representation of Aethelburg"""
    
    def __init__(self, player_stats, player_entity):
        self.player_stats = player_stats
        self.player_entity = player_entity
        self.current_district = "grand_terminal"
        
        # World entities
        self.district_portals: Dict[str, Entity] = {}
        self.location_entities: Dict[str, List[Entity]] = {}
        self.npc_entities: Dict[str, Entity] = {}
        self.enemy_entities: List[Entity] = []
        
        # UI elements
        self.district_hud = Text(parent=camera.ui, text="", x=-0.8, y=0.4, scale=1.2, origin=(0,0))
        self.story_hud = Text(parent=camera.ui, text="", x=-0.8, y=0.35, scale=1, origin=(0,0))
        
        self._create_world()
        self._update_hud()
    
    def _create_world(self):
        """Create the 3D representation of Aethelburg"""
        
        # Create district portals in a circular arrangement
        portal_positions = {
            "grand_terminal": (0, 1, 0),      # Center - starting point
            "syndicate_plaza": (0, 1, 20),    # North
            "underdeck": (0, -2, -15),        # Underground south  
            "casino_district": (25, 1, 10),   # Northeast
            "printing_quarter": (-25, 1, 10), # Northwest
            "residential_gardens": (20, 1, -15), # Southeast
            "factory_district": (-20, 1, -15),   # Southwest
            "the_depths": (0, -8, 0),         # Deep underground
        }
        
        # Create portal entities for each district
        for district_id, position in portal_positions.items():
            district = world_state.districts[district_id]
            
            # Choose color based on district state and theme
            if district.state.value == "locked":
                portal_color = color.dark_gray
                portal_scale = (6, 3, 6)
            elif district.state.value == "accessible":
                portal_color = self._get_district_color(district.theme)
                portal_scale = (8, 4, 8)
            else:
                portal_color = color.green
                portal_scale = (8, 4, 8)
            
            portal = Entity(
                model='cube',
                color=portal_color,
                scale=portal_scale,
                position=position,
                collider='box'
            )
            
            # Add district label
            Text(
                text=district.name,
                parent=portal,
                position=(0, 3, 0),
                scale=2,
                billboard=True,
                color=color.white
            )
            
            self.district_portals[district_id] = portal
        
        # Create location entities within districts
        self._create_district_locations()
        
        # Create story NPCs
        self._create_story_npcs()
        
        # Create enemies
        self._spawn_district_enemies()
        
        # Create environmental elements
        self._create_environment()
    
    def _get_district_color(self, theme: str) -> Color:
        """Get color based on district theme"""
        theme_colors = {
            "tutorial_combat": color.orange,
            "story_hub": color.gold,
            "companions": color.cyan,
            "wealth_corruption": color.yellow,
            "information_control": color.blue,
            "domestic_horror": color.pink,
            "industrial_nightmare": color.red,
            "final_confrontation": color.black,
        }
        return theme_colors.get(theme, color.gray)
    
    def _create_district_locations(self):
        """Create location entities within each district"""
        for district_id, district in world_state.districts.items():
            portal_pos = self.district_portals[district_id].position
            locations = []
            
            # Arrange locations around the district portal
            for i, location in enumerate(district.locations):
                angle = (i / len(district.locations)) * 2 * math.pi
                offset_x = math.cos(angle) * 12
                offset_z = math.sin(angle) * 12
                
                loc_pos = (
                    portal_pos[0] + offset_x,
                    portal_pos[1],
                    portal_pos[2] + offset_z
                )
                
                # Choose model and color based on location type
                if location.location_type == "shop":
                    loc_color = color.green
                    loc_model = 'cube'
                elif location.location_type == "combat":
                    loc_color = color.red
                    loc_model = 'cube'
                elif location.location_type == "story":
                    loc_color = color.blue
                    loc_model = 'cube'
                else:
                    loc_color = color.gray
                    loc_model = 'cube'
                
                loc_entity = Entity(
                    model=loc_model,
                    color=loc_color,
                    scale=(3, 2, 3),
                    position=loc_pos,
                    collider='box'
                )
                
                # Add location label
                Text(
                    text=location.name,
                    parent=loc_entity,
                    position=(0, 2, 0),
                    scale=1.5,
                    billboard=True,
                    color=color.white
                )
                
                locations.append(loc_entity)
            
            self.location_entities[district_id] = locations
    
    def _create_story_npcs(self):
        """Create story-important NPCs"""
        npc_positions = {
            "valerius": (0, 1, 25),           # Syndicate Plaza
            "cartomancer": (30, 1, 15),      # Casino District
            "syndicate_scientist": (-5, 1, 25), # Syndicate Plaza
        }
        
        for npc_id, position in npc_positions.items():
            if npc_id in STORY_NPCS:
                npc = STORY_NPCS[npc_id]
                
                npc_entity = Entity(
                    model='cube',
                    color=color.magenta,
                    scale=(2, 4, 2),
                    position=position,
                    collider='box'
                )
                
                # Add NPC name label
                Text(
                    text=npc.name,
                    parent=npc_entity,
                    position=(0, 3, 0),
                    scale=1.8,
                    billboard=True,
                    color=color.white
                )
                
                self.npc_entities[npc_id] = npc_entity
    
    def _spawn_district_enemies(self):
        """Spawn enemies in accessible districts"""
        for district_id, district in world_state.districts.items():
            if district.state.value != "accessible":
                continue
            
            portal_pos = self.district_portals[district_id].position
            enemy_types = get_district_enemies(district_id)
            
            # Spawn 2-3 enemies per district
            for i in range(random.randint(2, 3)):
                enemy_type = random.choice(enemy_types)
                
                # Random position around district
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(15, 25)
                enemy_pos = (
                    portal_pos[0] + math.cos(angle) * distance,
                    portal_pos[1],
                    portal_pos[2] + math.sin(angle) * distance
                )
                
                enemy_entity = Entity(
                    model='cube',
                    color=color.red,
                    scale=(2, 2, 2),
                    position=enemy_pos,
                    collider='box'
                )
                
                # Store enemy type for combat
                enemy_entity.enemy_type = enemy_type
                enemy_entity.district = district_id
                
                # Add enemy label
                Text(
                    text=enemy_type,
                    parent=enemy_entity,
                    position=(0, 2.5, 0),
                    scale=1.2,
                    billboard=True,
                    color=color.white
                )
                
                self.enemy_entities.append(enemy_entity)
    
    def _create_environment(self):
        """Create environmental elements"""
        # Larger ground plane
        Entity(model="plane", scale=200, texture="grass", collider="box")
        
        # Atmospheric elements
        Sky(color=color.dark_gray)  # Darker sky for the corrupted city
        
        # Fortuna crystal formations
        for _ in range(20):
            crystal_pos = (
                random.uniform(-80, 80),
                random.uniform(1, 5),
                random.uniform(-80, 80)
            )
            Entity(
                model='cube',
                color=color.cyan,
                scale=(1, random.uniform(3, 8), 1),
                position=crystal_pos,
                rotation_y=random.uniform(0, 360)
            )
    
    def update_world_state(self):
        """Update world based on story progression"""
        # Update district portal states
        for district_id, district in world_state.districts.items():
            portal = self.district_portals[district_id]
            
            if district.state.value == "locked":
                portal.color = color.dark_gray
                portal.scale = (6, 3, 6)
            elif district.state.value == "accessible":
                portal.color = self._get_district_color(district.theme)
                portal.scale = (8, 4, 8)
            else:
                portal.color = color.green
                portal.scale = (8, 4, 8)
        
        # Update HUD
        self._update_hud()
        
        # Spawn new enemies in newly accessible districts
        self._spawn_new_enemies()
    
    def _spawn_new_enemies(self):
        """Spawn enemies in newly accessible districts"""
        for district_id, district in world_state.districts.items():
            if district.state.value != "accessible":
                continue
            
            # Check if this district already has enemies
            district_has_enemies = any(
                e.district == district_id for e in self.enemy_entities if hasattr(e, 'district')
            )
            
            if not district_has_enemies:
                # Spawn enemies for this district
                portal_pos = self.district_portals[district_id].position
                enemy_types = get_district_enemies(district_id)
                
                for i in range(random.randint(2, 3)):
                    enemy_type = random.choice(enemy_types)
                    
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(15, 25)
                    enemy_pos = (
                        portal_pos[0] + math.cos(angle) * distance,
                        portal_pos[1],
                        portal_pos[2] + math.sin(angle) * distance
                    )
                    
                                         enemy_entity = Entity(
                         model='cube',
                         color=color.red,
                         scale=(2, 2, 2),
                         position=enemy_pos,
                         collider='box'
                     )
                    
                    enemy_entity.enemy_type = enemy_type
                    enemy_entity.district = district_id
                    
                    Text(
                        text=enemy_type,
                        parent=enemy_entity,
                        position=(0, 2.5, 0),
                        scale=1.2,
                        billboard=True,
                        color=color.white
                    )
                    
                    self.enemy_entities.append(enemy_entity)
    
    def _update_hud(self):
        """Update the world HUD with current information"""
        context = world_state.get_current_story_context()
        
        # District info
        current_district = world_state.districts.get(self.current_district)
        if current_district:
            self.district_hud.text = f"District: {current_district.name}"
        
        # Story progress info
        act_text = context["act"].value.upper().replace("_", " ")
        clues_text = f"Maestro Clues: {context['maestro_clues']}/3"
        trust_text = f"Valerius Trust: {context['valerius_trust']}"
        
        self.story_hud.text = f"{act_text} | {clues_text} | {trust_text}"
    
    def get_nearby_interactables(self, player_pos: Vec3, max_distance: float = 8) -> Dict[str, Any]:
        """Get nearby interactable objects"""
        interactables = {}
        
        # Check district portals
        for district_id, portal in self.district_portals.items():
            if distance(player_pos, portal.position) < max_distance:
                district = world_state.districts[district_id]
                if district.state.value == "accessible":
                    interactables[f"district_{district_id}"] = {
                        "type": "district",
                        "name": district.name,
                        "entity": portal
                    }
        
        # Check NPCs
        for npc_id, npc_entity in self.npc_entities.items():
            if distance(player_pos, npc_entity.position) < max_distance:
                interactables[f"npc_{npc_id}"] = {
                    "type": "npc",
                    "name": STORY_NPCS[npc_id].name,
                    "entity": npc_entity,
                    "npc_id": npc_id
                }
        
        # Check enemies
        for enemy_entity in self.enemy_entities:
            if distance(player_pos, enemy_entity.position) < max_distance:
                interactables[f"enemy_{id(enemy_entity)}"] = {
                    "type": "enemy",
                    "name": enemy_entity.enemy_type,
                    "entity": enemy_entity
                }
        
        return interactables
    
    def remove_enemy(self, enemy_entity: Entity):
        """Remove an enemy from the world"""
        if enemy_entity in self.enemy_entities:
            self.enemy_entities.remove(enemy_entity)
            destroy(enemy_entity)
    
    def trigger_story_event(self, event: str) -> List[str]:
        """Trigger a story event and return updates"""
        updates = world_state.advance_story(event)
        self.update_world_state()
        return updates
    
    def get_current_district_info(self) -> Dict[str, Any]:
        """Get information about the current district"""
        district = world_state.districts.get(self.current_district)
        if not district:
            return {}
        
        return {
            "name": district.name,
            "description": district.description,
            "theme": district.theme,
            "state": district.state.value,
            "locations": len(district.locations),
            "boss_defeated": district.boss_defeated
        } 