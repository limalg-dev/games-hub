# Tower Defense Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete tower defense game with free-form placement, A* pathfinding, 5 tower types with upgrades, 10 waves, competitive multiplayer, and persistent economy.

**Architecture:** Backend handles game logic, pathfinding, and wave management. Frontend uses Canvas 2D for rendering and DOM for UI. WebSocket enables competitive mode.

**Tech Stack:** FastAPI, SQLModel, SQLite, Canvas 2D, vanilla JS (ES modules), pytest

## Global Constraints

- Python >=3.11
- fastapi==0.115, uvicorn==0.30, sqlmodel==0.0.21
- No build tools — pure vanilla JS with ES modules
- SQLite database at `./games.db` (or `DATABASE_URL` env var)
- Games auto-discovered from `games/` directory

---

## File Structure

### Files to Create

| File | Responsibility |
|------|---------------|
| `games/towerdefense/__init__.py` | Package init |
| `games/towerdefense/pathfinding.py` | A* algorithm |
| `games/towerdefense/engine.py` | Server-side game loop, wave spawning |
| `games/towerdefense/towers.py` | Tower definitions, upgrades, combos |
| `games/towerdefense/economy.py` | Gold, gems, shop logic |
| `games/towerdefense/waves.py` | Wave configurations |
| `games/towerdefense/models.py` | SQLModel: PlayerProfile, ShopItem |
| `games/towerdefense/static/board.js` | Canvas rendering, camera, input |
| `games/towerdefense/static/logic.js` | Client game loop, collision |
| `games/towerdefense/static/pathfinding.js` | Client-side A* preview |
| `games/towerdefense/static/towers.js` | Tower rendering, range display |
| `games/towerdefense/static/ui.js` | DOM HUD, shop, leaderboard |
| `games/towerdefense/static/enemies.js` | Enemy sprites, animations |
| `games/towerdefense/static/maps.js` | Map definitions |
| `games/towerdefense/static/preview.js` | Modal preview |
| `games/towerdefense/tests/__init__.py` | Test package |
| `games/towerdefense/tests/test_pathfinding.py` | A* unit tests |
| `games/towerdefense/tests/test_engine.py` | Engine unit tests |
| `games/towerdefense/tests/test_towers.py` | Tower unit tests |
| `games/towerdefense/tests/test_economy.py` | Economy unit tests |
| `games/towerdefense/tests/test_waves.py` | Wave unit tests |

### Files to Modify

| File | Changes |
|------|---------|
| `app/main.py` | Add TD endpoints, shop seeding |
| `app/models.py` | PlayerProfile, ShopItem models |
| `app/schemas.py` | TD schemas |
| `app/websocket.py` | Competitive TD handler |
| `static/app.js` | Register TD in GAMES |
| `static/styles.css` | TD-specific styles |

---

## Agent Dispatch Strategy

This plan is designed for **5 parallel agents**:

| Agent | Scope | Dependencies |
|-------|-------|-------------|
| **Agent 1: Pathfinding** | `pathfinding.py` + `pathfinding.js` + tests | None |
| **Agent 2: Towers + Waves** | `towers.py`, `waves.py` + tests | None |
| **Agent 3: Engine + Economy** | `engine.py`, `economy.py`, `models.py` + tests | Agents 1, 2 (imports) |
| **Agent 4: Frontend** | All `static/td/*.js` + app.js integration | Agents 1, 2 (API contract) |
| **Agent 5: Backend Integration** | `main.py`, `websocket.py`, `schemas.py` + API/WS tests | Agent 3 (models) |

Agents 1 and 2 run fully in parallel. Agent 3 depends on 1+2. Agents 4 and 5 can run in parallel after Agent 3.

---

### Task 1: Pathfinding (A*)

**Files:**
- Create: `games/towerdefense/pathfinding.py`
- Create: `games/towerdefense/tests/__init__.py`
- Create: `games/towerdefense/tests/test_pathfinding.py`

**Interfaces:**
- Produces: `astar(grid, start, end) -> List[Tuple[int, int]]` or `None`
- Grid is `List[List[int]]` — 0 = walkable, 1 = blocked

- [ ] **Step 1: Create package init and test init**

```python
# games/towerdefense/__init__.py
# games/towerdefense/tests/__init__.py
```

- [ ] **Step 2: Write failing tests**

