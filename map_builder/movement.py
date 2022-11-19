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

    def get_above_coordinate(self):
        return Coordinate(self._row - 1, self.col)

    def get_below_coordinate(self):
        return Coordinate(self._row + 1, self.col)

    def get_right_coordinate(self):
        return Coordinate(self._row, self._col + 1)

    def get_left_coordinate(self):
        return Coordinate(self._row, self._col - 1)
