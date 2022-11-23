import threading


class Piece:
    def __init__(self, text: str,
                 accept_top_conn: bool = False,
                 accept_bottom_conn: bool = False,
                 accept_left_conn: bool = False,
                 accept_right_conn: bool = False,
                 is_available_spot: bool = False):
        self.text = text
        self.accept_top_conn = accept_top_conn
        self.accept_bottom_conn = accept_bottom_conn
        self.accept_left_conn = accept_left_conn
        self.accept_right_conn = accept_right_conn
        self._is_available_spot = is_available_spot
        self._visited = set()
        self._visiting = 0

    @property
    def is_available_spot(self):
        return self._is_available_spot

    @property
    def visited(self):
        return self._visited

    @visited.setter
    def visited(self, value):
        self._visited.add(value)

    def visiting(self):
        self._visiting += 1

    def unvisiting(self) -> bool:
        self._visiting -= 1
        self._visiting = 0 if self._visiting < 0 else self._visiting
        return self._visiting == 0