```python
# games/towerdefense/tests/test_pathfinding.py
from games.towerdefense.pathfinding import astar

def test_astar_finds_path():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    path = astar(grid, (0, 0), (4, 4))
    assert path is not None
    assert len(path) > 0
    assert path[0] == (0, 0)
    assert path[-1] == (4, 4)

def test_astar_no_path():
    grid = [
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
    ]
    path = astar(grid, (0, 0), (0, 4))
    assert path is None

def test_astar_straight_line():
    grid = [[0, 0, 0, 0, 0]]
    path = astar(grid, (0, 0), (0, 4))
    assert path == [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]

def test_astar_start_equals_end():
    grid = [[0, 0], [0, 0]]
    path = astar(grid, (0, 0), (0, 0))
    assert path == [(0, 0)]

def test_astar_around_obstacle():
    grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    path = astar(grid, (0, 0), (2, 2))
    assert path is not None
    assert len(path) == 5
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest games/towerdefense/tests/test_pathfinding.py -v`
Expected: FAIL with ImportError

- [ ] **Step 4: Implement A* pathfinding**

```python
# games/towerdefense/pathfinding.py
import heapq
from typing import List, Tuple, Optional

def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(grid: List[List[int]], start: Tuple[int, int], end: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    rows, cols = len(grid), len(grid[0])
    if not (0 <= start[0] < rows and 0 <= start[1] < cols):
        return None
    if not (0 <= end[0] < rows and 0 <= end[1] < cols):
        return None
    if grid[start[0]][start[1]] == 1 or grid[end[0]][end[1]] == 1:
        return None
    if start == end:
        return [start]

    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (current[0] + dr, current[1] + dc)
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
                if grid[neighbor[0]][neighbor[1]] == 1:
                    continue
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, end)
                    heapq.heappush(open_set, (f_score, neighbor))

    return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest games/towerdefense/tests/test_pathfinding.py -v`
Expected: 5 PASS

- [ ] **Step 6: Create client-side pathfinding mirror**

```javascript
// games/towerdefense/static/pathfinding.js
export function astar(grid, start, end) {
    const rows = grid.length, cols = grid[0].length;
    if (start[0] < 0 || start[0] >= rows || start[1] < 0 || start[1] >= cols) return null;
    if (end[0] < 0 || end[0] >= rows || end[1] < 0 || end[1] >= cols) return null;
    if (grid[start[0]][start[1]] === 1 || grid[end[0]][end[1]] === 1) return null;
    if (start[0] === end[0] && start[1] === end[1]) return [start];

    const openSet = [[0, start[0], start[1]]];
    const cameFrom = {};
    const gScore = {};
    gScore[`${start[0]},${start[1]}`] = 0;

    const dirs = [[-1,0],[1,0],[0,-1],[0,1]];

    while (openSet.length > 0) {
        openSet.sort((a, b) => a[0] - b[0]);
        const [, cr, cc] = openSet.shift();
        if (cr === end[0] && cc === end[1]) {
            const path = [];
            let key = `${cr},${cc}`;
            while (key) {
                const [r, c] = key.split(',').map(Number);
                path.unshift([r, c]);
                key = cameFrom[key];
            }
            return path;
        }
        for (const [dr, dc] of dirs) {
            const nr = cr + dr, nc = cc + dc;
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] !== 1) {
                const tentG = gScore[`${cr},${cc}`] + 1;
                const nKey = `${nr},${nc}`;
                if (tentG < (gScore[nKey] ?? Infinity)) {
                    cameFrom[nKey] = `${cr},${cc}`;
                    gScore[nKey] = tentG;
                    openSet.push([tentG + Math.abs(nr - end[0]) + Math.abs(nc - end[1]), nr, nc]);
                }
            }
        }
    }
    return null;
}
```

- [ ] **Step 7: Commit**

```bash
git add games/towerdefense/__init__.py games/towerdefense/pathfinding.py games/towerdefense/static/pathfinding.js games/towerdefense/tests/
git commit -m "feat(td): add A* pathfinding (backend + client)"
```

---

### Task 2: Tower Definitions + Wave Configs

**Files:**
- Create: `games/towerdefense/towers.py`
- Create: `games/towerdefense/waves.py`
- Create: `games/towerdefense/tests/test_towers.py`
- Create: `games/towerdefense/tests/test_waves.py`

**Interfaces:**
- Produces: `TOWER_TYPES` dict, `get_tower_stats(type, level) -> dict`
- Produces: `WAVES` list, `get_wave(n) -> dict`

