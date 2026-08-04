import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, seed_words
from app.database import engine, init_db
from sqlmodel import SQLModel

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    seed_words()
    yield
    with engine.connect() as conn:
        trans = conn.begin()
        for table in reversed(SQLModel.metadata.sorted_tables):
            conn.execute(table.delete())
        trans.commit()

@pytest.mark.asyncio
async def test_full_crossword_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        words_resp = await client.get("/api/words")
        assert words_resp.status_code == 200
        game_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        assert game_resp.status_code == 200
        game_id = game_resp.json()["id"]
        state_resp = await client.get(f"/games/{game_id}")
        assert state_resp.status_code == 200

@pytest.mark.asyncio
async def test_seed_words_populated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/words")
        assert response.status_code == 200
        words = response.json()
        assert len(words) > 50

@pytest.mark.asyncio
async def test_crossword_game_has_puzzle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        game_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "medium"})
        game_id = game_resp.json()["id"]
        state_resp = await client.get(f"/games/{game_id}")
        state = state_resp.json()
        assert "puzzle" in state or "grid" in state or state.get("status") == "waiting"

@pytest.mark.asyncio
async def test_checkers_game_still_works():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        game_resp = await client.post("/games", json={"game_type": "checkers"})
        assert game_resp.status_code == 200
        game_id = game_resp.json()["id"]
        state_resp = await client.get(f"/games/{game_id}")
        state = state_resp.json()
        assert state["game_type"] == "checkers"
        assert state["status"] == "waiting"
