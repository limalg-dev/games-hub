# Colônia Hex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement **Colônia Hex**, a turn-based hex territory strategy game inspired by *Antiyoy* / *Slay*, fully integrated into the GameHub platform with procedural map generation, unit fusion, economy & upkeep, AI bots, HTML5 Canvas frontend with WebAudio SFX, and leaderboard.

**Architecture:**
- `games/colonia_hex/logic.py`: pure logic module for axial hex grid $(q, r)$, BFS province discovery, unit fusion ($1+1=2, 1+2=3, 2+2=4$), defense calculations, bankruptcy collapse, procedural island generation, and 3 AI bot levels.
- `games/colonia_hex/routes.py`: FastAPI router exposing `/colonia-hex/api/*` endpoints and `/play/colonia_hex`.
- `games/colonia_hex/static/index.html`: self-contained standalone HTML5 Canvas UI with procedural Web Audio synthesis, interactive province inspection, and touch/click controls.
- `app/main.py` & `static/games.js`: GameHub platform integration.

**Tech Stack:** Python 3.11+, FastAPI, SQLModel, Pytest + HTTPX, Vanilla JS (HTML5 Canvas + Web Audio API).

---

### Task 1: Backend Logic & Unit Tests (`games/colonia_hex/logic.py`)

**Files:**
- Create: `games/colonia_hex/__init__.py`
- Create: `games/colonia_hex/logic.py`
- Create: `games/colonia_hex/test_colonia_hex_logic.py`

**Interfaces:**
- `HexGame`: main game state class managing grid, provinces, player turns, actions, and bot steps.
- `HexCell`: `q: int, r: int, owner: Optional[int], unit_level: int, has_moved: bool, building: Optional[str], has_tree: bool`.
- `Province`: `id: str, owner: int, cells: List[Tuple[int, int]], gold: int, income: int, upkeep: int, castle_pos: Tuple[int, int]`.
- Actions: `recruit(province_id, q, r, level)`, `move(from_q, from_r, to_q, to_r)`, `build(province_id, q, r, building)`, `end_turn()`.

- [ ] **Step 1: Write failing unit tests in `games/colonia_hex/test_colonia_hex_logic.py`**

```python
import pytest
from games.colonia_hex.logic import HexGame, HexCell, UNIT_COSTS, UNIT_UPKEEP

def test_hex_coordinates_and_neighbors():
    game = HexGame(map_size="small", num_players=2)
    neighbors = game.get_neighbors(0, 0)
    assert len(neighbors) == 6
    assert (1, 0) in neighbors
    assert (0, 1) in neighbors

def test_unit_fusion():
    game = HexGame(map_size="small", num_players=2)
    # Unit level 1 + Unit level 1 = Unit level 2
    assert game.calc_fusion_level(1, 1) == 2
    assert game.calc_fusion_level(1, 2) == 3
    assert game.calc_fusion_level(2, 2) == 4
    assert game.calc_fusion_level(1, 3) == 4
    assert game.calc_fusion_level(2, 3) is None  # Exceeds max level 4

def test_province_economy_and_bankruptcy():
    game = HexGame(map_size="small", num_players=2)
    p = game.provinces[0]
    initial_gold = p.gold
    # End turn generates income = hex_count - upkeep
    game.end_turn()
    # Verifies gold update
    assert game.turn_number >= 1

def test_combat_defense_rule():
    game = HexGame(map_size="small", num_players=2)
    # Strength 2 defeats defense 1
    assert game.can_conquer(attacker_level=2, target_defense=1) is True
    # Strength 1 cannot defeat defense 1
    assert game.can_conquer(attacker_level=1, target_defense=1) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest games/colonia_hex/test_colonia_hex_logic.py -q`
Expected: FAIL (ModuleNotFoundError).

- [ ] **Step 3: Implement `logic.py`**

