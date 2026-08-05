TOWER_TYPES = {
    "rifle": {
        "damage": 10, "range": 3, "cost": 50, "fire_rate": 0.5,
        "upgrades": [
            {"damage": 15, "range": 3, "cost": 50},
            {"damage": 15, "range": 4, "cost": 75},
            {"damage": 15, "range": 4, "fire_rate": 0.25, "cost": 100},
        ]
    },
    "sniper": {
        "damage": 50, "range": 6, "cost": 120, "fire_rate": 2.0,
        "upgrades": [
            {"damage": 75, "range": 6, "cost": 120},
            {"damage": 75, "range": 6, "pierce": 2, "cost": 180},
            {"damage": 75, "range": 7, "crit_chance": 0.5, "cost": 240},
        ]
    },
    "missile": {
        "damage": 30, "range": 4, "cost": 150, "fire_rate": 1.5, "aoe": 1,
        "upgrades": [
            {"damage": 30, "range": 4, "aoe": 2, "cost": 150},
            {"damage": 45, "range": 4, "aoe": 2, "cost": 225},
            {"damage": 45, "range": 5, "aoe": 3, "cluster": True, "cost": 300},
        ]
    },
    "tesla": {
        "damage": 15, "range": 3, "cost": 100, "fire_rate": 1.0, "chain": 3,
        "upgrades": [
            {"damage": 15, "range": 3, "chain": 5, "cost": 100},
            {"damage": 20, "range": 3, "chain": 5, "stun": 0.5, "cost": 150},
            {"damage": 30, "range": 4, "chain": 7, "stun": 0.5, "cost": 200},
        ]
    },
    "slow": {
        "damage": 0, "range": 3, "cost": 80, "fire_rate": 0.5, "slow": 0.5,
        "upgrades": [
            {"damage": 0, "range": 3, "slow": 0.7, "cost": 80},
            {"damage": 0, "range": 4, "slow": 0.7, "cost": 120},
            {"damage": 0, "range": 4, "slow": 1.0, "freeze": 2.0, "cost": 160},
        ]
    },
}

COMBOS = {
    ("rifle", "tesla"): 0.2,
    ("sniper", "slow"): 0.15,
    ("missile", "tesla"): 0.25,
}

def get_tower_stats(tower_type: str, level: int) -> dict:
    base = TOWER_TYPES[tower_type].copy()
    if level > 1:
        upgrade = TOWER_TYPES[tower_type]["upgrades"][level - 2]
        base.update(upgrade)
    return base

def get_combo_bonus(tower_type: str, placed: dict) -> float:
    bonus = 0.0
    pos = placed.get(tower_type)
    if pos is None:
        return 0.0
    for (t1, t2), mult in COMBOS.items():
        if tower_type in (t1, t2):
            other = t2 if tower_type == t1 else t1
            other_pos = placed.get(other)
            if other_pos and abs(pos[0] - other_pos[0]) <= 1 and abs(pos[1] - other_pos[1]) <= 1:
                bonus = max(bonus, mult)
    return bonus
