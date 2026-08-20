"""
Super Bomberman Game Logic & Map Generation
"""
import random
from typing import List, Dict, Tuple, Optional

# Grid Dimensions (Classic 15x13)
GRID_COLS = 15
GRID_ROWS = 13

# Cell Types
CELL_EMPTY = 0
CELL_WALL = 1       # Indestructible solid pillar/border
CELL_CRATE = 2      # Destructible soft block
CELL_EXIT = 3       # Stage exit door (revealed under crate)

# Power-Up Types
POWERUP_NONE = 0
POWERUP_BOMB = 1     # Extra bomb capacity (+1)
POWERUP_FIRE = 2     # Extra explosion radius (+1)
POWERUP_SPEED = 3    # Speed boost (+1)
POWERUP_KICK = 4     # Bomb kick
POWERUP_SHIELD = 5   # One-hit shield
POWERUP_REMOTE = 6   # Remote detonator

# Spawn Locations for 4-Player Battle Arena (Row, Col)
SPAWN_CORNERS = [
    (1, 1),                    # Player 1 (Top-Left)
    (GRID_ROWS - 2, GRID_COLS - 2), # Player 2 (Bottom-Right)
    (1, GRID_COLS - 2),        # Player 3 (Top-Right)
    (GRID_ROWS - 2, 1),        # Player 4 (Bottom-Left)
]

# Stage configurations for Arcade / Adventure mode
STAGE_CONFIGS = [
    {
        "stage": 1,
        "name": "Jardim Verde",
        "theme": "garden",
        "enemies": [{"type": "ballom", "count": 4}],
        "time_seconds": 200,
        "crate_density": 0.65,
    },
    {
        "stage": 2,
        "name": "Ruínas de Pedra",
        "theme": "ruins",
        "enemies": [{"type": "ballom", "count": 3}, {"type": "pass", "count": 2}],
        "time_seconds": 180,
        "crate_density": 0.60,
    },
    {
        "stage": 3,
        "name": "Caverna Sombria",
        "theme": "cave",
        "enemies": [{"type": "ballom", "count": 2}, {"type": "pass", "count": 3}, {"type": "phantom", "count": 1}],
        "time_seconds": 180,
        "crate_density": 0.55,
    },
    {
        "stage": 4,
        "name": "Vulcão Ardente",
        "theme": "volcano",
        "enemies": [{"type": "pass", "count": 3}, {"type": "pontan", "count": 2}, {"type": "phantom", "count": 1}],
        "time_seconds": 160,
        "crate_density": 0.50,
    },
    {
        "stage": 5,
        "name": "Cidadela Cibernética",
        "theme": "cyber",
        "enemies": [{"type": "pass", "count": 3}, {"type": "pontan", "count": 3}, {"type": "phantom", "count": 2}],
        "time_seconds": 150,
        "crate_density": 0.45,
    },
]


def generate_map(
    cols: int = GRID_COLS,
    rows: int = GRID_ROWS,
    crate_density: float = 0.65,
    mode: str = "battle",
    seed: Optional[int] = None,
) -> Dict:
    """
    Generates a classic Bomberman arena with indestructible pillars,
    procedurally placed destructible crates, and powerups.
    """
    if seed is not None:
        random.seed(seed)

    grid = [[CELL_EMPTY for _ in range(cols)] for _ in range(rows)]
    powerup_map = [[POWERUP_NONE for _ in range(cols)] for _ in range(rows)]

    # 1. Outer perimeter walls
    for r in range(rows):
        for c in range(cols):
            if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                grid[r][c] = CELL_WALL
            elif r % 2 == 0 and c % 2 == 0:
                grid[r][c] = CELL_WALL

    # 2. Identify safe spawn zones (must be kept empty so players/bots aren't trapped)
    safe_tiles = set()
    if mode == "battle":
        for r_s, c_s in SPAWN_CORNERS:
            safe_tiles.add((r_s, c_s))
            safe_tiles.add((r_s + 1, c_s))
            safe_tiles.add((r_s - 1, c_s))
            safe_tiles.add((r_s, c_s + 1))
            safe_tiles.add((r_s, c_s - 1))
    else:
        # Arcade mode player spawn at (1, 1)
        safe_tiles.add((1, 1))
        safe_tiles.add((1, 2))
        safe_tiles.add((2, 1))

    # 3. Fill destructible crates and power-ups
    candidate_tiles: List[Tuple[int, int]] = []
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r][c] == CELL_EMPTY and (r, c) not in safe_tiles:
                if random.random() < crate_density:
                    grid[r][c] = CELL_CRATE
                    candidate_tiles.append((r, c))

    # Distribute powerups inside crates (~40% of crates hold powerups)
    powerup_pool = [
        POWERUP_BOMB,
        POWERUP_BOMB,
        POWERUP_FIRE,
        POWERUP_FIRE,
        POWERUP_SPEED,
        POWERUP_SPEED,
        POWERUP_KICK,
        POWERUP_SHIELD,
        POWERUP_REMOTE,
    ]

    random.shuffle(candidate_tiles)
    exit_tile = None
    if mode == "arcade" and candidate_tiles:
        exit_tile = candidate_tiles[0]  # Door hidden under first chosen crate

    for idx, tile in enumerate(candidate_tiles):
        r, c = tile
        if mode == "arcade" and (r, c) == exit_tile:
            continue
        if random.random() < 0.40:
            powerup_map[r][c] = random.choice(powerup_pool)

    return {
        "cols": cols,
        "rows": rows,
        "grid": grid,
        "powerups": powerup_map,
        "exit_door": exit_tile,
        "spawns": SPAWN_CORNERS if mode == "battle" else [(1, 1)],
    }


class HighScoreManager:
    """In-memory highscore keeper with initial classic arcade scores."""
    def __init__(self):
        self.scores: List[Dict] = [
            {"name": "BOMBER_MASTER", "score": 25000, "mode": "battle", "difficulty": "hard"},
            {"name": "SHIRO_BOM", "score": 18500, "mode": "arcade", "difficulty": "medium"},
            {"name": "KURO_NINJA", "score": 14200, "mode": "battle", "difficulty": "medium"},
            {"name": "RETRO_CHAMP", "score": 9800, "mode": "arcade", "difficulty": "easy"},
            {"name": "BLASTER", "score": 6400, "mode": "battle", "difficulty": "easy"},
        ]

    def get_scores(self, limit: int = 10) -> List[Dict]:
        return sorted(self.scores, key=lambda x: x["score"], reverse=True)[:limit]

    def add_score(self, name: str, score: int, mode: str = "battle", difficulty: str = "medium") -> Dict:
        entry = {
            "name": (name or "ANON")[:15].upper(),
            "score": max(0, int(score)),
            "mode": mode,
            "difficulty": difficulty,
        }
        self.scores.append(entry)
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:50]
        return entry


high_score_manager = HighScoreManager()