- [ ] **Step 1: Write failing tests for towers**

```python
# games/towerdefense/tests/test_towers.py
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
```

- [ ] **Step 2: Write failing tests for waves**

```python
# games/towerdefense/tests/test_waves.py
from games.towerdefense.waves import WAVES, get_wave

def test_waves_count():
    assert len(WAVES) == 10

def test_wave_has_required_fields():
    for wave in WAVES:
        assert "enemies" in wave
        assert "boss" in wave

def test_get_wave():
    wave = get_wave(1)
    assert wave["enemies"]["type"] == "zombie"
    assert wave["enemies"]["count"] == 15

def test_wave_5_has_boss():
    wave = get_wave(5)
    assert wave["boss"] is not None
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest games/towerdefense/tests/test_towers.py games/towerdefense/tests/test_waves.py -v`
Expected: FAIL with ImportError

- [ ] **Step 4: Implement towers.py**

```python
# games/towerdefense/towers.py
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
```

- [ ] **Step 5: Implement waves.py**

```python
# games/towerdefense/waves.py
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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest games/towerdefense/tests/ -v`
Expected: 9 PASS

- [ ] **Step 7: Commit**

```bash
git add games/towerdefense/towers.py games/towerdefense/waves.py games/towerdefense/tests/test_towers.py games/towerdefense/tests/test_waves.py
git commit -m "feat(td): add tower definitions, upgrade tree, and wave configs"
```

---

### Task 3: Game Engine + Economy + Models

**Files:**
- Create: `games/towerdefense/engine.py`
- Create: `games/towerdefense/economy.py`
- Create: `games/towerdefense/models.py`
- Create: `games/towerdefense/tests/test_engine.py`
- Create: `games/towerdefense/tests/test_economy.py`

**Interfaces:**
- Consumes: `astar()`, `TOWER_TYPES`, `WAVES`
- Produces: `GameEngine` class, `Economy` class

- [ ] **Step 1: Write failing tests for engine**

```python
# games/towerdefense/tests/test_engine.py
from games.towerdefense.engine import GameEngine

def test_engine_init():
    engine = GameEngine({"grid": [[0]*5 for _ in range(5)], "spawn": (0,0), "base": (4,4)})
    assert engine.lives == 20
    assert engine.wave == 0

def test_engine_place_tower():
    engine = GameEngine({"grid": [[0]*5 for _ in range(5)], "spawn": (0,0), "base": (4,4)})
    result = engine.place_tower("rifle", 2, 2, 50)
    assert result is True

def test_engine_place_tower_invalid():
    engine = GameEngine({"grid": [[0,1,0],[0,0,0],[0,0,0]], "spawn": (0,0), "base": (2,2)})
    result = engine.place_tower("rifle", 0, 1, 50)
    assert result is False

def test_engine_spawn_wave():
    engine = GameEngine({"grid": [[0]*5 for _ in range(5)], "spawn": (0,0), "base": (4,4)})
    engine.start_wave()
    assert engine.wave == 1
    assert len(engine.enemies) > 0

def test_engine_enemy_reaches_base():
    engine = GameEngine({"grid": [[0]*5 for _ in range(5)], "spawn": (0,0), "base": (0,4)})
    engine.start_wave()
    # Simulate enemies moving to base
    for _ in range(100):
        engine.update(0.1)
    assert engine.lives < 20 or len(engine.enemies) == 0
```

- [ ] **Step 2: Write failing tests for economy**

```python
# games/towerdefense/tests/test_economy.py
from games.towerdefense.economy import Economy

def test_economy_init():
    eco = Economy()
    assert eco.gold == 200
    assert eco.gems == 0

def test_economy_spend_gold():
    eco = Economy()
    result = eco.spend(50)
    assert result is True
    assert eco.gold == 150

def test_economy_spend_insufficient():
    eco = Economy()
    result = eco.spend(300)
    assert result is False
    assert eco.gold == 200

def test_economy_earn_gold():
    eco = Economy()
    eco.earn_gold(100)
    assert eco.gold == 300

def test_economy_earn_gems():
    eco = Economy()
    eco.earn_gems(5)
    assert eco.gems == 5
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest games/towerdefense/tests/test_engine.py games/towerdefense/tests/test_economy.py -v`
Expected: FAIL with ImportError

- [ ] **Step 4: Implement engine.py**