Implement `HexGame`, `HexCell`, `Province`, coordinate math, unit fusion, defense checks, BFS province formation, income/upkeep calculations, starvation collapse, map generator, and bot turns.

- [ ] **Step 4: Run unit tests to verify pass**

Run: `venv/bin/pytest games/colonia_hex/test_colonia_hex_logic.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add games/colonia_hex/
git commit -m "feat(colonia_hex): implement hex strategy core logic, economy, fusion, and tests"
```

---

### Task 2: API Router & Endpoints (`games/colonia_hex/routes.py`)

**Files:**
- Create: `games/colonia_hex/routes.py`
- Create: `tests/test_colonia_hex_integration.py`

**Interfaces:**
- `router = APIRouter(prefix="/colonia-hex", tags=["colonia_hex"])`
- `POST /colonia-hex/api/new`
- `GET /colonia-hex/api/state/{game_id}`
- `POST /colonia-hex/api/action`
- `GET /colonia-hex/api/highscores` & `POST /colonia-hex/api/highscores`
- `GET /colonia-hex/play` & `GET /play/colonia_hex`

- [ ] **Step 1: Write integration tests in `tests/test_colonia_hex_integration.py`**

Test creating games, executing moves, ending turns, and highscore ranking.

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/test_colonia_hex_integration.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement `routes.py`**

Implement router endpoints and in-memory active games dictionary + `ColoniaHexHighScoreManager`.

- [ ] **Step 4: Run tests to verify pass**

Run: `venv/bin/pytest tests/test_colonia_hex_integration.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add games/colonia_hex/routes.py tests/test_colonia_hex_integration.py
git commit -m "feat(colonia_hex): add REST API routes, highscores, and integration tests"
```

---

### Task 3: Platform Integration (`app/main.py`, `static/games.js`, docs)

**Files:**
- Modify: `app/main.py`
- Modify: `static/games.js`
- Modify: `README.md`
- Modify: `PRODUCT.md`

- [ ] **Step 1: Wire router and static files in `app/main.py`**
- [ ] **Step 2: Add game metadata card in `static/games.js`**
- [ ] **Step 3: Document game in `README.md` and `PRODUCT.md`**
- [ ] **Step 4: Commit**

```bash
git add app/main.py static/games.js README.md PRODUCT.md
git commit -m "feat(colonia_hex): integrate Colonia Hex into GameHub main app, catalog, and docs"
```

---

### Task 4: Frontend HTML5 Canvas Game (`games/colonia_hex/static/index.html`)

**Files:**
- Create: `games/colonia_hex/static/index.html`

- [ ] **Step 1: Implement Hexagonal Canvas 2D renderer**
  - Pointy-topped hexes with ant territory colors, province borders, fog/neutral territory.
  - Draw units (Operária, Soldado, Guardião, Elite) with level badges and idle animation.
  - Draw buildings (Castelo, Fazenda, Torre de Vigia, Árvores).
- [ ] **Step 2: Implement WebAudio Sound Synthesizer**
  - Clicks, recruitment, movement, unit fusion, conquering, building, starvation collapse, turn bell, victory.
- [ ] **Step 3: Implement HUD & Action Controls**
  - Province stats banner: Gold 🍃, Income (+/-), Upkeep.
  - Action buttons: Recrutar Operária [10🍃], Construir Fazenda [12🍃], Construir Torre [15🍃], Passar Turno [Espaço].
  - New Game modal (Tamanho do Mapa, Dificuldade da IA, Quantidade de Jogadores).
  - Victory/Defeat screen with highscore submission.
- [ ] **Step 4: Commit**

```bash
git add games/colonia_hex/static/index.html
git commit -m "feat(colonia_hex): implement standalone HTML5 Canvas frontend with WebAudio SFX"
```

---

### Task 5: Full Suite Verification & Polish

- [ ] **Step 1: Run entire test suite**
Run: `venv/bin/pytest -q`
Expected: 100% pass across all games.
