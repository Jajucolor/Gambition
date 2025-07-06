class Enemy:
    """Basic enemy with attack and optional defense."""

    def __init__(self, name: str, hp: int, attack: int, defense: int = 0):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attack_value = attack
        self.defense = defense

    # ------------------------------------------------------------------
    # Combat behaviour
    # ------------------------------------------------------------------
    def take_damage(self, dmg: float) -> None:
        actual = max(0, int(dmg) - self.defense)
        self.hp = max(0, self.hp - actual)
        print(f"{self.name} took {actual} damage. HP {self.hp}/{self.max_hp}")

    def attack_player(self, player: 'Player') -> None:  # type: ignore
        print(f"{self.name} attacks for {self.attack_value}!")
        player.take_damage(self.attack_value)

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