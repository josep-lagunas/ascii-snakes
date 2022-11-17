class Piece:
    def __init__(self, text: str,
                 accept_top_conn: bool = False,
                 accept_bottom_conn: bool = False,
                 accept_left_conn: bool = False,
                 accept_right_conn: bool = False,):
        self.text = text
        self.accept_top_conn = accept_top_conn
        self.accept_bottom_conn = accept_bottom_conn
        self.accept_left_conn = accept_left_conn
        self.accept_right_conn = accept_right_conn
