"""Checkers AI — Minimax with alpha-beta pruning + positional heuristics."""
from __future__ import annotations
from typing import Optional
from games.checkers.game import Board


# ── Positional weights: prefer center squares ────────────────────
_POSITION = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 4, 4, 4, 4, 4, 0],
    [0, 4, 6, 6, 6, 6, 4, 0],
    [0, 4, 6, 8, 8, 6, 4, 0],
    [0, 4, 6, 8, 8, 6, 4, 0],
    [0, 4, 6, 6, 6, 6, 4, 0],
    [0, 4, 4, 4, 4, 4, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]


def _apply_board_move(b: Board, m):
    if isinstance(m, dict):
        b.apply_move(m["from"], m["to"], m.get("captured"))
    else:
        b.apply_move(m[0], m[1])


def _extract_move_coords(m) -> tuple[tuple[int, int], tuple[int, int]]:
    if isinstance(m, dict):
        return (m["from"], m["to"])
    return (m[0], m[1])


def choose_move(board: Board, color: str = "w", depth: int = 3):
    """Return the best move for `color` using minimax(depth)."""
    moves = board.legal_moves(color)
    if not moves:
        return None
    if len(moves) == 1:
        return moves[0]

    opp = "b" if color == "w" else "w"
    best_move = moves[0]
    best_score = -1e9

    for i, move in enumerate(moves):
        child = Board()
        child.board = [row[:] for row in board.board]
        _apply_board_move(child, move)
        score = -minimax(child, depth - 1, -1e9, 1e9, opp)
        score += (i % 7) * 1e-4
        if score > best_score:
            best_score = score
            best_move = move
    return best_move


def minimax(board: Board, depth: int, alpha: float, beta: float,
            color: str) -> float:
    if depth == 0:
        return evaluate(board, color)

    moves = board.legal_moves(color)
    if not moves:
        return -10000

    opp = "b" if color == "w" else "w"

    if color == "w":
        value = -1e9
        for move in moves:
            child = Board()
            child.board = [row[:] for row in board.board]
            _apply_board_move(child, move)
            value = max(value, minimax(child, depth - 1, alpha, beta, opp))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 1e9
        for move in moves:
            child = Board()
            child.board = [row[:] for row in board.board]
            _apply_board_move(child, move)
            value = min(value, minimax(child, depth - 1, alpha, beta, opp))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def evaluate(board: Board, ai_color: str = "w") -> float:
    """
    Evaluate the board: 10 per regular piece, 15 per king.
    Positive = good for White (when ai_color == 'w').
    """
    score = 0.0
    for r in range(8):
        for c in range(8):
            p = board.board[r][c]
            if not p:
                continue
            val = 15.0 if p.isupper() else 10.0
            if p.lower() == "w":
                score += val
            else:
                score -= val
    return score if ai_color == "w" else -score