```python
# games/towerdefense/engine.py
from typing import List, Tuple, Dict, Optional
from games.towerdefense.pathfinding import astar
from games.towerdefense.towers import get_tower_stats, get_combo_bonus
from games.towerdefense.waves import get_wave

class Enemy:
    def __init__(self, hp: int, speed: float, path: List[Tuple[int, int]], enemy_type: str, **kwargs):
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.path = path
        self.path_index = 0
        self.x = float(path[0][0])
        self.y = float(path[0][1])
        self.type = enemy_type
        self.alive = True
        self.reached_base = False
        for k, v in kwargs.items():
            setattr(self, k, v)

class Projectile:
    def __init__(self, x: float, y: float, target: Enemy, damage: int, tower_type: str, **kwargs):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.tower_type = tower_type
        self.speed = 8.0
        for k, v in kwargs.items():
            setattr(self, k, v)

class Tower:
    def __init__(self, tower_type: str, row: int, col: int, level: int = 1):
        self.type = tower_type
        self.row = row
        self.col = col
        self.level = level
        stats = get_tower_stats(tower_type, level)
        self.damage = stats["damage"]
        self.range = stats["range"]
        self.fire_rate = stats.get("fire_rate", 1.0)
        self.cooldown = 0.0
        for k, v in stats.items():
            if k not in ("damage", "range", "fire_rate"):
                setattr(self, k, v)

class GameEngine:
    def __init__(self, map_config: dict):
        self.grid = map_config["grid"]
        self.spawn = map_config["spawn"]
        self.base = map_config["base"]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.lives = 20
        self.gold = 200
        self.wave = 0
        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.tower_grid: Dict[Tuple[int, int], Tower] = {}

    def can_place(self, row: int, col: int) -> bool:
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return False
        if self.grid[row][col] != 0:
            return False
        if (row, col) in self.tower_grid:
            return False
        test_grid = [r[:] for r in self.grid]
        test_grid[row][col] = 1
        return astar(test_grid, self.spawn, self.base) is not None

    def place_tower(self, tower_type: str, row: int, col: int, cost: int) -> bool:
        if not self.can_place(row, col):
            return False
        if self.gold < cost:
            return False
        self.gold -= cost
        tower = Tower(tower_type, row, col)
        self.towers.append(tower)
        self.tower_grid[(row, col)] = tower
        return True

    def start_wave(self):
        self.wave += 1
        wave_config = get_wave(self.wave)
        ec = wave_config["enemies"]
        path = astar(self.grid, self.spawn, self.base)
        if not path:
            return
        for _ in range(ec["count"]):
            self.enemies.append(Enemy(ec["hp"], ec["speed"], list(path), ec["type"]))
        if wave_config["boss"]:
            bc = wave_config["boss"]
            self.enemies.append(Enemy(bc["hp"], bc["speed"], list(path), bc["type"]))

    def update(self, dt: float):
        for tower in self.towers:
            tower.cooldown -= dt
            if tower.cooldown <= 0:
                target = self._find_target(tower)
                if target:
                    self.projectiles.append(Projectile(
                        float(tower.row), float(tower.col), target, tower.damage, tower.type
                    ))
                    tower.cooldown = tower.fire_rate

        for proj in list(self.projectiles):
            dx = proj.target.x - proj.x
            dy = proj.target.y - proj.y
            dist = (dx*dx + dy*dy) ** 0.5
            if dist < 0.3:
                proj.target.hp -= proj.damage
                if proj.target.hp <= 0:
                    proj.target.alive = False
                    self.gold += 10
                self.projectiles.remove(proj)
            else:
                proj.x += (dx / dist) * proj.speed * dt
                proj.y += (dy / dist) * proj.speed * dt

        for enemy in list(self.enemies):
            if not enemy.alive:
                self.enemies.remove(enemy)
                continue
            if enemy.path_index < len(enemy.path) - 1:
                target = enemy.path[enemy.path_index + 1]
                dx = target[0] - enemy.x
                dy = target[1] - enemy.y
                dist = (dx*dx + dy*dy) ** 0.5
                move = enemy.speed * dt
                if move >= dist:
                    enemy.x = float(target[0])
                    enemy.y = float(target[1])
                    enemy.path_index += 1
                else:
                    enemy.x += (dx / dist) * move
                    enemy.y += (dy / dist) * move
            else:
                enemy.reached_base = True
                enemy.alive = False
                self.lives -= 1

        self.enemies = [e for e in self.enemies if e.alive]

    def _find_target(self, tower: Tower) -> Optional[Enemy]:
        best = None
        best_dist = float('inf')
        for enemy in self.enemies:
            dx = enemy.x - tower.row
            dy = enemy.y - tower.col
            dist = (dx*dx + dy*dy) ** 0.5
            if dist <= tower.range and dist < best_dist:
                best = enemy
                best_dist = dist
        return best
```

