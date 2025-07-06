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
from event_system import random_event, Event as GameEvent

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
    player = FirstPersonController(model='cube', color=color.azure, scale_y=2, collider='box')
    camera.z = -5
    player.speed = 6

    # World HUD (gold)
    hud_gold = Text(parent=camera.ui, text=f"Gold: {player_stats.gold}", x=-0.8, y=0.46, scale=1.5, origin=(0,0))

    # Guild building
    guild_building = Entity(model='cube', color=color.dark_gray, scale=(4,4,4), position=(0,2,15), collider='box')
    guild_prompt = Text(parent=camera.ui, text="Press G to enter Guild", origin=(0,0), y=0.3, x=0, enabled=False)

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

    # Ground and environment
    Entity(model="plane", scale=100, texture="grass", collider="box")
    Sky()

    enemies: list[Entity] = []
    for pos in [(5, 0.5, 5), (-8, 0.5, -3), (12, 0.5, -10)]:
        cube = Entity(model="cube", color=color.red, scale=1, position=pos, collider="box")
        enemies.append(cube)

    state = {
        'combat_ui': None,
        'guild_ui': None,
        'event_ui': None,
        'guild_close': None,
        'event_close': None,
    }

    def update():
        # update_camera()
        # move_player()

        # Skip movement if any overlay active
        if state['combat_ui'] or state['guild_ui'] or state['event_ui']:
            return

        # Update gold HUD visibility and value
        hud_gold.text = f"Gold: {player_stats.gold}"
        hud_gold.enabled = not (state['combat_ui'] or state['guild_ui'] or state['event_ui'])

        # Guild proximity check
        if distance(player.position, guild_building.position) < 5:
            guild_prompt.enabled = not (state['combat_ui'] or state['guild_ui'] or state['event_ui'])
        else:
            guild_prompt.enabled = False

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

                state['combat_ui'] = CombatUI(world_player=player, player_stats=player_stats, on_finish=_combat_done)
                break

    # Register the update function globally (Ursina auto-detects a global named `update`)
    globals()['update'] = update

    # Key presses for guild and event
    def input(key):
        if state['combat_ui'] or state['guild_ui'] or state['event_ui']:
            return

        # Only allow guild entry near building
        if key == 'g' and distance(player.position, guild_building.position) < 6:
            open_guild_ui()
        elif key == 'v':  # e for event taken
            open_event_ui()

    # ------------------------------------------------------------------
    # Overlay helpers
    def open_guild_ui():
        offers: list[CompanionOffer] = generate_guild_offers()

        ui_root = Entity(parent=camera.ui)

        title = Text(parent=ui_root, text="Adventurers Guild", y=.45, scale=2, origin=(0,0))

        buttons: list[Button] = []

        def refresh():
            # clear buttons
            for b in buttons:
                destroy(b)
            buttons.clear()
            start_y = 0.2
            for idx, off in enumerate(offers):
                btn = Button(parent=ui_root, text=f"{off.name} ({off.cost}g)",
                              position=(-0.2, start_y - idx*0.12), scale=(0.4, 0.08))
                btn.offer = off  # type: ignore
                def _click(btn=btn):
                    if btn.offer.recruit(player_stats):
                        offers.remove(btn.offer)
                        refresh()
                btn.on_click = _click
                buttons.append(btn)

            leave = Button(parent=ui_root, text="Leave (Esc)", position=(0.3, -0.4), scale=(0.2,0.08))
            leave.on_click = close_guild
            buttons.append(leave)

        def close_guild():
            for e in buttons:
                destroy(e)
            destroy(title)
            destroy(ui_root)
            state['guild_ui'] = None
            state['guild_close'] = close_guild
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

    # attach input globally
    globals()['input'] = input


# ---------------------------------------------------------------------------


if __name__ == "__main__":
    app = Ursina()
    setup_world()
    app.run() 