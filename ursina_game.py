"""Prototype 3-D world using Ursina.

Walk around with WASD, space jump.
Touch an enemy cube to launch the existing Gambition CLI combat.
After combat ends (victory), the enemy disappears and you continue exploring.

Requires:
    pip install ursina
"""
from __future__ import annotations

import sys
from threading import Thread
import math

# Ursina main imports
from ursina import *  # type: ignore
from ursina.prefabs.first_person_controller import FirstPersonController

# Import existing combat loop
from game import play_game  # CLI combat; blocks main thread


# ---------------------------------------------------------------------------
# Threaded combat wrapper
# ---------------------------------------------------------------------------


class CombatThread(Thread):
    """Runs the CLI combat loop in a background thread so Ursina UI does not freeze."""

    def __init__(self):
        super().__init__(daemon=True)
        self.result: bool | None = None  # True if player won

    def run(self):
        try:
            play_game()
            self.result = True
        except SystemExit:
            # play_game ends with sys.exit()
            self.result = True
        except Exception as e:
            print("Combat error:", e)
            self.result = False


# ---------------------------------------------------------------------------
# World setup using standard Ursina pattern
# ---------------------------------------------------------------------------


def setup_world():
    """Create ground, player, and enemy cubes. Attach update logic."""

    # Player entity
    player = FirstPersonController(model='cube', color=color.azure, scale_y=2, collider='box')
    camera.z = -5
    player.speed = 6

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
    # Movement relative to camera forward
    def move_player():
        # forward & right vectors on horizontal plane
        fwd = Vec3(camera.forward.x, 0, camera.forward.z).normalized()
        right = Vec3(camera.right.x, 0, camera.right.z).normalized()

        move_dir = (fwd * (held_keys['w'] - held_keys['s']) +
                    right * (held_keys['d'] - held_keys['a']))

        if move_dir.length() > 0:
            move_dir = move_dir.normalized() * time.dt * player.speed
            player.position += move_dir
            player.look_at(player.position + move_dir)

    # Ground and environment
    Entity(model="plane", scale=100, texture="grass", collider="box")
    Sky()

    enemies: list[Entity] = []
    for pos in [(5, 0.5, 5), (-8, 0.5, -3), (12, 0.5, -10)]:
        cube = Entity(model="cube", color=color.red, scale=1, position=pos, collider="box")
        enemies.append(cube)

    state = {'combat_thread': None}

    def update():
        # update_camera()
        move_player()

        ct: CombatThread | None = state['combat_thread']
        if ct and not ct.is_alive():
            # combat finished
            state['combat_thread'] = None
            player.visible = True
            print("Combat finished, continue exploring.")
            return

        if state['combat_thread']:
            return

        for enemy in list(enemies):
            if distance(enemy.position, player.position) < 1.5:
                print("Encounter! Launching Gambition combat…")
                player.visible = False  # hide during combat
                ct2 = CombatThread()
                ct2.start()
                state['combat_thread'] = ct2
                enemy.disable()
                enemies.remove(enemy)
                break

    # Register the update function globally (Ursina auto-detects a global named `update`)
    globals()['update'] = update


# ---------------------------------------------------------------------------


if __name__ == "__main__":
    app = Ursina()
    setup_world()
    app.run() 