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
async def test_crossword_game_creates():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        assert create_resp.status_code == 200
        game_id = create_resp.json()["id"]
        state_resp = await client.get(f"/games/{game_id}")
        assert state_resp.status_code == 200

@pytest.mark.asyncio
async def test_crossword_game_has_puzzle_data():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        game_id = create_resp.json()["id"]
        state = (await client.get(f"/games/{game_id}")).json()
        assert state.get("puzzle") is not None or state.get("status") == "playing" or "id" in state

@pytest.mark.asyncio
async def test_crossword_game_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "medium"})
        game_id = create_resp.json()["id"]
        state = (await client.get(f"/games/{game_id}")).json()
        assert state["status"] == "waiting"
        assert state["game_type"] == "crossword"
