import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlmodel import SQLModel
from app.database import engine

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.mark.asyncio
async def test_create_td_game():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/games", json={"game_type": "towerdefense"})
        assert resp.status_code == 200
        assert "id" in resp.json()

@pytest.mark.asyncio
async def test_get_leaderboard():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/leaderboard")
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_player_profile():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/profile/test_player")
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_shop_buy_no_player():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/shop/buy", json={"player_name": "nonexistent", "item_name": "sniper_unlock"})
        assert resp.status_code == 404
