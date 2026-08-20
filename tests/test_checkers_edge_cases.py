"""
Tests for Checkers game edge cases: king promotion, king movement,
capture rules, game over detection, AI behavior, evaluate function.
"""

import pytest
from games.checkers.game import Board
from games.checkers.ai import choose_move, evaluate


class TestKingPromotion:
    """Tests for king promotion"""

    def test_white_promotion(self):
        """White piece reaching row 0 becomes king 'W'"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[1][0] = "w"  # White piece one step from promotion

        board.apply_move((1, 0), (0, 1))
        assert board.board[0][1] == "W"

    def test_black_promotion(self):
        """Black piece reaching row 7 becomes king 'B'"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[6][1] = "b"  # Black piece one step from promotion

        board.apply_move((6, 1), (7, 0))
        assert board.board[7][0] == "B"

    def test_no_promotion_mid_board(self):
        """Piece moving within the board does not promote"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[3][2] = "w"

        board.apply_move((3, 2), (2, 3))
        assert board.board[2][3] == "w"  # Still lowercase


class TestKingMovement:
    """Tests for king movement in all directions"""

    def test_white_king_moves_all_directions(self):
        """White king can move forward and backward"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "W"  # White king in center

        moves = board.legal_moves("w")
        destinations = {m[1] for m in moves}

        # King should be able to move in all 4 diagonal directions
        assert (3, 3) in destinations  # up-left
        assert (3, 5) in destinations  # up-right
        assert (5, 3) in destinations  # down-left
        assert (5, 5) in destinations  # down-right

    def test_black_king_moves_all_directions(self):
        """Black king can move forward and backward"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "B"  # Black king in center

        moves = board.legal_moves("b")
        destinations = {m[1] for m in moves}

        assert (3, 3) in destinations
        assert (3, 5) in destinations
        assert (5, 3) in destinations
        assert (5, 5) in destinations

    def test_regular_white_cannot_move_backward(self):
        """Regular white piece cannot move backward (down)"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "w"

        moves = board.legal_moves("w")
        destinations = {m[1] for m in moves}

        # White moves UP only (dr < 0)
        assert (3, 3) in destinations
        assert (3, 5) in destinations
        assert (5, 3) not in destinations
        assert (5, 5) not in destinations

    def test_regular_black_cannot_move_backward(self):
        """Regular black piece cannot move backward (up)"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "b"

        moves = board.legal_moves("b")
        destinations = {m[1] for m in moves}

        # Black moves DOWN only (dr > 0)
        assert (5, 3) in destinations
        assert (5, 5) in destinations
        assert (3, 3) not in destinations
        assert (3, 5) not in destinations


class TestCaptureRules:
    """Tests for capture mechanics"""

    def test_capture_removes_opponent_piece(self):
        """After a capture, the jumped piece is removed"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "w"
        board.board[3][3] = "b"  # Opponent piece to capture

        board.apply_move((4, 4), (2, 2))
        assert board.board[2][2] == "w"
        assert board.board[3][3] == ""  # Captured piece removed
        assert board.board[4][4] == ""  # Original position empty

    def test_forced_capture_rule(self):
        """When captures exist, only captures are returned (no regular moves)"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "w"
        board.board[3][3] = "b"  # Can capture this

        moves = board.legal_moves("w")
        # Should only return captures, not regular moves
        for move in moves:
            fr, to = move
            assert abs(to[0] - fr[0]) == 2  # All moves should be captures (2 squares)

    def test_multiple_captures_available(self):
        """When multiple captures exist, all are returned"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "w"
        board.board[3][3] = "b"  # Can capture left
        board.board[3][5] = "b"  # Can capture right

        moves = board.legal_moves("w")
        assert len(moves) == 2
        destinations = {m[1] for m in moves}
        assert (2, 2) in destinations
        assert (2, 6) in destinations

    def test_king_capture_backward(self):
        """King can capture backward"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[2][2] = "W"  # White king
        board.board[3][3] = "b"  # Black piece behind

        moves = board.legal_moves("w")
        captures = [m for m in moves if abs(m[1][0] - m[0][0]) == 2]
        destinations = {m[1] for m in captures}
        assert (4, 4) in destinations


class TestGameOver:
    """Tests for game over detection"""

    def test_no_moves_means_game_over(self):
        """When a color has no legal moves, game is effectively over"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        # Black piece trapped in corner with no moves
        board.board[7][0] = "b"
        board.board[6][1] = "w"  # This blocks the only forward diagonal
        board.board[5][2] = "w"  # This blocks the capture landing square

        moves = board.legal_moves("b")
        assert len(moves) == 0

    def test_empty_board_no_moves(self):
        """Empty board returns no legal moves"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]

        assert board.legal_moves("w") == []
        assert board.legal_moves("b") == []


class TestAI:
    """Tests for AI behavior"""

    def test_ai_chooses_capture_when_available(self):
        """AI should choose a capture move when one is available"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "w"
        board.board[3][3] = "b"
        # White must capture (forced by legal_moves)

        move = choose_move(board, "w")
        assert move is not None
        fr, to = move
        assert abs(to[0] - fr[0]) == 2  # It's a capture

    def test_ai_returns_none_when_no_moves(self):
        """choose_move returns None when no legal moves exist"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        # No white pieces
        result = choose_move(board, "w")
        assert result is None

    def test_ai_returns_valid_move(self):
        """AI returns a move that is in legal_moves"""
        board = Board()  # Standard initial board
        move = choose_move(board, "w")
        assert move is not None
        assert move in board.legal_moves("w")


class TestEvaluate:
    """Tests for the evaluate function"""

    def test_evaluate_equal_board(self):
        """Initial board should have roughly equal score"""
        board = Board()
        score = evaluate(board)
        assert score == 0.0  # 12 white = 120, 12 black = -120, net = 0

    def test_evaluate_white_advantage(self):
        """Board with more white pieces scores positive"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "w"  # +10

        score = evaluate(board)
        assert score == 10.0

    def test_evaluate_black_advantage(self):
        """Board with more black pieces scores negative"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "b"  # -10

        score = evaluate(board)
        assert score == -10.0

    def test_evaluate_kings_worth_more(self):
        """Kings are worth 15, regular pieces 10"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[4][4] = "W"  # +15
        board.board[3][3] = "b"  # -10

        score = evaluate(board)
        assert score == 5.0  # 15 - 10

    def test_evaluate_mixed(self):
        """Mixed board with kings and regular pieces"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[0][0] = "W"  # +15
        board.board[1][1] = "w"  # +10
        board.board[6][6] = "B"  # -15
        board.board[5][5] = "b"  # -10

        score = evaluate(board)
        assert score == 0.0  # 25 - 25


class TestBoardBoundary:
    """Tests for board boundary checks"""

    def test_piece_at_edge_limited_moves(self):
        """Piece at board edge has limited moves"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[5][0] = "w"  # Left edge

        moves = board.legal_moves("w")
        # Can only move up-right (4, 1), not up-left (4, -1)
        assert len(moves) == 1
        assert moves[0] == ((5, 0), (4, 1))

    def test_piece_at_corner(self):
        """Piece at corner has very limited moves"""
        board = Board()
        board.board = [[""] * 8 for _ in range(8)]
        board.board[7][7] = "b"  # Bottom-right corner, black can't move down

        moves = board.legal_moves("b")
        assert len(moves) == 0  # Black at row 7 can't move further down
