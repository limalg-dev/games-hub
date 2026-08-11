"""
Tests for API error handling and ConnectionManager cleanup logic
"""

import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app, engine
from app.websocket import ConnectionManager
from sqlmodel import SQLModel


@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def transport():
    return ASGITransport(app=app)


# --- API Error Handling ---


@pytest.mark.asyncio
async def test_get_nonexistent_game_returns_404(transport):
    """GET /games/{non_existent_id} returns 404"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/games/totally-fake-uuid-12345")
        assert resp.status_code == 404
        assert "Game not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_game_404_has_detail(transport):
    """404 response includes meaningful error detail"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/games/does-not-exist")
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_play_snake_returns_200(transport):
    """/play/snake returns 200 with HTML content"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/play/snake")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_play_ant_defense_returns_200(transport):
    """/play/ant_defense returns 200"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/play/ant_defense")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_play_tower_defense_returns_200(transport):
    """/play/tower_defense returns 200"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/play/tower_defense")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_play_checkers_returns_200(transport):
    """/play/checkers returns 200"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/play/checkers")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_root_returns_200(transport):
    """/ returns 200"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_game_default_type(transport):
    """POST /games with default game_type creates a checkers game"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/games")
        assert resp.status_code == 200
        data = resp.json()
        assert data["game_type"] == "checkers"


@pytest.mark.asyncio
async def test_no_cache_headers_on_static(transport):
    """Static .js files get no-cache headers"""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/static/app.js")
        assert resp.status_code == 200
        assert "no-cache" in resp.headers.get("cache-control", "")


# --- ConnectionManager Unit Tests ---


class TestConnectionManagerDisconnect:
    """Tests for ConnectionManager.disconnect cleanup logic"""

    def test_disconnect_removes_client(self):
        """Disconnecting removes the client from the game's client dict"""
        mgr = ConnectionManager()
        mock_ws = MagicMock()
        ws_id = id(mock_ws)

        # Simulate a connected client
        mgr.clients["game1"] = {ws_id: {"ws": mock_ws, "color": "w"}}

        mgr.disconnect("game1", mock_ws)
        # Last client removed => entire game entry removed
        assert "game1" not in mgr.clients

    def test_disconnect_cleans_up_boards(self):
        """When last client disconnects, boards/turn state is cleaned up"""
        mgr = ConnectionManager()
        mock_ws = MagicMock()
        ws_id = id(mock_ws)

        from games.checkers.game import Board
        mgr.clients["game1"] = {ws_id: {"ws": mock_ws, "color": "w"}}
        mgr.boards["game1"] = Board()
        mgr.turn["game1"] = "w"

        mgr.disconnect("game1", mock_ws)
        assert "game1" not in mgr.boards
        assert "game1" not in mgr.turn

    def test_disconnect_cleans_up_crossword_state(self):
        """When last client disconnects, crossword_state is cleaned up"""
        mgr = ConnectionManager()
        mock_ws = MagicMock()
        ws_id = id(mock_ws)

        mgr.clients["game1"] = {ws_id: {"ws": mock_ws, "color": "w"}}
        mgr.crossword_state["game1"] = {"some": "state"}

        mgr.disconnect("game1", mock_ws)
        assert "game1" not in mgr.crossword_state

    def test_disconnect_keeps_other_clients(self):
        """Disconnecting one client keeps other clients in the same game"""
        mgr = ConnectionManager()
        ws1 = MagicMock()
        ws2 = MagicMock()
        ws1_id = id(ws1)
        ws2_id = id(ws2)

        mgr.clients["game1"] = {
            ws1_id: {"ws": ws1, "color": "w"},
            ws2_id: {"ws": ws2, "color": "b"},
        }

        mgr.disconnect("game1", ws1)
        assert "game1" in mgr.clients
        assert ws2_id in mgr.clients["game1"]
        assert ws1_id not in mgr.clients["game1"]

    def test_disconnect_unknown_game_no_crash(self):
        """Disconnecting from an unknown game does not crash"""
        mgr = ConnectionManager()
        mock_ws = MagicMock()

        # Should not raise
        mgr.disconnect("nonexistent_game", mock_ws)

    def test_disconnect_unknown_websocket_no_crash(self):
        """Disconnecting an unknown websocket does not crash"""
        mgr = ConnectionManager()
        ws1 = MagicMock()
        ws2 = MagicMock()
        ws1_id = id(ws1)

        mgr.clients["game1"] = {ws1_id: {"ws": ws1, "color": "w"}}

        # ws2 was never connected, should not crash
        mgr.disconnect("game1", ws2)
        # ws1 should still be there
        assert ws1_id in mgr.clients["game1"]

    def test_multiple_games_independent(self):
        """Disconnecting from one game does not affect others"""
        mgr = ConnectionManager()
        ws1 = MagicMock()
        ws2 = MagicMock()

        mgr.clients["game1"] = {id(ws1): {"ws": ws1, "color": "w"}}
        mgr.clients["game2"] = {id(ws2): {"ws": ws2, "color": "w"}}

        mgr.disconnect("game1", ws1)
        assert "game1" not in mgr.clients
        assert "game2" in mgr.clients
