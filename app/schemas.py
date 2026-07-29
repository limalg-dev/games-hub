from pydantic import BaseModel
from typing import Optional

class GameCreate(BaseModel):
    pass  # fields can be added later

class GameRead(BaseModel):
    id: str
    player1: Optional[str] = None
    player2: Optional[str] = None
    status: str
    model_config = {"from_attributes": True}
