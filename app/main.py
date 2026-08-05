from __future__ import annotations
from uuid import uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, Request, Query
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, Response, JSONResponse
from sqlmodel import Session, select
import json
from app.models import Game
from app.schemas import GameRead, GameCreate, WordCreate, WordRead, ShopBuyRequest
from app.websocket import websocket_endpoint
from app.database import engine, init_db
from games.crossword.models import Word
from games.crossword.words import SEED_WORDS
from games.crossword.generator import generate_crossword
from games.towerdefense.models import PlayerProfile, ShopItem
import os

DIFFICULTY_MAP = {"easy": 1, "medium": 2, "hard": 3}

def seed_words():
    with Session(engine) as session:
        existing = session.exec(select(Word).limit(1)).first()
        if existing:
            return
        for w in SEED_WORDS:
            session.add(Word(**w))
        session.commit()

SHOP_ITEMS = [
    {"item_type": "tower", "name": "sniper_unlock", "cost_gems": 5, "description": "Unlock Sniper tower"},
    {"item_type": "tower", "name": "missile_unlock", "cost_gems": 8, "description": "Unlock Missile tower"},
    {"item_type": "tower", "name": "tesla_unlock", "cost_gems": 10, "description": "Unlock Tesla tower"},
    {"item_type": "tower", "name": "slow_unlock", "cost_gems": 6, "description": "Unlock Slow tower"},
    {"item_type": "skin", "name": "gold_rifle", "cost_gems": 3, "description": "Gold Rifle skin"},
    {"item_type": "skin", "name": "fire_missile", "cost_gems": 4, "description": "Fire Missile skin"},
]

def seed_shop_items():
    with Session(engine) as session:
        existing = session.exec(select(ShopItem).limit(1)).first()
        if existing:
            return
        for item in SHOP_ITEMS:
            session.add(ShopItem(**item))
        session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_words()
    seed_shop_items()
    yield

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith(('.js', '.html', '.css')):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")
games_dir = "games"
for game_name in os.listdir(games_dir):
    game_static = os.path.join(games_dir, game_name, "static")
    if os.path.isdir(game_static) and not game_name.startswith("."):
        app.mount(f"/games/{game_name}/static", StaticFiles(directory=game_static), name=f"{game_name}_static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/api/words", response_model=WordRead)
async def create_word(word_in: WordCreate):
    with Session(engine) as session:
        word = Word(**word_in.model_dump())
        session.add(word)
        session.commit()
        session.refresh(word)
        return word

@app.get("/api/words", response_model=list[WordRead])
async def list_words(
    category: str | None = Query(default=None),
    difficulty: int | None = Query(default=None),
):
    with Session(engine) as session:
        stmt = select(Word)
        if category:
            stmt = stmt.where(Word.category == category)
        if difficulty:
            stmt = stmt.where(Word.difficulty == difficulty)
        words = session.exec(stmt).all()
        return words

@app.post("/games", response_model=GameRead)
async def create_game(game_in: GameCreate = GameCreate()):
    with Session(engine) as session:
        puzzle_data = None
        if game_in.game_type == "crossword":
            diff_num = DIFFICULTY_MAP.get(game_in.difficulty, 1)
            words_stmt = select(Word)
            all_words = session.exec(words_stmt).all()
            word_dicts = [{"word": w.word, "hint": w.hint} for w in all_words]
            puzzle_data = generate_crossword(word_dicts, difficulty=diff_num)

        if game_in.game_type == "towerdefense":
            game = Game(id=str(uuid4()), game_type="towerdefense", status="playing")
        else:
            game = Game(id=str(uuid4()), status="waiting", game_type=game_in.game_type)
        
        if puzzle_data is not None:
            game.puzzle_data = json.dumps(puzzle_data)
        session.add(game)
        session.commit()
        session.refresh(game)

        result = GameRead.model_validate(game).model_dump()
        if puzzle_data is not None:
            result["puzzle"] = puzzle_data
        return result

@app.get("/games/{game_id}", response_model=GameRead)
async def get_game(game_id: str):
    with Session(engine) as session:
        game = session.exec(select(Game).where(Game.id == game_id)).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return game

@app.post("/api/shop/buy")
async def shop_buy(req: ShopBuyRequest):
    with Session(engine) as session:
        profile = session.exec(select(PlayerProfile).where(PlayerProfile.player_name == req.player_name)).first()
        if not profile:
            return JSONResponse({"error": "Player not found"}, status_code=404)
        item = session.exec(select(ShopItem).where(ShopItem.name == req.item_name)).first()
        if not item:
            return JSONResponse({"error": "Item not found"}, status_code=404)
        if profile.gems < item.cost_gems:
            return JSONResponse({"error": "Not enough gems"}, status_code=400)
        profile.gems -= item.cost_gems
        if item.item_type == "tower":
            owned = set(profile.unlocked_towers.split(",")) if profile.unlocked_towers else set()
            owned.add(req.item_name.replace("_unlock", ""))
            profile.unlocked_towers = ",".join(owned)
        session.add(profile)
        session.commit()
        return {"success": True, "gems_remaining": profile.gems}

@app.get("/api/leaderboard")
async def get_leaderboard():
    with Session(engine) as session:
        profiles = session.exec(select(PlayerProfile).order_by(PlayerProfile.high_score.desc()).limit(10)).all()
        return [{"player_name": p.player_name, "high_score": p.high_score} for p in profiles]

@app.get("/api/profile/{player_name}")
async def get_profile(player_name: str):
    with Session(engine) as session:
        profile = session.exec(select(PlayerProfile).where(PlayerProfile.player_name == player_name)).first()
        if not profile:
            profile = PlayerProfile(player_name=player_name)
            session.add(profile)
            session.commit()
            session.refresh(profile)
        return profile

app.websocket("/ws/{game_id}")(websocket_endpoint)
