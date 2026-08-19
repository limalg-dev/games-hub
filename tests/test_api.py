import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, engine
from sqlmodel import SQLModel

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.mark.asyncio
async def test_create_game():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/games")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data

@pytest.mark.asyncio
async def test_create_game_rejects_unknown_difficulty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/games", json={"game_type": "crossword", "difficulty": "banana"})
        assert resp.status_code == 422
        resp2 = await ac.post("/games", json={"game_type": "crossword", "difficulty": 2})
        assert resp2.status_code == 422

@pytest.mark.asyncio
async def test_get_game():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/games")
        game_id = resp.json()["id"]
        resp2 = await ac.get(f"/games/{game_id}")
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["id"] == game_id
