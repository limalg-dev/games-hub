from __future__ import annotations

class Board:
    def __init__(self):
        self.board = [[""] * 8 for _ in range(8)]
        self._setup()

    def _setup(self):
        for r in range(3):
            for c in range(8):
                if (r + c) % 2 == 0:
                    self.board[r][c] = "b"
        for r in range(5, 8):
            for c in range(8):
                if (r + c) % 2 == 0:
                    self.board[r][c] = "w"

    def _is_on_board(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def legal_moves(self, color):
        moves = []
        captures = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if not piece or piece.lower() != color:
                    continue
                is_king = piece.isupper()
                for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    if not is_king and dr < 0 and color == "b":
                        continue
                    if not is_king and dr > 0 and color == "w":
                        continue
                    nr, nc = r + dr, c + dc
                    if self._is_on_board(nr, nc) and self.board[nr][nc] == "":
                        moves.append(((r, c), (nr, nc)))
                    # capture
                    cr, cc = r + 2 * dr, c + 2 * dc
                    if self._is_on_board(cr, cc) and self.board[cr][cc] == "":
                        mid = self.board[nr][nc]
                        if mid and mid.lower() != color:
                            captures.append(((r, c), (cr, cc)))
        if captures:
            return captures
        return moves

    def apply_move(self, fr, to):
        fr_r, fr_c = fr
        to_r, to_c = to
        piece = self.board[fr_r][fr_c]
        self.board[fr_r][fr_c] = ""
        self.board[to_r][to_c] = piece
        # remove captured piece if it was a capture
        if abs(to_r - fr_r) == 2:
            mid_r = (fr_r + to_r) // 2
            mid_c = (fr_c + to_c) // 2
            self.board[mid_r][mid_c] = ""
        # promote to king
        if piece == "w" and to_r == 0:
            self.board[to_r][to_c] = "W"
        elif piece == "b" and to_r == 7:
            self.board[to_r][to_c] = "B"
