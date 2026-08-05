from games.towerdefense.towers import TOWER_TYPES, get_tower_stats, get_combo_bonus

def test_tower_types_count():
    assert len(TOWER_TYPES) == 5

def test_tower_has_required_fields():
    for name, tower in TOWER_TYPES.items():
        assert "damage" in tower
        assert "range" in tower
        assert "cost" in tower
        assert "upgrades" in tower
        assert len(tower["upgrades"]) == 3

def test_get_tower_stats_level_1():
    stats = get_tower_stats("rifle", 1)
    assert stats["damage"] == 10
    assert stats["range"] == 3

def test_get_tower_stats_level_3():
    stats = get_tower_stats("rifle", 3)
    assert stats["damage"] > 10
    assert stats["range"] > 3

def test_combo_bonus():
    placed = {"rifle": (0, 0), "tesla": (0, 1)}
    bonus = get_combo_bonus("rifle", placed)
    assert bonus == 0.2
