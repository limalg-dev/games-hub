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
async def test_td_game_creates():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/games", json={"game_type": "towerdefense"})
        assert resp.status_code == 200
        game_id = resp.json()["id"]
        state = await client.get(f"/games/{game_id}")
        assert state.status_code == 200
