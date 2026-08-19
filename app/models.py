from __future__ import annotations
from sqlmodel import SQLModel, Field
from typing import Optional

class Game(SQLModel, table=True):
    id: str = Field(primary_key=True)
    player1: Optional[str] = None
    player2: Optional[str] = None
    status: str = Field(default="waiting")
    game_type: str = Field(default="checkers")
    puzzle_data: Optional[str] = Field(default=None)  # JSON string for crossword puzzle data
