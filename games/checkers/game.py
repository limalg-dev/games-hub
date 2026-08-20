"""Checkers (Damas) — Board with Brazilian/international rules.

Rules enforced:
- Mandatory capture: if a capture exists, only captures are legal.
- Multi-capture chain: after a capture, if the same piece can capture
  again, the turn continues (the full chain is one logical move).
- King movement: slides any number of empty squares along a diagonal
  (like a bishop in chess). Captures still land exactly one square
  beyond the jumped piece.
"""
from __future__ import annotations
from typing import List, Tuple, Optional, Any


class CheckersMove(dict):
    """Dict-compatible move representation that also supports 2-tuple unpacking (fr, to)."""
    def __init__(self, fr: Tuple[int, int], to: Tuple[int, int],
                 capture: bool = False, captured: Optional[List[Tuple[int, int]]] = None,
                 distance: int = 1):
        super().__init__({
            "from": fr,
            "to": to,
            "capture": capture,
            "captured": captured or [],
            "distance": distance,
        })

    def __iter__(self):
        return iter((self["from"], self["to"]))

    def __getitem__(self, key: Any):
        if key == 0:
            return self["from"]
        if key == 1:
            return self["to"]
        return super().__getitem__(key)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, tuple) and len(other) == 2:
            return (self["from"], self["to"]) == other
        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash((self["from"], self["to"]))


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

    def _is_on_board(self, r: int, c: int) -> bool:
        return 0 <= r < 8 and 0 <= c < 8

    def _piece_color(self, r: int, c: int) -> Optional[str]:
        p = self.board[r][c]
        return p.lower() if p else None

    def _is_enemy(self, r: int, c: int, color: str) -> bool:
        p = self.board[r][c]
        return bool(p) and p.lower() != color

    # ── Normal (non-capture) moves ───────────────────────────────

    def _normal_moves_for(self, r: int, c: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Return simple moves for the piece at (r, c)."""
        piece = self.board[r][c]
        if not piece:
            return []
        color = piece.lower()
        is_king = piece.isupper()
        moves: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []

        if is_king:
            # King slides along each diagonal until blocked
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                for dist in range(1, 8):
                    nr, nc = r + dr * dist, c + dc * dist
                    if not self._is_on_board(nr, nc):
                        break
                    if self.board[nr][nc]:
                        break  # blocked
                    moves.append(((r, c), (nr, nc)))
        else:
            # Regular piece: one step forward
            dirs = [(-1, -1), (-1, 1)] if color == "w" else [(1, -1), (1, 1)]
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if self._is_on_board(nr, nc) and not self.board[nr][nc]:
                    moves.append(((r, c), (nr, nc)))
        return moves

    # ── Capture moves (single + multi-chain) ─────────────────────

    def _find_captures_from(self, r: int, c: int, color: str, is_king: bool
                            ) -> List[CheckersMove]:
        """Find all capture sequences starting from (r, c)."""
        results: List[CheckersMove] = []
        self._dfs_captures(r, c, color, is_king, [], set(), results, r, c)
        return results

    def _dfs_captures(self, r: int, c: int, color: str, is_king: bool,
                      path: List[Tuple[int, int]],
                      visited: set, results: List[CheckersMove],
                      start_r: int, start_c: int):
        found_any = False
        if is_king:
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                for dist in range(1, 8):
                    mid_r, mid_c = r + dr * dist, c + dc * dist
                    if not self._is_on_board(mid_r, mid_c):
                        break
                    if self.board[mid_r][mid_c]:
                        if self._is_enemy(mid_r, mid_c, color) and (mid_r, mid_c) not in visited:
                            for land_dist in range(dist + 1, 8):
                                land_r, land_c = r + dr * land_dist, c + dc * land_dist
                                if not self._is_on_board(land_r, land_c):
                                    break
                                if self.board[land_r][land_c]:
                                    break
                                found_any = True
                                new_visited = visited | {(mid_r, mid_c)}
                                new_path = path + [(mid_r, mid_c)]
                                self._dfs_captures(
                                    land_r, land_c, color, True,
                                    new_path, new_visited, results,
                                    start_r, start_c
                                )
                        break
        else:
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                mid_r, mid_c = r + dr, c + dc
                land_r, land_c = r + 2 * dr, c + 2 * dc
                if not self._is_on_board(land_r, land_c):
                    continue
                if not self._is_on_board(mid_r, mid_c):
                    continue
                if (mid_r, mid_c) in visited:
                    continue
                if (self._is_enemy(mid_r, mid_c, color)
                        and not self.board[land_r][land_c]):
                    found_any = True
                    new_visited = visited | {(mid_r, mid_c)}
                    new_path = path + [(mid_r, mid_c)]
                    self._dfs_captures(
                        land_r, land_c, color, False,
                        new_path, new_visited, results,
                        start_r, start_c
                    )

        if not found_any and path:
            dist = max(abs(r - start_r), abs(c - start_c))
            results.append(CheckersMove(
                fr=(start_r, start_c),
                to=(r, c),
                capture=True,
                captured=list(path),
                distance=dist,
            ))

    # ── Legal moves (enforcing mandatory capture) ────────────────

    def legal_moves(self, color: str) -> List[CheckersMove]:
        """Return all legal moves for `color`.
        Format: CheckersMove ({ from, to, capture: bool, captured?: list, distance?: int })
        If any capture exists, ONLY captures are returned (mandatory capture).
        """
        all_captures: List[CheckersMove] = []
        all_normal: List[CheckersMove] = []

        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if not piece or piece.lower() != color:
                    continue
                is_king = piece.isupper()

                caps = self._find_captures_from(r, c, color, is_king)
                all_captures.extend(caps)

                for (fr, fc), (tr, tc) in self._normal_moves_for(r, c):
                    dist = max(abs(tr - fr), abs(tc - fc))
                    all_normal.append(CheckersMove(
                        fr=(fr, fc),
                        to=(tr, tc),
                        capture=False,
                        distance=dist,
                    ))

        if all_captures:
            return all_captures
        return all_normal

    # ── Apply move ───────────────────────────────────────────────

    def apply_move(self, fr: Tuple[int, int], to: Tuple[int, int],
                   captured: Optional[List[Tuple[int, int]]] = None):
        """Move piece from fr to to, removing captured pieces."""
        fr_r, fr_c = fr
        to_r, to_c = to
        piece = self.board[fr_r][fr_c]
        if not piece:
            return

        self.board[fr_r][fr_c] = ""
        self.board[to_r][to_c] = piece

        if captured:
            for mr, mc in captured:
                self.board[mr][mc] = ""
        elif abs(to_r - fr_r) == 2 or abs(to_c - fr_c) == 2:
            mid_r = (fr_r + to_r) // 2
            mid_c = (fr_c + to_c) // 2
            self.board[mid_r][mid_c] = ""

        # King promotion
        if piece == "w" and to_r == 0:
            self.board[to_r][to_c] = "W"
        elif piece == "b" and to_r == 7:
            self.board[to_r][to_c] = "B"

    def has_captures(self, color: str) -> bool:
        """Check if `color` has any capture available."""
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if not piece or piece.lower() != color:
                    continue
                is_king = piece.isupper()
                if self._find_captures_from(r, c, color, is_king):
                    return True
        return False

    def get_captures_for(self, r: int, c: int, color: str) -> List[CheckersMove]:
        """Get capture moves for a specific piece at (r, c)."""
        piece = self.board[r][c]
        if not piece or piece.lower() != color:
            return []
        return self._find_captures_from(r, c, color, piece.isupper())
