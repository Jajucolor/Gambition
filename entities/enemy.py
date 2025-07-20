from status_effects import StatusEffectManager, StunEffect


class Enemy:
    """Basic enemy with attack and optional defense."""

    def __init__(self, name: str, hp: int, attack: int, defense: int = 0):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack_value = attack
        self.defense = defense
        
        # Status effects manager
        self.status_effects: StatusEffectManager = StatusEffectManager()

    # ------------------------------------------------------------------
    # Combat behaviour
    # ------------------------------------------------------------------
    def take_damage(self, dmg: float) -> None:
        # Apply status effect damage reduction and shields
        actual_damage = self.status_effects.modify_incoming_damage(int(dmg))
        actual_damage = max(0, actual_damage - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        print(f"{self.name} took {actual_damage} damage. HP {self.hp}/{self.max_hp}")

    def attack_player(self, player: 'Player') -> bool:  # type: ignore
        """Attack the player. Returns True if attack was successful, False if stunned."""
        # Check if stunned
        if self.status_effects.has_effect(StunEffect):
            print(f"{self.name} is stunned and cannot attack!")
            return False
        
        # Apply damage buffs if any
        damage = self.status_effects.modify_outgoing_damage(self.attack_value)
        
        print(f"{self.name} attacks for {damage}!")
        player.take_damage(damage)
        return True
    
    def start_turn(self) -> None:
        """Called at the start of the enemy's turn to process status effects."""
        self.status_effects.tick_effects(self)
    
    def end_turn(self) -> None:
        """Called at the end of the enemy's turn."""
        pass

    # Utility --------------------------------------------------------------
    def is_alive(self) -> bool:
        return self.hp > 0


# ---------------------------------------------------------------------------
# Enemy factory / catalogue
# ---------------------------------------------------------------------------

ENEMY_TEMPLATES = {
    'Goblin': dict(hp=50, attack=10, defense=0),
    'Orc': dict(hp=80, attack=12, defense=2),
    'Skeleton': dict(hp=40, attack=8, defense=1),
    'Bandit': dict(hp=60, attack=15, defense=0),
    'Troll': dict(hp=120, attack=18, defense=4),
    'Dragonling': dict(hp=150, attack=25, defense=5),
}

def create_enemy(name: str) -> 'Enemy':
    tmpl = ENEMY_TEMPLATES[name]
    return Enemy(name, **tmpl) 