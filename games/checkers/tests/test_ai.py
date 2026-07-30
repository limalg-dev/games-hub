from games.checkers.game import Board
from games.checkers.ai import choose_move

def test_choose_move_returns_valid():
    board = Board()
    move = choose_move(board, "w")
    assert move is not None
    fr, to = move
    assert board.board[fr[0]][fr[1]] != ""
    assert board.board[to[0]][to[1]] == ""
