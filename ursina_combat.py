from ursina import *  # type: ignore
from typing import Any, cast

from entities.player import Player
from encounter import EncounterManager
from entities.enemy import Enemy

# Overlay sizes (viewport units −1..1)
CARD_W, CARD_H = .15, .25
BUTTON_Y = -.65
ENEMY_DELAY = 0.6  # seconds before enemy strikes (visual anticipation)

# Helper
_fmt = lambda v: int(v)


class CombatUI(Entity):
    """3-D battle overlay reusing core logic and showing detailed stats."""

    def __init__(self, *, world_player: Entity, player_stats: Player, on_finish):
        super().__init__()
        self.world_player = world_player
        self.on_finish = on_finish

        # Core state
        self.player = player_stats
        self.encounters = EncounterManager(stages=1)
        self.enemy: Enemy | None = self.encounters.next_enemy()

        self.selected: list[int] = []
        self.hand_buttons: list[Button] = []
        self.action_buttons: list[Button] = []

        # Last turn summary
        self.last_damage_dealt = 0
        self.last_damage_taken = 0
        self.last_hand: str = ''

        # Flag to block inputs during enemy wind-up
        self.in_enemy_phase: bool = False

        # Build scene & UI
        self.lock_world()
        self._setup_scene_models()
        self._setup_ui()
        self.start_player_turn()

    # ------------------------------------------------------------------
    # Scene helpers
    # ------------------------------------------------------------------
    def lock_world(self):
        if hasattr(self.world_player, 'enabled'):
            self.world_player.enabled = False
        self.world_player.visible = False

    def unlock_world(self):
        if hasattr(self.world_player, 'enabled'):
            self.world_player.enabled = True
        self.world_player.visible = True

    def _setup_scene_models(self):
        self.player_model = Entity(model='cube', color=cast(Any, color.azure), position=(-2, 0.75, 4), scale=1.5)
        self.enemy_model = Entity(model='cube', color=cast(Any, color.red), position=(2, 0.75, 4), scale=1.5)
        camera.position = (0, 3, 7)
        camera.look_at(Vec3(0, 1, 4))

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _setup_ui(self):
        self.ui_root = Entity(parent=camera.ui)
        self.status_text = Text(parent=self.ui_root, y=.45, scale=2, origin=(0, 0))

        self.txt_player = Text(parent=self.ui_root, x=-0.48, y=0.45, scale=1.5, origin=(0, 0))
        self.txt_enemy = Text(parent=self.ui_root, x=0.05, y=0.45, scale=1.5, origin=(0, 0))
        self.txt_gold = Text(parent=self.ui_root, x=-0.48, y=0.38, scale=1.2, origin=(0, 0))
        self.txt_jokers = Text(parent=self.ui_root, x=-0.48, y=0.31, scale=1, origin=(0, 0))
        self.txt_last = Text(parent=self.ui_root, x=-0.48, y=0.24, scale=1, origin=(0, 0))

        self._update_stats()

    def _refresh_hand_ui(self):
        for b in self.hand_buttons:
            destroy(b)
        self.hand_buttons.clear()

        for idx, card in enumerate(self.player.hand):
            x = (-.5 + idx * CARD_W * 1.2)
            btn = Button(parent=self.ui_root, text=f'{card.rank}{card.suit[0]}', color=cast(Any, color.gray),
                         position=(x, -0.4), scale=(CARD_W, CARD_H))
            btn.card_index = idx  # type: ignore

            def _on_click(btn=btn):
                ci = btn.card_index  # type: ignore
                if ci in self.selected:
                    self.selected.remove(ci)
                    btn.color = cast(Any, color.gray)
                else:
                    if len(self.selected) >= 5:
                        # Deselect the earliest selected card
                        earliest = self.selected.pop(0)
                        # Find its button and revert color
                        for hb in self.hand_buttons:
                            if getattr(hb, 'card_index', None) == earliest:
                                hb.color = cast(Any, color.gray)
                                break
                    self.selected.append(ci)
                    btn.color = cast(Any, color.yellow)
            btn.on_click = _on_click
            self.hand_buttons.append(btn)

        # Actions
        for b in self.action_buttons:
            destroy(b)
        self.action_buttons.clear()

        def _mk(label: str, ox: float, cb):
            b = Button(parent=self.ui_root, text=label, position=(ox, BUTTON_Y), scale=.1)
            b.on_click = cb
            self.action_buttons.append(b)

        _mk('[A] Attack', -.3, self.attack_selected)
        _mk('[D] Discard', 0, self.discard_selected)
        _mk('[E] End Turn', .3, self.end_turn)

        self._update_stats()

    # ------------------------------------------------------------------
    # Turn flow
    # ------------------------------------------------------------------
    def start_player_turn(self):
        self.player.draw_cards()
        self.selected.clear()
        self._refresh_hand_ui()

    def attack_selected(self):
        if not self.selected:
            return
        dmg, hand_type = self.player.form_hand_and_attack(self.selected)
        if hand_type and self.enemy:
            self.enemy.take_damage(dmg)
            self.last_damage_dealt = _fmt(dmg)
            self.last_hand = hand_type
            self.last_damage_taken = 0
        self.selected.clear()
        self._refresh_hand_ui()
        if self.enemy and not self.enemy.is_alive():
            self._finish_combat(True)
        else:
            self.enemy_turn()

    def discard_selected(self):
        if not self.selected:
            return
        self.player.discard_cards(self.selected)
        self.selected.clear()
        self._refresh_hand_ui()

    def end_turn(self):
        self.selected.clear()
        self.enemy_turn()

    def enemy_turn(self):
        """Schedule the enemy's counter-attack after a short delay."""
        if self.enemy and self.enemy.is_alive():
            self.in_enemy_phase = True
            invoke(self._enemy_attack, delay=ENEMY_DELAY)
        else:
            self.start_player_turn()

    def _enemy_attack(self):
        if not (self.enemy and self.enemy.is_alive()):
            self.in_enemy_phase = False
            self.start_player_turn()
            return

        self.enemy.attack_player(self.player)
        self.last_damage_taken = self.enemy.attack_value
        self.last_damage_dealt = 0
        self.last_hand = ''
        self._update_stats()

        self.in_enemy_phase = False
        if not self.player.is_alive():
            self._finish_combat(False)
        else:
            self.start_player_turn()

    # ------------------------------------------------------------------
    def input(self, key):
        if self.in_enemy_phase:
            return  # ignore inputs while enemy is winding up

        if key == 'a':
            self.attack_selected()
        elif key == 'd':
            self.discard_selected()
        elif key == 'e':
            self.end_turn()

    # ------------------------------------------------------------------
    # Cleanup & HUD
    # ------------------------------------------------------------------
    def _finish_combat(self, player_won: bool):
        self.status_text.text = 'Victory!' if player_won else 'Defeat…'
        invoke(self._cleanup, delay=1.5)

    def _cleanup(self):
        destroy(self.player_model)
        destroy(self.enemy_model)
        destroy(self.ui_root)
        self.unlock_world()
        if callable(self.on_finish):
            self.on_finish()
        destroy(self)

    def _update_stats(self):
        self.txt_player.text = f'HP: {self.player.hp}/{self.player.max_hp}'
        self.txt_enemy.text = f'{self.enemy.name} HP {self.enemy.hp}' if self.enemy else ''
        self.txt_gold.text = f'Gold: {self.player.gold}'
        self.txt_jokers.text = f'Jokers: {", ".join(self.player.jokers)}'

        if self.last_damage_dealt:
            self.txt_last.text = f'You dealt {self.last_damage_dealt} ({self.last_hand})'
        elif self.last_damage_taken:
            self.txt_last.text = f'Enemy hit you for {self.last_damage_taken}'
        else:
            self.txt_last.text = '' 