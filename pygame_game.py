import os
import sys
from pathlib import Path
from typing import List

import pygame

from constants import WHITE, BLACK
from entities.player import Player
from encounter import EncounterManager
from entities.enemy import Enemy
from card import Card
from shop import generate_shop_items, ShopItem
from event_system import random_event, Event as GameEvent

# ---------------------------------------------------------------------------
# Visual constants (inspired by Clair Obscur & Hollow Knight aesthetics)
# ---------------------------------------------------------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 576  # 16:9 widescreen
FPS = 60
CARD_W, CARD_H = 80, 110
CARD_GAP = 20
HAND_Y = SCREEN_HEIGHT - CARD_H - 30
BACKGROUND_COLOR = (22, 24, 35)  # Deep desaturated blue-black
ACCENT_COLOR = (230, 230, 235)    # Soft off-white for outlines / text

ASSETS_DIR = Path(__file__).with_suffix('').parent / 'assets'


def load_sprite(name: str, fallback_size: tuple[int, int]):
    path = ASSETS_DIR / name
    if path.exists():
        return pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), fallback_size)
    else:
        surf = pygame.Surface(fallback_size, pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        pygame.draw.rect(surf, ACCENT_COLOR, surf.get_rect(), width=2)
        return surf


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def draw_text(surface: pygame.Surface, text: str, pos: tuple[int, int], font: pygame.font.Font):
    img = font.render(text, True, ACCENT_COLOR)
    surface.blit(img, pos)


def card_rect(index: int) -> pygame.Rect:
    x = (CARD_GAP + CARD_W) * index + CARD_GAP
    return pygame.Rect(x, HAND_Y, CARD_W, CARD_H)


# ---------------------------------------------------------------------------
# Main GameUI class
# ---------------------------------------------------------------------------


class GameUI:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Gambition – Expedition of Cards')
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)

        self.player = Player()
        self.encounters = EncounterManager(stages=5)
        self.enemy: Enemy | None = self.encounters.next_enemy()

        self.player.add_joker('joker')

        # preload sprites (placeholder squares for now)
        self.player_sprite = load_sprite('player.png', (120, 160))
        self.enemy_sprite = load_sprite('enemy.png', (120, 160))

        # state
        self.selected: List[int] = []

        # UI state
        self.state: str = 'battle'  # battle | shop | event | gameover
        self.shop_items: List[ShopItem] = []
        self.current_event: GameEvent | None = None

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_events(self) -> bool:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.state == 'battle':
                    self.handle_click(ev.pos)
                elif self.state == 'shop':
                    self.handle_shop_click(ev.pos)
                elif self.state == 'event':
                    self.handle_event_click(ev.pos)
            if ev.type == pygame.KEYDOWN:
                if self.state == 'battle':
                    if ev.key == pygame.K_a:
                        self.attack_selected()
                    elif ev.key == pygame.K_d:
                        self.discard_selected()
                    elif ev.key == pygame.K_e:
                        self.end_turn()
                elif self.state in ['shop', 'event'] and ev.key == pygame.K_ESCAPE:
                    # exit to battle (or gameover)
                    self.close_overlay()
        return True

    def handle_click(self, pos):
        for idx, rect in enumerate(self.card_rects()):
            if rect.collidepoint(pos):
                if idx in self.selected:
                    self.selected.remove(idx)
                else:
                    self.selected.append(idx)
                    if len(self.selected) > 5:
                        self.selected.pop(0)  # deselect earliest
                break

    # ------------------------------------------------------------------
    # Turn mechanics bridging to core logic
    # ------------------------------------------------------------------
    def start_player_turn(self):
        self.player.draw_cards()
        self.selected.clear()

    def attack_selected(self):
        if not self.selected:
            print("Select at least 1 card before attacking.")
            return  # need exactly 5
        dmg, hand_type = self.player.form_hand_and_attack(self.selected)
        if hand_type and self.enemy:
            self.enemy.take_damage(dmg)
            self.selected.clear()
            if not self.enemy.is_alive():
                # Victory over enemy
                if self.encounters.has_more():
                    # Decide overlay: shop or event
                    import random as _r
                    if _r.random() < 0.5:
                        self.open_shop_ui()
                    else:
                        self.open_event_ui()
                else:
                    print("All enemies defeated!")
                    self.enemy = None
                    self.state = 'gameover'
            else:
                self.enemy_turn()

    def discard_selected(self):
        if not self.selected:
            return
        self.player.discard_cards(self.selected)
        self.selected.clear()

    def end_turn(self):
        self.selected.clear()
        self.enemy_turn()

    def enemy_turn(self):
        if self.enemy and self.enemy.is_alive():
            self.enemy.attack_player(self.player)
        if not self.player.is_alive():
            print("Player defeated – Game Over")
            self.state = 'gameover'

    # ------------------------------------------------------------------
    def run(self):
        self.start_player_turn()
        running = True
        while running and self.player.is_alive() and (self.enemy or self.state != 'battle'):
            running = self.handle_events()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)

        # background vignette (simple radial transparency)
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(vignette, (0, 0, 0, 180), (-SCREEN_WIDTH*0.25, SCREEN_HEIGHT*0.25, SCREEN_WIDTH*1.5, SCREEN_HEIGHT*1.5))
        self.screen.blit(vignette, (0, 0))

        # Draw enemy & player sprites centrally
        if self.enemy_sprite:
            self.screen.blit(self.enemy_sprite, (SCREEN_WIDTH//2 + 120, SCREEN_HEIGHT//2 - self.enemy_sprite.get_height()//2))
        if self.player_sprite:
            self.screen.blit(self.player_sprite, (SCREEN_WIDTH//2 - 240, SCREEN_HEIGHT//2 - self.player_sprite.get_height()//2))

        # draw according to state
        if self.state == 'battle':
            self.draw_battle()
        elif self.state == 'shop':
            self.draw_shop()
        elif self.state == 'event':
            self.draw_event()
        elif self.state == 'gameover':
            self.draw_gameover()

        pygame.display.flip()

    # ------------------------------------------------------------------
    def card_rects(self):
        return [card_rect(i) for i in range(len(self.player.hand))]

    # ------------------------------------------------------------------
    # SHOP UI -----------------------------------------------------------
    def open_shop_ui(self):
        self.shop_items = generate_shop_items()
        self.state = 'shop'

    def handle_shop_click(self, pos):
        # Layout: items vertically spaced
        start_y = 150
        for idx, item in enumerate(self.shop_items):
            rect = pygame.Rect(200, start_y + idx * 70, 600, 60)
            if rect.collidepoint(pos):
                if item.buy(self.player):
                    self.shop_items.pop(idx)
                break
        # leave area (bottom)
        leave_rect = pygame.Rect(400, SCREEN_HEIGHT - 80, 200, 40)
        if leave_rect.collidepoint(pos):
            self.close_overlay()

    # ------------------------------------------------------------------
    # EVENT UI ----------------------------------------------------------
    def open_event_ui(self):
        self.current_event = random_event()
        self.state = 'event'

    def handle_event_click(self, pos):
        if not self.current_event:
            return
        start_y = 200
        for idx, (text, _) in enumerate(self.current_event.choices):
            rect = pygame.Rect(150, start_y + idx * 60, 700, 50)
            if rect.collidepoint(pos):
                # execute choice
                self.current_event.choices[idx][1](self.player)
                break
        # anywhere click afterwards closes overlay
        self.close_overlay()

    def close_overlay(self):
        # If more enemies, continue battle; else end game
        if self.encounters.has_more():
            self.enemy = self.encounters.next_enemy()
            self.start_player_turn()
            self.state = 'battle'
        else:
            self.state = 'gameover'

    # ------------------------------------------------------------------
    def draw_battle(self):
        # HUD text
        draw_text(self.screen, f"HP: {self.player.hp}/{self.player.max_hp}", (20, 20), self.font)
        if self.enemy:
            draw_text(self.screen, f"Enemy: {self.enemy.name} HP {self.enemy.hp}", (20, 50), self.font)
        draw_text(self.screen, f"Gold: {self.player.gold}", (20, 80), self.font)
        draw_text(self.screen, f"Jokers: {', '.join(self.player.jokers)}", (20, 110), self.font)

        # Draw hand
        for idx, card in enumerate(self.player.hand):
            rect = card_rect(idx)
            color = ACCENT_COLOR if idx in self.selected else (100, 100, 110)
            pygame.draw.rect(self.screen, color, rect, width=2)
            rank_surf = self.font.render(card.rank, True, ACCENT_COLOR)
            suit_surf = self.font.render(card.suit[0], True, ACCENT_COLOR)
            self.screen.blit(rank_surf, (rect.x + 6, rect.y + 6))
            self.screen.blit(suit_surf, (rect.centerx - suit_surf.get_width()//2, rect.y + rect.height//2))

    # ------------------------------------------------------------------
    def draw_shop(self):
        draw_text(self.screen, "Merchant's Caravan", (SCREEN_WIDTH//2 - 120, 40), self.font)
        draw_text(self.screen, f"Gold: {self.player.gold}", (20, 20), self.font)

        start_y = 150
        for idx, item in enumerate(self.shop_items):
            rect = pygame.Rect(200, start_y + idx * 70, 600, 60)
            pygame.draw.rect(self.screen, (50, 50, 70), rect)
            pygame.draw.rect(self.screen, ACCENT_COLOR, rect, 2)
            draw_text(self.screen, f"{item.name} (Cost {item.cost})", (rect.x + 10, rect.y + 20), self.font)

        # leave button
        leave_rect = pygame.Rect(400, SCREEN_HEIGHT - 80, 200, 40)
        pygame.draw.rect(self.screen, (80, 30, 30), leave_rect)
        draw_text(self.screen, "Leave (Esc)", (leave_rect.x + 40, leave_rect.y + 10), self.font)

    # ------------------------------------------------------------------
    def draw_event(self):
        if not self.current_event:
            return
        draw_text(self.screen, "Mysterious Encounter", (SCREEN_WIDTH//2 - 140, 40), self.font)
        # description wrap naive
        draw_text(self.screen, self.current_event.description, (80, 100), self.font)
        start_y = 200
        for idx, (text, _) in enumerate(self.current_event.choices):
            rect = pygame.Rect(150, start_y + idx * 60, 700, 50)
            pygame.draw.rect(self.screen, (50, 50, 70), rect)
            pygame.draw.rect(self.screen, ACCENT_COLOR, rect, 2)
            draw_text(self.screen, text, (rect.x + 10, rect.y + 15), self.font)

    # ------------------------------------------------------------------
    def draw_gameover(self):
        msg = "You Win!" if self.player.is_alive() else "Game Over"
        draw_text(self.screen, msg, (SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT//2 - 20), self.font)
        draw_text(self.screen, "Press ESC to quit", (SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 + 20), self.font)


if __name__ == '__main__':
    GameUI().run() 