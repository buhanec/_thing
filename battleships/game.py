import itertools
import random
from typing import Type, Sequence, Tuple, List, Optional

from .board import Board, ShotResult
from .players import Player, TimedPlayer

__all__ = ("NaiveGame", "Game")

FeedbackBuffer = List[Optional[Tuple[int, int, ShotResult]]]


class NaiveGame:

    def __init__(self,
                 player_one: Type[Player],
                 player_two: Type[Player],
                 size: int = 12,
                 max_turns: int = 144,
                 max_fn_time: int = 0,
                 feedback_delay: int = 0,
                 ships: Sequence[int] = (2, 3, 3, 4, 5)) -> None:
        self.p1_class = player_one
        self.p2_class = player_two
        self.size = size
        self.max_turns = max_turns
        self.max_fn_time = max_fn_time
        self.feedback_delay = feedback_delay
        self.ships = ships

    def _play_round(self) -> Tuple[int, int]:
        p1 = self.p1_class(
            size=self.size,
            max_turns=self.max_turns,
            max_fn_time=self.max_fn_time,
            feedback_delay=self.feedback_delay,
            ships=self.ships
        )
        p2 = self.p2_class(
            size=self.size,
            max_turns=self.max_turns,
            max_fn_time=self.max_fn_time,
            feedback_delay=self.feedback_delay,
            ships=self.ships
        )

        p1_board = Board()
        p1_buffer = [None] * self.feedback_delay  # type: FeedbackBuffer
        p2_board = Board()
        p2_buffer = [None] * self.feedback_delay  # type: FeedbackBuffer

        bunches = [(p1, p1_board, p1_buffer, p2, p2_board, p2_buffer),
                   (p2, p2_board, p2_buffer, p1, p1_board, p1_buffer)]
        random.shuffle(bunches)

        # Set up ships
        for player, board, _1, _2, _3, _4 in bunches:
            for ship in player.ship_locations():
                board.place_ship(*ship)

        # Play game
        turn = 0
        for att, att_b, buffer, tgt, tgt_b, _ in itertools.cycle(bunches):
            turn += 1

            # Terminate game if sunken
            if not att_b.still_floating or turn > self.max_turns * 2:
                break

            # Try getting bomb effect
            x, y = att.drop_bomb()
            result = tgt_b.drop_bomb(x, y)

            # Try reporting bomb effect to target
            tgt.bombed_feedback(x, y, result)

            # Report whatever is in the buffer to attacker
            buffer.append((x, y, result))
            feedback = buffer.pop(0)
            if result is not None:
                att.bomb_feedback(*feedback)

        # Scoring
        score = p1_board.still_floating * 2, p2_board.still_floating * 2
        if sum(score) != 2:
            return 1, 1
        else:
            return score

    def play(self, games: int = 1000) -> Tuple[int, int]:
        p1_score = 0
        p2_score = 0
        for _ in range(games):
            p1_round_score, p2_round_score = self._play_round()
            p1_score += p1_round_score
            p2_score += p2_round_score
        return p1_score, p2_score


class Game(NaiveGame):

    def _play_round(self) -> Tuple[int, int]:
        # Check for successful init
        try:
            if self.max_fn_time > 0:
                p1 = TimedPlayer(
                    size=self.size,
                    max_turns=self.max_turns,
                    max_fn_time=self.max_fn_time,
                    feedback_delay=self.feedback_delay,
                    ships=self.ships,
                    base_player=self.p1_class
                )  # type: Player
            else:
                p1 = self.p1_class(
                    size=self.size,
                    max_turns=self.max_turns,
                    max_fn_time=self.max_fn_time,
                    feedback_delay=self.feedback_delay,
                    ships=self.ships
                )
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            p1 = None
        try:
            if self.max_fn_time > 0:
                p2 = TimedPlayer(
                    size=self.size,
                    max_turns=self.max_turns,
                    max_fn_time=self.max_fn_time,
                    feedback_delay=self.feedback_delay,
                    ships=self.ships,
                    base_player=self.p2_class
                )  # type: Player
            else:
                p2 = self.p2_class(
                    size=self.size,
                    max_turns=self.max_turns,
                    max_fn_time=self.max_fn_time,
                    feedback_delay=self.feedback_delay,
                    ships=self.ships
                )
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            p2 = None
        if p1 is None and p2 is None:
            return 1, 1
        if p1 is None or p2 is None:
            return (p2 is None) * 2, (p1 is None) * 2

        p1_board = Board()
        p1_buffer = [None] * self.feedback_delay  # type: FeedbackBuffer
        p2_board = Board()
        p2_buffer = [None] * self.feedback_delay  # type: FeedbackBuffer

        bunches = [(p1, p1_board, p1_buffer, p2, p2_board, p2_buffer),
                   (p2, p2_board, p2_buffer, p1, p1_board, p1_buffer)]
        random.shuffle(bunches)

        # Set up ships
        for player, board, _1, _2, _3, _4 in bunches:
            try:
                ships = player.ship_locations()
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException as e:
                import inspect
                ships = []
            try:
                for ship in ships:
                    try:
                        board.place_ship(*ship)
                    except ValueError:
                        pass
            except TypeError:
                pass

        # Play game
        turn = 0
        for att, att_b, buffer, tgt, tgt_b, _ in itertools.cycle(bunches):
            turn += 1

            # Terminate game if sunken
            if not att_b.still_floating or turn > self.max_turns * 2:
                break

            # Try getting bomb effect
            try:
                x, y = att.drop_bomb()
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException:
                continue
            try:
                result = tgt_b.drop_bomb(x, y)
            except ValueError:
                continue

            # Try reporting bomb effect to target
            try:
                tgt.bombed_feedback(x, y, result)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException:
                pass

            # Report whatever is in the buffer to attacker
            buffer.append((x, y, result))
            feedback = buffer.pop(0)
            if result is not None:
                try:
                    att.bomb_feedback(*feedback)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except BaseException:
                    pass

        # Scoring
        score = p1_board.still_floating * 2, p2_board.still_floating * 2
        if sum(score) != 2:
            return 1, 1
        else:
            return score
