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


class PlayerRating(SQLModel, table=True):
    """ELO rating for a player on a specific game + difficulty combination.

    key format: ``{game_type}:{difficulty}`` (e.g. ``checkers:easy``).
    The ``player_id`` column identifies the human player (browser session).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: str = Field(index=True)
    game_type: str = Field(default="checkers")
    difficulty: str = Field(default="medium")
    rating: int = Field(default=1000)
    wins: int = Field(default=0)
    losses: int = Field(default=0)
    draws: int = Field(default=0)
    peak_rating: int = Field(default=1000)
    games_played: int = Field(default=0)
