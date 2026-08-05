WAVES = [
    {"enemies": {"type": "zombie", "hp": 50, "speed": 1.0, "count": 15}, "boss": None},
    {"enemies": {"type": "zombie_fast", "hp": 30, "speed": 2.0, "count": 20}, "boss": None},
    {"enemies": {"type": "tank", "hp": 150, "speed": 0.6, "count": 8}, "boss": None},
    {"enemies": {"type": "suicide", "hp": 40, "speed": 1.5, "count": 12, "explode_dmg": 30}, "boss": None},
    {"enemies": {"type": "vampire", "hp": 100, "speed": 1.0, "count": 10, "lifesteal": 0.2}, "boss": {"type": "dracula", "hp": 300, "speed": 0.8}},
    {"enemies": {"type": "stealth", "hp": 60, "speed": 1.2, "count": 15, "stealth": True}, "boss": None},
    {"enemies": {"type": "swarm", "hp": 10, "speed": 2.5, "count": 100}, "boss": None},
    {"enemies": {"type": "shield", "hp": 80, "speed": 0.8, "count": 1, "shield": 200}, "boss": {"type": "golem", "hp": 500, "speed": 0.4}},
    {"enemies": {"type": "necro", "hp": 80, "speed": 0.8, "count": 8, "resurrect": True}, "boss": None},
    {"enemies": {"type": "final", "hp": 1000, "speed": 0.5, "count": 1}, "boss": {"type": "reaper", "hp": 1000, "speed": 0.5}},
]

def get_wave(n: int) -> dict:
    if n <= len(WAVES):
        return WAVES[n - 1]
    scale = 1 + (n - len(WAVES)) * 0.5
    base = WAVES[-1].copy()
    base["enemies"] = base["enemies"].copy()
    base["enemies"]["hp"] = int(base["enemies"]["hp"] * scale)
    base["enemies"]["count"] = min(base["enemies"]["count"] + (n - len(WAVES)) * 5, 200)
    return base
