import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, seed_words
from sqlmodel import SQLModel, Session, select
from app.database import engine
from app.models import Game
import json

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    seed_words()
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.mark.asyncio
async def test_create_word():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/words", json={"word": "TESTWORD", "hint": "A test word", "category": "test", "difficulty": 1})
        assert response.status_code == 200
        assert response.json()["word"] == "TESTWORD"

@pytest.mark.asyncio
async def test_list_words():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/words")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_list_words_filter_category():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/words?category=tech")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_crossword_game():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        assert response.status_code == 200
        assert "id" in response.json()

@pytest.mark.asyncio
async def test_get_crossword_game():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        game_id = create_resp.json()["id"]
        response = await client.get(f"/games/{game_id}")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_crossword_puzzle_persisted():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        assert create_resp.status_code == 200
        game_id = create_resp.json()["id"]
        with Session(engine) as session:
            game = session.exec(select(Game).where(Game.id == game_id)).first()
            assert game.puzzle_data is not None
            data = json.loads(game.puzzle_data)
            assert "grid" in data
            assert "clues" in data
            assert "size" in data

@pytest.mark.asyncio
async def test_crossword_puzzle_structure():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "medium"})
        assert create_resp.status_code == 200
        game_id = create_resp.json()["id"]
        with Session(engine) as session:
            game = session.exec(select(Game).where(Game.id == game_id)).first()
            puzzle = json.loads(game.puzzle_data)
            assert puzzle["size"] <= 12
            assert puzzle["words_placed"] > 0
            grid_text = "".join(cell or "" for row in puzzle["grid"] for cell in row)
            assert len(grid_text) > 0
