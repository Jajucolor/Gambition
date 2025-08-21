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

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from direct.actor.Actor import Actor 

from ursina_combat import CombatUI
from guild import generate_guild_offers, CompanionOffer
from card_shop import generate_shop_offers, ShopOffer

from npc_system import create_random_npc, NPC, DialogueChoice
from texture_manager import apply_world_texture, apply_character_texture

from entities.player import Player


# ---------------------------------------------------------------------------
# World setup using standard Ursina pattern
# ---------------------------------------------------------------------------


def setup_world():
    """Create a massive 7-district world of Aethelburg with proper scale and transitions."""

    global world_map, story_manager, quest_manager, boss_manager, environmental_storytelling, district_renderer, game_state
    global quest_text, quest_progress, quest_objective, district_prompt
    global guild_prompt, market_prompt, npc_prompt, env_prompt, current_quest, quest_complete

    from texture_manager import texture_manager
    texture_manager.load_textures()

    from world_map import WorldMap, DistrictType, EnvironmentalStorytelling, DistrictRenderer
    from quest_system import QuestManager, StoryManager, ActType
    from boss_encounters import BossManager
    from final_choice import EndingManager, EndingType
    from game_integration import GameState
    
    world_map = WorldMap()
    story_manager = StoryManager(world_map)
    quest_manager = QuestManager(world_map, story_manager)
    boss_manager = BossManager(world_map)
    environmental_storytelling = EnvironmentalStorytelling(world_map)
    district_renderer = DistrictRenderer(world_map)
    
    player_stats = Player()

    player_stats.deck.shuffle()
    
    game_state = GameState()
    game_state.player = player_stats 
    game_state.ending_manager.player = player_stats  
    
    quest_manager.start_quest("tutorial")
    game_state.start_game()

    # player = FirstPersonController(collider='box')

    # player_model = Actor(
    # "assets/3.glb"
    # )
    # player_model.reparent_to(player)
    # player_model.set_pos = (0, 0, 0)
    # player_model.set_scale = 1.5
    # player_model.set_h = 180
    # camera.z = -5
    # camera.x = 1.5
    # camera.y = 0.35
    # player.speed = 12  # Faster movement for bigger world
    player = FirstPersonController(collider='box')
    player.speed = 12

    model_holder = Entity(parent=player, position=(0,0,0), scale=1.5)

    player_model = Actor("assets/3.glb")
    player_model.reparent_to(model_holder)
    player_model.enableBlend() 
    model_holder.rotation_y = 180
    target_rotation = model_holder.rotation_y 

    camera.z = -5
    camera.x = 1.5
    camera.y = 0.35

    current_anim = None 

    STEP_HEIGHT = 1              # max height to auto-step
    STEP_CHECK_DISTANCE = 0.6    # how far ahead to check for a step
    STEP_FORWARD_NUDGE = 0.3     # forward nudge when stepping up
    LOW_RAY_HEIGHT = 0.1         # knee/ankle height ray to detect obstacle
    STEP_DURATION = 0.1         # animation time for a smooth step
    is_stepping = False

    def attempt_step_climb(move_input_present: bool):
        nonlocal is_stepping
        if is_stepping:
            return
        if not move_input_present:
            return
        forward_vec = Vec3(camera.forward.x, 0, camera.forward.z).normalized()
        right_vec = Vec3(camera.right.x, 0, camera.right.z).normalized()
        desired = (
            forward_vec * (held_keys['w'] - held_keys['s']) +
            right_vec   * (held_keys['d'] - held_keys['a'])
        )
        if desired.length() <= 0:
            return
        desired = desired.normalized()

        origin_low = player.world_position + Vec3(0, LOW_RAY_HEIGHT, 0)
        low_hit = raycast(origin_low, desired, distance=STEP_CHECK_DISTANCE, ignore=[player], traverse_target=scene)
        if not low_hit.hit:
            return

        origin_high = origin_low + Vec3(0, STEP_HEIGHT, 0)
        high_hit = raycast(origin_high, desired, distance=STEP_CHECK_DISTANCE, ignore=[player], traverse_target=scene)
        if high_hit.hit:
            return

        is_stepping = True
        target_y = player.y + STEP_HEIGHT
        target_x = player.x + desired.x * STEP_FORWARD_NUDGE
        target_z = player.z + desired.z * STEP_FORWARD_NUDGE

        player.animate_y(target_y, duration=STEP_DURATION, curve=curve.in_out_sine)
        player.animate_x(target_x, duration=STEP_DURATION, curve=curve.in_out_sine)
        player.animate_z(target_z, duration=STEP_DURATION, curve=curve.in_out_sine)

        def _end_step():
            nonlocal is_stepping
            is_stepping = False
        invoke(_end_step, delay=STEP_DURATION)

    hud_gold = Text(parent=camera.ui, text=f"Gold: {player_stats.gold}", x=-0.6, y=0.46, scale=1.5, origin=(0,0))
    hud_gold.enabled = False 
    
    district_prompt = Text(parent=camera.ui, text="", x=0, y=0.3, scale=1.5, origin=(0,0), color=color.gold)
    district_prompt.enabled = False
    
    guild_prompt = Text(parent=camera.ui, text="Press f to enter Guild", x=0, y=0.2, scale=1.2, origin=(0,0), color=color.cyan)
    guild_prompt.enabled = False
    
    market_prompt = Text(parent=camera.ui, text="Press f to enter Market", x=0, y=0.15, scale=1.2, origin=(0,0), color=color.green)
    market_prompt.enabled = False
    
    npc_prompt = Text(parent=camera.ui, text="Press f to talk", x=0, y=0.1, scale=1.2, origin=(0,0), color=color.yellow)
    npc_prompt.enabled = False
    
    env_prompt = Text(parent=camera.ui, text="Press R for Audio Log", x=0, y=0.05, scale=1.2, origin=(0,0), color=color.orange)
    env_prompt.enabled = False
    
    current_quest = None
    quest_complete = False

    minimap_panel = Entity(parent=camera.ui, enabled=True)
    minimap_bg = Panel(
        parent=minimap_panel,
        position=(-0.78, -0.42),
        scale=(0.35, 0.35),
        color=color.black
    )
    minimap_border = Entity(parent=minimap_panel, model='quad', color=color.white, scale=(0.36, 0.36), position=minimap_bg.position, z=0.1)
    minimap_enabled = True

    # World scale for minimap conversion
    world_scale = 0.0006
    
    # Map container that will move (all map elements are children of this)
    minimap_world_container = Entity(parent=minimap_panel)
    
    # Grand Terminal (center) - Main hub
    terminal_area = Entity(parent=minimap_world_container, model='quad', color=color.white, scale=(0.045, 0.035), position=(0, 0))
    terminal_building = Entity(parent=minimap_world_container, model='quad', color=color.light_gray, scale=(0.02, 0.015), position=(0, -40 * world_scale))
    
    # Casino District (north) - Gold area
    casino_area = Entity(parent=minimap_world_container, model='quad', color=color.blue, scale=(0.04, 0.04), position=(0, 150 * world_scale))
    casino_building = Entity(parent=minimap_world_container, model='quad', color=color.gold, scale=(0.015, 0.015), position=(0, 150 * world_scale))
    
    # Printing Press Quarter (east) - Industrial brown
    press_area = Entity(parent=minimap_world_container, model='quad', color=color.brown, scale=(0.04, 0.04), position=(150 * world_scale, 0))
    press_building = Entity(parent=minimap_world_container, model='quad', color=color.dark_gray, scale=(0.012, 0.012), position=(150 * world_scale, 0))
    
    # Gilded Promenade (west) - Wealthy yellow
    promenade_area = Entity(parent=minimap_world_container, model='quad', color=color.gold, scale=(0.04, 0.04), position=(-150 * world_scale, 0))
    promenade_building = Entity(parent=minimap_world_container, model='quad', color=color.white, scale=(0.012, 0.015), position=(-150 * world_scale, 0))
    
    # Quarantine Zone (south) - Dangerous red
    quarantine_area = Entity(parent=minimap_world_container, model='quad', color=color.red, scale=(0.04, 0.04), position=(0, -150 * world_scale))
    quarantine_walls = Entity(parent=minimap_world_container, model='quad', color=color.red, scale=(0.035, 0.008), position=(0, -130 * world_scale))
    
    # The Underdeck (below center) - Hidden underground
    underdeck_area = Entity(parent=minimap_world_container, model='quad', color=color.dark_gray, scale=(0.03, 0.03), position=(0, -15 * world_scale))
    underdeck_entrance = Entity(parent=minimap_world_container, model='quad', color=color.black, scale=(0.008, 0.008), position=(0, 30 * world_scale))
    
    # Syndicate Headquarters (elevated center) - Imposing black tower
    hq_platform = Entity(parent=minimap_world_container, model='quad', color=color.gray, scale=(0.025, 0.025), position=(0, 30 * world_scale))
    hq_building = Entity(parent=minimap_world_container, model='quad', color=color.black, scale=(0.012, 0.018), position=(0, 30 * world_scale))
    
    # Connecting paths - Gray lines between districts
    path_terminal_casino = Entity(parent=minimap_world_container, model='quad', color=color.gray, scale=(0.004, 0.06), position=(0, 75 * world_scale))
    path_terminal_press = Entity(parent=minimap_world_container, model='quad', color=color.gray, scale=(0.06, 0.004), position=(75 * world_scale, 0))
    path_terminal_promenade = Entity(parent=minimap_world_container, model='quad', color=color.gray, scale=(0.06, 0.004), position=(-75 * world_scale, 0))
    path_terminal_quarantine = Entity(parent=minimap_world_container, model='quad', color=color.gray, scale=(0.004, 0.06), position=(0, -75 * world_scale))
    
    # Important buildings
    guild_marker = Entity(parent=minimap_world_container, model='quad', color=color.cyan, scale=(0.006, 0.006), position=(20 * world_scale, 20 * world_scale))
    market_marker = Entity(parent=minimap_world_container, model='quad', color=color.orange, scale=(0.006, 0.006), position=(-20 * world_scale, 20 * world_scale))
    
    # Player dot - Stays fixed at center of minimap
    minimap_player_dot = Entity(parent=minimap_panel, model='quad', color=color.lime, scale=(0.008, 0.008), position=minimap_bg.position)

    def _minimap_set_enabled(flag: bool):
        minimap_panel.enabled = flag

    def _minimap_update():
        world_x, world_z = float(player.position.x), float(player.position.z)
        # Move the world container opposite to player movement to keep player centered
        offset_x = -world_x * world_scale
        offset_z = -world_z * world_scale
        minimap_world_container.position = (minimap_bg.position.x + offset_x, minimap_bg.position.y + offset_z)
    
    main_ground = Entity(model='plane', color=color.light_gray, scale=(500, 1, 500), position=(0, 0, 0), texture='white_cube')
    
    terminal_building = Entity(model='cube', color=color.white, scale=(30, 15, 20), position=(0, 7.5, -40), collider='box')
    apply_world_texture(terminal_building, 'building')
    terminal_roof = Entity(model='cube', color=color.dark_gray, scale=(32, 2, 22), position=(0, 16, -40))
    apply_world_texture(terminal_roof, 'metal')
    
    for i in range(-3, 4):
        track = Entity(model='cube', color=color.dark_gray, scale=(80, 0.5, 2), position=(0, 0.25, -20 + i*8), collider='box')
        platform = Entity(model='cube', color=color.gray, scale=(20, 1, 6), position=(0, 0.5, -20 + i*8), collider='box')
    
    for i in range(-4, 5):
        for j in range(-2, 3):
            if abs(i) == 4 or abs(j) == 2: 
                column = Entity(model='cube', color=color.white, scale=(1, 12, 1), position=(i*8, 6, -30 + j*10), collider='box')
    
    clock_tower = Entity(model='cube', color=color.gold, scale=(3, 20, 3), position=(0, 10, -60), collider='box')
    clock_face = Entity(model='sphere', color=color.white, scale=(4, 4, 0.5), position=(0, 10, -60), collider='sphere')
    
    casino_ground = Entity(model='plane', color=color.blue, scale=(80, 1, 80), position=(0, -0.1, 150), texture='white_cube')
    
    casino_path = Entity(model='plane', color=color.gray, scale=(20, 1, 50), position=(0, -0.1, 75), texture='white_cube')
    
    for i in range(-3, 4):
        marker = Entity(model='cube', color=color.cyan, scale=(1, 3, 1), position=(i*20, 1.5, 110))
    
    casino_main = Entity(model='cube', color=color.gold, scale=(25, 12, 25), position=(0, 6, 150), collider='box')
    apply_world_texture(casino_main, 'building')
    casino_roof = Entity(model='cube', color=color.orange, scale=(27, 2, 27), position=(0, 13, 150))
    apply_world_texture(casino_roof, 'metal')
    
    casino_side1 = Entity(model='cube', color=color.magenta, scale=(15, 8, 15), position=(-30, 4, 130), collider='box')
    apply_world_texture(casino_side1, 'building')
    casino_side2 = Entity(model='cube', color=color.red, scale=(15, 8, 15), position=(30, 4, 130), collider='box')
    apply_world_texture(casino_side2, 'building')
    
    for i in range(-5, 6):
        neon = Entity(model='cube', color=color.cyan, scale=(0.2, 8, 0.2), position=(i*8, 4, 170))
    
    press_ground = Entity(model='plane', color=color.brown, scale=(80, 1, 80), position=(150, -0.1, 0), texture='white_cube')
    
    press_path = Entity(model='plane', color=color.gray, scale=(50, 1, 20), position=(75, -0.1, 0), texture='white_cube')
    
    for i in range(-3, 4):
        marker = Entity(model='cube', color=color.orange, scale=(1, 3, 1), position=(110, 1.5, i*20))
    
    press_main = Entity(model='cube', color=color.dark_gray, scale=(20, 10, 20), position=(150, 5, 0), collider='box')
    press_chimney = Entity(model='cube', color=color.gray, scale=(2, 15, 2), position=(150, 12.5, 0))
    
    for i in range(-2, 3):
        workshop = Entity(model='cube', color=color.gray, scale=(8, 6, 8), position=(130 + i*15, 3, 20), collider='box')
    
    # underdeck_entrance = Entity(model='cube', color=color.black, scale=(8, 1, 8), position=(0, -0.5, 30), collider='box')
    underdeck_stairs = Entity(model='cube', color=color.dark_gray, scale=(6, 0.5, 6), position=(0, -1, 30))
    
    ground_underdeck = Entity(model='plane', color=color.dark_gray, scale=(60, 1, 60), position=(0, -15, 0), texture='white_cube')
    
    underdeck_main = Entity(model='cube', color=color.black, scale=(15, 8, 15), position=(0, -11, 0), collider='box')
    underdeck_tunnels = []
    for i in range(-3, 4):
        tunnel = Entity(model='cube', color=color.dark_gray, scale=(5, 4, 5), position=(i*15, -13, 0), collider='box')
        underdeck_tunnels.append(tunnel)
    # Promenade ground (gold area)
    promenade_ground = Entity(model='plane', color=color.gold, scale=(80, 1, 80), position=(-150, -0.1, 0), texture='white_cube')
    
    promenade_path = Entity(model='plane', color=color.gray, scale=(50, 1, 20), position=(-75, -0.1, 0), texture='white_cube')
    
    for i in range(-3, 4):
        marker = Entity(model='cube', color=color.yellow, scale=(1, 3, 1), position=(-110, 1.5, i*20))
    
    promenade_main = Entity(model='cube', color=color.white, scale=(20, 12, 20), position=(-150, 6, 0), collider='box')
    promenade_roof = Entity(model='cube', color=color.gold, scale=(22, 2, 22), position=(-150, 13, 0))
    
    for i in range(-3, 4):
        boutique = Entity(model='cube', color=color.magenta, scale=(6, 4, 6), position=(-170 + i*12, 2, 20), collider='box')
    
    # Quarantine ground (red area)
    quarantine_ground = Entity(model='plane', color=color.red, scale=(80, 1, 80), position=(0, -0.1, -150), texture='white_cube')
    
    quarantine_path = Entity(model='plane', color=color.gray, scale=(20, 1, 50), position=(0, -0.1, -75), texture='white_cube')
    
    for i in range(-3, 4):
        marker = Entity(model='cube', color=color.red, scale=(1, 3, 1), position=(i*20, 1.5, -110))
    
    for i in range(-5, 6):
        wall = Entity(model='cube', color=color.red, scale=(2, 8, 2), position=(i*20, 4, -130), collider='box')
    
    quarantine_main = Entity(model='cube', color=color.red, scale=(15, 6, 15), position=(0, 3, -150), collider='box')
    
    hq_platform = Entity(model='cube', color=color.dark_gray, scale=(50, 2, 50), position=(0, 30, 0), collider='box')
    
    # Headquarters building
    hq_main = Entity(model='cube', color=color.black, scale=(20, 15, 20), position=(0, 37.5, 0), collider='box')
    hq_spire = Entity(model='cube', color=color.dark_gray, scale=(3, 20, 3), position=(0, 50, 0))
    

    guild_building = Entity(model='cube', color=color.dark_gray, scale=(8, 6, 8), position=(20, 3, 20), collider='box')
    apply_world_texture(guild_building, 'building')
    guild_roof = Entity(model='cube', color=color.gray, scale=(9, 1, 9), position=(20, 6.5, 20))
    apply_world_texture(guild_roof, 'metal')
    
    market_building = Entity(model='cube', color=color.brown, scale=(8, 6, 8), position=(-20, 3, 20), collider='box')
    apply_world_texture(market_building, 'wood')
    market_roof = Entity(model='cube', color=color.brown, scale=(9, 1, 9), position=(-20, 6.5, 20))
    apply_world_texture(market_roof, 'wood')


    
    visual_cue_objects = [
        Entity(model='sphere', color=color.magenta, scale=0.5, position=(50, 5, 50)),
        Entity(model='sphere', color=color.magenta, scale=0.5, position=(-50, 5, -50)),
        Entity(model='sphere', color=color.magenta, scale=0.5, position=(0, 5, 120)),
        
        Entity(model='cube', color=color.cyan, scale=(3, 2, 3), position=(80, 1, 50)),
        Entity(model='cube', color=color.cyan, scale=(3, 2, 3), position=(-80, 1, -50)),
        
        Entity(model='sphere', color=color.orange, scale=0.8, position=(0, 10, 0)),
        Entity(model='sphere', color=color.orange, scale=0.8, position=(120, 5, 120)),
        
        Entity(model='cube', color=color.gray, scale=(2, 4, 2), position=(0, 35, 0)),
        Entity(model='cube', color=color.gray, scale=(2, 4, 2), position=(200, 5, 200)),
    ]

    # TODO: Third person camera control --> fixed camera.x 딸깍
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
    #     yaw_rad = math.radians(cam_yaw)
    #     x = math.sin(yaw_rad) * cam_dist
    #     z = math.cos(yaw_rad) * cam_dist
    #     offset = Vec3(x, cam_height, z)
    #     camera.position = player.position + offset
    #     camera.look_at(player.position + Vec3(0, 1, 0))

    # def move_player():
    #     fwd = Vec3(camera.forward.x, 0, camera.forward.z).normalized()
    #     right = Vec3(camera.right.x, 0, camera.right.z).normalized()

    #     move_dir = (fwd * (held_keys['w'] - held_keys['s']) +
    #                 right * (held_keys['d'] - held_keys['a']))

    #     if move_dir.length() > 0:
    #         move_dir = move_dir.normalized() * time.dt * player.speed
    #         player.position += move_dir
    #         player.look_at(player.position + move_dir)

    Entity(model="plane", scale=(1000, 1, 1000), position=(0, -0.1, 0), texture="white_cube", texture_scale = (1000, 1000), collider="box")
    Sky()

    enemies: list[Entity] = []
    for pos in [(20, 0.5, 10), (-18, 0.5, -30), (12, 0.5, -10)]:
        twisted_guard = Entity(
            model="cube", 
            color=color.red, 
            scale=(1.2, 1.5, 1.2), 
            position=pos, 
            collider="box"
        )
        corruption_effect = Entity(
            parent=twisted_guard,
            model="sphere",
            color=color.magenta,
            scale=0.3,
            position=(0, 0.8, 0),
            alpha=0.6
        )
        twisted_guard.name = "Twisted Guard"
        twisted_guard.display_name = "Twisted Guard"
        enemies.append(twisted_guard)

    from npc_system import DialogueManager
    
    dm = DialogueManager(quest_manager, world_map)
    
    npcs: list[tuple[Entity, NPC]] = []
    
    valerius_entity = Entity(model='cube', color=color.gold, scale=(2.5,3.5,2.5), position=(0, 0.5, -50), collider='box')
    valerius = dm.npcs.get('chairman_valerius')
    if valerius:
        npcs.append((valerius_entity, valerius))
    
    elder_entity = Entity(model='cube', color=color.blue, scale=(2,3,2), position=(-15, 0.5, 5), collider='box')
    elder = dm.npcs.get('quest_giver')
    if elder:
        npcs.append((elder_entity, elder))
    
    merchant_entity = Entity(model='cube', color=color.green, scale=(2,3,2), position=(5, 0.5, 10), collider='box')
    merchant = dm.npcs.get('wandering_merchant')
    if merchant:
        npcs.append((merchant_entity, merchant))
    
    intruder_entity = Entity(model='cube', color=color.red, scale=(2,3,2), position=(-8, 0.5, -12), collider='box')
    intruder = dm.npcs.get('suspicious_intruder')
    if intruder:
        npcs.append((intruder_entity, intruder))

    beggar = dm.npcs.get('beggar_mystery')
    beggar_entity = Entity(model='cube', color=color.gray, scale=(2,3,2), position=(10, 0.5, 10), collider='box')
    if beggar:
        npcs.append((beggar_entity, beggar))

    from typing import Dict, Any, Optional, Callable
    
    state: Dict[str, Any] = {
        'combat_ui': None,
        'guild_ui': None,
        'event_ui': None,
        'shop_ui': None,
        'dialogue_ui': None,
        'inv_ui': None,
        'quest_ui': None,
        'guild_close': None,
        'shop_close': None,
        'dialogue_close': None,
        'event_close': None,
        'inv_close': None,
        'quest_close': None,
        'current_npc': None,
        'quest_manager': quest_manager,
        'world_map': world_map,
        'story_manager': story_manager,
        'boss_manager': boss_manager,
        'triggered_visual_cues': [],
        'triggered_world_events': [],
    }



    animation_weights = {}  

    def play_anim(anim_name, blend_speed=5):

        nonlocal current_anim

        if current_anim != anim_name:
            if anim_name not in animation_weights:
                player_model.loop(anim_name)
                animation_weights[anim_name] = 0  
            current_anim = anim_name

        for anim, weight in animation_weights.items():
            if anim == anim_name:
                animation_weights[anim] = min(weight + time.dt * blend_speed, 1)
            else:
                animation_weights[anim] = max(weight - time.dt * blend_speed, 0)
            
            player_model.setControlEffect(anim, animation_weights[anim])

    def lerp_angle(a, b, t):
        diff = (b - a + 180) % 360 - 180
        return a + diff * t

    def update():
        nonlocal target_rotation
        key_vectors = {
            'w': Vec3(0, 0, -1), 
            's': Vec3(0, 0, 1), 
            'a': Vec3(-1, 0, 0), 
            'd': Vec3(1, 0, 0)  
        }

        move_vector = Vec3(0, 0, 0)
        for k, v in key_vectors.items():
            if held_keys[k]:
                move_vector += v

        if move_vector != Vec3(0, 0, 0):
            target_rotation = -math.degrees(math.atan2(move_vector.x, move_vector.z))
            play_anim("walking")
        else:
            play_anim("idle")

        model_holder.rotation_y = lerp_angle(model_holder.rotation_y, target_rotation, time.dt * 10)
            
        if any([state['combat_ui'], state['guild_ui'], state['event_ui'], 
                state['shop_ui'], state['dialogue_ui'], state['inv_ui'], state['quest_ui']]):
            return

        attempt_step_climb(move_vector != Vec3(0, 0, 0))

        hud_gold.text = f"Gold: {player_stats.gold}"
        hud_gold.enabled = state['inv_ui'] is not None

        guild_dist = distance(player.position, guild_building.position)
        market_dist = distance(player.position, market_building.position)
        
        guild_prompt.enabled = guild_dist < 8 and not any([state['guild_ui'], state['shop_ui'], state['dialogue_ui'], state['inv_ui']])
        market_prompt.enabled = market_dist < 8 and not any([state['guild_ui'], state['shop_ui'], state['dialogue_ui'], state['inv_ui']])

        npc_nearby = False
        current_nearby_npc = None
        for npc_entity, npc in npcs:
            if distance(player.position, npc_entity.position) < 5:
                npc_nearby = True
                current_nearby_npc = npc
                break
        
        state['current_npc'] = current_nearby_npc if npc_nearby else None
        
        npc_prompt.enabled = npc_nearby and not any([state['guild_ui'], state['shop_ui'], state['dialogue_ui'], state['inv_ui']])

        env_nearby = False
        for visual_cue in visual_cue_objects:
            if distance(player.position, visual_cue.position) < 3:
                env_nearby = True
                break
        
        env_prompt.enabled = env_nearby and not any([state['guild_ui'], state['shop_ui'], state['dialogue_ui'], state['inv_ui']])

        current_district = world_map.get_current_district()
        if current_district:
            current_district_name = current_district.name
            current_district_type = current_district.district_type
            
            if hasattr(player, 'last_district'):
                if player.last_district != current_district_type:
                    district_prompt.text = f"Entering {current_district_name}"
                    district_prompt.enabled = True
                    import time as pytime
                    if not hasattr(player, 'district_change_time'):
                        player.district_change_time = pytime.time()
                    elif pytime.time() - player.district_change_time > 3:
                        district_prompt.enabled = False
                    
                    game_state.change_district(current_district_type)
            else:
                player.last_district = current_district_type
            
            world_map.player_position = Vec3(player.position.x, player.position.y, player.position.z)
            world_map.player_rotation = player.rotation_y
            
            transition = world_map.is_near_transition(world_map.player_position)
            if transition:
                district_prompt.text = f"Press T to enter {transition['name']}"
                district_prompt.enabled = True
            
            if hasattr(player, 'last_district') and player.last_district != current_district_type:
                active_quests = quest_manager.get_active_quests()
                print(f"DEBUG: Player entered district {current_district_type}")
                print(f"DEBUG: Active quests: {[q.quest_id for q in active_quests]}")
                print(f"DEBUG: Completed quests: {quest_manager.completed_quests}")
                print(f"DEBUG: Available quests: {list(quest_manager.available_quests.keys())}")
                
                for quest in active_quests:
                    if quest.quest_id == "first_investigation" and current_district_type == DistrictType.CASINO_DISTRICT:
                        print(f"DEBUG: Found active first_investigation quest! Updating 'explore_casino' objective.")
                        quest_manager.update_quest_progress("first_investigation", "explore_casino", 1)
                        print(f"DEBUG: Casino quest objective updated successfully!")
                    elif quest.quest_id == "uncovering_truth" and current_district_type == DistrictType.PRINTING_PRESS_QUARTER:
                        quest_manager.update_quest_progress("uncovering_truth", "explore_press_quarter", 1)
                    elif quest.quest_id == "underdeck_investigation" and current_district_type == DistrictType.THE_UNDERDECK:
                        quest_manager.update_quest_progress("underdeck_investigation", "explore_underdeck", 1)
                    elif quest.quest_id == "final_confrontation" and current_district_type == DistrictType.SYNDICATE_HEADQUARTERS:
                        quest_manager.update_quest_progress("final_confrontation", "reach_headquarters", 1)
        else:
            current_district_name = "Unknown Territory"

        _minimap_update()

        for enemy in list(enemies):
            if distance(enemy.position, player.position) < 1.5:
                print("Encounter! Launching Gambition combat…")

                def _combat_done():
                    state['combat_ui'] = None
                    enemy.disable() 
                enemies.remove(enemy)

                try:
                    if any(q.quest_id == "arrival" for q in quest_manager.get_active_quests()):
                        quest_manager.update_quest_progress("arrival", "fight_twisted", 1)
                except Exception:
                    pass
                
                try:
                    active_quests = quest_manager.get_active_quests()
                    for quest in active_quests:
                        if hasattr(quest, 'boss_trigger') and quest.boss_trigger:
                            if enemy.name.lower().startswith(quest.boss_trigger.lower()):
                                print(f"Boss encounter triggered: {enemy.name}")
                                start_boss_combat(quest.boss_trigger)
                                break
                except Exception:
                    pass


                if 'explorer' in player_stats.jokers:
                    import random as _r
                    if _r.random() < 0.3:
                        from card import Card
                        from tarot import TAROT_DEFINITIONS, TarotCard
                        if _r.random() < 0.5:
                            ranks = list('23456789TJQKA')
                            suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
                            rc = Card(ranks[_r.randint(0,12)], suits[_r.randint(0,3)])
                            player_stats.add_card_to_deck(rc)
                            print(f"Explorer found a card: {rc}")
                        else:
                            key = _r.choice(list(TAROT_DEFINITIONS.keys()))
                            td = TAROT_DEFINITIONS[key]
                            player_stats.items.append(TarotCard(key=key, name=td['name'], description=td['description'], on_use=td['on_use']))
                            print(f"Explorer found a tarot: {td['name']}")

                if 'beggar' in player_stats.jokers:
                    if player_stats.beggar_fights_remaining is None:
                        player_stats.beggar_fights_remaining = 5
                    if player_stats.beggar_fights_remaining > 0:
                        take = min(player_stats.gold, 5)
                        player_stats.gold -= take
                        player_stats.beggar_fights_remaining -= 1
                        print(f"The Beggar takes {take} gold. Fights left: {player_stats.beggar_fights_remaining}")
                    if player_stats.beggar_fights_remaining == 0:
                        player_stats.permanent_damage_multiplier = round(player_stats.permanent_damage_multiplier * 1.5, 3)
                        player_stats.jokers.remove('beggar')
                        player_stats.beggar_fights_remaining = None
                        print("The Beggar reveals true power! Permanent damage +50%. Then vanishes.")

                try:
                    dv = Vec3(enemy.position.x - player.position.x, 0, enemy.position.z - player.position.z)
                    approach_dir = dv.normalized() if dv.length() > 0 else Vec3(0, 0, 1)
                except Exception:
                    approach_dir = Vec3(0, 0, 1)

                state['combat_ui'] = CombatUI(
                    world_player=player,
                    player_stats=player_stats,
                    on_finish=_combat_done,
                    enemy_position=enemy.position,
                    approach_dir=approach_dir,
                )
                break

    globals()['update'] = update

    def input(key):
        if key == 'escape':
            if state['guild_close']:
                state['guild_close']()
            elif state['shop_close']:
                state['shop_close']()
            elif state['dialogue_close']:
                state['dialogue_close']()
            elif state['event_close']:
                state['event_close']()
            elif state.get('inv_close'):
                state['inv_close']()
            elif state.get('discovery_ui'):
                state['discovery_ui'].close_discovery()
                state['discovery_ui'] = None
            return

        if key == 'q':
            if state.get('discovery_ui'):
                state['discovery_ui'].close_discovery()
                state['discovery_ui'] = None
            else:
                discovery_ui = _show_discovery_log()
                state['discovery_ui'] = discovery_ui
                print(state['discovery_ui'])
            return

        # if key == 'c':
        #     print("DEBUG: Manually completing current quest objectives...")
        #     try:
        #         active_quests = quest_manager.get_active_quests()
        #         if active_quests:
        #             current_quest = active_quests[0]
        #             print(f"DEBUG: Completing quest: {current_quest.quest_id}")
        #             for objective in current_quest.objectives:
        #                 if not objective.completed:
        #                     quest_manager.update_quest_progress(current_quest.quest_id, objective.id, objective.required_count)
        #             print("DEBUG: Quest objectives completed!")
        #             print(f"DEBUG: Active quests after completion: {[q.quest_id for q in quest_manager.get_active_quests()]}")
        #             print(f"DEBUG: Completed quests: {quest_manager.completed_quests}")
        #         else:
        #             print("DEBUG: No active quests to complete")
        #     except Exception as e:
        #         print(f"DEBUG: Error completing quest: {e}")
        #     return

        # if any([state['combat_ui'], state['guild_ui'], state['event_ui'], 
        #         state['shop_ui'], state['dialogue_ui'], state.get('inv_ui'), state.get('discovery_ui')]):
        #     return

        if key == 'e':
            if state.get('inv_ui'):
                state['inv_close']()
            else:
                open_inventory_ui()
            return

        if any([state['combat_ui'], state['guild_ui'], state['event_ui'], 
                state['shop_ui'], state['dialogue_ui'], state.get('inv_ui'), state.get('discovery_ui')]):
            return

        if key == 'm':
            nonlocal minimap_enabled
            minimap_enabled = not minimap_enabled
            _minimap_set_enabled(minimap_enabled)
            return

        if key == 't':
            transition = world_map.is_near_transition(world_map.player_position)
            if transition:
                target_district = transition['target']
                if world_map.change_district(target_district):
                    new_district = world_map.districts[target_district]
                    if new_district.spawn_points:
                        spawn_point = new_district.spawn_points[0]
                        player.position = Vec3(spawn_point.x, spawn_point.y, spawn_point.z)
                        print(f"Entered {new_district.name}")
                    else:
                        player.position = Vec3(0, 1, 0)
            return

        if key == 'r':
            # Check for nearby environmental content
            _trigger_environmental_content(player.position)
            return

        if key == 'f':
            for cp in checkpoints:
                if distance(player.position, cp['entity'].position) < 5:
                    open_checkpoint_ui(cp)
                    return

        if key == 'f' and distance(player.position, guild_building.position) < 6:
            open_guild_ui()
        elif key == 'f' and distance(player.position, market_building.position) < 6:
            open_market_ui()
        elif key == 'f' and state.get('current_npc') and not state.get('dialogue_ui'):
            current_npc = state['current_npc']
            print(f"Opening dialogue with {current_npc.name}")
            print(f"DEBUG: NPC type: {current_npc.npc_type if hasattr(current_npc, 'npc_type') else 'No npc_type'}")
            print(f"DEBUG: NPC type value: {current_npc.npc_type.value if hasattr(current_npc, 'npc_type') else 'N/A'}")
            
            open_dialogue_ui(current_npc)
            

            

            
            try:
                if current_npc.npc_id == "chairman_valerius":
                    if any(q.quest_id == "meet_chairman" for q in quest_manager.get_active_quests()):
                        print("DEBUG: Meeting Chairman Valerius for first time")
                        quest_manager.update_quest_progress("meet_chairman", "find_valerius", 1)
                        # Give the player The Joker companion
                        player_stats.add_joker('joker')
                        print("✓ The Joker has joined your party!")
                        quest_manager.update_quest_progress("meet_chairman", "receive_joker", 1)
                        print("DEBUG: Meet chairman quest updated")
                    # Return to Valerius after clearing terminal
                    elif any(q.quest_id == "clear_terminal" for q in quest_manager.get_active_quests()):
                        print("DEBUG: Returning to Chairman Valerius after clearing terminal")
                        quest_manager.update_quest_progress("clear_terminal", "return_to_valerius", 1)
                        print("DEBUG: Clear terminal quest completed")
            except Exception as e:
                print(f"DEBUG: Error updating quest progress: {e}")
                pass

       

    def open_guild_ui():
        from jokers import JOKER_DEFINITIONS
        offers: list[CompanionOffer] = generate_guild_offers()

        ui_root = Entity(parent=camera.ui)

        title = Text(parent=ui_root, text="Adventurers Guild", y=.45, scale=2, origin=(0,0))
        companion_limit_text = Text(parent=ui_root, text=f"Companions: {len(player_stats.jokers)}/5", y=.35, scale=1, origin=(0,0))

        buttons: list[Button] = []

        def refresh():
            for b in buttons:
                destroy(b)
            buttons.clear()
            
            companion_limit_text.text = f"Companions: {len(player_stats.jokers)}/5"
            
            if player_stats.jokers:
                current_title = Text(parent=ui_root, text="Current Companions:", y=0.25, x=-0.4, scale=1.2, origin=(0,0))
                buttons.append(current_title) 
                
                for idx, joker_key in enumerate(player_stats.jokers):
                    joker_name = JOKER_DEFINITIONS[joker_key]["name"]
                    farewell_btn = Button(parent=ui_root, text=f"Farewell {joker_name}",
                                        position=(-0.4, 0.15 - idx*0.08), scale=(0.35, 0.06))
                    farewell_btn.joker_key = joker_key  
                    def _farewell(btn=farewell_btn):
                        if player_stats.remove_joker(btn.joker_key):
                            refresh()
                    farewell_btn.on_click = _farewell
                    buttons.append(farewell_btn)
            
            recruit_title = Text(parent=ui_root, text="Recruit New Companions:", y=0.25, x=0.2, scale=1.2, origin=(0,0))
            buttons.append(recruit_title) 
            
            if len(player_stats.jokers) >= 5:
                full_text = Text(parent=ui_root, text="Companion limit reached!", y=0.15, x=0.2, scale=1, origin=(0,0), color=color.red)
                buttons.append(full_text)
            else:
                for idx, off in enumerate(offers):
                    btn = Button(parent=ui_root, text=f"{off.name} ({off.cost}g)",
                                  position=(0.2, 0.15 - idx*0.08), scale=(0.35, 0.06))
                    btn.offer = off 
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
            mouse.locked = True
            player.enabled = True

        mouse.locked = False
        player.enabled = False

        refresh()
        state['guild_ui'] = ui_root
        state['guild_close'] = close_guild

    def open_quest_ui():
        ui_root = Entity(parent=camera.ui)
        title = Text(parent=ui_root, text="Quest Log", y=.45, scale=2, origin=(0,0))
        
        active_quests = quest_manager.get_active_quests()
        available_quests = quest_manager.get_available_quests()
        completed_quests = [q for q in quest_manager.quests.values() if q.status.value == "completed"]
        
        current_act = story_manager.current_act
        act_desc = story_manager.get_act_description(current_act)
        Text(parent=ui_root, text=f"Act: {current_act.value.replace('_', ' ').title()}", y=0.35, scale=1.2, origin=(0,0), color=color.gold)
        Text(parent=ui_root, text=act_desc, y=0.28, scale=0.8, origin=(0,0), color=color.white)
        
        story_progress = story_manager.get_act_progress(current_act)
        if story_progress > 0:
            Text(parent=ui_root, text=f"Act Progress: {story_progress:.0%}", y=0.22, scale=0.9, origin=(0,0), color=color.light_blue)
        
        next_milestone = story_manager.get_next_milestone()
        if next_milestone:
            Text(parent=ui_root, text=f"Next: {next_milestone}", y=0.18, scale=0.8, origin=(0,0), color=color.yellow)
        
        if active_quests:
            Text(parent=ui_root, text="Active Quests:", y=0.18, scale=1.1, origin=(0,0), color=color.cyan)
            start_y = 0.12
            for i, quest in enumerate(active_quests):
                progress = quest.get_progress()
                quest_text = f"{quest.title} - {progress['completed_objectives']}/{len(quest.objectives)} objectives"
                Text(parent=ui_root, text=quest_text, y=start_y - i*0.08, scale=0.9, origin=(0,0), color=color.white)
                
                desc_text = quest.description[:80] + "..." if len(quest.description) > 80 else quest.description
                Text(parent=ui_root, text=desc_text, y=start_y - i*0.08 - 0.04, scale=0.6, origin=(0,0), color=color.light_gray)
                
                for j, objective in enumerate(quest.objectives):
                    if objective.required_count > 1:
                        obj_text = f"  • {objective.description} ({objective.current_count}/{objective.required_count})"
                    else:
                        obj_text = f"  • {objective.description}"
                    
                    if objective.completed:
                        obj_text += " ✓"
                        obj_color = color.green
                    else:
                        obj_color = color.yellow
                    
                    Text(parent=ui_root, text=obj_text, y=start_y - i*0.08 - 0.06 - j*0.04, scale=0.7, origin=(0,0), color=obj_color)
        else:
            Text(parent=ui_root, text="No active quests", y=0.18, scale=1.0, origin=(0,0), color=color.gray)
        
        if available_quests:
            Text(parent=ui_root, text="Available Quests:", y=-0.05, scale=1.1, origin=(0,0), color=color.yellow)
            start_y = -0.11
            for i, quest in enumerate(available_quests):
                Text(parent=ui_root, text=f"• {quest.title}", y=start_y - i*0.06, scale=0.8, origin=(0,0), color=color.white)
                desc_text = quest.description[:60] + "..." if len(quest.description) > 60 else quest.description
                Text(parent=ui_root, text=desc_text, y=start_y - i*0.06 - 0.04, scale=0.6, origin=(0,0), color=color.light_gray)
        
        if completed_quests:
            Text(parent=ui_root, text=f"Completed: {len(completed_quests)}", y=-0.25, scale=0.9, origin=(0,0), color=color.green)
        
        button_row_y = -0.35
        if quest_manager.get_available_quests():
            progress_btn = Button(parent=ui_root, text="Start Next Quest", position=(-0.15, button_row_y), scale=(0.3, 0.08), color=color.green)
            
            def start_next_quest():
                available = quest_manager.get_available_quests()
                if available:
                    next_quest = available[0]
                    if quest_manager.start_quest(next_quest.quest_id):
                        print(f"Started quest: {next_quest.title}")
                        destroy(ui_root)
                        open_quest_ui()
                    else:
                        print(f"Failed to start quest: {next_quest.title}")
            
            progress_btn.on_click = start_next_quest
        
        if quest_manager.get_active_quests():
            debug_btn = Button(parent=ui_root, text="Complete Quest (Debug)", position=(0, button_row_y), scale=(0.3, 0.08), color=color.orange)
            
            def complete_current_quest():
                active = quest_manager.get_active_quests()
                if active:
                    quest = active[0]
                    print(f"Debug: Completing all objectives for {quest.title}")
                    for objective in quest.objectives:
                        if not objective.completed:
                            quest_manager.update_quest_progress(quest.quest_id, objective.id, objective.required_count)
                    destroy(ui_root)
                    open_quest_ui()
            
            debug_btn.on_click = complete_current_quest
        
        # Close button
        close_btn = Button(parent=ui_root, text="Close", position=(0.15, -0.35), scale=(0.2, 0.08))
        
        def close_quest():
            destroy(ui_root)
            state['quest_ui'] = None
            state['quest_close'] = None
            mouse.locked = True
            player.enabled = True
        
        close_btn.on_click = close_quest
        state['quest_ui'] = ui_root
        state['quest_close'] = close_quest
        
        # Lock controls
        mouse.locked = False
        player.enabled = False



    # Inventory UI ---------------------------------------------------
    class GridInventory(Entity):
        def __init__(self, width=6, height=8, **kwargs):
            super().__init__(
                parent=camera.ui,
                model=Quad(radius=.015),
                texture='white_cube',
                texture_scale=(width, height),
                scale=(width*.08, height*.08),
                origin=(-.5,.5),
                position=(-.2,.2),
                color=color.hsv(0, 0, .1, .9),
            )

            self.width = width
            self.height = height
            self.grid = [[None for _ in range(width)] for _ in range(height)]
            
            for key, value in kwargs.items():
                setattr(self, key, value)

        def find_free_spot(self):
            for y in range(self.height):
                for x in range(self.width):
                    if self.grid[y][x] is None:
                        return x, y
            return None, None

        def add_item(self, item_data, item_type='item'):
            """Add an item to the grid inventory"""
            x, y = self.find_free_spot()
            if x is None or y is None:
                print('Inventory full')
                return False

            # Create item icon
            icon = Draggable(
                parent=self,
                model='quad',
                texture=self.get_item_texture(item_data, item_type),
                color=self.get_item_color(item_data, item_type),
                scale_x=1/self.texture_scale[0],
                scale_y=1/self.texture_scale[1],
                origin=(-.5,.5),
                x=x * 1/self.texture_scale[0],
                y=-y * 1/self.texture_scale[1],
                z=-1,
            )
            
            # Store item data
            icon.item_data = item_data
            icon.item_type = item_type
            icon.grid_x = x
            icon.grid_y = y
            
            # Add text overlay for cards (like in combat UI)
            if item_type == 'card':
                # Add rank text (top-left)
                rank_text = Text(
                    parent=icon,
                    text=str(item_data.rank),
                    position=(-0.35, 0.35),
                    scale=0.8,
                    origin=(0, 0),
                    color=color.white if item_data.suit in ['♠', '♣'] else color.red
                )
                
                # Add suit text (bottom-right)
                suit_text = Text(
                    parent=icon,
                    text=str(item_data.suit),
                    position=(0.35, -0.35),
                    scale=1.2,
                    origin=(0, 0),
                    color=color.white if item_data.suit in ['♠', '♣'] else color.red
                )
                
                # Store text references for cleanup
                icon.rank_text = rank_text
                icon.suit_text = suit_text
            
            # Create tooltip
            tooltip_text = self.get_item_tooltip(item_data, item_type)
            icon.tooltip = Tooltip(tooltip_text)
            icon.tooltip.background.color = color.hsv(0,0,0,.8)
            
            # Update grid
            self.grid[y][x] = icon
            
            # Drag and drop functionality
            def drag():
                icon.org_pos = (icon.x, icon.y)
                icon.org_grid_pos = (icon.grid_x, icon.grid_y)
                icon.z = -2

            def drop():
                # Calculate new grid position
                new_x = int((icon.x + (icon.scale_x/2)) * self.width)
                new_y = int((icon.y - (icon.scale_y/2)) * self.height)
                
                # Check bounds
                if new_x < 0 or new_x >= self.width or new_y < 0 or new_y >= self.height:
                    icon.position = icon.org_pos
                    return
                
                # Check if spot is occupied
                if self.grid[new_y][new_x] is not None and self.grid[new_y][new_x] != icon:
                    # Swap positions
                    other_icon = self.grid[new_y][new_x]
                    other_icon.x = icon.org_pos[0]
                    other_icon.y = icon.org_pos[1]
                    other_icon.grid_x = icon.org_grid_pos[0]
                    other_icon.grid_y = icon.org_grid_pos[1]
                    self.grid[icon.org_grid_pos[1]][icon.org_grid_pos[0]] = other_icon
                    
                    # Update grid
                    self.grid[icon.org_grid_pos[1]][icon.org_grid_pos[0]] = other_icon
                    self.grid[new_y][new_x] = icon
                    
                    # Update icon position
                    icon.x = new_x * 1/self.texture_scale[0]
                    icon.y = -new_y * 1/self.texture_scale[1]
                    icon.grid_x = new_x
                    icon.grid_y = new_y
                else:
                    # Move to empty spot
                    self.grid[icon.org_grid_pos[1]][icon.org_grid_pos[0]] = None
                    self.grid[new_y][new_x] = icon
                    icon.x = new_x * 1/self.texture_scale[0]
                    icon.y = -new_y * 1/self.texture_scale[1]
                    icon.grid_x = new_x
                    icon.grid_y = new_y
                
                icon.z = -1

            icon.drag = drag
            icon.drop = drop
            return True

        def get_item_texture(self, item_data, item_type):
            """Get appropriate texture for item type"""
            if item_type == 'card':
                # Use the same texture logic as combat UI
                from texture_manager import texture_manager
                texture = texture_manager.get_card_texture(item_data.suit, item_data.rank)
                return texture if texture else 'card_back'
            elif item_type == 'joker':
                return 'player'  # Use player texture for jokers
            elif item_type == 'tarot':
                return 'card_ace_hearts'  # Use ace texture for tarot cards
            else:
                return 'white_cube'  # Default texture

        def get_item_color(self, item_data, item_type):
            """Get appropriate color for item type"""
            if item_type == 'card':
                # Use white color to show the card texture properly
                return color.white
            elif item_type == 'joker':
                return color.gold
            elif item_type == 'tarot':
                return color.purple
            else:
                return color.white

        def get_item_tooltip(self, item_data, item_type):
            """Get tooltip text for item"""
            try:
                if item_type == 'card':
                    return str(item_data) if item_data else "Unknown Card"
                elif item_type == 'joker':
                    return f"Joker: {item_data}" if item_data else "Unknown Joker"
                elif item_type == 'tarot':
                    if item_data and hasattr(item_data, 'name') and hasattr(item_data, 'description'):
                        return f"{item_data.name}: {item_data.description}"
                    else:
                        return "Unknown Tarot Card"
                elif item_type == 'quest':
                    if item_data and hasattr(item_data, 'name') and hasattr(item_data, 'description'):
                        return f"{item_data.name}: {item_data.description}"
                    else:
                        return "Unknown Quest"
                else:
                    return str(item_data) if item_data else "Unknown Item"
            except Exception:
                return "Unknown Item"

        def clear_grid(self):
            """Clear all items from the grid"""
            for y in range(self.height):
                for x in range(self.width):
                    if self.grid[y][x]:
                        destroy(self.grid[y][x])
                        self.grid[y][x] = None

        def populate_items_tab(self, player_stats):
            """Populate the items tab with player items"""
            self.clear_grid()
            
            # Add tarot cards
            for item in player_stats.items:
                self.add_item(item, 'tarot')
            
            # Add progression info
            self.add_progression_info(player_stats)

        def populate_deck_tab(self, player_stats):
            """Populate the deck tab with cards"""
            self.clear_grid()
            
            # Sort cards by suit and rank before displaying
            sorted_cards = self.sort_cards(player_stats.deck.cards)
            
            # Add cards from deck
            for card in sorted_cards[:self.width * self.height]:
                self.add_item(card, 'card')
        
        def sort_cards(self, cards):
            """Sort cards by suit (Clubs, Diamonds, Hearts, Spades) then by rank"""
            # Define suit order: Clubs, Diamonds, Hearts, Spades
            suit_order = {'♣': 0, 'Clubs': 0, '♦': 1, 'Diamonds': 1, 
                         '♥': 2, 'Hearts': 2, '♠': 3, 'Spades': 3}
            
            # Define rank order using CARD_VALUES from constants
            from constants import CARD_VALUES
            
            def card_sort_key(card):
                # Get suit priority (0-3)
                suit_priority = suit_order.get(card.suit, 999)  # 999 for unknown suits
                # Get rank priority (2-14)
                rank_priority = CARD_VALUES.get(card.rank, 0)
                return (suit_priority, rank_priority)
            
            return sorted(cards, key=card_sort_key)

        def populate_companions_tab(self, player_stats):
            """Populate the companions tab with jokers"""
            self.clear_grid()
            
            # Add jokers
            for joker in player_stats.jokers:
                self.add_item(joker, 'joker')

        def populate_quests_tab(self, quest_manager):
            """Populate the quests tab with quest information"""
            self.clear_grid()
            
            if quest_manager:
                active_quests = quest_manager.get_active_quests()
                if active_quests:
                    for i, quest in enumerate(active_quests[:self.width * self.height]):
                        # Create a quest item representation
                        quest_item = type('QuestItem', (), {
                            'name': quest.title,
                            'description': quest.description[:50] + "..." if len(quest.description) > 50 else quest.description
                        })()
                        self.add_item(quest_item, 'quest')
            else:
                # Show "No active quests" message
                no_quests = type('NoQuests', (), {
                    'name': 'No Active Quests',
                    'description': 'All quests completed or none available'
                })()
                self.add_item(no_quests, 'quest')

        def add_progression_info(self, player_stats):
            """Add progression information to the inventory"""
            # This will be displayed separately from the grid
            pass

    def open_inventory_ui():
        # Ensure items list exists
        if not hasattr(player_stats, 'items'):
            player_stats.items = []  # type: ignore

        ui_root = Entity(parent=camera.ui)
        title = Text(parent=ui_root, text='Inventory', y=.45, scale=2, origin=(0,0))

        # Tab buttons ------------------------------------------------
        tabs = ['Items', 'Deck', 'Companions', 'Quests']
        current_tab = {'name': 'Items'}

        btns: list[Button] = []
        for i, tname in enumerate(tabs):
            bx = -0.3 + i*0.25
            b = Button(parent=ui_root, text=tname, position=(bx, 0.32), scale=(0.22,0.08))
            btns.append(b)
        
        # Create grid inventory
        grid_inventory = GridInventory(width=8, height=10, position=(-0.4, 0.2), scale=(0.5, 0.6))
        
        # Progression info panel (right side)
        progression_panel = Entity(parent=ui_root, position=(0.4, 0))
        
        def update_progression_info():
            # Clear existing progression info
            for child in list(progression_panel.children):
                destroy(child)

            # Add progression information
            Text(parent=progression_panel, text='Character Info', y=0.2, scale=1.5, origin=(0,0), color=color.gold)
            Text(parent=progression_panel, text=f'Level: {player_stats.level}', y=0.15, scale=1.2, origin=(0,0))
            Text(parent=progression_panel, text=f'EXP: {player_stats.exp}/{player_stats.exp_to_next}', y=0.1, scale=1.0, origin=(0,0))
            Text(parent=progression_panel, text=f'Skill Points: {player_stats.skill_points}', y=0.05, scale=1.0, origin=(0,0))
            Text(parent=progression_panel, text=f'Gold: {player_stats.gold}', y=0, scale=1.0, origin=(0,0), color=color.yellow)
            
            # Skill tree buttons
            st_y = -0.1
            def _skill_btn(text, cb, order):
                b = Button(parent=progression_panel, text=text, position=(0, st_y - order*0.1), scale=(0.35, 0.08))
                b.on_click = cb
            
            def spend_point(effect_fn, label):
                if player_stats.skill_points <= 0:
                    print('No skill points available')
                    return
                effect_fn()
                player_stats.skill_points -= 1
                update_progression_info()
            
            _skill_btn('Increase Discards (+1)', lambda: spend_point(lambda: setattr(player_stats, 'max_discards', player_stats.max_discards+1), '+discard'), 0)
            _skill_btn('Increase Joker Slots (+1)', lambda: spend_point(lambda: setattr(player_stats, 'max_jokers', player_stats.max_jokers+1), '+joker'), 1)
            _skill_btn('Unlock Abilities', lambda: spend_point(lambda: setattr(player_stats, 'abilities_unlocked', True), 'abilities'), 2)
            _skill_btn('Increase Attack (+10%)', lambda: spend_point(lambda: setattr(player_stats, 'permanent_damage_multiplier', round(player_stats.permanent_damage_multiplier*1.1, 3)), '+atk'), 3)

        def populate_items():
            grid_inventory.populate_items_tab(player_stats)
            update_progression_info()

        def populate_deck():
            grid_inventory.populate_deck_tab(player_stats)
            update_progression_info()

        def populate_comp():
            grid_inventory.populate_companions_tab(player_stats)
            update_progression_info()

        def populate_quests():
            quest_manager = state.get('quest_manager')
            grid_inventory.populate_quests_tab(quest_manager)
            update_progression_info()

        tab_funcs = {'Items': populate_items, 'Deck': populate_deck, 'Companions': populate_comp, 'Quests': populate_quests}

        def set_tab(t):
            current_tab['name'] = t
            tab_funcs[t]()
        
        for b in btns:
            b.on_click = lambda t=b.text: set_tab(t)  # capture

        # initial tab
        populate_items()

        def close_inv():
            destroy(grid_inventory)
            for e in [*btns, title, progression_panel]:
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
        
        return ui_root

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


    bonfire_prompt = Text(parent=camera.ui, text='Press f to rest', origin=(0,0), y=0.12, x=0, enabled=False)
    checkpoints = [
        {'name':'Grand Terminal Site','entity': Entity(model='cube', color=color.orange, scale=(0.5, 4, 0.5), position=(2,0.5,2), collider='box')},
        {'name':'Casino Site','entity': Entity(model='cube', color=color.orange, scale=(0.5, 4, 0.5), position=(0,0.5,120), collider='box')},
        {'name':'Press Site','entity': Entity(model='cube', color=color.orange, scale=(0.5, 4, 0.5), position=(140,0.5,0), collider='box')},
        {'name':'Promenade Site','entity': Entity(model='cube', color=color.orange, scale=(0.5, 4, 0.5), position=(-140,0.5,0), collider='box')},
        {'name':'Quarantine Site','entity': Entity(model='cube', color=color.orange, scale=(0.5, 4, 0.5), position=(0,0.5,-140), collider='box')},
    ]

    def open_checkpoint_ui(cp):
        player.enabled = False
        mouse.locked = False
        
        ui_root = Entity(parent=camera.ui)
        
        bg = Panel(parent=ui_root, color=color.hsv(0, 0, 0, 0.5), scale=(1.8, 1.2))
        
        title = Text(parent=ui_root, text=cp['name'], y=.35, scale=1.5, origin=(0,0), color=color.gold)
        info = Text(parent=ui_root, text='Rest to heal and set checkpoint, or fast travel to an activated site.', y=.25, origin=(0,0))
        btns: list[Button] = []

        def _rest():
            pos = tuple(cp['entity'].position)
            if pos not in player_stats.activated_checkpoints:
                player_stats.activated_checkpoints.append(pos)  # type: ignore
            player_stats.respawn_position = pos 
            player_stats.hp = player_stats.max_hp
            close()
            print('Rested. Checkpoint set.')

        def _fast_travel():
            if not player_stats.activated_checkpoints:
                return
            start_y = 0.1
            for idx, p in enumerate(player_stats.activated_checkpoints):
                b = Button(parent=ui_root, text=f'Site {idx+1}', position=(-0.2, start_y - idx*0.12), scale=(0.4, 0.08))
                def _go(target=p):
                    player.position = Vec3(*target)
                    close()
                b.on_click = _go
                btns.append(b)

        rest_btn = Button(parent=ui_root, text='Rest', position=(-0.25, -0.2), scale=(0.3,0.08))
        rest_btn.on_click = _rest
        btns.append(rest_btn)

        travel_btn = Button(parent=ui_root, text='Fast Travel', position=(0.05, -0.2), scale=(0.3,0.08))
        travel_btn.on_click = _fast_travel
        btns.append(travel_btn)

        close_btn = Button(parent=ui_root, text='Close', position=(0.3,-0.35), scale=(0.2,0.08))
        btns.append(close_btn)

        def close():
            for b in btns:
                destroy(b)
            destroy(title)
            destroy(info)
            destroy(bg)
            destroy(ui_root)
            player.enabled = True
            mouse.locked = True

        close_btn.on_click = close

    def open_dialogue_ui(npc: NPC):
        npc.reset_dialogue()
        
        ui_root = Entity(parent=camera.ui)
        
        bg = Panel(parent=ui_root, color=color.hsv(0, 0, 0, 0.5), scale=(1.5,1.5))
        
        npc_name = Text(parent=ui_root, text=npc.name, y=0.42, scale=1.8, origin=(0,0))
        
        dialogue_text = Text(parent=ui_root, text='', y=0.25, x=0, scale=1.2, origin=(0,0))
        
        choice_buttons: list[Button] = []
        
        def update_dialogue():
            nonlocal choice_buttons
            for btn in choice_buttons:
                destroy(btn)
            choice_buttons.clear()
            
            current = npc.get_current_dialogue()
            
            if not current:
                print(f"No dialogue available for {npc.name}")
                close_dialogue()
                return
            
            if not current.choices:
                print(f"Dialogue ended with {npc.name}")
                close_dialogue()
                return
            
            if not hasattr(npc, 'dialogue_tree') or not npc.dialogue_tree:
                print(f"No dialogue available for {npc.name}")
                close_dialogue()
                return
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
            
            start_y = 0.0
            for idx, choice in enumerate(current.choices):
                if choice.condition and not choice.condition():
                    continue
                    
                btn = Button(parent=ui_root, text=f"{idx+1}. {choice.text}", 
                           position=(0, start_y - idx*0.12), scale=(0.7, 0.08))
                
                def make_choice_handler(choice_idx=idx):
                    def handle():
                        result = npc.process_choice(choice_idx, player_stats)
                        hud_gold.text = f"Gold: {player_stats.gold}" 
                        
                        if result == 'END':
                            close_dialogue()
                        elif result == 'combat_triggered':
                            close_dialogue()
                            start_npc_combat(npc)
                        elif result != 'INVALID':
                            update_dialogue()
                    return handle
                
                btn.on_click = make_choice_handler()
                choice_buttons.append(btn)
        
        def start_npc_combat(combat_npc):
            """Start combat with the given NPC."""
            print(f"Starting combat with {combat_npc.name}!")
            
            npc_entity = None
            for entity, npc in npcs:
                if npc == combat_npc:
                    npc_entity = entity
                    break
            
            if npc_entity:
                def _npc_combat_done():
                    state['combat_ui'] = None
                    print(f"Defeated {combat_npc.name}!")
                    npcs.remove((npc_entity, combat_npc))
                    destroy(npc_entity)
                    
                    try:
                        if any(q.quest_id == "tutorial" for q in quest_manager.get_active_quests()):
                            if combat_npc.npc_type.value == "hostile": 
                                quest_manager.update_quest_progress("tutorial", "defeat_intruder", 1)
                        elif any(q.quest_id == "clear_terminal" for q in quest_manager.get_active_quests()):
                            quest_manager.update_quest_progress("clear_terminal", "kill_twisted", 1)
                    except Exception:
                        pass
                
                from entities.enemy import Enemy
                npc_enemy = Enemy("Chaos Dealer", 80, 15)
                
                try:
                    dv = Vec3(npc_entity.position.x - player.position.x, 0, npc_entity.position.z - player.position.z)
                    approach_dir = dv.normalized() if dv.length() > 0 else Vec3(0, 0, 1)
                except Exception:
                    approach_dir = Vec3(0, 0, 1)
                
                state['combat_ui'] = CombatUI(
                    world_player=player,
                    player_stats=player_stats,
                    on_finish=_npc_combat_done,
                    enemy_position=npc_entity.position,
                    approach_dir=approach_dir,
                )
        
        def close_dialogue():
            if not state.get('dialogue_ui'):
                return
                
            for btn in choice_buttons:
                destroy(btn)
            destroy(dialogue_text)
            destroy(npc_name)
            destroy(bg)
            destroy(ui_root)
            state['dialogue_ui'] = None
            state['dialogue_close'] = None
            state['current_npc'] = None 
            mouse.locked = True
            player.enabled = True
            print(f"Dialogue with {npc.name} closed, player movement restored")
        npc.met_player = True
        
        update_dialogue()
        
        mouse.locked = False
        player.enabled = False
        
        state['dialogue_ui'] = ui_root
        state['dialogue_close'] = close_dialogue

    def start_npc_combat(npc: NPC):
        """Start combat against a hostile NPC."""
        from entities.enemy import Enemy
        
        def _combat_done():
            state['combat_ui'] = None
            print(f"Defeated {npc.name}!")
            reward = 15
            player_stats.gold += reward
            print(f"You earned {reward} gold!")
        
        if npc.npc_type.value == 'story_npc' and 'intruder' in npc.name.lower():
            npc_enemy = Enemy(npc.name, hp=70, attack=12, defense=2)
        elif npc.npc_type.value == 'merchant':
            npc_enemy = Enemy("Angry " + npc.name, hp=50, attack=8, defense=1)
        else: 
            npc_enemy = Enemy("Corrupted " + npc.name, hp=80, attack=10, defense=3)
        
        npc_position = None
        for npc_entity, npc_data in npcs:
            if npc_data == npc:
                npc_position = npc_entity.position
                break
        
        combat_ui = CombatUI(world_player=player, player_stats=player_stats, on_finish=_combat_done, enemy_position=npc_position, enemy=npc_enemy)
        
        state['combat_ui'] = combat_ui

    def start_boss_combat(boss_encounter):
        """Start combat against a boss encounter."""
        from entities.enemy import Enemy
        
        def _boss_combat_done():
            state['combat_ui'] = None
            print(f"Boss defeated: {boss_encounter.name}!")
            
            if hasattr(boss_encounter, 'rewards'):
                for reward in boss_encounter.rewards:
                    if reward['type'] == 'gold':
                        player_stats.gold += reward['amount']
                        print(f"Earned {reward['amount']} gold!")
                    elif reward['type'] == 'card':
                        player_stats.add_card(reward['card'])
                        print(f"Earned card: {reward['card']}")
                    elif reward['type'] == 'story_progression':
                        story_manager.advance_story(boss_encounter.story_trigger)
                        print(f"Story advanced: {boss_encounter.story_trigger}")
            
            boss_manager.mark_boss_defeated(boss_encounter.id)
        
        boss_enemy = Enemy(
            boss_encounter.name, 
            hp=boss_encounter.hp, 
            attack=boss_encounter.attack, 
            defense=boss_encounter.defense
        )
        
        combat_ui = CombatUI(
            world_player=player, 
            player_stats=player_stats, 
            on_finish=_boss_combat_done, 
            enemy_position=boss_encounter.position, 
            enemy=boss_enemy
        )
        
        state['combat_ui'] = combat_ui

    def _trigger_environmental_content(position: Vec3):
        """Trigger environmental content using the EnvironmentalStorytelling system."""
        current_district = world_map.get_current_district()
        if not current_district:
            return
        

        visual_cues = environmental_storytelling.get_discoverable_content(current_district.district_type)
        for content in visual_cues:
            if content.startswith("visual_cue:"):
                cue_id = content.split(":", 1)[1]
                if environmental_storytelling.trigger_visual_cue(cue_id):
                    print(f"\n=== VISUAL CUE TRIGGERED: {cue_id.replace('_', ' ').title()} ===")
                    visual_cue = environmental_storytelling.visual_cues.get(cue_id)
                    if visual_cue:
                        print(f"👁️ {visual_cue.description}")
                    print("=== END CUE ===\n")
        
        world_events = environmental_storytelling.get_discoverable_content(current_district.district_type)
        for content in world_events:
            if content.startswith("world_event:"):
                event_id = content.split(":", 1)[1]
                if environmental_storytelling.trigger_world_event(event_id):
                    print(f"\n=== WORLD EVENT: {event_id.replace('_', ' ').title()} ===")
                    world_event = environmental_storytelling.world_events.get(event_id)
                    if world_event:
                        print(f"🌍 {world_event.description}")
                    print("=== END EVENT ===\n")

    def _show_discovery_log():
        ui_root = Entity(parent=camera.ui)
        bg = Panel(parent=ui_root, color=color.hsv(0, 0, 0, 0.5), scale=(1.8, 1.2))
        
        title = Text(parent=ui_root, text="DISCOVERY LOG", y=0.4, scale=2, origin=(0,0), color=color.gold)
        
        discoveries = []
        
        gs_cues = getattr(game_state, 'visual_cues_triggered', state.get('triggered_visual_cues', []))
        gs_events = getattr(game_state, 'world_events_triggered', state.get('triggered_world_events', []))
        
        for cue_id in gs_cues:
            if cue_id in environmental_storytelling.visual_cues:
                visual_cue = environmental_storytelling.visual_cues[cue_id]
            discoveries.append(f"👁️ {visual_cue.description} - {visual_cue.district.value.replace('_', ' ').title()}")
        
        for event_id in gs_events:
            if event_id in environmental_storytelling.world_events:
                world_event = environmental_storytelling.world_events[event_id]
            discoveries.append(f"🌍 {world_event.title} - {world_event.district.value.replace('_', ' ').title()}")
        
        active_quests = quest_manager.get_active_quests()
        for quest in active_quests:
            progress = quest.get_progress()
            discoveries.append(f"📋 {quest.title} - {progress['completed_objectives']}/{len(quest.objectives)} objectives")
        
        current_act = story_manager.current_act
        discoveries.append(f"🎭 {current_act.value.replace('_', ' ').title()} - {story_manager.get_act_description(current_act)}")
        
        if not discoveries:
            discoveries = ["No discoveries yet. Explore the world to find content!"]
        
        for i, discovery in enumerate(discoveries):
            y_pos = 0.3 - (i * 0.05)
            if y_pos > -0.4: 
                Text(parent=ui_root, text=discovery, y=y_pos, scale=0.8, origin=(0,0), color=color.white)
        
        def close_discovery():
            destroy(ui_root)
            mouse.locked = True
            player.enabled = True
        
        mouse.locked = False
        player.enabled = False
        
        class DiscoveryUI:
            def __init__(self, ui_root, close_func):
                self.ui_root = ui_root
                self.close_discovery = close_func
        
        return DiscoveryUI(ui_root, close_discovery)



















if __name__ == "__main__":
    app = Ursina()
    
    window.borderless = False 
    window.fullscreen = True 
    window.exit_button.visible = True
    window.fps_counter.enabled = True
    window.title = "Gambition - Card Combat RPG"
    
    window.resizable = True 

    def create_loading_screen():
        ui_root = Entity(parent=camera.ui)
        bg = Panel(parent=ui_root, color=color.rgba(0, 0, 0, 200), scale=(1.8, 1.2))
        Text(parent=ui_root, text='Loading...', y=0.05, scale=2, origin=(0,0), color=color.gold)
        Text(parent=ui_root, text='Please wait', y=-0.05, scale=1, origin=(0,0), color=color.white)
        return ui_root

    loading_ui = create_loading_screen()

    def _bootstrap():
        setup_world()
        destroy(loading_ui)

    invoke(_bootstrap, delay=3)
    app.run() 