- [ ] **Step 5: Implement economy.py**

```python
# games/towerdefense/economy.py
class Economy:
    def __init__(self, gold: int = 200, gems: int = 0):
        self.gold = gold
        self.gems = gems

    def spend(self, amount: int) -> bool:
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    def earn_gold(self, amount: int):
        self.gold += amount

    def earn_gems(self, amount: int):
        self.gems += amount

    def can_afford(self, amount: int) -> bool:
        return self.gold >= amount
```

- [ ] **Step 6: Implement models.py**

```python
# games/towerdefense/models.py
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
```

- [ ] **Step 7: Run all tests**

Run: `.venv/bin/python -m pytest games/towerdefense/tests/ -v`
Expected: 14 PASS

- [ ] **Step 8: Commit**

```bash
git add games/towerdefense/engine.py games/towerdefense/economy.py games/towerdefense/models.py games/towerdefense/tests/test_engine.py games/towerdefense/tests/test_economy.py
git commit -m "feat(td): add game engine, economy, and models"
```

---

### Task 4: Backend Integration (API + WebSocket)

**Files:**
- Modify: `app/main.py`
- Modify: `app/models.py`
- Modify: `app/schemas.py`
- Modify: `app/websocket.py`
- Create: `tests/test_td_api.py`
- Create: `tests/test_td_ws.py`

**Interfaces:**
- Consumes: `GameEngine`, `Economy`, models

- [ ] **Step 1: Read existing files to understand structure**

Read `app/main.py`, `app/models.py`, `app/schemas.py`, `app/websocket.py`

- [ ] **Step 2: Add TD models to app/models.py**

Add `PlayerProfile` and `ShopItem` imports, add game_type support

- [ ] **Step 3: Add TD endpoints to app/main.py**

- `POST /api/shop/buy` — purchase shop item
- `GET /api/leaderboard` — global ranking
- `GET /api/profile/{player}` — player profile
- Update `POST /games` to support `game_type: "towerdefense"`

- [ ] **Step 4: Add competitive TD WebSocket handler**

In `app/websocket.py`, add `handle_towerdefense_ws()`:
- Validate tower placements server-side
- Sync wave timing
- Send enemies that pass to opponent

- [ ] **Step 5: Write API tests**

```python
# tests/test_td_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_create_td_game():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/games", json={"game_type": "towerdefense"})
        assert resp.status_code == 200
        assert "id" in resp.json()

@pytest.mark.asyncio
async def test_get_leaderboard():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/leaderboard")
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_shop_buy():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/shop/buy", json={"player": "test", "item": "sniper_unlock"})
        assert resp.status_code in (200, 400)
```

- [ ] **Step 6: Write WebSocket tests**

```python
# tests/test_td_ws.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_td_game_creates():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/games", json={"game_type": "towerdefense"})
        assert resp.status_code == 200
        game_id = resp.json()["id"]
        state = await client.get(f"/games/{game_id}")
        assert state.status_code == 200
```

- [ ] **Step 7: Run ALL tests to verify no regression**

Run: `.venv/bin/python -m pytest tests/ games/checkers/tests/ games/crossword/tests/ games/towerdefense/tests/ -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add app/ tests/test_td_api.py tests/test_td_ws.py
git commit -m "feat(td): add API endpoints, WebSocket handler, and tests"
```

---

### Task 5: Frontend — Canvas Rendering + Game UI

**Files:**
- Create: `games/towerdefense/static/board.js`
- Create: `games/towerdefense/static/logic.js`
- Create: `games/towerdefense/static/towers.js`
- Create: `games/towerdefense/static/enemies.js`
- Create: `games/towerdefense/static/maps.js`
- Create: `games/towerdefense/static/ui.js`
- Create: `games/towerdefense/static/preview.js`
- Modify: `static/app.js`
- Modify: `static/styles.css`

**Interfaces:**
- Consumes: Pathfinding A*, tower configs, wave configs
- Produces: `TowerDefenseGame` class

- [ ] **Step 1: Read existing frontend patterns**

