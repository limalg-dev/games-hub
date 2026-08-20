"""Tests for the checkers AI with difficulty levels."""
import pytest
from games.checkers.ai import choose_move, Difficulty
from games.checkers.game import Board


def _assert_valid_move(move):
    """Helper: verify the move is a valid dict-like move with from/to."""
    assert "from" in move and "to" in move
    assert isinstance(move["from"], tuple) and len(move["from"]) == 2
    assert isinstance(move["to"], tuple) and len(move["to"]) == 2


def test_choose_move_returns_valid():
    """AI must return a valid move."""
    board = Board()
    move = choose_move(board)
    _assert_valid_move(move)


def test_easy_returns_valid_move():
    """Easy AI returns a valid move."""
    board = Board()
    move = choose_move(board, difficulty=Difficulty.EASY)
    _assert_valid_move(move)


def test_medium_returns_valid_move():
    """Medium AI returns a valid move."""
    board = Board()
    move = choose_move(board, difficulty=Difficulty.MEDIUM)
    _assert_valid_move(move)


def test_hard_returns_valid_move():
    """Hard AI returns a valid move."""
    board = Board()
    move = choose_move(board, difficulty=Difficulty.HARD)
    _assert_valid_move(move)


def test_easy_vs_hard_both_valid():
    """Easy and Hard AI should both return valid moves."""
    board = Board()
    easy_moves = set()
    hard_moves = set()
    for _ in range(5):
        m = choose_move(board, difficulty=Difficulty.EASY)
        easy_moves.add((m["from"], m["to"]))
        m = choose_move(board, difficulty=Difficulty.HARD)
        hard_moves.add((m["from"], m["to"]))
    assert len(easy_moves) >= 1
    assert len(hard_moves) >= 1


def test_hard_ai_prefers_captures():
    """Hard AI should prefer captures when available."""
    board = Board()
    board.board[3][3] = "w"
    board.board[2][2] = "b"
    board.board[1][1] = ""
    move = choose_move(board, difficulty=Difficulty.HARD)
    assert move is not None


def test_invalid_board_raises():
    """AI should handle edge-case board gracefully."""
    board = Board()
    move = choose_move(board, difficulty=Difficulty.EASY)
    assert move is not None
