"""
Tests for Ant Defense game API routes
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, engine
from sqlmodel import SQLModel
from games.ant_defense.routes import active_games, game_connections


@pytest.fixture(autouse=True)
def setup_db_and_games():
    SQLModel.metadata.create_all(engine)
    active_games.clear()
    game_connections.clear()
    yield
    active_games.clear()
    game_connections.clear()
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def transport():
    return ASGITransport(app=app)


# --- Helper ---

async def create_game(ac):
    """Helper to create a game and return game_id"""
    resp = await ac.post("/games/ant_defense")
    assert resp.status_code == 200
    return resp.json()["game_id"]


# --- REST API Tests ---


@pytest.mark.asyncio
async def test_create_game(transport):
    """POST /games/ant_defense creates a game"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/games/ant_defense")
        assert resp.status_code == 200
        data = resp.json()
        assert "game_id" in data
        assert data["game_type"] == "ant_defense"
        assert data["status"] == "created"
        assert "initial_state" in data
        state = data["initial_state"]
        assert state["gold"] == 100
        assert state["lives"] == 20


@pytest.mark.asyncio
async def test_list_games_empty(transport):
    """GET /games/ant_defense lists games - empty"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/games/ant_defense")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["games"] == []


@pytest.mark.asyncio
async def test_list_games_after_create(transport):
    """GET /games/ant_defense lists games after creating some"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await create_game(ac)
        import asyncio
        await asyncio.sleep(0.002)  # Ensure different timestamp-based IDs
        await create_game(ac)

        resp = await ac.get("/games/ant_defense")
        data = resp.json()
        assert data["count"] == 2
        assert len(data["games"]) == 2


@pytest.mark.asyncio
async def test_get_game(transport):
    """GET /games/ant_defense/{game_id} returns state"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        game_id = await create_game(ac)

        resp = await ac.get(f"/games/ant_defense/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["game_id"] == game_id
        assert "state" in data


@pytest.mark.asyncio
async def test_get_game_not_found(transport):
    """GET /games/ant_defense/{game_id} with invalid id returns 404"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/games/ant_defense/nonexistent")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_place_tower_mandible(transport):
    """POST place tower (mandible) - succeeds, gold decreases"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        game_id = await create_game(ac)

        resp = await ac.post(
            f"/games/ant_defense/{game_id}/tower",
            params={"grid_x": 8, "grid_y": 0, "tower_type": "mandible"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["remaining_gold"] == 50  # 100 - 50


@pytest.mark.asyncio
async def test_place_tower_insufficient_gold(transport):
    """POST place tower with insufficient gold fails"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        game_id = await create_game(ac)

        # Place mandible (50) at valid position
        await ac.post(
            f"/games/ant_defense/{game_id}/tower",
            params={"grid_x": 8, "grid_y": 0, "tower_type": "mandible"},
        )
        # Now only 50 gold left, acid costs 80
        resp = await ac.post(
            f"/games/ant_defense/{game_id}/tower",
            params={"grid_x": 12, "grid_y": 0, "tower_type": "acid"},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_place_tower_invalid_type(transport):
    """POST place tower with invalid type fails"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        game_id = await create_game(ac)

        resp = await ac.post(
            f"/games/ant_defense/{game_id}/tower",
            params={"grid_x": 8, "grid_y": 0, "tower_type": "laser"},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_place_tower_game_not_found(transport):
    """POST place tower on nonexistent game returns 404"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/games/ant_defense/fake/tower",
            params={"grid_x": 6, "grid_y": 6, "tower_type": "mandible"},
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_start_wave(transport):
    """POST start wave activates wave"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        game_id = await create_game(ac)

        resp = await ac.post(
            f"/games/ant_defense/{game_id}/wave",
            params={"wave_number": 1},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["wave_number"] == 1
        assert data["state"]["wave_active"] is True


@pytest.mark.asyncio
async def test_start_wave_while_active(transport):
    """POST start wave while another wave is active fails"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        game_id = await create_game(ac)

        await ac.post(
            f"/games/ant_defense/{game_id}/wave",
            params={"wave_number": 1},
        )
        resp = await ac.post(
            f"/games/ant_defense/{game_id}/wave",
            params={"wave_number": 2},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_toggle_pause(transport):
    """POST toggle pause"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        game_id = await create_game(ac)

        resp = await ac.post(f"/games/ant_defense/{game_id}/pause")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["paused"] is True

        resp2 = await ac.post(f"/games/ant_defense/{game_id}/pause")
        assert resp2.json()["paused"] is False


@pytest.mark.asyncio
async def test_delete_game(transport):
    """DELETE game removes it"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        game_id = await create_game(ac)

        resp = await ac.delete(f"/games/ant_defense/{game_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Should be gone
        resp2 = await ac.get(f"/games/ant_defense/{game_id}")
        assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_game_not_found(transport):
    """DELETE nonexistent game returns 404"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.delete("/games/ant_defense/nonexistent")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_full_lifecycle(transport):
    """Full lifecycle: create -> place tower -> start wave -> check state"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create
        game_id = await create_game(ac)

        # Place tower at valid position (off-path)
        await ac.post(
            f"/games/ant_defense/{game_id}/tower",
            params={"grid_x": 8, "grid_y": 0, "tower_type": "mandible"},
        )

        # Start wave
        await ac.post(
            f"/games/ant_defense/{game_id}/wave",
            params={"wave_number": 1},
        )

        # Check state
        resp = await ac.get(f"/games/ant_defense/{game_id}")
        state = resp.json()["state"]
        assert state["wave_active"] is True
        assert state["gold"] == 50  # 100 - 50 mandible
        assert len(state["towers"]) == 1
        assert state["towers"][0]["type"] == "mandible"
