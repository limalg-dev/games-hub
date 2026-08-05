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

class PlayerProfileRead(BaseModel):
    player_name: str
    gems: int = 0
    high_score: int = 0
    unlocked_towers: str = "rifle"
    skins: str = ""
    model_config = {"from_attributes": True}

class ShopItemRead(BaseModel):
    id: int
    item_type: str
    name: str
    cost_gems: int
    description: str
    model_config = {"from_attributes": True}

class LeaderboardEntry(BaseModel):
    player_name: str
    high_score: int

class ShopBuyRequest(BaseModel):
    player_name: str
    item_name: str
