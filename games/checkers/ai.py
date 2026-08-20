"""Checkers AI — Minimax with alpha-beta pruning + difficulty levels.

Difficulty levels control search depth and evaluation sophistication:
  EASY   (depth 2): material only, no positional heuristics.
  MEDIUM (depth 3): material + positional weights.
  HARD   (depth 5): material + positional + mobility + advancement + king safety.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional
from games.checkers.game import Board


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


CHALLENGE_CONFIGS = {
    Difficulty.EASY: {
        "depth": 2,
        "use_positional": False,
        "use_mobility": False,
        "use_advancement": False,
        "label": "Fácil",
    },
    Difficulty.MEDIUM: {
        "depth": 3,
        "use_positional": True,
        "use_mobility": False,
        "use_advancement": True,
        "label": "Médio",
    },
    Difficulty.HARD: {
        "depth": 5,
        "use_positional": True,
        "use_mobility": True,
        "use_advancement": True,
        "label": "Difícil",
    },
}


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


# ── Helpers ──────────────────────────────────────────────────────

def _apply_board_move(b: Board, m):
    if isinstance(m, dict):
        b.apply_move(m["from"], m["to"], m.get("captured"))
    else:
        b.apply_move(m[0], m[1])


def _extract_move_coords(m):
    if isinstance(m, dict):
        return (m["from"], m["to"])
    return (m[0], m[1])


# ── Main entry point ─────────────────────────────────────────────

def choose_move(board: Board, color: str = "w",
                difficulty: Difficulty | str = Difficulty.MEDIUM):
    """Return the best move for `color` at the given difficulty level."""
    if isinstance(difficulty, str):
        difficulty = Difficulty(difficulty.lower())

    config = CHALLENGE_CONFIGS[difficulty]
    depth = config["depth"]

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
        score = -minimax(child, depth - 1, -1e9, 1e9, opp, config)
        # Small tiebreak for variety
        score += (i % 7) * 1e-4
        if score > best_score:
            best_score = score
            best_move = move

    return best_move


# ── Minimax with alpha-beta pruning ──────────────────────────────

def minimax(board: Board, depth: int, alpha: float, beta: float,
            color: str, config: dict | None = None) -> float:
    if config is None:
        config = {}
    if depth == 0:
        return evaluate(board, color, config)

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
            value = max(value, minimax(child, depth - 1, alpha, beta, opp, config))
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
            value = min(value, minimax(child, depth - 1, alpha, beta, opp, config))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


# ── Evaluation function ──────────────────────────────────────────

def evaluate(board: Board, ai_color: str = "w", config: dict | None = None) -> float:
    """
    Evaluate the board from ai_color's perspective.
    Positive = good for ai_color.
    """
    if config is None:
        config = {}
    score = 0.0
    my_pieces = 0
    opp_pieces = 0
    my_kings = 0
    opp_kings = 0
    my_advancement = 0
    opp_advancement = 0

    for r in range(8):
        for c in range(8):
            p = board.board[r][c]
            if not p:
                continue
            is_white = p.lower() == "w"
            is_mine = (is_white and ai_color == "w") or (not is_white and ai_color == "b")
            is_king = p.isupper()

            # Material value
            mat = 15.0 if is_king else 10.0

            # Positional bonus (center control)
            pos = _POSITION[r][c] if config.get("use_positional") else 0

            # Advancement bonus (closer to promotion row)
            adv = 0
            if config.get("use_advancement"):
                adv = (7 - r) if is_white else r

            if is_mine:
                my_pieces += 1
                my_kings += int(is_king)
                my_advancement += adv
                score += mat + pos * 0.5 + adv * 0.8
            else:
                opp_pieces += 1
                opp_kings += int(is_king)
                opp_advancement += adv
                score -= mat + pos * 0.5 + adv * 0.8

    # King advantage bonus
    if config.get("use_king_bonus"):
        score += (my_kings - opp_kings) * 5.0

    # Back row defense bonus
    if config.get("use_back_row") and my_pieces > 0:
        if ai_color == "w":
            back_row = all(board.board[7][c] != "" for c in range(0, 8, 2))
        else:
            back_row = all(board.board[0][c] != "" for c in range(0, 8, 2))
        if back_row:
            score += 3.0

    return score
