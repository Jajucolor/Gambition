"""Prototype 3-D world using Ursina.

Walk around with WASD, space jump.
Touch an enemy cube to launch the existing Gambition CLI combat.
After combat ends (victory), the enemy disappears and you continue exploring.

Requires:
    pip install ursina
"""
from __future__ import annotations

import sys
import math
import random

# Ursina main imports
from ursina import *  # type: ignore
from ursina.prefabs.first_person_controller import FirstPersonController

from ursina_combat import CombatUI
from guild import generate_guild_offers, CompanionOffer
from card_shop import generate_shop_offers, ShopOffer
from event_system import random_event, Event as GameEvent
from npc_system import create_random_npc, NPC

from entities.player import Player


# ---------------------------------------------------------------------------
# World setup using standard Ursina pattern
# ---------------------------------------------------------------------------


def setup_world():
    """Create ground, player, and enemy cubes. Attach update logic."""

    # Gameplay stats
    player_stats = Player()
    player_stats.add_joker('joker')

    # Player entity (visual)
    player = FirstPersonController(model='cube', color=color.azure, collider='box')
    camera.z = -5
    player.speed = 6

    # World HUD (gold)
    hud_gold = Text(parent=camera.ui, text=f"Gold: {player_stats.gold}", x=-0.8, y=0.46, scale=1.5, origin=(0,0))
    hud_gold.enabled = False  # only visible in inventory

    # Guild building
    guild_building = Entity(model='cube', color=color.dark_gray, scale=(4,4,4), position=(0,2,15), collider='box')
    market_building = Entity(model='cube', color=color.brown, scale=(4,4,4), position=(10,2,15), collider='box')
    # Story HUD elements
    story_hud = Text(parent=camera.ui, text="ACT I: THE ANTE | Find Chairman Valerius at Syndicate Plaza (North)", x=-0.8, y=0.4, scale=1, origin=(0,0), color=color.yellow)
    
    guild_prompt = Text(parent=camera.ui, text="Press G to enter Guild", origin=(0,0), y=0.3, x=0, enabled=False)
    market_prompt = Text(parent=camera.ui, text="Press H to enter Market", origin=(0,0), y=0.25, x=0, enabled=False)
    npc_prompt = Text(parent=camera.ui, text="Press T to talk to Chairman Valerius", origin=(0,0), y=0.2, x=0, enabled=False)
    
    # Story introduction
    story_intro = Text(
        parent=camera.ui,
        text="Welcome to Aethelburg, City of Fortune!\nYou are The Ace, a mysterious gambler seeking your mentor 'Maestro'.\nFind Chairman Valerius at Syndicate Plaza (North) to begin your story.",
        origin=(0,0), y=0.0, x=0, enabled=True, scale=1.2, color=color.white
    )
    
    # Hide intro after 10 seconds
    def hide_intro():
        story_intro.enabled = False
    invoke(hide_intro, delay=10)

    # ------------------------------------------------------------------
    # Camera orbit parameters
    # cam_dist = 8
    # cam_yaw = 0.0   # horizontal angle
    # cam_height = 3.0  # vertical offset

    # mouse_sens = 100   # lower is slower

    # def update_camera():
    #     nonlocal cam_yaw, cam_height
    #     if held_keys['right mouse']:
    #         cam_yaw -= mouse.velocity.x * mouse_sens
    #         cam_height += mouse.velocity.y * 10  # adjust speed
    #         cam_height = clamp(cam_height, 1, 10)
    #     # Convert yaw to circular offset, keep flat, then set height
    #     yaw_rad = math.radians(cam_yaw)
    #     x = math.sin(yaw_rad) * cam_dist
    #     z = math.cos(yaw_rad) * cam_dist
    #     offset = Vec3(x, cam_height, z)
    #     camera.position = player.position + offset
    #     camera.look_at(player.position + Vec3(0, 1, 0))

    # ------------------------------------------------------------------
    # # Movement relative to camera forward
    # def move_player():
    #     # forward & right vectors on horizontal plane
    #     fwd = Vec3(camera.forward.x, 0, camera.forward.z).normalized()
    #     right = Vec3(camera.right.x, 0, camera.right.z).normalized()

    #     move_dir = (fwd * (held_keys['w'] - held_keys['s']) +
    #                 right * (held_keys['d'] - held_keys['a']))

    #     if move_dir.length() > 0:
    #         move_dir = move_dir.normalized() * time.dt * player.speed
    #         player.position += move_dir
    #         player.look_at(player.position + move_dir)

    # Enhanced world with story districts
    Entity(model="plane", scale=200, texture="grass", collider="box")
    Sky(color=color.dark_gray)  # Darker sky for corrupted city
    
    # Create district portals (story areas)
    districts = {}
    
    # Grand Terminal (starting area) - Orange (no collider - you can walk through)
    districts['grand_terminal'] = Entity(model='cube', color=color.orange, scale=(8,4,8), position=(0,2,0))
    Text(text="Grand Terminal", parent=districts['grand_terminal'], position=(0,3,0), scale=2, billboard=True, color=color.white)
    
    # Syndicate Plaza (main story) - Gold (no collider - you can walk through)
    districts['syndicate_plaza'] = Entity(model='cube', color=color.gold, scale=(8,4,8), position=(0,2,25))
    Text(text="Syndicate Plaza", parent=districts['syndicate_plaza'], position=(0,3,0), scale=2, billboard=True, color=color.white)
    
    # Casino District - Yellow (no collider - you can walk through)
    districts['casino_district'] = Entity(model='cube', color=color.yellow, scale=(8,4,8), position=(30,2,15))
    Text(text="Casino District", parent=districts['casino_district'], position=(0,3,0), scale=2, billboard=True, color=color.white)
    
    # The Underdeck (companions) - Cyan (no collider - you can walk through)
    districts['underdeck'] = Entity(model='cube', color=color.cyan, scale=(8,2,8), position=(0,-1,-20))
    Text(text="The Underdeck", parent=districts['underdeck'], position=(0,3,0), scale=2, billboard=True, color=color.white)
    
    # Story NPCs
    # Chairman Valerius at Syndicate Plaza
    valerius_npc = Entity(model='cube', color=color.magenta, scale=(2,4,2), position=(0,2,30), collider='box')
    Text(text="Chairman Valerius", parent=valerius_npc, position=(0,3,0), scale=1.8, billboard=True, color=color.white)
    
    # Fortuna crystals (atmosphere)
    for _ in range(15):
        crystal_pos = (
            random.uniform(-60, 60),
            random.uniform(1, 4),
            random.uniform(-60, 60)
        )
        Entity(model='cube', color=color.cyan, scale=(1, random.uniform(2, 6), 1), position=crystal_pos, rotation_y=random.uniform(0, 360))

    enemies: list[Entity] = []
    # Spawn enemies near districts
    enemy_positions = [(8, 0.5, 8), (-12, 0.5, -8), (18, 0.5, -15), (25, 0.5, 10), (-15, 0.5, 20)]
    for pos in enemy_positions:
        cube = Entity(model="cube", color=color.red, scale=(2,2,2), position=pos, collider="box")
        cube.enemy_type = "Twisted Guard"
        Text(text="Twisted Enemy", parent=cube, position=(0,2.5,0), scale=1.2, billboard=True, color=color.white)
        enemies.append(cube)

    # Fixed NPCs at specific locations
    from npc_system import create_quest_giver, create_wandering_merchant, create_suspicious_intruder
    
    npcs: list[tuple[Entity, NPC]] = []
    
    # Village Elder (Quest Giver) - near spawn
    elder = create_quest_giver()
    elder_entity = Entity(model='cube', color=color.blue, scale=(2,3,2), position=(-15, 0.5, 5), collider='box')
    npcs.append((elder_entity, elder))
    
    # Wandering Merchant - between guild and market
    merchant = create_wandering_merchant()
    merchant_entity = Entity(model='cube', color=color.green, scale=(2,3,2), position=(5, 0.5, 10), collider='box')
    npcs.append((merchant_entity, merchant))
    
    # Suspicious Intruder - isolated area
    intruder = create_suspicious_intruder()
    intruder_entity = Entity(model='cube', color=color.red, scale=(2,3,2), position=(-8, 0.5, -12), collider='box')
    npcs.append((intruder_entity, intruder))

    from typing import Dict, Any, Optional, Callable
    
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
    }

    def update():
        # update_camera()
        # move_player()

        # Skip movement if any overlay active
        if state['combat_ui'] or state['guild_ui'] or state['event_ui'] or state['shop_ui'] or state['inv_ui'] or state['dialogue_ui']:
            return

        # Update gold HUD visibility and value
        hud_gold.text = f"Gold: {player_stats.gold}"
        hud_gold.enabled = state['inv_ui'] is not None

        # Guild / Market proximity check
        if distance(player.position, guild_building.position) < 5:
            guild_prompt.enabled = not (state['combat_ui'] or state['guild_ui'] or state['event_ui'] or state['inv_ui'] or state.get('shop_ui') or state.get('dialogue_ui'))
        else:
            guild_prompt.enabled = False

        if distance(player.position, market_building.position) < 5:
            market_prompt.enabled = not (state['combat_ui'] or state['guild_ui'] or state['event_ui'] or state['inv_ui'] or state.get('shop_ui') or state.get('dialogue_ui'))
        else:
            market_prompt.enabled = False

        # Story NPC proximity check (Valerius)
        valerius_nearby = distance(player.position, valerius_npc.position) < 8
        
        # NPC proximity check
        closest_npc = None
        for npc_entity, npc_data in npcs:
            if distance(player.position, npc_entity.position) < 3:
                closest_npc = (npc_entity, npc_data)
                break
        
        # Show NPC prompt for either story NPC or regular NPCs
        if (valerius_nearby or closest_npc) and not any(state[k] for k in ['combat_ui', 'guild_ui', 'event_ui', 'inv_ui', 'shop_ui', 'dialogue_ui']):
            npc_prompt.enabled = True
            if closest_npc:
                state['current_npc'] = closest_npc[1]
            else:
                state['current_npc'] = 'valerius'  # Story NPC
        else:
            npc_prompt.enabled = False
            state['current_npc'] = None

        for enemy in list(enemies):
            if distance(enemy.position, player.position) < 1.5:
                print("Encounter! Launching Gambition combat…")

                def _combat_done():
                    state['combat_ui'] = None
                    enemy.disable()  # ensure enemy stays gone
                enemies.remove(enemy)

                # Reward coins
                reward = random.randint(8, 15)
                player_stats.gold += reward
                print(f"You earned {reward} gold!")

                state['combat_ui'] = CombatUI(world_player=player, player_stats=player_stats, on_finish=_combat_done, enemy_position=enemy.position)
                break

    # Register the update function globally (Ursina auto-detects a global named `update`)
    globals()['update'] = update

    # Key presses for guild and event
    def input(key):
        # First, allow ESC to close any UI overlays
        if key == 'escape':
            if state.get('guild_close'):
                state['guild_close'](); return
            if state.get('event_close'):
                state['event_close'](); return
            if state.get('inv_close'):
                state['inv_close'](); return
            if state.get('shop_close'):
                state['shop_close'](); return
            if state.get('dialogue_close'):
                state['dialogue_close'](); return

        # Block other keys when overlay present
        if state['combat_ui'] or state['guild_ui'] or state['event_ui'] or state['inv_ui'] or state['shop_ui'] or state['dialogue_ui']:
            return

        # Only allow guild entry near building
        if key == 'g' and distance(player.position, guild_building.position) < 6:
            open_guild_ui()
        elif key == 'h' and distance(player.position, market_building.position) < 6:
            open_market_ui()
        elif key == 't' and state.get('current_npc'):
            if state['current_npc'] == 'valerius':
                open_valerius_dialogue()
            else:
                open_dialogue_ui(state['current_npc'])
        elif key == 'v':  # event overlay
            open_event_ui()
        elif key == 'e':  # inventory
            open_inventory_ui()

    # ------------------------------------------------------------------
    # Overlay helpers
    def open_guild_ui():
        from jokers import JOKER_DEFINITIONS
        offers: list[CompanionOffer] = generate_guild_offers()

        ui_root = Entity(parent=camera.ui)

        title = Text(parent=ui_root, text="Adventurers Guild", y=.45, scale=2, origin=(0,0))
        companion_limit_text = Text(parent=ui_root, text=f"Companions: {len(player_stats.jokers)}/5", y=.35, scale=1, origin=(0,0))

        buttons: list[Button] = []

        def refresh():
            # clear buttons
            for b in buttons:
                destroy(b)
            buttons.clear()
            
            # Update companion count
            companion_limit_text.text = f"Companions: {len(player_stats.jokers)}/5"
            
            # Show current companions section
            if player_stats.jokers:
                current_title = Text(parent=ui_root, text="Current Companions:", y=0.25, x=-0.4, scale=1.2, origin=(0,0))
                buttons.append(current_title)  # Add to buttons list for cleanup
                
                for idx, joker_key in enumerate(player_stats.jokers):
                    joker_name = JOKER_DEFINITIONS[joker_key]["name"]
                    farewell_btn = Button(parent=ui_root, text=f"Farewell {joker_name}",
                                        position=(-0.4, 0.15 - idx*0.08), scale=(0.35, 0.06))
                    farewell_btn.joker_key = joker_key  # type: ignore
                    def _farewell(btn=farewell_btn):
                        if player_stats.remove_joker(btn.joker_key):
                            refresh()
                    farewell_btn.on_click = _farewell
                    buttons.append(farewell_btn)
            
            # Show recruitment section
            recruit_title = Text(parent=ui_root, text="Recruit New Companions:", y=0.25, x=0.2, scale=1.2, origin=(0,0))
            buttons.append(recruit_title)  # Add to buttons list for cleanup
            
            if len(player_stats.jokers) >= 5:
                full_text = Text(parent=ui_root, text="Companion limit reached!", y=0.15, x=0.2, scale=1, origin=(0,0), color=color.red)
                buttons.append(full_text)
            else:
                for idx, off in enumerate(offers):
                    btn = Button(parent=ui_root, text=f"{off.name} ({off.cost}g)",
                                  position=(0.2, 0.15 - idx*0.08), scale=(0.35, 0.06))
                    btn.offer = off  # type: ignore
                    def _click(btn=btn):
                        if btn.offer.recruit(player_stats):
                            offers.remove(btn.offer)
                            hud_gold.text = f"Gold: {player_stats.gold}"
                            refresh()
                    btn.on_click = _click
                    buttons.append(btn)

            leave = Button(parent=ui_root, text="Leave", position=(0, -0.4), scale=(0.2,0.08))
            leave.on_click = close_guild
            buttons.append(leave)

        def close_guild():
            for e in buttons:
                destroy(e)
            destroy(title)
            destroy(companion_limit_text)
            destroy(ui_root)
            state['guild_ui'] = None
            state['guild_close'] = None
            # Re-lock mouse & re-enable player controls
            mouse.locked = True
            player.enabled = True

        # Unlock mouse & stop player movement while shopping
        mouse.locked = False
        player.enabled = False

        refresh()
        state['guild_ui'] = ui_root
        state['guild_close'] = close_guild

    # Event UI -------------------------------------------------------
    def open_event_ui():
        ev: GameEvent = random_event()

        ui_root = Entity(parent=camera.ui)
        title = Text(parent=ui_root, text="Mysterious Event", y=.45, scale=2, origin=(0,0))
        desc = Text(parent=ui_root, text=ev.description, y=0.3, x=-0.4, scale=1, origin=(0,0))

        btns: list[Button] = []
        start_y = 0.1
        for idx, (text_choice, action) in enumerate(ev.choices):
            btn = Button(parent=ui_root, text=text_choice, position=(-0.25, start_y - idx*0.12), scale=(0.5,0.08))
            def _click(act=action):
                act(player_stats)
                hud_gold.text = f"Gold: {player_stats.gold}"
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
            state['event_close'] = close_event
            mouse.locked = True
            player.enabled = True

        state['event_ui'] = ui_root

    # Inventory UI ---------------------------------------------------
    def open_inventory_ui():
        # Ensure items list exists
        if not hasattr(player_stats, 'items'):
            player_stats.items = []  # type: ignore

        ui_root = Entity(parent=camera.ui)
        title = Text(parent=ui_root, text='Inventory', y=.45, scale=2, origin=(0,0))

        # Tab buttons ------------------------------------------------
        tabs = ['Items', 'Deck', 'Companions']
        current_tab = {'name': 'Items'}

        btns: list[Button] = []
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
            # Text(parent=content_parent, text=f'Gold: {player_stats.gold}', x=-0.35, y=0.18, scale=1.2, origin=(0,0))
            Text(parent=content_parent, text='Items:', x=0, y=0.10, scale=1.2, origin=(0,0))
            if player_stats.items:  # type: ignore
                for idx, it in enumerate(player_stats.items):  # type: ignore
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
            b.on_click = lambda t=b.text: set_tab(t)  # capture

        # initial tab
        populate_items()

        # Close hint
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

        # lock mouse, stop movement
        mouse.locked = False
        player.enabled = False

        state['inv_ui'] = ui_root
        state['inv_close'] = close_inv

    # attach input globally
    globals()['input'] = input

    # Market UI ------------------------------------------------------
    def open_market_ui():
        offers: list[ShopOffer] = generate_shop_offers()

        ui_root = Entity(parent=camera.ui)
        title = Text(parent=ui_root, text='Card Market', y=.45, scale=2, origin=(0,0))

        btns: list[Button] = []

        def refresh():
            for b in btns:
                destroy(b)
            btns.clear()
            start_y = 0.25
            for idx, off in enumerate(offers):
                b = Button(parent=ui_root, text=f"{off.name} ({off.cost}g)", position=(-0.25, start_y-idx*0.12), scale=(0.5,0.08))
                def _buy(btn=b, offer=off):
                    if offer.buy(player_stats):
                        offers.remove(offer)
                        hud_gold.text = f"Gold: {player_stats.gold}"
                        refresh()
                b.on_click = _buy
                btns.append(b)

            leave = Button(parent=ui_root, text='Leave (Esc)', position=(0.3,-0.4), scale=(0.2,0.08))
            leave.on_click = close_market
            btns.append(leave)

        def close_market():
            for b in btns:
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

    # Story Dialogue UI ---------------------------------------------
    def open_valerius_dialogue():
        """Simple story dialogue with Chairman Valerius"""
        ui_root = Entity(parent=camera.ui)
        
        # Background
        bg = Panel(parent=ui_root, color=color.rgba(0,0,0,180), scale=(1.5,1.5))
        
        # NPC name
        npc_name = Text(parent=ui_root, text="Chairman Valerius", y=0.42, scale=1.8, origin=(0,0), color=color.gold)
        
        # Dialogue text
        dialogue_text = Text(
            parent=ui_root, 
            text="Ah, you must be the one who caused such a stir at the Grand Terminal.\nYour unique talents have not gone unnoticed. I am Chairman Valerius,\nand I believe you may be exactly what Aethelburg needs in these dark times.", 
            y=0.15, x=-0.4, scale=1.1, origin=(0,0)
        )
        
        # Response options
        option1 = Button(parent=ui_root, text="Tell me about this 'Dissonance'", position=(-0.3, -0.1), scale=(0.6,0.08))
        option2 = Button(parent=ui_root, text="I'm looking for someone called Maestro", position=(-0.3, -0.2), scale=(0.6,0.08))
        option3 = Button(parent=ui_root, text="How can I help?", position=(-0.3, -0.3), scale=(0.6,0.08))
        
        def choice1():
            story_hud.text = "ACT I: THE ANTE | Learned about the Dissonance plague"
            print("STORY: You learned about the Fortuna Dissonance corrupting the city")
            close_valerius_dialogue()
        
        def choice2():
            story_hud.text = "ACT I: THE ANTE | Valerius claims Maestro disappeared"
            print("STORY: Valerius says Maestro became obsessed with conspiracy theories")
            close_valerius_dialogue()
        
        def choice3():
            story_hud.text = "ACT I: THE ANTE | Accepted mission from Valerius"
            print("STORY: Valerius wants you to find the 'Heart of Chaos' and purify it")
            close_valerius_dialogue()
        
        option1.on_click = choice1
        option2.on_click = choice2
        option3.on_click = choice3
        
        def close_valerius_dialogue():
            destroy(bg)
            destroy(npc_name)
            destroy(dialogue_text)
            destroy(option1)
            destroy(option2)
            destroy(option3)
            destroy(ui_root)
            state['dialogue_ui'] = None
            state['dialogue_close'] = None
            mouse.locked = True
            player.enabled = True
        
        # Lock controls
        mouse.locked = False
        player.enabled = False
        state['dialogue_ui'] = ui_root
        state['dialogue_close'] = close_valerius_dialogue

    # Dialogue UI ----------------------------------------------------
    def open_dialogue_ui(npc: NPC):
        ui_root = Entity(parent=camera.ui)
        
        # Semi-transparent background
        bg = Panel(parent=ui_root, color=color.rgba(0,0,0,180), scale=(1.5,1.5))
        
        # NPC name and portrait area
        npc_name = Text(parent=ui_root, text=npc.name, y=0.42, scale=1.8, origin=(0,0))
        
        # Dialogue text area
        dialogue_text = Text(parent=ui_root, text='', y=0.25, x=-0.4, scale=1.2, origin=(0,0))
        
        # Choice buttons container
        choice_buttons: list[Button] = []
        
        def update_dialogue():
            nonlocal choice_buttons
            # Clear old buttons
            for btn in choice_buttons:
                destroy(btn)
            choice_buttons.clear()
            
            # Get current dialogue
            current = npc.get_current_dialogue()
            # Manual word wrap for long text
            wrapped_text = current.text
            if len(wrapped_text) > 60:
                words = wrapped_text.split(' ')
                lines = []
                current_line = ''
                for word in words:
                    if len(current_line + word) > 60:
                        lines.append(current_line.strip())
                        current_line = word + ' '
                    else:
                        current_line += word + ' '
                if current_line:
                    lines.append(current_line.strip())
                wrapped_text = '\n'.join(lines)
            dialogue_text.text = wrapped_text
            
            # Create choice buttons
            start_y = 0.0
            for idx, choice in enumerate(current.choices):
                # Check if choice should be shown
                if choice.requirement and not choice.requirement(player_stats):
                    continue
                    
                btn = Button(parent=ui_root, text=f"{idx+1}. {choice.text}", 
                           position=(-0.35, start_y - idx*0.12), scale=(0.7, 0.08))
                
                def make_choice_handler(choice_idx=idx):
                    def handle():
                        result = npc.process_choice(choice_idx, player_stats)
                        hud_gold.text = f"Gold: {player_stats.gold}"  # update gold display
                        
                        if result == 'END':
                            close_dialogue()
                        elif result == 'combat_triggered':
                            close_dialogue()
                            # Trigger combat with hostile NPC
                            start_npc_combat(npc)
                        elif result != 'INVALID':
                            update_dialogue()  # Continue conversation
                    return handle
                
                btn.on_click = make_choice_handler()
                choice_buttons.append(btn)
        
        def close_dialogue():
            for btn in choice_buttons:
                destroy(btn)
            destroy(dialogue_text)
            destroy(npc_name)
            destroy(bg)
            destroy(ui_root)
            state['dialogue_ui'] = None
            state['dialogue_close'] = None
            mouse.locked = True
            player.enabled = True
        
        # Initial dialogue setup
        update_dialogue()
        
        # Lock controls
        mouse.locked = False
        player.enabled = False
        
        state['dialogue_ui'] = ui_root
        state['dialogue_close'] = close_dialogue

    # NPC Combat helper ---------------------------------------------- 
    def start_npc_combat(npc: NPC):
        """Start combat against a hostile NPC."""
        from entities.enemy import Enemy
        
        def _combat_done():
            state['combat_ui'] = None
            print(f"Defeated {npc.name}!")
            # Reward for defeating hostile NPC
            reward = 15
            player_stats.gold += reward
            print(f"You earned {reward} gold!")
        
        # Create enemy stats based on NPC
        if npc.npc_type == 'intruder':
            npc_enemy = Enemy(npc.name, hp=70, attack=12, defense=2)
        elif npc.npc_type == 'merchant':
            npc_enemy = Enemy("Angry " + npc.name, hp=50, attack=8, defense=1)
        else:  # quest_giver or other
            npc_enemy = Enemy("Corrupted " + npc.name, hp=80, attack=10, defense=3)
        
        # Find the NPC's world position
        npc_position = None
        for npc_entity, npc_data in npcs:
            if npc_data == npc:
                npc_position = npc_entity.position
                break
        
        # Start combat with the NPC as enemy at their location
        combat_ui = CombatUI(world_player=player, player_stats=player_stats, on_finish=_combat_done, enemy_position=npc_position, enemy=npc_enemy)
        
        state['combat_ui'] = combat_ui


# ---------------------------------------------------------------------------


if __name__ == "__main__":
    app = Ursina()
    setup_world()
    app.run() 