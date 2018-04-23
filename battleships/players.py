"""Sample AIs to compete against."""
import signal
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from typing import Sequence, Tuple, Type

import itertools

import sys

from .board import ShotResult
from random import randint, shuffle

__all__ = ("Player", "TimedPlayer", "RandomPlayer", "BetterRandomPlayer",
           "StrategicPlayer", "MirrorPlayer")


class Player(metaclass=ABCMeta):

    def __init__(self,
                 size: int,
                 max_turns: int,
                 max_fn_time: int,
                 feedback_delay: int,
                 ships: Sequence[int]) -> None:
        self.size = size
        self.max_turns = max_turns
        self.max_fn_time = max_fn_time
        self.feedback_delay = feedback_delay
        self.ships = ships

    @abstractmethod
    def ship_locations(self) -> Sequence[Tuple[int, int, int, bool]]:
        """
        Method that will place ships at the beginning of the game.

        This will be a list of ship positions, where each position has
        four components:
         * size of the ship
         * x-coordinate
         * y-coordinate
         * is horizontal

        If a ship is horizontal, it will span fields covered by
        incrementing the x-coordinate by "size" number of times.

        If a ship is not horizontal, it will span fields covered by
        incrementing the y-coordinate by "size" number of times.

        Therefore, (3, 1, 2, True) would span:
         * (1, 2)
         * (2, 2)
         * (3, 2)

        And (4, 0, 0, False) would span:
         * (0, 0)
         * (0, 1)
         * (0, 2)
         * (0, 3)

        Note that there are two cases of invalid placements:
         * Going out of the board
         * Intersecting ships

        If a ship goes out of bounds it will not be placed at all.
        E.g. (3, 10, 2, True) on a board of size 12 would try to span
         * (10, 2)
         * (11, 2)
         * (12, 2) -- out of bounds

        and would not be placed.

        If two ships were defined as (2, 0, 0, True)
        and (2, 0, 0, False), the following allocation would happen.
        First ship would successfully be placed across
         * (0, 0)
         * (1, 0)

        Second ship would fail as it would try to span
         * (0, 0) -- already occupied
         * (0, 1)

        :return: Ship locations
        """
        return NotImplemented

    @abstractmethod
    def drop_bomb(self) -> Tuple[int, int]:
        """
        Method that will choose where to drop a bomb next. The return
        type is a tuple of (x-coordinate, y-coordinate).

        Sending invalid coordinates (outside of the bounds of the
        board) will result in no bomb dropped.

        Feedback is sent to the bomb_feedback method.

        :return: Bomb dropping coordinates
        """
        return NotImplemented

    @abstractmethod
    def bomb_feedback(self, x: int, y: int, result: ShotResult) -> None:
        """
        Method that will receive feedback on fired bombs. These reflect
        the state of the opponent's board.

        Feedback is one of the following:
         * ShotResult.MISS - did not hit any ships
         * ShotResult.PREVIOUS_MISS - did not hit any ships and already
                                      fired at this spot
         * ShotResult.HIT - hit a ship field
         * ShotResult.PREVIOUS_HIT - hit a ship field that had been
                                     already hit previously

        :param x: x-coordinate of last shot
        :param y: y-coordinate of last shot
        :param result: result of last shot
        """

    @abstractmethod
    def bombed_feedback(self, x: int, y: int, result: ShotResult) -> None:
        """
        Method that will receive feedback on enemy bombs dropped on
        your board. These reflect the state of your board.

        Feedback is one of the following:
         * ShotResult.MISS - did not hit any ships
         * ShotResult.PREVIOUS_MISS - did not hit any ships and already
                                      fired at this spot
         * ShotResult.HIT - hit a ship field
         * ShotResult.PREVIOUS_HIT - hit a ship field that had been
                                     already hit previously

        :param x: x-coordinate of last shot
        :param y: y-coordinate of last shot
        :param result: result of last shot
        """


