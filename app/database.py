from __future__ import annotations
from sqlmodel import SQLModel, create_engine

engine = create_engine("sqlite:///./games.db", connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)
