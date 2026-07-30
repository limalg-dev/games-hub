from sqlmodel import Session, select, SQLModel, create_engine
from app.models import Game, Move

def test_create_game():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        game = Game(id="test-id", player1="p1", player2=None, status="waiting")
        session.add(game)
        session.commit()
        loaded = session.exec(select(Game).where(Game.id == "test-id")).first()
        assert loaded is not None
        assert loaded.status == "waiting"
