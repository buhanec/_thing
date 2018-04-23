"""Game runner board."""

from enum import Enum
from typing import List, Sequence, Union


class FieldState(Enum):
    EMPTY = " "
    SHIP = "O"
    HIT = "H"
    MISSED = "X"


class ShotResult(Enum):
    MISS = "miss"
    PREVIOUS_MISS = "previous_miss"
    HIT = "hit"
    PREVIOUS_HIT = "previous_hit"
    INVALID = "invalid"


class Field:
    _transitions = {
        FieldState.EMPTY: (FieldState.MISSED, ShotResult.MISS),
        FieldState.SHIP: (FieldState.HIT, ShotResult.HIT),
        FieldState.HIT: (FieldState.HIT, ShotResult.PREVIOUS_HIT),
        FieldState.MISSED: (FieldState.MISSED, ShotResult.PREVIOUS_MISS)
    }

    def __init__(self) -> None:
        """Instantiate an empty field."""
        self.state = FieldState.EMPTY

    def drop_bomb(self) -> ShotResult:
        """
        Drop bomb on field. Field will change its state appropriately
        and return an informative result to the user.

        :return: Informative shot result
        """
        self.state, result = self._transitions[self.state]
        return result

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {self.state}>"


class Board:

    def __init__(self,
                 size: int = 12,
                 ships: Sequence[int] = (2, 3, 3, 4, 5)) -> None:
        self.size = size
        self._board = [[Field() for _ in range(size)] for _ in range(size)]
        self._ships = []  # type: List[List[Field]]
        self._remaining_ships = list(ships)

    def drop_bomb(self, x: int, y: int) -> ShotResult:
        """
        Drop bomb on field. Field will change its state appropriately
        and return an informative result to the user. If the
        coordinates point to an invalid field, an exception will be
        raised.

        :param x: Shot x-coordinate
        :param y: Shot y-coordinate
        :return: Shot result
        :raise ValueError: Invalid coordinates
        """
        try:
            field = self._board[y][x]
        except IndexError as e:
            raise ValueError("Invalid coordinates") from e
        else:
            return field.drop_bomb()

    def place_ship(self, size: int, x: int, y: int, horizontal: bool):
        """
        Places a ship starting from the field (x, y) and increasing in
        x values if horizontal is true or increasing in y values if
        horizontal is false.

        If unsuccessful in placing ship (not enough fields or they are
        already taken) it will raise a ValueError exception.

        :param size: Ship size
        :param x: Starting x-coordinate
        :param y: Starting y-coordinate
        :param horizontal: Ship direction
        :raise ValueError: Incorrect arguments
        """
        # Check if ship size is valid
        try:
            self._remaining_ships.remove(size)
        except ValueError as e:
            raise ValueError(f"No more ships of size {size} allowed") from e

        # Check if we can allocate enough fields
        try:
            if horizontal:
                fields = self._board[y][x:x + size]
            else:
                fields = [column[x] for column in self._board[y:y + size]]
        except IndexError as e:
            raise ValueError("Not enough space to place ship") from e
        if len(fields) != size:
            raise ValueError("Not enough space to place ship")

        # Check if fields are already taken
        for field in fields:
            if field.state is not FieldState.EMPTY:
                raise ValueError("Trying to place on existing ship")

        # Assign fields to a ship
        self._ships.append(fields)
        for field in fields:
            field.state = FieldState.SHIP

    @property
    def still_floating(self) -> bool:
        """
        Simple check to see if anything is still floating.

        :return: true if something floats, false otherwise
        """
        for ship in self._ships:
            for part in ship:
                if part.state is FieldState.SHIP:
                    return True
        return False

    def emojify(self, print_board: bool = True) -> Union[str, None]:
        """
        Compact representation of a board leveraging the latest and
        greatest UI toolkits.

        :param print_board: Print instead of returning representation.
        :return: If not print_board, return representation.
        """
        emojis = {
            FieldState.EMPTY: '🌊',
            FieldState.SHIP: '🚣 ',
            FieldState.HIT: '💥',
            FieldState.MISSED: '🎣'
        }
        meme = '\n'.join(''.join(emojis[f.state] for f in row)
                         for row in reversed(self._board))
        if print_board:
            print(meme)
            return None
        else:
            return meme

    def __getitem__(self, item):
        if not isinstance(item, tuple) and len(item) == 2:
            raise ValueError(f"Expecting coordinates, got {item}")
        return self._board[item[1]][item[0]]

    def __str__(self) -> str:
        """
        Have mercy on me. Pipe-y drawing of a board.

        :return: Something nicer than the implementation.
        """
        num = f'   {" ".join(str(n).center(3) for n in range(self.size))}\n'
        top = f'  ╔{"╤".join(["═══"] * self.size)}╗\n'
        mid = f'  ╟{"┼".join(["───"] * self.size)}╢\n'
        bot = f'  ╚{"╧".join(["═══"] * self.size)}╝\n'

        rows = []
        for number, row in enumerate(reversed(self._board)):
            n = str(self.size - 1 - number)
            r = [field.state.value.center(3) for field in row]
            rows.append(f'{n.rjust(2)}║{"│".join(r)}║{n.ljust(2)}\n')
        return (num + top + mid.join(rows) + bot + num).rstrip()
