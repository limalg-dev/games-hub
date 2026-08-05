"""A crossword is never stored with nothing to solve.

The word bank lives in the same database the suite tears down, so a running
server can find the table empty. generate_crossword([]) then returns a grid of
all-black cells, and the browser crashes on it. Creating the game has to notice
first.

The puzzle is read from the stored row rather than the POST response: the route
declares response_model=GameRead, which strips any key that model lacks.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, delete, select

from app.database import engine, init_db
from app.main import app, seed_words
from app.models import Game
from games.crossword.models import Word


@pytest.fixture(autouse=True)
def _setup_db():
    init_db()
    seed_words()
    yield
    with engine.connect() as conn:
        trans = conn.begin()
        for table in reversed(SQLModel.metadata.sorted_tables):
            conn.execute(table.delete())
        trans.commit()


client = TestClient(app)


def stored_playable_cells(game_id: str) -> int:
    with Session(engine) as session:
        game = session.exec(select(Game).where(Game.id == game_id)).first()
        assert game is not None and game.puzzle_data, "no puzzle was stored"
        puzzle = json.loads(game.puzzle_data)
    return sum(1 for row in puzzle["grid"] for cell in row if cell)


def test_a_seeded_crossword_has_cells_to_fill():
    resp = client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
    assert resp.status_code == 200
    assert stored_playable_cells(resp.json()["id"]) > 0


def test_an_empty_word_bank_never_yields_an_unplayable_puzzle():
    with Session(engine) as session:
        session.exec(delete(Word))
        session.commit()

    resp = client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})

    # Either the server refills the bank and serves a real puzzle, or it
    # refuses. What it must never do is store a grid with nothing in it.
    if resp.status_code == 200:
        assert stored_playable_cells(resp.json()["id"]) > 0
    else:
        assert resp.status_code == 503
