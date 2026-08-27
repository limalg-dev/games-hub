"""WS state persistence (Task 3): live game state must survive a server restart.

Simulates: connect WS -> play a move -> wipe the in-memory ConnectionManager
(simulating a process restart) -> reconnect -> state must be restored from
SQLite, not re-initialized from scratch.

Uses an isolated SQLite database in tmp_path — NEVER the root games.db.
"""
import json

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from app.main import app
from app.models import Game
from app.websocket import ConnectionManager
from app import database as app_database
from app import main as app_main
from app import websocket as app_websocket
from games.checkers.game import Board


@pytest.fixture()
def isolated_env(tmp_path, monkeypatch):
    """Isolated SQLite DB (tmp_path) wired into every module that uses `engine`,
    plus a fresh ConnectionManager (simulates a freshly started server)."""
    db_file = tmp_path / "test_games.db"
    engine = create_engine(
        f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(app_database, "engine", engine)
    monkeypatch.setattr(app_main, "engine", engine)
    monkeypatch.setattr(app_websocket, "engine", engine)
    monkeypatch.setattr(app_websocket, "manager", ConnectionManager())
    yield engine


@pytest.fixture()
def client():
    return TestClient(app)


def _create_game(engine, **kwargs):
    with Session(engine) as session:
        session.add(Game(**kwargs))
        session.commit()


def _next_board(ws):
    while True:
        msg = json.loads(ws.receive_text())
        if msg.get("type") == "board":
            return msg


# Minimal 2x2 crossword: solution A/_ , B/C (_ = black cell)
CROSSWORD_PUZZLE = {
    "size": 2,
    "grid": [["A", None], ["B", "C"]],
    "clues": {
        "across": [{"row": 0, "col": 0, "number": 1}],
        "down": [{"row": 0, "col": 0, "number": 1}],
    },
}


def test_checkers_move_restored_from_sqlite_after_restart(isolated_env, client, monkeypatch):
    _create_game(
        isolated_env,
        id="gp1",
        game_type="checkers",
        player2="connected",
        status="active",
    )
    with client.websocket_connect("/ws/gp1") as ws:
        color_msg = json.loads(ws.receive_text())
        assert color_msg == {"type": "color", "color": "w"}
        initial = _next_board(ws)
        assert initial["board"][5][1] == "w"

        ws.send_text(json.dumps({"type": "move", "from": [5, 1], "to": [4, 0]}))
        moved = _next_board(ws)
        assert moved["board"][4][0] == "w"
        assert moved["board"][5][1] == ""

    # The move was persisted to SQLite (Game.puzzle_data carries ws_state)
    with Session(isolated_env) as session:
        game = session.get(Game, "gp1")
        persisted = json.loads(game.puzzle_data)["ws_state"]
        assert persisted["board"][4][0] == "w"
        assert persisted["turn"] == "b"

    # Simulate server restart: brand-new ConnectionManager (RAM wiped)
    monkeypatch.setattr(app_websocket, "manager", ConnectionManager())

    with client.websocket_connect("/ws/gp1") as ws:
        color_msg = json.loads(ws.receive_text())
        assert color_msg["color"] == "w"
        restored = _next_board(ws)
        assert restored["type"] == "board"
        assert restored["board"][4][0] == "w", "state must come from SQLite, not a fresh board"
        assert restored["board"][5][1] == ""


def test_crossword_filled_cells_restored_from_sqlite_after_restart(isolated_env, client, monkeypatch):
    _create_game(
        isolated_env,
        id="gp2",
        game_type="crossword",
        puzzle_data=json.dumps(CROSSWORD_PUZZLE),
        status="active",
    )
    with client.websocket_connect("/ws/gp2") as ws:
        assert json.loads(ws.receive_text())["type"] == "color"
        init_msg = json.loads(ws.receive_text())
        assert init_msg["type"] == "crossword_init"
        assert init_msg["filled"][0][1] is True  # black cell starts filled

        ws.send_text(json.dumps({"type": "input", "row": 0, "col": 0, "letter": "A"}))
        ack = json.loads(ws.receive_text())
        assert ack["type"] == "correct"

    # Restart: RAM wiped
    monkeypatch.setattr(app_websocket, "manager", ConnectionManager())

    with client.websocket_connect("/ws/gp2") as ws:
        assert json.loads(ws.receive_text())["type"] == "color"
        init_msg = json.loads(ws.receive_text())
        assert init_msg["type"] == "crossword_init"
        assert init_msg["filled"][0][0] is True, "solved cell must be restored from SQLite"
        assert init_msg["filled"][1][1] is False, "unsolved cell stays open"


def test_finished_game_is_not_resurrected(isolated_env, client):
    _create_game(
        isolated_env,
        id="gp3",
        game_type="checkers",
        status="finished",
        puzzle_data=json.dumps(
            {"ws_state": {"board": [["w"] + [""] * 7] + [[""] * 8 for _ in range(7)], "turn": "b"}}
        ),
    )
    with client.websocket_connect("/ws/gp3") as ws:
        assert json.loads(ws.receive_text())["type"] == "color"
        restored = _next_board(ws)
        # finished games ignore stale snapshots -> brand-new standard board
        assert restored["board"] == Board().board
