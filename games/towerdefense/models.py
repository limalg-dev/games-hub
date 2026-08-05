from __future__ import annotations
from typing import Optional
from sqlmodel import SQLModel, Field


class PlayerProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_name: str
    gems: int = 0
    high_score: int = 0
    unlocked_towers: str = "rifle"  # comma-separated
    skins: str = ""  # comma-separated


class ShopItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_type: str  # "tower", "skin", "emote"
    name: str
    cost_gems: int
    description: str