Read `static/app.js`, `games/wordsearch/static/board.js`, `games/crossword/static/board.js`

- [ ] **Step 2: Create maps.js (map definitions)**

```javascript
// games/towerdefense/static/maps.js
export const MAPS = {
    urban: {
        name: "Urban Wasteland",
        grid: [
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,1,1,1,0,0,0,0,0,0,1,1,1,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2],
        ],
        spawn: [0, 0],
        base: [9, 19],
    },
};

export const TILE_SIZE = 32;
export const TILE_TYPES = {
    0: { name: "grass", buildable: true, color: "#2d5a1e" },
    1: { name: "road", buildable: false, color: "#8B7355" },
    2: { name: "water", buildable: false, color: "#1a4a7a" },
    3: { name: "building", buildable: false, color: "#555" },
};
```

- [ ] **Step 3: Create enemies.js (enemy rendering)**

```javascript
// games/towerdefense/static/enemies.js
export const ENEMY_COLORS = {
    zombie: "#4a7a4a",
    zombie_fast: "#7a7a4a",
    tank: "#5a5a5a",
    suicide: "#ff4444",
    vampire: "#8a2a8a",
    stealth: "rgba(100,100,100,0.3)",
    swarm: "#6a8a6a",
    shield: "#4a6a8a",
    necro: "#3a3a6a",
    final: "#8a2a2a",
    dracula: "#6a1a6a",
    golem: "#4a4a4a",
    reaper: "#2a2a2a",
};

export function drawEnemy(ctx, enemy, tileSize) {
    const x = enemy.x * tileSize;
    const y = enemy.y * tileSize;
    const color = ENEMY_COLORS[enemy.type] || "#ff0000";

    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x + tileSize/2, y + tileSize/2, tileSize/3, 0, Math.PI * 2);
    ctx.fill();

    const hpPct = enemy.hp / enemy.max_hp;
    ctx.fillStyle = "#333";
    ctx.fillRect(x + 4, y - 4, tileSize - 8, 3);
    ctx.fillStyle = hpPct > 0.5 ? "#4caf50" : hpPct > 0.25 ? "#ff9800" : "#f44336";
    ctx.fillRect(x + 4, y - 4, (tileSize - 8) * hpPct, 3);
}
```

- [ ] **Step 4: Create towers.js (tower rendering)**

```javascript
// games/towerdefense/static/towers.js
export const TOWER_COLORS = {
    rifle: "#4a8af4",
    sniper: "#f4a84a",
    missile: "#f44a4a",
    tesla: "#a44af4",
    slow: "#4af4f4",
};

export function drawTower(ctx, tower, tileSize) {
    const x = tower.col * tileSize;
    const y = tower.row * tileSize;
    const color = TOWER_COLORS[tower.type] || "#fff";

    ctx.fillStyle = color;
    ctx.fillRect(x + 4, y + 4, tileSize - 8, tileSize - 8);

    ctx.fillStyle = "#fff";
    ctx.font = "10px monospace";
    ctx.textAlign = "center";
    ctx.fillText(tower.level, x + tileSize/2, y + tileSize/2 + 4);
}

export function drawRange(ctx, row, col, range, tileSize) {
    ctx.strokeStyle = "rgba(255, 255, 255, 0.3)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(col * tileSize + tileSize/2, row * tileSize + tileSize/2, range * tileSize, 0, Math.PI * 2);
    ctx.stroke();
}
```

- [ ] **Step 5: Create board.js (main game class)**

