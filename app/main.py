from __future__ import annotations
from uuid import uuid4
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, Request, Query
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, Response
from sqlmodel import Session, select
import json
from app.models import Game, PlayerRating
from app.schemas import GameRead, GameCreate, WordCreate, WordRead
from app.websocket import websocket_endpoint
from app.database import engine, init_db
from games.crossword.models import Word
from games.crossword.words import SEED_WORDS
from games.crossword.generator import generate_crossword
from games.snake.routes import router as snake_router
from games.tower_defense.routes import router as tower_defense_router, start_game_loop as start_tower_defense_loop
from games.bomberman.routes import router as bomberman_router
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_words()
    start_tower_defense_loop()
    yield

app = FastAPI(lifespan=lifespan)

# Include Snake game routes
app.include_router(snake_router, prefix="/api")

# Include Tower Defense game routes (router já tem prefix=/tower-defense)
app.include_router(tower_defense_router)

# Include Bomberman game routes
app.include_router(bomberman_router)

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith(('.js', '.html', '.css')):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount static files for all games
games_dir = "games"
for game_name in os.listdir(games_dir):
    game_static = os.path.join(games_dir, game_name, "static")
    if os.path.isdir(game_static) and not game_name.startswith("."):
        app.mount(f"/games/{game_name}/static", StaticFiles(directory=game_static), name=f"{game_name}_static")

# Specific routes for each game to avoid conflicts
# Note: Some games have their own index.html, others use the main static/index.html
@app.get("/play/snake")
async def play_snake():
    return FileResponse(os.path.join(games_dir, "snake", "index.html"))

@app.get("/play/ant_defense")
async def play_ant_defense():
    # Redirect to unified tower defense game
    return FileResponse(os.path.join(games_dir, "tower_defense", "static", "index.html"))

@app.get("/play/tower_defense")
async def play_tower_defense():
    return FileResponse(os.path.join(games_dir, "tower_defense", "static", "index.html"))

# Games that use the main static/index.html (legacy games)
@app.get("/play/checkers")
async def play_checkers():
    return FileResponse("static/index.html")

@app.get("/play/wordsearch")
async def play_wordsearch():
    return FileResponse("static/index.html")

@app.get("/play/crossword")
async def play_crossword():
    return FileResponse("static/index.html")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

PLAYABLE_GAMES = ("checkers", "wordsearch", "crossword", "snake", "tower_defense", "bomberman")

# Rota genérica removida para evitar conflitos com rotas específicas acima
# As rotas específicas estão definidas acima para cada jogo

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
            diff_num = DIFFICULTY_MAP[game_in.difficulty]
            all_words = session.exec(select(Word)).all()
            if not all_words:
                # The bank is seeded at startup, so a long-running server can be
                # left with an empty table (a dropped schema, a wiped database).
                # Without words the generator returns an all-black grid, which
                # the browser cannot render.
                seed_words()
                all_words = session.exec(select(Word)).all()
            if not all_words:
                raise HTTPException(
                    status_code=503, detail="Word bank is empty; cannot build a crossword"
                )
            word_dicts = [{"word": w.word, "hint": w.hint} for w in all_words]
            puzzle_data = generate_crossword(word_dicts, difficulty=diff_num)

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

@app.get("/api/ratings/{player_id}")
async def get_player_ratings(player_id: str, game_type: str = "checkers"):
    """Return all ELO ratings for a player across difficulties."""
    with Session(engine) as session:
        records = session.exec(
            select(PlayerRating).where(
                PlayerRating.player_id == player_id,
                PlayerRating.game_type == game_type,
            )
        ).all()
        return {
            "player_id": player_id,
            "game_type": game_type,
            "ratings": {
                r.difficulty: {
                    "rating": r.rating,
                    "wins": r.wins,
                    "losses": r.losses,
                    "draws": r.draws,
                    "games_played": r.games_played,
                    "peak_rating": r.peak_rating,
                }
                for r in records
            },
        }


@app.websocket("/ws/{game_id}")(websocket_endpoint)
