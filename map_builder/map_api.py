import asyncio
import logging
from asyncio import Future
from copy import deepcopy
from random import choice
from typing import List, Callable

from map_builder.movement import Coordinate
from map_builder.pieces import Piece
from twimap.cancel_token import CancelToken


logger = logging.getLogger(__name__)


free_space_piece = Piece(" ", True, True, True, True, True)
double_vertical_connection_piece = Piece("║", accept_top_conn=True, accept_bottom_conn=True)

pieces0 = [
    # free_space_piece,
    Piece("═", accept_left_conn=True, accept_right_conn=True),
    double_vertical_connection_piece,
    Piece("╔", accept_bottom_conn=True, accept_right_conn=True),
    Piece("╗", accept_bottom_conn=True, accept_left_conn=True),
    Piece("╚", accept_top_conn=True, accept_right_conn=True),
    Piece("╝", accept_top_conn=True, accept_left_conn=True),
    Piece("╠", accept_top_conn=True, accept_bottom_conn=True, accept_right_conn=True),
    Piece("╣", accept_top_conn=True, accept_bottom_conn=True, accept_left_conn=True),
    Piece("╦", accept_bottom_conn=True, accept_left_conn=True, accept_right_conn=True),
    Piece("╩", accept_top_conn=True, accept_left_conn=True, accept_right_conn=True),
    Piece("╬", accept_top_conn=True, accept_bottom_conn=True, accept_left_conn=True, accept_right_conn=True),
]

mix_vertical_connection_piece = Piece("│", accept_top_conn=True, accept_bottom_conn=True)

pieces1 = [
    # free_space_piece,
    Piece("═", accept_left_conn=True, accept_right_conn=True),
    mix_vertical_connection_piece,
    Piece("╒", accept_bottom_conn=True, accept_right_conn=True),
    Piece("╕", accept_bottom_conn=True, accept_left_conn=True),
    Piece("╘", accept_top_conn=True, accept_right_conn=True),
    Piece("╛", accept_top_conn=True, accept_left_conn=True),
    Piece("╞", accept_top_conn=True, accept_bottom_conn=True, accept_right_conn=True),
    Piece("╡", accept_top_conn=True, accept_bottom_conn=True, accept_left_conn=True),
    Piece("╤", accept_bottom_conn=True, accept_left_conn=True, accept_right_conn=True),
    Piece("╧", accept_top_conn=True, accept_left_conn=True, accept_right_conn=True),
    Piece("╪", accept_top_conn=True, accept_bottom_conn=True, accept_left_conn=True, accept_right_conn=True),
]

single_vertical_connection_piece = Piece("│", accept_top_conn=True, accept_bottom_conn=True)
pieces2 = [
    # free_space_piece,
    Piece("─", accept_left_conn=True, accept_right_conn=True),
    single_vertical_connection_piece,
    Piece("┌", accept_bottom_conn=True, accept_right_conn=True),
    Piece("┐", accept_bottom_conn=True, accept_left_conn=True),
    Piece("└", accept_top_conn=True, accept_right_conn=True),
    Piece("┘", accept_top_conn=True, accept_left_conn=True),
    Piece("├", accept_top_conn=True, accept_bottom_conn=True, accept_right_conn=True),
    Piece("┤", accept_top_conn=True, accept_bottom_conn=True, accept_left_conn=True),
    Piece("┬", accept_bottom_conn=True, accept_left_conn=True, accept_right_conn=True),
    Piece("┴", accept_top_conn=True, accept_left_conn=True, accept_right_conn=True),
    Piece("┼", accept_top_conn=True, accept_bottom_conn=True, accept_left_conn=True, accept_right_conn=True),
]

block_piece_text = "@"
block_vertical_connection_piece = Piece(block_piece_text, accept_top_conn=True, accept_bottom_conn=True)
pieces3 = [
    # free_space_piece,
    Piece(block_piece_text, accept_left_conn=True, accept_right_conn=True),
    block_vertical_connection_piece,
    Piece(block_piece_text, accept_bottom_conn=True, accept_right_conn=True),
    Piece(block_piece_text, accept_bottom_conn=True, accept_left_conn=True),
    Piece(block_piece_text, accept_top_conn=True, accept_right_conn=True),
    Piece(block_piece_text, accept_top_conn=True, accept_left_conn=True),
    Piece(block_piece_text, accept_top_conn=True, accept_bottom_conn=True, accept_right_conn=True),
    Piece(block_piece_text, accept_top_conn=True, accept_bottom_conn=True, accept_left_conn=True),
    Piece(block_piece_text, accept_bottom_conn=True, accept_left_conn=True, accept_right_conn=True),
    Piece(block_piece_text, accept_top_conn=True, accept_left_conn=True, accept_right_conn=True),
    Piece(block_piece_text, accept_top_conn=True, accept_bottom_conn=True, accept_left_conn=True,
          accept_right_conn=True),
]

