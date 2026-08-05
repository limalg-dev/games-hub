from games.checkers.game import Board

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
    for fr, to in moves:
        assert 0 <= fr[0] < 8 and 0 <= fr[1] < 8
        assert 0 <= to[0] < 8 and 0 <= to[1] < 8

def test_apply_move():
    b = Board()
    b.apply_move((5,1), (4,0))
    assert b.board[5][1] == ""
    assert b.board[4][0] == "w"
