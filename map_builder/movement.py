class Coordinate:
    def __init__(self, row, col):
        self._row = row
        self._col = col

    @property
    def row(self):
        return self._row

    @property
    def col(self):
        return self._col

    def get_north_coordinate(self):
        return Coordinate(self.row - 1, self.col)

    def get_north_east_coordinate(self):
        return Coordinate(self.row - 1, self.col + 1)

    def get_north_west_coordinate(self):
        return Coordinate(self.row - 1, self.col - 1)

    def get_south_coordinate(self):
        return Coordinate(self.row + 1, self.col)

    def get_south_east_coordinate(self):
        return Coordinate(self.row + 1, self.col + 1)

    def get_south_west_coordinate(self):
        return Coordinate(self.row + 1, self.col - 1)

    def get_east_coordinate(self):
        return Coordinate(self.row, self.col + 1)

    def get_west_coordinate(self):
        return Coordinate(self.row, self.col - 1)

    def __eq__(self, other):
        if not other:
            return False
        return self._row == other.row and self._col == other.col

    def __hash__(self):
        return hash((self._row, self._col,))

    def __str__(self):
        return f"{self._row}, {self. _col}"