pieces = {
    0: {"pieces": pieces0, "vertical_connection_piece": double_vertical_connection_piece},
    1: {"pieces": pieces1, "vertical_connection_piece": mix_vertical_connection_piece},
    2: {"pieces": pieces2, "vertical_connection_piece": single_vertical_connection_piece},
    3: {"pieces": pieces3, "vertical_connection_piece": block_vertical_connection_piece},
    4: {"pieces": pieces0 + pieces1 + pieces2 + pieces3,
        "vertical_connection_piece": choice([double_vertical_connection_piece,
                                             mix_vertical_connection_piece,
                                             single_vertical_connection_piece,
                                             block_vertical_connection_piece])}
}


# check all chars here: https://en.wikipedia.org/wiki/List_of_Unicode_characters


class MapApi:

    def __init__(
            self,
            progress_creation_callback: Callable[[int, str, str], Future[None]],
            cancel_token: CancelToken
    ):
        self._map = []
        self._progress_creation_callback = progress_creation_callback
        self._cancel_token = cancel_token

    @property
    def map(self) -> List[List[Piece]]:
        return self._map

    async def build_map(self, *, rows: int, cols: int, restricted: bool = True, wall_type: int = 0) -> bool:
        logger.info("World generation started")
        if restricted:
            return await self.build_map_with_restrictions(rows=rows, cols=cols, wall_type=wall_type)
        return await self.build_map_without_restrictions(rows=rows, cols=cols, wall_type=wall_type)

    @staticmethod
    async def build_map_without_restrictions(*, rows: int, cols: int, wall_type: int = 0) -> bool:
        "\n".join([
            "".join([choice(pieces[wall_type]["pieces"]).text for _ in range(cols)])
            for _ in range(rows)
        ])
        return True

    async def build_map_with_restrictions(self, *, rows: int, cols: int, wall_type: int = 0) -> bool:
        r = 0
        while r < rows and not self._cancel_token.is_cancelled:
            columns = []
            self._map.append(columns)
            new_file_required = False
            c = 0
            while c < cols and not self._cancel_token.is_cancelled:
                coordinate = Coordinate(r, c)
                piece = self._select_piece(coordinate, wall_type)
                if c > 0:
                    left_piece = self._map[coordinate.row][coordinate.col - 1]
                    if not piece.accept_left_conn and not left_piece.accept_right_conn:
                        columns.append(deepcopy(free_space_piece))
                        c += 1
                if c < cols:
                    columns.append(piece)
                    top_piece = self._map[coordinate.row][c]
                    free_horizontal_space_required = not top_piece.accept_bottom_conn and not piece.accept_top_conn
                    new_file_required = new_file_required or free_horizontal_space_required
                    c += 1

            if r > 0 and new_file_required and not self._cancel_token.is_cancelled:
                self._map.append(deepcopy(columns))
                r += 1
                c = 0
                while c < cols and not self._cancel_token.is_cancelled:
                    top_piece = self._map[r - 2][c]
                    piece = self._map[r][c]
                    if top_piece != free_space_piece and top_piece.accept_bottom_conn and piece.accept_top_conn:
                        vertical_conn_piece = pieces[wall_type]["vertical_connection_piece"]
                        self._map[r - 1][c] = deepcopy(vertical_conn_piece) if choice([True, False]) else deepcopy(
                            free_space_piece)
                    else:
                        self._map[r - 1][c] = deepcopy(free_space_piece)
                    c += 1
                if not self._cancel_token.is_cancelled:
                    self._progress_creation_callback(r, self.print_map_line(self._map[r - 1]),
                                                     "{:.2f}".format(min(100.00, (r / rows) * 100)))

            r += 1
            if not self._cancel_token.is_cancelled:
                self._progress_creation_callback(r, self.print_map_line(self._map[r - 1]),
                                                 "{:.2f}".format(min(100.00, (r / rows) * 100)))
            await asyncio.sleep(1e-9)
        if self._cancel_token.is_cancelled:
            logger.info("World generation canceled")
        else:
            logger.info("World generated successfully")

        return not self._cancel_token.is_cancelled

    def print_map(self):
        m = "\n".join([
            self.print_map_line(r)
            for r in self._map
        ])

        return m

    @staticmethod
    def print_map_line(row: List[Piece]) -> str:
        return "".join([p.text for p in row])

    def print_coordinate(self, coordinate: Coordinate):
        logger.info(self._map[coordinate.row][coordinate.col].text)

    def _select_piece(self, coordinate: Coordinate, wall_type: int = 0) -> Piece:
        """
        Apply ¬XOR ( not(A ^ B) )to ensure only if restrictions apply in both sides of connection
        the piece is accepted
        """
        piece = None
        match = False
        while not match:
            piece = deepcopy(choice(pieces[wall_type]["pieces"]))
            match_top = True
            match_left = True
            if coordinate.row > 0:
                top_piece = self._map[coordinate.row - 1][coordinate.col]
                match_top = not (piece.accept_top_conn ^ top_piece.accept_bottom_conn)
            if coordinate.col > 0:
                left_piece = self._map[coordinate.row][coordinate.col - 1]
                match_left = not (piece.accept_left_conn ^ left_piece.accept_right_conn)

            match = match_top and match_left

        return piece

    def _coordinate_in_bounds(self, coordinate: Coordinate) -> bool:
        return len(self._map) > coordinate.row >= 0 and len(self._map[0]) > coordinate.col >= 0
