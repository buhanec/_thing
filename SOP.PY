"""Sophie Tan's special AI."""
from typing import Sequence, Tuple

from battleships import Player, ShotResult
from random import randint


class SophiesAI(Player):
    """Sophie Tan's Random Shot Magic."""

    def ship_locations(self) -> Sequence[Tuple[int, int, int, bool]]:
        return [(2, 0, 0, True)]

    def drop_bomb(self) -> Tuple[int, int]:
        return randint(0, self.size - 1), randint(0, self.size - 1)

    def bomb_feedback(self, x: int, y: int, result: ShotResult):
        pass

    def bombed_feedback(self, x: int, y: int, result: ShotResult):
        pass
