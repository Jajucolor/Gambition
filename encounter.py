import random
from typing import List

from entities.enemy import create_enemy, ENEMY_TEMPLATES, Enemy


class EncounterManager:
    """Generates a sequence of enemies for a run."""

    def __init__(self, stages: int = 5):
        self.stages = stages
        self.queue: List[Enemy] = []
        self._populate_queue()

    def _populate_queue(self):
        names = list(ENEMY_TEMPLATES.keys())
        for _ in range(self.stages):
            name = random.choice(names)
            self.queue.append(create_enemy(name))

    # ------------------------------------------------------------------
    def next_enemy(self) -> Enemy | None:
        if self.queue:
            return self.queue.pop(0)
        return None

    def has_more(self) -> bool:
        return bool(self.queue) 