class TimedPlayer(Player):

    def __init__(self,
                 size: int,
                 max_turns: int,
                 max_fn_time: int,
                 feedback_delay: int,
                 ships: Sequence[int],
                 base_player: Type[Player]) -> None:
        super().__init__(size, max_turns, max_fn_time, feedback_delay, ships)
        self.player = base_player(
            size=size,
            max_turns=max_turns,
            max_fn_time=max_fn_time,
            feedback_delay=feedback_delay,
            ships=ships
        )

    @staticmethod
    def _raise_timeout(signum, frame) -> None:
        raise TimeoutError("Function timeout")

    # noinspection PyUnresolvedReferences
    @contextmanager
    def timed(self):
        if sys.platform == 'linux':
            signal.signal(signal.SIGALRM, self._raise_timeout)
            signal.alarm(self.max_fn_time / 1000)
            try:
                yield
            finally:
                signal.alarm(0)
        else:
            yield

    def ship_locations(self) -> Sequence[Tuple[int, int, int, bool]]:
        with self.timed():
            return self.player.ship_locations()

    def drop_bomb(self) -> Tuple[int, int]:
        with self.timed():
            return self.player.drop_bomb()

    def bomb_feedback(self, x: int, y: int, result: ShotResult) -> None:
        with self.timed():
            self.player.bomb_feedback(x, y, result)

    def bombed_feedback(self, x: int, y: int, result: ShotResult) -> None:
        with self.timed():
            self.player.bombed_feedback(x, y, result)


class RandomPlayer(Player):

    def _rxy(self) -> Tuple[int, int]:
        return randint(0, self.size - 1), randint(0, self.size - 1)

    def ship_locations(self) -> Sequence[Tuple[int, int, int, bool]]:
        return [(ship_size, *self._rxy(), bool(randint(0, 1)))
                for ship_size in self.ships]

    def drop_bomb(self) -> Tuple[int, int]:
        return self._rxy()

    def bomb_feedback(self, x: int, y: int, result: ShotResult) -> None:
        pass

    def bombed_feedback(self, x: int, y: int, result: ShotResult) -> None:
        pass


class BetterRandomPlayer(RandomPlayer):

    def __init__(self,
                 size: int,
                 max_turns: int,
                 max_fn_time: int,
                 feedback_delay: int,
                 ships: Sequence[int]):
        super().__init__(size, max_turns, max_fn_time, feedback_delay, ships)
        self.bomb_sequence = list(itertools.product(range(size), range(size)))
        shuffle(self.bomb_sequence)

    def drop_bomb(self) -> Tuple[int, int]:
        try:
            return self.bomb_sequence.pop()
        except IndexError:
            return self._rxy()


class StrategicPlayer(Player):

    def __init__(self,
                 size: int,
                 max_turns: int,
                 max_fn_time: int,
                 feedback_delay: int,
                 ships: Sequence[int]):
        super().__init__(size, max_turns, max_fn_time, feedback_delay, ships)
        self.scanning_index = 0
        self.forced_drops = []

    def ship_locations(self) -> Sequence[Tuple[int, int, int, bool]]:
        locations = []
        for x, ship_size in enumerate(sorted(self.ships, reverse=True)):
            adjusted_x = self.size - 1 - 2 * x
            y = self.size - 1 - ship_size
            locations.append((ship_size, adjusted_x * 2, y, False))
        return locations

    def drop_bomb(self) -> Tuple[int, int]:
        try:
            return self.forced_drops.pop()
        except IndexError:
            coordinates = self.scanning_index // 3, self.scanning_index % 3
            self.scanning_index += 1
            return coordinates

    def bomb_feedback(self, x: int, y: int, result: ShotResult) -> None:
        if result is ShotResult.HIT and not self.forced_drops:
            for x_offset in range(-2, 3):
                for y_offset in range(-2, 3):
                    if x_offset == y_offset == 0:
                        continue
                    self.forced_drops.append((x + x_offset, y + y_offset))

    def bombed_feedback(self, x: int, y: int, result: ShotResult) -> None:
        pass


class MirrorPlayer(StrategicPlayer):

    def __init__(self,
                 size: int,
                 max_turns: int,
                 max_fn_time: int,
                 feedback_delay: int,
                 ships: Sequence[int]):
        super().__init__(size, max_turns, max_fn_time, feedback_delay, ships)
        self.last_enemy_move = None

    def drop_bomb(self) -> Tuple[int, int]:
        if self.last_enemy_move is None:
            return 0, 0
        else:
            return self.last_enemy_move

    def bombed_feedback(self, x: int, y: int, result: ShotResult) -> None:
        self.last_enemy_move = x, y
