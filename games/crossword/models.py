from __future__ import annotations
from typing import Optional
from sqlmodel import SQLModel, Field

class Word(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    word: str = ""
    hint: str = ""
    category: str = ""
    difficulty: int = 1  # 1=easy, 2=medium, 3=hard
