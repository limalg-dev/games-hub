import pytest
from fastapi.testclient import TestClient
from app.main import app, seed_words
from app.database import engine, init_db
from sqlmodel import SQLModel


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


@pytest.mark.parametrize("game", ["checkers", "wordsearch", "crossword"])
def test_play_serves_the_same_document_as_root(game):
    resp = client.get(f"/play/{game}")
    assert resp.status_code == 200
    assert resp.text == client.get("/").text


def test_play_rejects_an_unknown_game():
    assert client.get("/play/xadrez").status_code == 404


def test_play_ignores_query_string():
    resp = client.get("/play/wordsearch?difficulty=hard&category=animals")
    assert resp.status_code == 200
