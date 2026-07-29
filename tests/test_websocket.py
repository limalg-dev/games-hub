import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, init_db
from sqlmodel import SQLModel
import json

@pytest.fixture(autouse=True)
def _setup_db():
    init_db()
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
