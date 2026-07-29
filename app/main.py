from __future__ import annotations
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, create_engine, Session, select
from app.models import Game
from app.schemas import GameRead

engine = create_engine("sqlite:///./games.db", connect_args={"check_same_thread": False})
SQLModel.metadata.create_all(engine)

app = FastAPI()

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
