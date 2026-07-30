from __future__ import annotations
from games.checkers.game import Board

def choose_move(board: Board, color: str) -> tuple[tuple[int, int], tuple[int, int]] | None:
    moves = board.legal_moves(color)
    if not moves:
        return None
    best_move = moves[0]
    best_score = -1e9
    for move in moves:
        child = Board()
        child.board = [row[:] for row in board.board]
        child.apply_move(*move)
        score = -minimax(child, 2, -1e9, 1e9, "b" if color == "w" else "w")
        if score > best_score:
            best_score = score
            best_move = move
    return best_move

def minimax(board: Board, depth: int, alpha: float, beta: float, color: str) -> float:
    if depth == 0:
        return evaluate(board)
    moves = board.legal_moves(color)
    if not moves:
        return -10000
    if color == "w":
        value = -1e9
        for move in moves:
            child = Board()
            child.board = [row[:] for row in board.board]
            child.apply_move(*move)
            value = max(value, minimax(child, depth - 1, alpha, beta, "b"))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 1e9
        for move in moves:
            child = Board()
            child.board = [row[:] for row in board.board]
            child.apply_move(*move)
            value = min(value, minimax(child, depth - 1, alpha, beta, "w"))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

def evaluate(board: Board) -> float:
    score = 0.0
    for r in range(8):
        for c in range(8):
            p = board.board[r][c]
            if p == "":
                continue
            val = 10 if p.lower() == p else 15
            if p.lower() == "w":
                score += val
            else:
                score -= val
    return score
