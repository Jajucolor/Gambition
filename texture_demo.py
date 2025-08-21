"""
Texture Demo for Gambition
Shows how textures are applied to cards, characters, and world objects.
"""
from ursina import *
from texture_manager import texture_manager, apply_card_texture, apply_character_texture, apply_world_texture

def main():
    app = Ursina()
    
    # Configure window settings for full adjustability
    window.borderless = False       # gives normal window borders
    window.fullscreen = True        # start in fullscreen
    window.exit_button.visible = True
    window.fps_counter.enabled = True
    window.title = "Gambition - Texture Demo"
    
    # Fullscreen settings (size will be auto-detected)
    window.resizable = True         # allow resizing when switching to windowed mode
    
    # Load textures
    texture_manager.load_textures()
    
    # Create a simple scene to demonstrate textures
    
    # Ground with texture
    ground = Entity(model='plane', scale=(10, 1, 10), position=(0, 0, 0))
    apply_world_texture(ground, 'ground')
    
    # Player character with texture
    player = Entity(model='cube', position=(-2, 1, 0), scale=1)
    apply_character_texture(player, 'player')
    
    # Enemy character with texture
    enemy = Entity(model='cube', position=(2, 1, 0), scale=1)
    apply_character_texture(enemy, 'enemy')
    
    # NPC with texture
    npc = Entity(model='sphere', position=(0, 1, 2), scale=1)
    apply_character_texture(npc, 'npc', 0)
    
    # Building with texture
    building = Entity(model='cube', position=(0, 2, -3), scale=(2, 2, 2))
    apply_world_texture(building, 'building')
    
    # Card buttons with textures
    from card import Card
    
    # Create some test cards
    test_cards = [
        Card('A', 'hearts'),
        Card('K', 'spades'),
        Card('Q', 'diamonds'),
        Card('J', 'clubs')
    ]
    
    # Create card buttons
    for i, card in enumerate(test_cards):
        x = (i - 1.5) * 0.3
        btn = Button(
            parent=camera.ui,
            text=f'{card.rank}{card.suit[0]}',
            position=(x, 0.2),
            scale=(0.2, 0.3)
        )
        apply_card_texture(btn, card)
    
    # Info text
    info = Text(
        parent=camera.ui,
        text="Texture Demo\nWASD to move, ESC to exit",
        position=(-0.8, 0.4),
        scale=0.8
    )
    
    # Camera setup
    camera.position = (0, 5, 10)
    camera.look_at(Vec3(0, 0, 0))
    
    # Player controller
    player_controller = FirstPersonController()
    player_controller.position = (0, 2, 5)
    
    def input(key):
        if key == 'escape':
            application.quit()
    
    app.run()

if __name__ == "__main__":
    main() 