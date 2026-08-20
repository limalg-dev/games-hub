"""Tests for Checkers (Damas) — Brazilian rules."""
from games.checkers.game import Board


# ── Basic board tests ────────────────────────────────────────────

def test_initial_board():
    b = Board()
    assert len(b.board) == 8
    assert len(b.board[0]) == 8


def test_initial_piece_count():
    b = Board()
    assert sum(row.count("b") for row in b.board) == 12
    assert sum(row.count("w") for row in b.board) == 12


def test_piece_at_start():
    b = Board()
    assert b.board[0][0] == "b"
    assert b.board[7][1] == "w"


def test_moves_initial_white():
    b = Board()
    moves = b.legal_moves("w")
    assert len(moves) > 0
    for m in moves:
        assert "from" in m and "to" in m
        fr, to = m["from"], m["to"]
        assert 0 <= fr[0] < 8 and 0 <= fr[1] < 8
        assert 0 <= to[0] < 8 and 0 <= to[1] < 8


def test_apply_move():
    b = Board()
    b.apply_move((5, 1), (4, 0))
    assert b.board[5][1] == ""
    assert b.board[4][0] == "w"


def test_apply_move_with_captured():
    """Test apply_move removes captured pieces."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[4][3] = "w"
    b.board[3][4] = "b"
    b.apply_move((4, 3), (2, 5), captured=[(3, 4)])
    assert b.board[4][3] == ""
    assert b.board[3][4] == ""
    assert b.board[2][5] == "w"


# ── King sliding tests ──────────────────────────────────────────

def test_king_slides_multiple_squares():
    """King can slide multiple empty squares along a diagonal."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[4][4] = "W"  # White king

    moves = b.legal_moves("w")
    # King at (4,4) should be able to reach (3,3), (2,2), (1,1), (0,0)
    # and (3,5), (2,6), (1,7) and (5,3), (6,2), (7,1) and (5,5), (6,6), (7,7)
    king_moves = [m for m in moves if m["from"] == (4, 4)]
    targets = {m["to"] for m in king_moves}
    assert (3, 3) in targets  # 1 square
    assert (2, 2) in targets  # 2 squares
    assert (1, 1) in targets  # 3 squares
    assert (0, 0) in targets  # 4 squares
    assert (3, 5) in targets
    assert (5, 5) in targets
    assert (7, 7) in targets


def test_king_blocked_by_piece():
    """King cannot slide through or past another piece."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[4][4] = "W"
    b.board[2][2] = "w"  # Friendly piece blocks

    moves = b.legal_moves("w")
    king_moves = [m for m in moves if m["from"] == (4, 4)]
    targets = {m["to"] for m in king_moves}
    assert (3, 3) in targets  # Can reach one square before blocker
    assert (2, 2) not in targets  # Blocked
    assert (1, 1) not in targets  # Beyond blocker


def test_king_blocked_by_edge():
    """King cannot slide off the board."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[0][0] = "W"

    moves = b.legal_moves("w")
    king_moves = [m for m in moves if m["from"] == (0, 0)]
    # King at corner should only go down-right
    assert all(m["to"][0] >= 0 and m["to"][1] >= 0 for m in king_moves)


# ── Mandatory capture tests ─────────────────────────────────────

def test_mandatory_capture():
    """If a capture is available, only captures are returned."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[4][3] = "w"
    b.board[3][4] = "b"
    b.board[2][5] = ""  # Landing square

    moves = b.legal_moves("w")
    # Should only have captures, no normal moves
    assert all(m["capture"] for m in moves)
    assert len(moves) >= 1
    assert moves[0]["to"] == (2, 5)


def test_no_captures_returns_normal_moves():
    """When no captures exist, normal moves are returned."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[4][3] = "w"
    # No enemy nearby → only normal moves
    moves = b.legal_moves("w")
    assert all(not m["capture"] for m in moves)
    assert len(moves) > 0


def test_has_captures():
    """has_captures correctly detects available captures."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[4][3] = "w"
    b.board[3][4] = "b"
    b.board[2][5] = ""
    assert b.has_captures("w") is True

    b.board[3][4] = ""
    assert b.has_captures("w") is False


def test_get_captures_for():
    """get_captures_for returns captures for a specific piece."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[4][3] = "w"
    b.board[3][4] = "b"
    b.board[2][5] = ""

    caps = b.get_captures_for(4, 3, "w")
    assert len(caps) >= 1
    assert caps[0]["to"] == (2, 5)
    assert caps[0]["captured"] == [(3, 4)]


# ── Multi-capture chain tests ───────────────────────────────────

def test_multi_capture_chain():
    """Piece that can capture multiple times in a row."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    # Setup: w at (4,1), enemies at (3,2) and (1,2), landing at (2,3) and (0,1)
    b.board[4][1] = "w"
    b.board[3][2] = "b"
    b.board[1][2] = "b"
    b.board[2][3] = ""  # First landing
    b.board[0][1] = ""  # Second landing

    moves = b.legal_moves("w")
    # Should find a multi-capture: (4,1)→(2,3)→(0,1) capturing (3,2) and (1,2)
    chain_moves = [m for m in moves if m["capture"] and len(m.get("captured", [])) >= 2]
    assert len(chain_moves) >= 1, f"Expected multi-capture chain, got: {moves}"
    assert (3, 2) in chain_moves[0]["captured"]
    assert (1, 2) in chain_moves[0]["captured"]


def test_regular_piece_single_jump_only():
    """Regular (non-king) piece can only jump one square at a time."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[5][1] = "w"
    b.board[3][1] = "b"  # 2 squares away — can't jump directly
    b.board[4][1] = ""  # Empty between

    moves = b.legal_moves("w")
    # Regular piece at (5,1) should NOT be able to jump to (1,1)
    targets = {m["to"] for m in moves if m["from"] == (5, 1)}
    assert (1, 1) not in targets


# ── King capture tests ──────────────────────────────────────────

def test_king_capture_slides():
    """King can capture by sliding multiple squares to land beyond enemy."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[6][6] = "W"  # White king
    b.board[3][3] = "b"  # Enemy at distance

    moves = b.legal_moves("w")
    king_caps = [m for m in moves if m["capture"] and m["from"] == (6, 6)]
    # King should be able to capture (3,3) and land at (2,2), (1,1), or (0,0)
    assert len(king_caps) >= 1
    assert (3, 3) in king_caps[0]["captured"]


def test_king_cannot_jump_own_piece():
    """King cannot capture its own color."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[6][6] = "W"
    b.board[3][3] = "w"  # Own piece

    moves = b.legal_moves("w")
    king_caps = [m for m in moves if m["capture"] and m["from"] == (6, 6)]
    for cap in king_caps:
        assert (3, 3) not in cap["captured"]


# ── King promotion tests ────────────────────────────────────────

def test_white_king_promotion():
    """White piece promotes to king when reaching row 0."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[1][1] = "w"
    b.apply_move((1, 1), (0, 0))
    assert b.board[0][0] == "W"


def test_black_king_promotion():
    """Black piece promotes to king when reaching row 7."""
    b = Board()
    b.board = [[""] * 8 for _ in range(8)]
    b.board[6][6] = "b"
    b.apply_move((6, 6), (7, 7))
    assert b.board[7][7] == "B"


# ── AI integration test ─────────────────────────────────────────

def test_ai_handles_new_rules():
    """AI should work correctly with the new move format."""
    from games.checkers.ai import choose_move
    b = Board()
    move = choose_move(b, "w")
    assert move is not None
    # AI returns (from_tuple, to_tuple)
    fr, to = move
    assert len(fr) == 2 and len(to) == 2
