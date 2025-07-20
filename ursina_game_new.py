"""Gambition: The Complete Story-Driven Card RPG

Explore the Belle Époque city of Aethelburg, uncover the mystery of the Dissonance,
and discover the truth about your own identity in this poker-based RPG.

Controls:
- WASD: Move around
- Mouse: Look around  
- E: Open inventory
- G: Enter Guild (when near)
- H: Enter Card Market (when near)
- T: Talk to NPCs (when near)
- ESC: Close menus

Requires: pip install ursina pygame
"""
from __future__ import annotations

import sys
import math
import random
from typing import Dict, List, Optional, Any

# Ursina main imports
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

# Game systems
from ursina_combat import CombatUI
from guild import generate_guild_offers, CompanionOffer
from card_shop import generate_shop_offers, ShopOffer
from event_system import random_event, Event as GameEvent
from entities.player import Player

# New story systems
from world_system import world_state
from story_npcs import STORY_NPCS, get_npc_dialogue, process_npc_choice
from twisted_enemies import create_twisted_enemy, get_district_enemies, get_memory_echo_rewards
from ursina_world_manager import WorldManager


def setup_world():
    """Create the expanded world of Aethelburg with story integration."""
    
    # Initialize Ursina
    app = Ursina()
    
    # Gameplay stats - start player's story journey
    player_stats = Player()
    player_stats.start_combat()  # Initialize combat state
    
    # Player entity (visual)
    player = FirstPersonController(model='cube', color=color.azure, collider='box')
    camera.z = -5
    player.speed = 8  # Slightly faster for the bigger world
    
    # Initialize the world manager with all the new systems
    try:
        world_manager = WorldManager(player_stats, player)
    except Exception as e:
        print(f"World manager initialization failed: {e}")
        # Fallback to basic world
        Entity(model="plane", scale=100, texture="grass", collider="box")
        Sky()
        world_manager = None
    
    # UI State management
    state: Dict[str, Any] = {
        'combat_ui': None,
        'guild_ui': None,
        'event_ui': None,
        'shop_ui': None,
        'dialogue_ui': None,
        'inv_ui': None,
        'guild_close': None,
        'shop_close': None,
        'dialogue_close': None,
        'event_close': None,
        'inv_close': None,
        'current_npc': None,
        'current_enemy': None,
        'interaction_prompts': {},
    }
    
    # Interaction prompts
    interaction_hud = Text(parent=camera.ui, text="", origin=(0,0), y=-0.3, x=0, enabled=True, scale=1.2)
    
    # Story introduction text
    story_intro = Text(
        parent=camera.ui, 
        text="Welcome to Aethelburg, City of Fortune.\nFind Chairman Valerius at Syndicate Plaza (North) to begin your story.",
        origin=(0,0), 
        y=0.0, 
        x=0, 
        enabled=True, 
        scale=1.5,
        color=color.yellow
    )
    
    # Hide intro after 8 seconds
    def hide_intro():
        story_intro.enabled = False
    invoke(hide_intro, delay=8)

    def update():
        """Main game update loop with story integration."""
        # Skip updates if any overlay is active
        if any(state[key] for key in ['combat_ui', 'guild_ui', 'event_ui', 'shop_ui', 'inv_ui', 'dialogue_ui']):
            return
        
        # Update world manager
        world_manager.update_world_state()
        
        # Get nearby interactables
        nearby = world_manager.get_nearby_interactables(player.position, max_distance=10)
        
        # Update interaction prompts
        prompt_text = ""
        state['interaction_prompts'] = nearby
        
        for key, interactable in nearby.items():
            if interactable['type'] == 'district':
                prompt_text += f"[Enter {interactable['name']}] "
            elif interactable['type'] == 'npc':
                prompt_text += f"[T] Talk to {interactable['name']} "
            elif interactable['type'] == 'enemy':
                prompt_text += f"[Touch] Fight {interactable['name']} "
        
        # Add guild/market prompts if near old buildings (legacy support)
        if hasattr(world_manager, 'district_portals'):
            underdeck_portal = world_manager.district_portals.get('underdeck')
            if underdeck_portal and distance(player.position, underdeck_portal.position) < 12:
                prompt_text += "[G] Enter Guild "
        
        interaction_hud.text = prompt_text
        
        # Auto-trigger combat when touching enemies
        for key, interactable in nearby.items():
            if interactable['type'] == 'enemy' and distance(player.position, interactable['entity'].position) < 3:
                start_combat_with_enemy(interactable['entity'])
                break

    def start_combat_with_enemy(enemy_entity):
        """Start combat with a specific enemy."""
        if state['combat_ui']:
            return  # Already in combat
        
        # Create the twisted enemy
        enemy_type = getattr(enemy_entity, 'enemy_type', 'Twisted Guard')
        enemy = create_twisted_enemy(enemy_type)
        
        # Get combat position (at enemy location)
        combat_position = enemy_entity.position
        
        # Create combat UI
        state['combat_ui'] = CombatUI(player_stats, enemy)
        state['current_enemy'] = enemy_entity
        
        # Lock player movement and mouse
        player.enabled = False
        mouse.locked = False
        
        print(f"Combat started against {enemy.name} at {combat_position}")
        if hasattr(enemy, 'lore') and enemy.lore:
            print(f"You face {enemy.lore.former_identity}, twisted by {enemy.lore.obsession}")

    def end_combat(victory: bool):
        """End combat and handle results."""
        if not state['combat_ui']:
            return
        
        enemy_entity = state['current_enemy']
        enemy = state['combat_ui'].enemy
        
        if victory and enemy_entity:
            # Show memory echo for boss enemies
            if hasattr(enemy, 'is_boss') and enemy.is_boss:
                memory_echo = enemy.get_memory_echo()
                print(f"\n=== MEMORY ECHO ===")
                print(memory_echo)
                print("==================")
                
                # Give boss rewards
                rewards = get_memory_echo_rewards(enemy.name)
                player_stats.gold += rewards.get('gold', 0)
                
                # Trigger story progression
                if enemy.name == "The Dealer Supreme":
                    updates = world_manager.trigger_story_event("defeat_casino_boss")
                    for update in updates:
                        print(f"STORY: {update}")
            
            # Remove enemy from world
            world_manager.remove_enemy(enemy_entity)
            print(f"Victory! {enemy.name} has been defeated.")
        
        # Clean up combat UI
        state['combat_ui'].cleanup()
        state['combat_ui'] = None
        state['current_enemy'] = None
        
        # Re-enable player
        player.enabled = True
        mouse.locked = True

    # Input handling with story integration
    def input(key):
        # ESC closes any overlay
        if key == 'escape':
            if state.get('guild_close'):
                state['guild_close']()
                return
            if state.get('event_close'):
                state['event_close']()
                return
            if state.get('inv_close'):
                state['inv_close']()
                return
            if state.get('shop_close'):
                state['shop_close']()
                return
            if state.get('dialogue_close'):
                state['dialogue_close']()
                return

        # Block other keys when overlay present
        if any(state[key] for key in ['combat_ui', 'guild_ui', 'event_ui', 'inv_ui', 'shop_ui', 'dialogue_ui']):
            return

        # Story NPC dialogue
        if key == 't':
            for interactable_key, interactable in state['interaction_prompts'].items():
                if interactable['type'] == 'npc':
                    open_story_dialogue(interactable['npc_id'])
                    break

        # Legacy guild system (G key)
        if key == 'g':
            open_guild_ui()
        
        # Legacy market system (H key)  
        elif key == 'h':
            open_market_ui()
        
        # Inventory system
        elif key == 'e':
            open_inventory_ui()
        
        # Event system (V key for testing)
        elif key == 'v':
            open_event_ui()

    def open_story_dialogue(npc_id: str):
        """Open dialogue with a story NPC."""
        dialogue = get_npc_dialogue(npc_id)
        if not dialogue:
            return
        
        ui_root = Entity(parent=camera.ui)
        
        # NPC name and dialogue
        npc_name = Text(parent=ui_root, text=dialogue.speaker, y=0.4, scale=2, origin=(0,0), color=color.yellow)
        
        # Wrap dialogue text
        dialogue_lines = []
        words = dialogue.text.split(' ')
        current_line = ''
        for word in words:
            if len(current_line + word) > 80:
                dialogue_lines.append(current_line.strip())
                current_line = word + ' '
            else:
                current_line += word + ' '
        if current_line:
            dialogue_lines.append(current_line.strip())
        
        dialogue_texts = []
        for i, line in enumerate(dialogue_lines):
            text = Text(parent=ui_root, text=line, y=0.25-i*0.05, scale=1.2, origin=(0,0))
            dialogue_texts.append(text)
        
        # Dialogue options
        option_buttons = []
        for i, option in enumerate(dialogue.options):
            btn = Button(
                parent=ui_root, 
                text=option.text, 
                position=(-0.4, 0.0 - i*0.1), 
                scale=(0.8, 0.08),
                color=color.dark_gray
            )
            
            def make_choice(choice_idx=i):
                # Process the choice
                updates = process_npc_choice(npc_id, choice_idx)
                for update in updates:
                    print(f"DIALOGUE: {update}")
                
                # Update world state
                world_manager.update_world_state()
                close_dialogue()
            
            btn.on_click = make_choice
            option_buttons.append(btn)
        
        def close_dialogue():
            for btn in option_buttons:
                destroy(btn)
            for text in dialogue_texts:
                destroy(text)
            destroy(npc_name)
            destroy(ui_root)
            state['dialogue_ui'] = None
            state['dialogue_close'] = None
            mouse.locked = True
            player.enabled = True
        
        # Lock controls
        mouse.locked = False
        player.enabled = False
        state['dialogue_ui'] = ui_root
        state['dialogue_close'] = close_dialogue

    # Guild UI
    def open_guild_ui():
        offers: List[CompanionOffer] = generate_guild_offers()
        
        ui_root = Entity(parent=camera.ui)
        title = Text(parent=ui_root, text='Companion Guild', y=.45, scale=2, origin=(0,0))
        
        # Show current companions
        companion_limit_text = Text(parent=ui_root, text=f'Companions: {len(player_stats.jokers)}/5', y=.35, scale=1.2, origin=(0,0))
        
        buttons: List[Button] = []
        
        def refresh():
            nonlocal buttons
            for b in buttons:
                destroy(b)
            buttons.clear()
            
            start_y = 0.25
            for idx, offer in enumerate(offers):
                btn = Button(parent=ui_root, text=f"{offer.name} - {offer.cost}g", 
                           position=(-0.25, start_y - idx*0.12), scale=(0.5,0.08))
                def _click(off=offer):
                    if player_stats.gold >= off.cost:
                        if len(player_stats.jokers) < 5:
                            player_stats.gold -= off.cost
                            player_stats.add_joker(off.joker_type)
                            companion_limit_text.text = f'Companions: {len(player_stats.jokers)}/5'
                            refresh()
                        else:
                            print("Maximum companions reached!")
                    else:
                        print("Not enough gold!")
                btn.on_click = _click
                buttons.append(btn)
            
            # Farewell buttons for existing companions
            farewell_y = start_y - len(offers)*0.12 - 0.1
            Text(parent=ui_root, text='Farewell Companions:', y=farewell_y, scale=1.2, origin=(0,0))
            
            for idx, companion in enumerate(player_stats.jokers):
                farewell_btn = Button(parent=ui_root, text=f"Farewell {companion}", 
                                    position=(0.25, farewell_y - 0.05 - idx*0.08), scale=(0.4,0.06))
                def _farewell(comp=companion):
                    player_stats.remove_joker(comp)
                    companion_limit_text.text = f'Companions: {len(player_stats.jokers)}/5'
                    refresh()
                farewell_btn.on_click = _farewell
                buttons.append(farewell_btn)

        def close_guild():
            for e in buttons:
                destroy(e)
            destroy(title)
            destroy(companion_limit_text)
            destroy(ui_root)
            state['guild_ui'] = None
            state['guild_close'] = None
            mouse.locked = True
            player.enabled = True

        mouse.locked = False
        player.enabled = False
        refresh()
        state['guild_ui'] = ui_root
        state['guild_close'] = close_guild

    # Market UI
    def open_market_ui():
        offers: List[ShopOffer] = generate_shop_offers()

        ui_root = Entity(parent=camera.ui)
        title = Text(parent=ui_root, text='Card Market', y=.45, scale=2, origin=(0,0))

        buttons: List[Button] = []

        def refresh():
            for b in buttons:
                destroy(b)
            buttons.clear()
            start_y = 0.25
            for idx, off in enumerate(offers):
                btn = Button(parent=ui_root, text=f"{off.name} - {off.cost}g", 
                           position=(-0.25, start_y - idx*0.12), scale=(0.5,0.08))
                def _click(offer=off):
                    if player_stats.gold >= offer.cost:
                        player_stats.gold -= offer.cost
                        if hasattr(offer, 'tarot_card'):
                            player_stats.add_item(offer.tarot_card)
                        print(f"Purchased {offer.name}")
                    else:
                        print("Not enough gold!")
                btn.on_click = _click
                buttons.append(btn)

        def close_market():
            for b in buttons:
                destroy(b)
            destroy(title)
            destroy(ui_root)
            state['shop_ui'] = None
            state['shop_close'] = None
            mouse.locked = True
            player.enabled = True

        mouse.locked = False
        player.enabled = False
        refresh()
        state['shop_ui'] = ui_root
        state['shop_close'] = close_market

    # Event UI
    def open_event_ui():
        ev: GameEvent = random_event()

        ui_root = Entity(parent=camera.ui)
        title = Text(parent=ui_root, text="Mysterious Event", y=.45, scale=2, origin=(0,0))
        desc = Text(parent=ui_root, text=ev.description, y=0.3, x=-0.4, scale=1, origin=(0,0))

        btns: List[Button] = []
        start_y = 0.1
        for idx, (text_choice, action) in enumerate(ev.choices):
            btn = Button(parent=ui_root, text=text_choice, position=(-0.25, start_y - idx*0.12), scale=(0.5,0.08))
            def _click(act=action):
                act(player_stats)
                close_event()
            btn.on_click = _click
            btns.append(btn)

        def close_event():
            for b in btns:
                destroy(b)
            destroy(title)
            destroy(desc)
            destroy(ui_root)
            state['event_ui'] = None
            state['event_close'] = None
            mouse.locked = True
            player.enabled = True

        state['event_ui'] = ui_root
        state['event_close'] = close_event

    # Inventory UI
    def open_inventory_ui():
        if not hasattr(player_stats, 'items'):
            player_stats.items = []

        ui_root = Entity(parent=camera.ui)
        title = Text(parent=ui_root, text='Inventory', y=.45, scale=2, origin=(0,0))

        tabs = ['Items', 'Deck', 'Companions']
        current_tab = {'name': 'Items'}

        btns: List[Button] = []
        for i, tname in enumerate(tabs):
            bx = -0.3 + i*0.25
            b = Button(parent=ui_root, text=tname, position=(bx, 0.32), scale=(0.22,0.08))
            btns.append(b)
        
        content_parent = Entity(parent=ui_root, position=(0,0))

        def clear_content():
            for child in list(content_parent.children):
                destroy(child)

        def populate_items():
            clear_content()
            Text(parent=content_parent, text=f'Gold: {player_stats.gold}', x=0, y=0.18, scale=1.2, origin=(0,0))
            Text(parent=content_parent, text='Items:', x=0, y=0.10, scale=1.2, origin=(0,0))
            if player_stats.items:
                for idx, it in enumerate(player_stats.items):
                    Text(parent=content_parent, text=f'- {it}', x=0, y=0.05-idx*0.07, scale=1, origin=(0,0))
            else:
                Text(parent=content_parent, text='(none)', x=0, y=0.05, scale=1, origin=(0,0))

        def populate_deck():
            clear_content()
            Text(parent=content_parent, text='Deck (remaining):', x=0, y=0.18, scale=1.2, origin=(0,0))
            card_lines = []
            row = ''
            for idx, c in enumerate(player_stats.deck.cards):
                row += str(c) + ', '
                if len(row) > 60:
                    card_lines.append(row)
                    row = ''
            if row:
                card_lines.append(row)
            for i, ln in enumerate(card_lines):
                Text(parent=content_parent, text=ln, x=0, y=0.10-i*0.06, scale=0.8, origin=(0,0))

        def populate_comp():
            clear_content()
            Text(parent=content_parent, text='Companions:', x=0, y=0.18, scale=1.2, origin=(0,0))
            if player_stats.jokers:
                for idx, jk in enumerate(player_stats.jokers):
                    Text(parent=content_parent, text=f'- {jk}', x=0, y=0.10-idx*0.07, scale=1, origin=(0,0))
            else:
                Text(parent=content_parent, text='(none)', x=0, y=0.10, scale=1, origin=(0,0))

        tab_funcs = {'Items': populate_items, 'Deck': populate_deck, 'Companions': populate_comp}

        def set_tab(t):
            current_tab['name'] = t
            tab_funcs[t]()
        
        for b in btns:
            b.on_click = lambda t=b.text: set_tab(t)

        populate_items()

        esc_txt = Text(parent=ui_root, text='Press Esc to close', y=-0.45, scale=1, origin=(0,0))

        def close_inv():
            clear_content()
            for e in [*btns, title, esc_txt, content_parent]:
                destroy(e)
            destroy(ui_root)
            state['inv_ui'] = None
            state['inv_close'] = None
            mouse.locked = True
            player.enabled = True

        mouse.locked = False
        player.enabled = False
        state['inv_ui'] = ui_root
        state['inv_close'] = close_inv

    # Set up the main game loop
    globals()['input'] = input
    
    # Combat integration
    def combat_update():
        if state['combat_ui'] and state['combat_ui'].game_over:
            victory = player_stats.is_alive()
            end_combat(victory)
    
    # Add combat update to main update
    original_update = update
    def enhanced_update():
        original_update()
        combat_update()
    
    globals()['update'] = enhanced_update

    return app


if __name__ == "__main__":
    print("=== GAMBITION: THE COMPLETE STORY ===")
    print("Welcome to Aethelburg, City of Fortune!")
    print("Controls: WASD (move), E (inventory), G (guild), H (market), T (talk)")
    print("Find Chairman Valerius at Syndicate Plaza (North) to begin the story!")
    print("=====================================")
    
    app = setup_world()
    app.run() 