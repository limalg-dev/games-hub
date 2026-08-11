"""
Tests for Snake game API routes
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, engine
from sqlmodel import SQLModel
from games.snake.routes import active_games


@pytest.fixture(autouse=True)
def setup_db_and_games():
    SQLModel.metadata.create_all(engine)
    active_games.clear()
    yield
    active_games.clear()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def transport():
    return ASGITransport(app=app)


# --- REST API Tests ---


@pytest.mark.asyncio
async def test_get_snake_info(transport):
    """GET /api/snake returns game info"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/snake")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Snake"
        assert "controls" in data


@pytest.mark.asyncio
async def test_create_snake_game(transport):
    """POST /api/snake/new creates a game"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/snake/new")
        assert resp.status_code == 200
        data = resp.json()
        assert "game_id" in data
        assert "state" in data
        assert data["state"]["score"] == 0
        assert data["state"]["game_over"] is False


@pytest.mark.asyncio
async def test_get_snake_game(transport):
    """GET /api/snake/{game_id} returns game state"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/snake/new")
        game_id = create.json()["game_id"]

        resp = await ac.get(f"/api/snake/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["game_id"] == game_id
        assert "state" in data


@pytest.mark.asyncio
async def test_get_snake_game_not_found(transport):
    """GET /api/snake/{game_id} with invalid id returns 404"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/snake/nonexistent-id")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_set_direction_valid(transport):
    """POST /api/snake/{game_id}/direction with valid direction"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/snake/new")
        game_id = create.json()["game_id"]

        resp = await ac.post(
            f"/api/snake/{game_id}/direction",
            params={"direction": "right"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["direction"] == "right"


@pytest.mark.asyncio
async def test_set_direction_invalid(transport):
    """POST /api/snake/{game_id}/direction with invalid direction returns 400"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/snake/new")
        game_id = create.json()["game_id"]

        resp = await ac.post(
            f"/api/snake/{game_id}/direction",
            params={"direction": "diagonal"},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_set_direction_game_not_found(transport):
    """POST /api/snake/{game_id}/direction for nonexistent game returns 404"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/snake/fake-id/direction",
            params={"direction": "up"},
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_game(transport):
    """POST /api/snake/{game_id}/update advances game state"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/snake/new")
        game_id = create.json()["game_id"]

        resp = await ac.post(f"/api/snake/{game_id}/update")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "state" in data
        assert "game_over" in data


@pytest.mark.asyncio
async def test_update_game_not_found(transport):
    """POST /api/snake/{game_id}/update for nonexistent game returns 404"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/snake/fake-id/update")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_toggle_pause(transport):
    """POST /api/snake/{game_id}/pause toggles pause"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/snake/new")
        game_id = create.json()["game_id"]

        resp = await ac.post(f"/api/snake/{game_id}/pause")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["paused"] is True

        resp2 = await ac.post(f"/api/snake/{game_id}/pause")
        assert resp2.json()["paused"] is False


@pytest.mark.asyncio
async def test_toggle_pause_not_found(transport):
    """POST /api/snake/{game_id}/pause for nonexistent game returns 404"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/snake/fake-id/pause")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_game(transport):
    """DELETE /api/snake/{game_id} deletes the game"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        create = await ac.post("/api/snake/new")
        game_id = create.json()["game_id"]

        resp = await ac.delete(f"/api/snake/{game_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Should be gone now
        resp2 = await ac.get(f"/api/snake/{game_id}")
        assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_game_not_found(transport):
    """DELETE /api/snake/{game_id} for nonexistent game returns 404"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.delete("/api/snake/fake-id")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_full_lifecycle(transport):
    """Full lifecycle: create -> direction -> update -> check state"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create
        create = await ac.post("/api/snake/new")
        game_id = create.json()["game_id"]
        initial_state = create.json()["state"]

        # Set direction
        await ac.post(
            f"/api/snake/{game_id}/direction",
            params={"direction": "right"},
        )

        # Update (tick)
        resp = await ac.post(f"/api/snake/{game_id}/update")
        data = resp.json()
        state = data["state"]

        # Head should have moved right from initial position
        assert state["direction"] == "RIGHT"

        # Verify state is serializable and has expected fields
        assert isinstance(state["snake"], list)
        assert isinstance(state["score"], int)
        assert isinstance(state["speed"], int)
