from ursina import *  # type: ignore
from typing import Any, cast

from entities.player import Player
from encounter import EncounterManager
from entities.enemy import Enemy

# Overlay sizes (viewport units −1..1)
CARD_W, CARD_H = .12, .18  # smaller cards
CARD_GAP = 0.02            # horizontal gap between cards
BUTTON_Y = -.65
ENEMY_DELAY = 0.6  # seconds before enemy strikes (visual anticipation)

# Helper
_fmt = lambda v: int(v)


class CombatUI(Entity):
    """3-D battle overlay reusing core logic and showing detailed stats."""

    def __init__(self, *, world_player: Entity, player_stats: Player, on_finish, enemy_position=None, enemy=None):
        super().__init__()
        self.world_player = world_player
        self.on_finish = on_finish

        # Core state
        self.player = player_stats
        
        # Use provided enemy or create a random one
        if enemy:
            self.enemy = enemy
        else:
            self.encounters = EncounterManager(stages=1)
            self.enemy: Enemy | None = self.encounters.next_enemy()

        self.selected: list[int] = []
        self.hand_buttons: list[Button] = []
        self.action_buttons: list[Button] = []

        # Last turn summary
        self.last_damage_dealt = 0
        self.last_damage_taken = 0
        self.last_hand: str = ''

        # Discard limit per turn
        self.max_discards = 4
        self.discards_left = self.max_discards

        # Flag to block inputs during enemy wind-up
        self.in_enemy_phase: bool = False

        # Build scene & UI
        self.lock_world()
        self._setup_scene_models(enemy_position)
        self._setup_ui()
        self._setup_action_panel()
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

    def _setup_scene_models(self, enemy_position=None):
        if enemy_position:
            # Position combat around the enemy's location
            enemy_pos = Vec3(enemy_position)
            player_pos = enemy_pos + Vec3(-5, 0, 0)  # Player to the left of enemy
            camera_pos = enemy_pos + Vec3(-6, 0, -5)   # Camera above and back
            
            self.player_model = Entity(model='cube', color=cast(Any, color.azure), position=player_pos, scale=1.5)
            self.enemy_model = Entity(model='cube', color=cast(Any, color.red), position=enemy_pos, scale=1.5)
            camera.position = camera_pos
            camera.look_at(enemy_pos + Vec3(4, 1, 10))
        else:
            # Default positions for random encounters
            self.player_model = Entity(model='cube', color=cast(Any, color.azure), position=(-2, 0.75, 4), scale=1.5)
            self.enemy_model = Entity(model='cube', color=cast(Any, color.red), position=(2, 0.75, 4), scale=1.5)
            camera.position = (0, 3, 7)
            camera.look_at(Vec3(-3, 1, 10))

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
        self.txt_discards = Text(parent=self.ui_root, scale=1, origin=(0,0))

        # Update HUD
        self._update_stats()

    def _refresh_hand_ui(self):
        for b in self.hand_buttons:
            destroy(b)
        self.hand_buttons.clear()

        # Calculate centered start position
        total_w = len(self.player.hand) * CARD_W + max(0, len(self.player.hand) - 1) * CARD_GAP
        start_x = -total_w / 2

        for idx, card in enumerate(self.player.hand):
            x = start_x + idx * (CARD_W + CARD_GAP)
            btn = Button(parent=self.ui_root, text=f'{card.rank}{card.suit[0]}', color=cast(Any, color.gray),
                         position=(x, -0.3), scale=(CARD_W, CARD_H))
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

        # Sort buttons under the hand
        for b in self.action_buttons:
            destroy(b)
        self.action_buttons.clear()

        sort_rank_btn = Button(parent=self.ui_root, text='Sort Rank', position=(-0.15, -0.45), scale=(0.18, 0.08))
        sort_rank_btn.on_click = self.sort_by_rank
        self.action_buttons.append(sort_rank_btn)

        sort_suit_btn = Button(parent=self.ui_root, text='Sort Suit', position=(0.05, -0.45), scale=(0.18, 0.08))
        sort_suit_btn.on_click = self.sort_by_suit
        self.action_buttons.append(sort_suit_btn)

    # ------------------------------------------------------------------
    # Action panel
    # ------------------------------------------------------------------
    def _setup_action_panel(self):
        """Panel with Items / Skills / Attack / Discard next to player."""
        self.action_panel = Entity(parent=camera.ui)

        start_y = -0.05
        spacing = -0.12

        def _btn(text, order, cb):
            y = start_y + order * spacing
            b = Button(parent=self.action_panel, text=text, position=(-0.8, y), scale=(0.18, 0.08))
            b.on_click = cb
            return b

        # Items and Skills stubs
        _btn('Items', 0, self.use_item)
        _btn('Skills', 1, self.use_skill)
        _btn('Attack', 2, self.attack_selected)
        discard_btn = _btn('Discard', 3, self.discard_selected)

        # Position discards-left text right under Discard button
        self.txt_discards.parent = self.action_panel
        self.txt_discards.position = (discard_btn.position[0], discard_btn.position[1] - 0.06)

    def use_item(self):
        if getattr(self, 'item_overlay', None):
            return  # already open

        if not self.player.items:
            print('No items to use.')
            return

        from tarot import TarotCard  # local import

        overlay = Entity(parent=camera.ui)
        self.item_overlay = overlay

        bg = Panel(parent=overlay, color=color.rgba(0,0,0,150), scale=(1.2,1.2))

        title = Text(parent=overlay, text='Use an Item', y=0.4, origin=(0,0), scale=1.5)

        buttons: list[Button] = []
        start_y = 0.25
        for idx, itm in enumerate(list(self.player.items)):
            label = itm.name if isinstance(itm, TarotCard) else str(itm)
            btn = Button(parent=overlay, text=label, position=(-0.2, start_y-idx*0.12), scale=(0.4,0.08))

            def _choose(it=itm):
                # call effect
                if isinstance(it, TarotCard):
                    it.on_use(self)
                # remove item
                self.player.items.remove(it)
                self._refresh_hand_ui()
                close()

            btn.on_click = _choose
            buttons.append(btn)

        close_btn = Button(parent=overlay, text='Cancel', position=(0.3,-0.4), scale=(0.2,0.08))
        buttons.append(close_btn)

        def close():
            for b in buttons:
                destroy(b)
            destroy(title)
            destroy(bg)
            destroy(overlay)
            self.item_overlay = None

        close_btn.on_click = close

    def use_skill(self):
        print('TODO: implement skills')

    # ------------------------------------------------------------------
    # Sorting helpers
    # ------------------------------------------------------------------
    def sort_by_rank(self):
        self.player.hand.sort(key=lambda c: c.value)
        self.selected.clear()
        self._refresh_hand_ui()

    def sort_by_suit(self):
        suit_order = {s: i for i, s in enumerate(['Clubs', 'Diamonds', 'Hearts', 'Spades'])}
        self.player.hand.sort(key=lambda c: (suit_order.get(c.suit, 0), c.value))
        self.selected.clear()
        self._refresh_hand_ui()

    # ------------------------------------------------------------------
    # Turn flow
    # ------------------------------------------------------------------
    def start_player_turn(self):
        self.player.draw_cards()
        self.selected.clear()
        self.discards_left = self.max_discards  # reset per turn
        self._refresh_hand_ui()

    def attack_selected(self):
        if not self.selected:
            return
        dmg, hand_type = self.player.form_hand_and_attack(self.selected)
        bonus = getattr(self, '_tarot_bonus', 0)
        if bonus:
            dmg += bonus
            self._tarot_bonus = 0  # reset after use
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
        if self.discards_left <= 0:
            print('No discards left!')
            return
        self.player.discard_cards(self.selected)
        self.selected.clear()
        self.discards_left -= 1
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
        destroy(self.action_panel)
        self.unlock_world()
        if callable(self.on_finish):
            self.on_finish()
        destroy(self)

    def _update_stats(self):
        self.txt_player.text = f'HP: {self.player.hp}/{self.player.max_hp}'
        self.txt_enemy.text = f'{self.enemy.name} HP {self.enemy.hp}' if self.enemy else ''
        self.txt_gold.text = f'Gold: {self.player.gold}'
        self.txt_jokers.text = f'Jokers: {", ".join(self.player.jokers)}'

        self.txt_discards.text = f'Discards left: {self.discards_left}'

        if self.last_damage_dealt:
            self.txt_last.text = f'You dealt {self.last_damage_dealt} ({self.last_hand})'
        elif self.last_damage_taken:
            self.txt_last.text = f'Enemy hit you for {self.last_damage_taken}'
        else:
            self.txt_last.text = ''

    # Entity per-frame update to ensure discard text always reflects latest value
    def update(self):  # called automatically by Ursina each frame
        self.txt_discards.text = f'Discards left: {self.discards_left}' 