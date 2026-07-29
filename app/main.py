from __future__ import annotations
from uuid import uuid4
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from sqlmodel import Session, select
from app.models import Game
from app.schemas import GameRead
from app.websocket import websocket_endpoint
from app.database import engine, init_db

init_db()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/games", response_model=GameRead)
async def create_game():
    game = Game(id=str(uuid4()), status="waiting")
    with Session(engine) as session:
        session.add(game)
        session.commit()
        session.refresh(game)
    return game

@app.get("/games/{game_id}", response_model=GameRead)
async def get_game(game_id: str):
    with Session(engine) as session:
        game = session.exec(select(Game).where(Game.id == game_id)).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return game

app.websocket("/ws/{game_id}")(websocket_endpoint)
