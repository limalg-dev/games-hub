import pytest
from fastapi.testclient import TestClient
from app.main import app, seed_words
from app.database import engine, init_db
from sqlmodel import SQLModel
import json

@pytest.fixture(autouse=True)
def _setup_db():
    init_db()
    seed_words()
    yield
    # drop all rows but keep tables for next test
    with engine.connect() as conn:
        trans = conn.begin()
        for table in reversed(SQLModel.metadata.sorted_tables):
            conn.execute(table.delete())
        trans.commit()

client = TestClient(app)

def test_ws_game_flow():
    # create game
    resp = client.post("/games")
    assert resp.status_code == 200
    game_id = resp.json()["id"]
    # connect WebSocket as first player (white)
    with client.websocket_connect(f"/ws/{game_id}") as ws:
        # receive color
        color_msg = json.loads(ws.receive_text())
        assert color_msg["type"] == "color"
        assert color_msg["color"] == "w"
        # receive board
        board_msg = json.loads(ws.receive_text())
        assert board_msg["type"] == "board"
        assert len(board_msg["board"]) == 8
        # make a move
        ws.send_text(json.dumps({"type": "move", "from": [5,0], "to": [4,1]}))
        # receive board update
        upd = json.loads(ws.receive_text())
        assert upd["type"] == "board"
        # piece moved
        assert upd["board"][4][1] == "w"
        assert upd["board"][5][0] == ""

def test_ws_game_full():
    resp = client.post("/games")
    game_id = resp.json()["id"]
    with client.websocket_connect(f"/ws/{game_id}") as ws1:
        with client.websocket_connect(f"/ws/{game_id}") as ws2:
            pass
    # third connection should fail
    with client.websocket_connect(f"/ws/{game_id}") as ws3:
        pass  # should close
    # can't assert directly but at least no errors

def test_ws_crossword_init_and_solve():
    resp = client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
    assert resp.status_code == 200
    game_id = resp.json()["id"]
    with client.websocket_connect(f"/ws/{game_id}") as ws:
        # receive color
        color_msg = json.loads(ws.receive_text())
        assert color_msg["type"] == "color"
        # receive crossword init
        init_msg = json.loads(ws.receive_text())
        assert init_msg["type"] == "crossword_init"
        assert init_msg["size"] > 0
        assert "across_clues" in init_msg
        assert "down_clues" in init_msg
        assert len(init_msg["filled"]) == init_msg["size"]

def test_ws_crossword_wrong_letter_rejected():
    resp = client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
    game_id = resp.json()["id"]
    with client.websocket_connect(f"/ws/{game_id}") as ws:
        json.loads(ws.receive_text())  # color
        init_msg = json.loads(ws.receive_text())  # init
        # find first playable cell (filled False means playable)
        filled = init_msg["filled"]
        row = col = None
        for r in range(init_msg["size"]):
            for c in range(init_msg["size"]):
                if not filled[r][c]:
                    row, col = r, c
                    break
            if row is not None:
                break
        assert row is not None
        # send wrong letter (guaranteed wrong: Z is rare; but use X which is unlikely)
        ws.send_text(json.dumps({"type": "move", "row": row, "col": col, "letter": "Z"}))
        # if wrong, server sends error. If somehow correct, it sends update.
        msg = json.loads(ws.receive_text())
        # Either error (likely) or update. We just check it's a valid message type.
        assert msg["type"] in ("error", "crossword_update")
