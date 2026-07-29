from __future__ import annotations
from sqlmodel import SQLModel, Field
from typing import Optional

class Game(SQLModel, table=True):
    id: str = Field(primary_key=True)
    player1: Optional[str] = None
    player2: Optional[str] = None
    status: str = Field(default="waiting")

class Move(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: str = Field(foreign_key="game.id")
    move_number: int
    from_square: str
    to_square: str
