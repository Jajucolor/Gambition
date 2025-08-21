"""
Texture Creation Script for Gambition
Creates sample texture files for cards, characters, and world objects.
"""
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_assets_directory():
    """Create the assets directory if it doesn't exist."""
    assets_path = Path("assets")
    assets_path.mkdir(exist_ok=True)
    return assets_path

def create_card_textures():
    """Create playing card textures."""
    assets_path = create_assets_directory()
    
    # Card back texture
    card_back = Image.new('RGB', (256, 256), (25, 50, 100))
    draw = ImageDraw.Draw(card_back)
    
    # Draw card back pattern
    for i in range(0, 256, 20):
        for j in range(0, 256, 20):
            draw.rectangle([i, j, i+10, j+10], fill=(50, 100, 150))
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((128, 128), "GAMBITION", fill=(255, 255, 255), anchor="mm", font=font)
    card_back.save(assets_path / "card_back.png")
    
    # Suit symbols
    suits = {
        'hearts': '♥',
        'diamonds': '♦', 
        'clubs': '♣',
        'spades': '♠'
    }
    
    for suit_name, suit_symbol in suits.items():
        # Create suit texture
        suit_img = Image.new('RGB', (64, 64), (255, 255, 255))
        draw = ImageDraw.Draw(suit_img)
        
        # Draw suit symbol
        color = (255, 0, 0) if suit_name in ['hearts', 'diamonds'] else (0, 0, 0)
        try:
            font = ImageFont.truetype("arial.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        draw.text((32, 32), suit_symbol, fill=color, anchor="mm", font=font)
        suit_img.save(assets_path / f"card_{suit_name}.png")
        
        # Create rank-specific textures for face cards
        if suit_name == 'hearts':
            # Create some sample face card textures
            for rank in ['ace', 'king', 'queen', 'jack']:
                rank_img = Image.new('RGB', (128, 128), (255, 255, 255))
                draw = ImageDraw.Draw(rank_img)
                
                # Border
                draw.rectangle([0, 0, 127, 127], outline=(0, 0, 0), width=2)
                
                # Rank and suit
                try:
                    font_large = ImageFont.truetype("arial.ttf", 36)
                    font_small = ImageFont.truetype("arial.ttf", 24)
                except:
                    font_large = ImageFont.load_default()
                    font_small = ImageFont.load_default()
                
                draw.text((20, 20), rank.upper(), fill=(0, 0, 0), font=font_large)
                draw.text((20, 60), suit_symbol, fill=(255, 0, 0), font=font_small)
                draw.text((100, 100), suit_symbol, fill=(255, 0, 0), font=font_small)
                
                rank_img.save(assets_path / f"card_{rank}_{suit_name}.png")

def create_character_textures():
    """Create character textures."""
    assets_path = create_assets_directory()
    
    # Player texture
    player_img = Image.new('RGB', (128, 128), (100, 150, 255))
    draw = ImageDraw.Draw(player_img)
    
    # Draw player pattern
    for i in range(0, 128, 16):
        for j in range(0, 128, 16):
            if (i + j) % 32 == 0:
                draw.rectangle([i, j, i+8, j+8], fill=(150, 200, 255))
    
    player_img.save(assets_path / "player.png")
    
    # Enemy texture
    enemy_img = Image.new('RGB', (128, 128), (200, 50, 50))
    draw = ImageDraw.Draw(enemy_img)
    
    # Draw enemy pattern
    for i in range(0, 128, 12):
        for j in range(0, 128, 12):
            if (i + j) % 24 == 0:
                draw.rectangle([i, j, i+6, j+6], fill=(255, 100, 100))
    
    enemy_img.save(assets_path / "enemy.png")
    
    # NPC textures
    npc_colors = [
        (50, 100, 200),   # Blue
        (50, 200, 100),   # Green  
        (200, 50, 200),   # Magenta
        (200, 150, 50)    # Orange
    ]
    
    for i, color_val in enumerate(npc_colors):
        npc_img = Image.new('RGB', (128, 128), color_val)
        draw = ImageDraw.Draw(npc_img)
        
        # Draw NPC pattern (stripes)
        for j in range(0, 128, 8):
            if j % 16 == 0:
                draw.rectangle([0, j, 127, j+4], fill=tuple(c+50 for c in color_val))
        
        npc_img.save(assets_path / f"npc_{i}.png")

def create_world_textures():
    """Create world object textures."""
    assets_path = create_assets_directory()
    
    # Ground texture
    ground_img = Image.new('RGB', (512, 512), (150, 150, 150))
    draw = ImageDraw.Draw(ground_img)
    
    # Draw tile pattern
    for i in range(0, 512, 64):
        for j in range(0, 512, 64):
            draw.rectangle([i, j, i+63, j+63], outline=(100, 100, 100), width=2)
            # Add some variation
            if (i + j) % 128 == 0:
                draw.rectangle([i+8, j+8, i+55, j+55], fill=(180, 180, 180))
    
    ground_img.save(assets_path / "ground.png")
    
    # Building texture
    building_img = Image.new('RGB', (256, 256), (220, 220, 220))
    draw = ImageDraw.Draw(building_img)
    
    # Draw brick pattern
    for i in range(0, 256, 32):
        for j in range(0, 256, 16):
            offset = 16 if (j // 16) % 2 == 1 else 0
            draw.rectangle([i+offset, j, i+offset+30, j+14], outline=(180, 180, 180), width=1)
    
    building_img.save(assets_path / "building.png")
    
    # Wood texture
    wood_img = Image.new('RGB', (256, 256), (139, 69, 19))
    draw = ImageDraw.Draw(wood_img)
    
    # Draw wood grain
    for i in range(0, 256, 4):
        color_val = 139 + (i % 20) - 10
        color_val = max(100, min(180, color_val))
        draw.line([(i, 0), (i, 255)], fill=(color_val, color_val//2, color_val//4), width=2)
    
    wood_img.save(assets_path / "wood.png")
    
    # Metal texture
    metal_img = Image.new('RGB', (256, 256), (192, 192, 192))
    draw = ImageDraw.Draw(metal_img)
    
    # Draw metal pattern
    for i in range(0, 256, 8):
        for j in range(0, 256, 8):
            if (i + j) % 16 == 0:
                draw.rectangle([i, j, i+6, j+6], fill=(220, 220, 220))
    
    metal_img.save(assets_path / "metal.png")

def main():
    """Create all texture files."""
    print("🎨 Creating texture files for Gambition...")
    
    create_card_textures()
    print("✅ Created card textures")
    
    create_character_textures()
    print("✅ Created character textures")
    
    create_world_textures()
    print("✅ Created world textures")
    
    print("🎉 All textures created successfully!")
    print("📁 Check the 'assets' directory for the new texture files.")

if __name__ == "__main__":
    main() 