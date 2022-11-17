from random import choice
from typing import List

from map_builder.Piece import Piece

pieces0 = [
    Piece("═", accept_left_conn=True, accept_right_conn=True),
    Piece("║", accept_top_conn=True, accept_bottom_conn=True),
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

pieces1 = [
    Piece("═", accept_left_conn=True, accept_right_conn=True),
    Piece("│", accept_top_conn=True, accept_bottom_conn=True),
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

pieces2 = [
    Piece("─", accept_left_conn=True, accept_right_conn=True),
    Piece("│", accept_top_conn=True, accept_bottom_conn=True),
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

pieces = {
    0: pieces0, 1: pieces1, 2: pieces2
}


# ["═","║","╒","╓","╔","╕","╖","╗","╘","╙","╚","╛","╜","╝","╞","╟","╠","╡","╢","╣","╤","╥","╦","╧","╨","╩","╪"]
# check all chars here: https://en.wikipedia.org/wiki/List_of_Unicode_characters


class MapApi:

    def __init__(self):
        pass

    @staticmethod
    def build_map(*, rows: int, cols: int, restricted: bool = True, wall_type: int = 0) -> str:
        if restricted:
            return MapApi.build_map_with_restrictions(rows=rows, cols=cols, wall_type=wall_type)
        return MapApi.build_map_without_restrictions(rows=rows, cols=cols, wall_type=wall_type)

    @staticmethod
    def build_map_without_restrictions(*, rows: int, cols: int, wall_type: int = 0) -> List[List[str]]:
        random_pieces = "\n".join([
            "".join([choice(pieces[wall_type]).text for i in range(cols)])
            for r in range(rows)
        ])
        return random_pieces

    @staticmethod
    def build_map_with_restrictions(*, rows: int, cols: int, wall_type: int = 0) -> str:
        rowz = []
        for r in range(rows):
            colz = []
            rowz.append(colz)
            for c in range(cols):
                colz.append(MapApi._select_piece(rowz, r, c, wall_type))

        map = "\n".join([
            "".join([p.text for p in r])
            for r in rowz
        ])

        print()
        print(map)

        return map

    @staticmethod
    def _select_piece(matrix: List[List[Piece]], row: int, col: int, wall_type: int = 0) -> Piece:
        """
        Apply ¬XOR ( not(A ^ B) )to ensure only if restrictions apply in both sides of connection
        the piece is accepted
        """
        piece = None
        match = False
        while not match:
            piece = choice(pieces[wall_type])
            match_top = True
            match_left = True
            if row > 0:
                top_piece = matrix[row - 1][col]
                match_top = not (piece.accept_top_conn ^ top_piece.accept_bottom_conn)
            if col > 0:
                left_piece = matrix[row][col - 1]
                match_left = not (piece.accept_left_conn ^ left_piece.accept_right_conn)

            match = match_top and match_left

        return piece
