from games.towerdefense.engine import GameEngine


def test_engine_init():
    engine = GameEngine({"grid": [[0] * 5 for _ in range(5)], "spawn": (0, 0), "base": (4, 4)})
    assert engine.lives == 20
    assert engine.wave == 0


def test_engine_place_tower():
    engine = GameEngine({"grid": [[0] * 5 for _ in range(5)], "spawn": (0, 0), "base": (4, 4)})
    result = engine.place_tower("rifle", 2, 2, 50)
    assert result is True


def test_engine_place_tower_invalid():
    engine = GameEngine({"grid": [[0, 1, 0], [0, 0, 0], [0, 0, 0]], "spawn": (0, 0), "base": (2, 2)})
    result = engine.place_tower("rifle", 0, 1, 50)
    assert result is False


def test_engine_spawn_wave():
    engine = GameEngine({"grid": [[0] * 5 for _ in range(5)], "spawn": (0, 0), "base": (4, 4)})
    engine.start_wave()
    assert engine.wave == 1
    assert len(engine.enemies) > 0


def test_engine_enemy_reaches_base():
    engine = GameEngine({"grid": [[0] * 5 for _ in range(5)], "spawn": (0, 0), "base": (0, 4)})
    engine.start_wave()
    for _ in range(100):
        engine.update(0.1)
    assert engine.lives < 20 or len(engine.enemies) == 0
