"""
Texture Manager for Gambition
Handles loading and applying textures to characters, cards, and world objects.
"""
from __future__ import annotations
from typing import Dict, Optional, Any
from pathlib import Path
import os

from ursina import *  # type: ignore


class TextureManager:
    """Manages all game textures and provides easy access methods."""
    
    def __init__(self):
        self.textures: Dict[str, Any] = {}
        self.assets_path = Path("assets")
        self._load_all_textures()
    
    def _load_all_textures(self):
        """Load all texture files from the assets directory."""
        if not self.assets_path.exists():
            print("⚠️  Assets directory not found. Creating basic textures...")
            self._create_basic_textures()
            return
        
        # Load existing textures - defer loading until Ursina app is initialized
        self._texture_files = {}
        for texture_file in self.assets_path.glob("*.png"):
            texture_name = texture_file.stem
            self._texture_files[texture_name] = str(texture_file)
        
        for texture_file in self.assets_path.glob("*.jpg"):
            texture_name = texture_file.stem
            self._texture_files[texture_name] = str(texture_file)
        
        print(f"📁 Found {len(self._texture_files)} texture files")
    
    def load_textures(self):
        """Load textures when Ursina app is ready."""
        if not hasattr(self, '_texture_files'):
            return
        
        for texture_name, file_path in self._texture_files.items():
            try:
                self.textures[texture_name] = load_texture(file_path)
                print(f"✅ Loaded texture: {texture_name}")
            except Exception as e:
                print(f"❌ Failed to load texture {texture_name}: {e}")
        
        # Clear the file list after loading
        self._texture_files = {}
    
    def _create_basic_textures(self):
        """Create basic procedural textures if assets don't exist."""
        print("🎨 Creating basic procedural textures...")
        
        # Create assets directory
        self.assets_path.mkdir(exist_ok=True)
        
        # Basic card textures
        self._create_card_textures()
        
        # Basic character textures
        self._create_character_textures()
        
        # Basic world textures
        self._create_world_textures()
    
    def _create_card_textures(self):
        """Create basic card textures procedurally."""
        # Card back texture
        card_back = Texture.create_custom(
            size=(256, 256),
            color=color.dark_blue,
            pattern='noise'
        )
        self.textures['card_back'] = card_back
        
        # Suit textures
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        for suit in suits:
            suit_texture = Texture.create_custom(
                size=(64, 64),
                color=color.red if suit in ['hearts', 'diamonds'] else color.black,
                pattern='symbol'
            )
            self.textures[f'card_{suit}'] = suit_texture
    
    def _create_character_textures(self):
        """Create basic character textures procedurally."""
        # Player texture
        player_tex = Texture.create_custom(
            size=(128, 128),
            color=color.azure,
            pattern='gradient'
        )
        self.textures['player'] = player_tex
        
        # Enemy texture
        enemy_tex = Texture.create_custom(
            size=(128, 128),
            color=color.red,
            pattern='noise'
        )
        self.textures['enemy'] = enemy_tex
        
        # NPC textures
        npc_colors = [color.blue, color.green, color.magenta, color.orange]
        for i, color_val in enumerate(npc_colors):
            npc_tex = Texture.create_custom(
                size=(128, 128),
                color=color_val,
                pattern='stripes'
            )
            self.textures[f'npc_{i}'] = npc_tex
    
    def _create_world_textures(self):
        """Create basic world textures procedurally."""
        # Ground textures
        ground_tex = Texture.create_custom(
            size=(512, 512),
            color=color.gray,
            pattern='tiles'
        )
        self.textures['ground'] = ground_tex
        
        # Building textures
        building_tex = Texture.create_custom(
            size=(256, 256),
            color=color.white,
            pattern='bricks'
        )
        self.textures['building'] = building_tex
        
        # Wood texture
        wood_tex = Texture.create_custom(
            size=(256, 256),
            color=color.brown,
            pattern='wood'
        )
        self.textures['wood'] = wood_tex
    
    def get_texture(self, name: str) -> Optional[Any]:
        """Get a texture by name."""
        return self.textures.get(name)
    
    def get_card_texture(self, suit: str, rank: str) -> Any:
        """Get appropriate texture for a playing card."""
        # Try to get specific card texture
        card_name = f"card_{rank.lower()}_{suit.lower()}"
        if card_name in self.textures:
            return self.textures[card_name]
        
        # Fall back to suit texture
        suit_name = f"card_{suit.lower()}"
        if suit_name in self.textures:
            return self.textures[suit_name]
        
        # Fall back to card back
        return self.textures.get('card_back', None)
    
    def get_character_texture(self, character_type: str, variant: int = 0) -> Any:
        """Get texture for a character type."""
        texture_name = f"{character_type}_{variant}"
        return self.textures.get(texture_name, self.textures.get(character_type, None))
    
    def get_world_texture(self, texture_type: str) -> Any:
        """Get texture for world objects."""
        return self.textures.get(texture_type, None)


# Global texture manager instance
texture_manager = TextureManager()


def apply_card_texture(button: Button, card) -> None:
    """Apply appropriate texture to a card button."""
    texture = texture_manager.get_card_texture(card.suit, card.rank)
    if texture:
        button.texture = texture
        # Adjust text color for visibility
        if card.suit in ['♥', '♦']:  # Red suits
            button.text_color = color.white
        else:  # Black suits
            button.text_color = color.white


def apply_character_texture(entity: Entity, character_type: str, variant: int = 0) -> None:
    """Apply texture to a character entity."""
    texture = texture_manager.get_character_texture(character_type, variant)
    if texture:
        entity.texture = texture


def apply_world_texture(entity: Entity, texture_type: str) -> None:
    """Apply texture to a world entity."""
    texture = texture_manager.get_world_texture(texture_type)
    if texture:
        entity.texture = texture 