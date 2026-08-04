from pydantic import BaseModel
from typing import Optional

class GameCreate(BaseModel):
    game_type: str = "checkers"
    difficulty: str = "easy"

class GameRead(BaseModel):
    id: str
    player1: Optional[str] = None
    player2: Optional[str] = None
    status: str
    game_type: str = "checkers"
    model_config = {"from_attributes": True}

class WordCreate(BaseModel):
    word: str
    hint: str
    category: str
    difficulty: int = 1

class WordRead(BaseModel):
    id: int
    word: str
    hint: str
    category: str
    difficulty: int
    model_config = {"from_attributes": True}