```javascript
// games/towerdefense/static/board.js
import { MAPS, TILE_SIZE, TILE_TYPES } from './maps.js';
import { drawEnemy } from './enemies.js';
import { drawTower, drawRange } from './towers.js';
import { astar } from './pathfinding.js';

export class TowerDefenseGame {
    constructor(config) {
        this.containerId = config.containerId;
        this.canvas = null;
        this.ctx = null;
        this.map = MAPS[config.map || "urban"];
        this.grid = this.map.grid.map(r => [...r]);
        this.towers = [];
        this.enemies = [];
        this.projectiles = [];
        this.gold = 200;
        this.lives = 20;
        this.wave = 0;
        this.waveActive = false;
        this.selectedTower = null;
        this.camera = { x: 0, y: 0, zoom: 1 };
        this.running = false;
        this.lastTime = 0;
    }

    init() {
        const container = document.getElementById(this.containerId);
        this.canvas = document.createElement("canvas");
        this.canvas.width = this.map.grid[0].length * TILE_SIZE;
        this.canvas.height = this.map.grid.length * TILE_SIZE;
        this.canvas.style.background = "#1a1a2e";
        container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext("2d");

        this.canvas.addEventListener("click", (e) => this.handleClick(e));
        this.canvas.addEventListener("wheel", (e) => this.handleZoom(e));

        this.running = true;
        this.gameLoop(0);
    }

    destroy() {
        this.running = false;
        if (this.canvas) this.canvas.remove();
    }

    gameLoop(time) {
        if (!this.running) return;
        const dt = (time - this.lastTime) / 1000;
        this.lastTime = time;
        this.update(dt);
        this.render();
        requestAnimationFrame((t) => this.gameLoop(t));
    }

    update(dt) {
        for (const proj of this.projectiles) {
            const dx = proj.target.x - proj.x;
            const dy = proj.target.y - proj.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < 0.3) {
                proj.target.hp -= proj.damage;
                if (proj.target.hp <= 0) proj.target.alive = false;
                this.projectiles = this.projectiles.filter(p => p !== proj);
            } else {
                proj.x += (dx/dist) * 8 * dt;
                proj.y += (dy/dist) * 8 * dt;
            }
        }
        this.enemies = this.enemies.filter(e => e.alive);
    }

    render() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        for (let r = 0; r < this.grid.length; r++) {
            for (let c = 0; c < this.grid[r].length; c++) {
                const tile = TILE_TYPES[this.grid[r][c]];
                ctx.fillStyle = tile.color;
                ctx.fillRect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE - 1, TILE_SIZE - 1);
            }
        }

        for (const tower of this.towers) drawTower(ctx, tower, TILE_SIZE);
        for (const enemy of this.enemies) drawEnemy(ctx, enemy, TILE_SIZE);

        if (this.selectedTower) {
            drawRange(ctx, this.selectedTower.row, this.selectedTower.col, this.selectedTower.range, TILE_SIZE);
        }
    }

    handleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const col = Math.floor((e.clientX - rect.left) / TILE_SIZE);
        const row = Math.floor((e.clientY - rect.top) / TILE_SIZE);
        if (this.selectedType && this.grid[row]?.[col] === 0) {
            const testGrid = this.grid.map(r => [...r]);
            testGrid[row][col] = 1;
            if (astar(testGrid, this.map.spawn, this.map.base)) {
                this.grid[row][col] = 1;
                this.towers.push({ type: this.selectedType, row, col, level: 1, range: 3, damage: 10 });
                this.gold -= 50;
            }
        }
    }

    handleZoom(e) {
        e.preventDefault();
        this.camera.zoom += e.deltaY > 0 ? -0.1 : 0.1;
        this.camera.zoom = Math.max(0.5, Math.min(2, this.camera.zoom));
    }

    startWave() {
        this.waveActive = true;
        this.wave++;
    }
}
```

- [ ] **Step 6: Create ui.js, logic.js, preview.js**

Create the DOM UI for HUD (gold, lives, wave), shop panel, and leaderboard. Create preview.js for modal. Create logic.js for wave management.

- [ ] **Step 7: Register in app.js and add styles**

Add tower defense to `GAMES` object, add preview, game start, cleanup. Add `.td-*` CSS styles.

- [ ] **Step 8: Commit**

```bash
git add games/towerdefense/static/ static/app.js static/styles.css
git commit -m "feat(td): add frontend canvas rendering, UI, and SPA integration"
```

---

### Task 6: Integration Tests + Final Verification

**Files:**
- Create: `tests/test_td_integration.py`

- [ ] **Step 1: Write integration tests**

```python
# tests/test_td_integration.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_full_td_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/games", json={"game_type": "towerdefense"})
        assert resp.status_code == 200
        game_id = resp.json()["id"]
        state = await client.get(f"/games/{game_id}")
        assert state.status_code == 200

@pytest.mark.asyncio
async def test_leaderboard_after_game():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/leaderboard")
        assert resp.status_code == 200
```

- [ ] **Step 2: Run ALL tests**

Run: `.venv/bin/python -m pytest tests/ games/checkers/tests/ games/crossword/tests/ games/towerdefense/tests/ -v`

- [ ] **Step 3: Fix any failures**

- [ ] **Step 4: Commit**

```bash
git add tests/test_td_integration.py
git commit -m "test(td): add integration tests for tower defense"
```
