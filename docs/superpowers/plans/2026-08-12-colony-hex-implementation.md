# Colônia Hex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement "Colônia Hex" — a turn-based multiplayer light 4X strategy game with real-time WebSockets and hotseat/AI play, integrated into GameHub.

**Architecture:** A self-contained module at `games/colony_hex/` consisting of axial hex map generation (`mapgen.py`), turn-based state and rules engine (`logic.py`), REST/WS endpoints (`routes.py`), and a canvas-rendered UI (`static/`). Wired to the platform shell (`app/main.py`) and games catalog.

**Tech Stack:** Python 3.11+, FastAPI, SQLModel/SQLite, vanilla JS (ES Modules, Canvas).

## Global Constraints
- Grid size: hexagon of radius 4 (distance <= 4, total 61 cells). Axial coordinate bounds: -4 <= q <= 4, -4 <= r <= 4, -4 <= q+r <= 4.
- Player seats: `red`, `blue`, `green`, `yellow` (indices 0..3).
- Action budget: 2 actions per turn. Max turns: 20.
- Costs: Expand (3 leaves), Recruit Worker (2 leaves), Recruit Soldier (5 leaves).
- Standardize all UI copy to pt-BR.
- Execute strictly via TDD (tests/ directory) and test each task via pytest.

---

### Task 1: Axial Hex Map Generator

**Files:**
- Create: `games/colony_hex/mapgen.py`
- Test: `games/colony_hex/tests/test_mapgen.py`

**Interfaces:**
- Consumes: None
- Produces: 
  - `generate_map(nests_count: int) -> List[Dict[str, Any]]`: Returns 61 cells list where each cell has `q`, `r`, `terrain` ("plain" | "leaf" | "rock"), and `owner` (None).
  - Nest locations: `(-4, 0)` for red, `(0, -4)` for blue, `(4, 0)` for green, `(0, 4)` for yellow.
  - Rock locations: `(1, 1), (-1, -1), (2, -2), (-2, 2)` (fixed rocks).
  - Leaf locations: `(-2, 1), (2, -1), (1, -2), (-1, 2)` (fixed cosmetic leaf blocks).

- [ ] **Step 1: Write the failing test**

Create `games/colony_hex/tests/test_mapgen.py`:
```python
import pytest
from games.colony_hex.mapgen import generate_map

def test_generate_map_structure():
    hex_map = generate_map(4)
    assert len(hex_map) == 61
    for cell in hex_map:
        assert "q" in cell
        assert "r" in cell
        assert cell["terrain"] in ("plain", "leaf", "rock")
        assert cell["owner"] is None
        # Coords constraint: q + r + s = 0 where s = -q-r
        s = -cell["q"] - cell["r"]
        assert max(abs(cell["q"]), abs(cell["r"]), abs(s)) <= 4

def test_fixed_terrain_features():
    hex_map = generate_map(4)
    rocks = {(c["q"], c["r"]) for c in hex_map if c["terrain"] == "rock"}
    assert (1, 1) in rocks
    assert (-1, -1) in rocks
    assert (2, -2) in rocks
    assert (-2, 2) in rocks

    leaves = {(c["q"], c["r"]) for c in hex_map if c["terrain"] == "leaf"}
    assert (-2, 1) in leaves
    assert (2, -1) in leaves
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest games/colony_hex/tests/test_mapgen.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write minimal implementation**

Create `games/colony_hex/__init__.py` (empty file).
Create `games/colony_hex/mapgen.py`:
```python
from typing import List, Dict, Any

NEST_COORDS = [(-4, 0), (0, -4), (4, 0), (0, 4)]
ROCK_COORDS = {(1, 1), (-1, -1), (2, -2), (-2, 2)}
LEAF_COORDS = {(-2, 1), (2, -1), (1, -2), (-1, 2)}

def generate_map(nests_count: int) -> List[Dict[str, Any]]:
    cells = []
    for q in range(-4, 5):
        for r in range(-4, 5):
            if abs(-q - r) <= 4:
                coord = (q, r)
                terrain = "plain"
                if coord in ROCK_COORDS:
                    terrain = "rock"
                elif coord in LEAF_COORDS:
                    terrain = "leaf"
                cells.append({
                    "q": q,
                    "r": r,
                    "terrain": terrain,
                    "owner": None
                })
    return cells
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest games/colony_hex/tests/test_mapgen.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add games/colony_hex/mapgen.py games/colony_hex/__init__.py games/colony_hex/tests/test_mapgen.py
git commit -m "feat: add map generation logic for Colony Hex"
```

---

### Task 2: State and Rules Engine

**Files:**
- Create: `games/colony_hex/logic.py`
- Test: `games/colony_hex/tests/test_logic.py`

**Interfaces:**
- Consumes: `generate_map` from `games/colony_hex/mapgen.py`
- Produces:
  - `class GameState`: Representing the complete engine.
    - `__init__(game_id: str, players_setup: List[Dict[str, Any]])`: Setup game.
    - `to_dict() -> Dict[str, Any]`: State dump for WS/REST.
    - `execute_action(color: str, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]`: Execute expand/recruit/move/attack/end_turn. Returns (success, error_message).
    - `run_ai_turn()`: Perform greedy AI actions for active player if AI.

- [ ] **Step 1: Write the failing test**

Create `games/colony_hex/tests/test_logic.py`:
```python
import pytest
from games.colony_hex.logic import GameState

def test_initial_state():
    players = [
        {"color": "red", "is_ai": False},
        {"color": "blue", "is_ai": True}
    ]
    state = GameState("g1", players)
    data = state.to_dict()
    assert data["status"] == "lobby"
    assert len(data["players"]) == 2
    assert data["players"][0]["leaves"] == 10
    assert data["players"][0]["alive"] is True
    # Nest owned
    nest_cell = next(c for c in data["map"] if c["q"] == -4 and c["r"] == 0)
    assert nest_cell["owner"] == "red"

def test_execute_invalid_action():
    players = [{"color": "red", "is_ai": False}, {"color": "blue", "is_ai": False}]
    state = GameState("g1", players)
    state.status = "active"
    # Expand to non-adjacent
    success, err = state.execute_action("red", {"kind": "expand", "q": 0, "r": 0})
    assert success is False
    assert err is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest games/colony_hex/tests/test_logic.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write minimal implementation**

Create `games/colony_hex/logic.py`:
```python
from typing import List, Dict, Any, Tuple, Optional
from games.colony_hex.mapgen import generate_map, NEST_COORDS

def get_distance(q1: int, r1: int, q2: int, r2: int) -> int:
    return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2

class GameState:
    def __init__(self, game_id: str, players_setup: List[Dict[str, Any]]):
        self.game_id = game_id
        self.status = "lobby"
        self.turn_number = 1
        self.turn_index = 0
        self.actions_left = 2
        self.winner = None
        self.ranking = None
        
        self.players = []
        for i, p in enumerate(players_setup):
            self.players.append({
                "color": p["color"],
                "leaves": 10,
                "alive": True,
                "is_ai": p["is_ai"],
                "nest": NEST_COORDS[i]
            })
            
        self.map = generate_map(len(players_setup))
        # Nests owned by default
        for i, p in enumerate(self.players):
            nq, nr = p["nest"]
            for cell in self.map:
                if cell["q"] == nq and cell["r"] == nr:
                    cell["owner"] = p["color"]
                    
        # Initial units: 1 worker on each alive player nest
        self.units = []
        for i, p in enumerate(self.players):
            self.units.append({
                "id": f"u_{p['color']}_0",
                "owner": p["color"],
                "type": "worker",
                "q": p["nest"][0],
                "r": p["nest"][1]
            })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.game_id,
            "status": self.status,
            "map": self.map,
            "units": self.units,
            "players": self.players,
            "turn_index": self.turn_index,
            "turn_number": self.turn_number,
            "actions_left": self.actions_left,
            "winner": self.winner,
            "ranking": self.ranking
        }

    def execute_action(self, color: str, action: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        if self.status != "active":
            return False, "O jogo não está ativo"
        active_player = self.players[self.turn_index]
        if active_player["color"] != color:
            return False, "Não é a sua vez"
        if self.actions_left <= 0:
            return False, "Sem ações restantes"

        kind = action.get("kind")
        if kind == "end_turn":
            self.actions_left = 0
            self._next_turn()
            return True, None

        if kind == "expand":
            q, r = action.get("q"), action.get("r")
            if q is None or r is None:
                return False, "Coordenadas ausentes"
            cell = next((c for c in self.map if c["q"] == q and c["r"] == r), None)
            if not cell or cell["terrain"] == "rock" or cell["owner"] is not None:
                return False, "Célula inválida ou já ocupada"
            # Adjacency check
            adjacent = False
            for c in self.map:
                if c["owner"] == color and get_distance(q, r, c["q"], c["r"]) == 1:
                    adjacent = True
                    break
            if not adjacent:
                return False, "Célula não é adjacente ao seu território"
            # Unit block check
            if any(u["q"] == q and u["r"] == r for u in self.units):
                return False, "Célula contém uma unidade"
            if active_player["leaves"] < 3:
                return False, "Folhas insuficientes (custa 3)"
            active_player["leaves"] -= 3
            cell["owner"] = color
            self.actions_left -= 1
            if self.actions_left <= 0:
                self._next_turn()
            return True, None

        if kind == "recruit":
            u_type = action.get("unit_type")
            if u_type not in ("worker", "soldier"):
                return False, "Tipo de unidade inválido"
            cost = 2 if u_type == "worker" else 5
            if active_player["leaves"] < cost:
                return False, "Folhas insuficientes"
            nq, nr = active_player["nest"]
            # Nest occupied
            if any(u["q"] == nq and u["r"] == nr for u in self.units):
                return False, "Ninho ocupado"
            active_player["leaves"] -= cost
            self.units.append({
                "id": f"u_{color}_{len(self.units)}",
                "owner": color,
                "type": u_type,
                "q": nq,
                "r": nr
            })
            self.actions_left -= 1
            if self.actions_left <= 0:
                self._next_turn()
            return True, None

        if kind == "move":
            u_id = action.get("unit_id")
            to_q, to_r = action.get("to_q"), action.get("to_r")
            unit = next((u for u in self.units if u["id"] == u_id and u["owner"] == color), None)
            if not unit:
                return False, "Unidade não encontrada ou não é sua"
            if get_distance(unit["q"], unit["r"], to_q, to_r) != 1:
                return False, "Destino não é adjacente"
            target_cell = next((c for c in self.map if c["q"] == to_q and c["r"] == to_r), None)
            if not target_cell or target_cell["terrain"] == "rock":
                return False, "Destino inválido (obstáculo)"
            # Target empty or owned by me
            if target_cell["owner"] is not None and target_cell["owner"] != color:
                return False, "Destino pertence ao oponente"
            if any(u["q"] == to_q and u["r"] == to_r for u in self.units):
                return False, "Destino ocupado por outra unidade"
            unit["q"] = to_q
            unit["r"] = to_r
            self.actions_left -= 1
            if self.actions_left <= 0:
                self._next_turn()
            return True, None

        if kind == "attack":
            u_id = action.get("unit_id")
            to_q, to_r = action.get("to_q"), action.get("to_r")
            unit = next((u for u in self.units if u["id"] == u_id and u["owner"] == color), None)
            if not unit or unit["type"] != "soldier":
                return False, "Apenas soldados podem atacar"
            if get_distance(unit["q"], unit["r"], to_q, to_r) != 1:
                return False, "Alvo não é adjacente"
            target_cell = next((c for c in self.map if c["q"] == to_q and c["r"] == to_r), None)
            if not target_cell or target_cell["terrain"] == "rock":
                return False, "Alvo inválido"
            
            # Resolve attack
            enemy_unit = next((u for u in self.units if u["q"] == to_q and u["r"] == to_r), None)
            if enemy_unit:
                if enemy_unit["owner"] == color:
                    return False, "Não pode atacar sua própria unidade"
                # Combat resolution: Soldier wins, attacker always wins soldier vs soldier
                self.units.remove(enemy_unit)
                unit["q"] = to_q
                unit["r"] = to_r
                target_cell["owner"] = color
            elif target_cell["owner"] is not None and target_cell["owner"] != color:
                # Capture empty territory
                unit["q"] = to_q
                unit["r"] = to_r
                target_cell["owner"] = color
            else:
                return False, "Nenhum alvo de ataque válido na célula"

            # Check nest capture (elimination)
            for p in self.players:
                if p["alive"] and p["nest"] == (to_q, to_r) and p["color"] != color:
                    p["alive"] = False
                    # Remove all their units
                    self.units = [u for u in self.units if u["owner"] != p["color"]]
                    # Neutralize other hexes
                    for c in self.map:
                        if c["owner"] == p["color"]:
                            c["owner"] = None
            
            self._check_victory()
            self.actions_left -= 1
            if self.actions_left <= 0:
                self._next_turn()
            return True, None

        return False, "Ação desconhecida"

    def _next_turn(self):
        # Find next alive player
        attempts = 0
        while attempts < len(self.players):
            self.turn_index = (self.turn_index + 1) % len(self.players)
            if self.turn_index == 0:
                self.turn_number += 1
            if self.players[self.turn_index]["alive"]:
                break
            attempts += 1
            
        if self.turn_number > 20 or not self._check_victory():
            self.actions_left = 2
            # Add income
            active_player = self.players[self.turn_index]
            owned_count = sum(1 for c in self.map if c["owner"] == active_player["color"])
            active_player["leaves"] += owned_count

    def _check_victory(self) -> bool:
        alive_players = [p for p in self.players if p["alive"]]
        if len(alive_players) <= 1:
            self.status = "finished"
            self.winner = alive_players[0]["color"] if alive_players else None
            self._calculate_ranking()
            return True
        if self.turn_number > 20:
            self.status = "finished"
            self._calculate_ranking()
            self.winner = self.ranking[0]["color"] if self.ranking else None
            return True
        return False

    def _calculate_ranking(self):
        ranked = []
        for p in self.players:
            owned = sum(1 for c in self.map if c["owner"] == p["color"])
            score = (owned * 10) + p["leaves"] if p["alive"] else 0
            ranked.append({
                "color": p["color"],
                "score": score,
                "alive": p["alive"]
            })
        # Sort desc
        ranked.sort(key=lambda x: (-1 if x["alive"] else 0, -x["score"]))
        self.ranking = ranked

    def run_ai_turn(self):
        # Fast greedy AI logic
        active_color = self.players[self.turn_index]["color"]
        while self.actions_left > 0 and self.status == "active":
            ai_player = self.players[self.turn_index]
            # 1. Attack adjacent enemy if possible
            attack_made = False
            for u in self.units:
                if u["owner"] == active_color and u["type"] == "soldier":
                    for c in self.map:
                        if get_distance(u["q"], u["r"], c["q"], c["r"]) == 1:
                            target_unit = next((tu for tu in self.units if tu["q"] == c["q"] and tu["r"] == c["r"]), None)
                            if (target_unit and target_unit["owner"] != active_color) or (c["owner"] is not None and c["owner"] != active_color):
                                success, _ = self.execute_action(active_color, {"kind": "attack", "unit_id": u["id"], "to_q": c["q"], "to_r": c["r"]})
                                if success:
                                    attack_made = True
                                    break
                    if attack_made:
                        break
            if attack_made:
                continue

            # 2. Expand if leaves >= 3
            expand_made = False
            if ai_player["leaves"] >= 3:
                for c in self.map:
                    if c["owner"] is None and c["terrain"] != "rock":
                        # adjacent to mine?
                        for owned in self.map:
                            if owned["owner"] == active_color and get_distance(c["q"], c["r"], owned["q"], owned["r"]) == 1:
                                success, _ = self.execute_action(active_color, {"kind": "expand", "q": c["q"], "r": c["r"]})
                                if success:
                                    expand_made = True
                                    break
                        if expand_made:
                            break
            if expand_made:
                continue

            # 3. Recruit
            rec_made = False
            nq, nr = ai_player["nest"]
            nest_free = not any(u["q"] == nq and u["r"] == nr for u in self.units)
            if nest_free:
                if ai_player["leaves"] >= 5:
                    success, _ = self.execute_action(active_color, {"kind": "recruit", "unit_type": "soldier"})
                    if success: rec_made = True
                elif ai_player["leaves"] >= 2:
                    success, _ = self.execute_action(active_color, {"kind": "recruit", "unit_type": "worker"})
                    if success: rec_made = True
            if rec_made:
                continue

            # 4. End turn
            self.execute_action(active_color, {"kind": "end_turn"})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest games/colony_hex/tests/test_logic.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add games/colony_hex/logic.py games/colony_hex/tests/test_logic.py
git commit -m "feat: add rules engine and game logic for Colony Hex"
```

---

### Task 3: REST & WebSockets API Router

**Files:**
- Create: `games/colony_hex/routes.py`
- Test: `tests/test_colony_hex_api.py`

**Interfaces:**
- Consumes: `GameState` from `games/colony_hex/logic.py`
- Produces:
  - `colony_hex_router`: FastAPI router.
    - `POST /games/colony_hex`: Create lobby game body `{ max_players: 2..4, fill_ai: bool }`
    - `GET /games/colony_hex`: List lobbies
    - `GET /games/colony_hex/{id}`: State snapshot
    - `WS /games/colony_hex/ws/{game_id}`: Real-time game connection.

- [ ] **Step 1: Write the failing test**

Create `tests/test_colony_hex_api.py`:
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_colony_hex_lobby():
    resp = client.post("/games/colony_hex", json={"max_players": 2, "fill_ai": True})
    assert resp.status_code == 200
    data = resp.json()
    assert "game_id" in data
    assert data["state"]["status"] == "lobby"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_colony_hex_api.py -v`
Expected: FAIL (404 Not Found)

- [ ] **Step 3: Write minimal implementation**

Create `games/colony_hex/routes.py`:
```python
import json
from uuid import uuid4
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict
from games.colony_hex.logic import GameState

router = APIRouter(prefix="/games/colony_hex")

active_games: Dict[str, GameState] = {}
connections: Dict[str, Dict[WebSocket, str]] = {}  # game_id -> {ws: color}

SEATS = ["red", "blue", "green", "yellow"]

@router.post("")
async def create_game(body: dict = None):
    body = body or {}
    max_players = body.get("max_players", 2)
    fill_ai = body.get("fill_ai", True)
    
    game_id = str(uuid4())
    players_setup = []
    # Host is red
    players_setup.append({"color": "red", "is_ai": False})
    
    # Fill remaining seats
    for i in range(1, max_players):
        players_setup.append({"color": SEATS[i], "is_ai": fill_ai})
        
    game_state = GameState(game_id, players_setup)
    active_games[game_id] = game_state
    connections[game_id] = {}
    
    return {"game_id": game_id, "state": game_state.to_dict()}

@router.get("")
async def list_games():
    return [
        {
            "game_id": gid,
            "status": g.status,
            "players": [p["color"] for p in g.players if not p["is_ai"]]
        }
        for gid, g in active_games.items()
    ]

@router.get("/{game_id}")
async def get_game(game_id: str):
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return active_games[game_id].to_dict()

@router.websocket("/ws/{game_id}")
async def ws_endpoint(websocket: WebSocket, game_id: str):
    if game_id not in active_games:
        await websocket.close(code=4004, reason="Jogo não encontrado")
        return
    await websocket.accept()
    game = active_games[game_id]
    
    # Assign color
    conn = connections[game_id]
    assigned_color = None
    for p in game.players:
        if not p["is_ai"] and p["color"] not in conn.values():
            assigned_color = p["color"]
            break
            
    if not assigned_color:
        await websocket.close(code=4003, reason="Jogo cheio")
        return
        
    conn[websocket] = assigned_color
    await websocket.send_json({"type": "welcome", "seat": assigned_color, "state": game.to_dict()})
    
    # Broadcast current connections state
    await broadcast_state(game_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            m_type = msg.get("type")
            
            if m_type == "start":
                if assigned_color == "red" and game.status == "lobby":
                    game.status = "active"
                    await broadcast_state(game_id)
            elif m_type == "action":
                if game.status != "active":
                    await websocket.send_json({"type": "error", "message": "Jogo não está ativo"})
                    continue
                action_data = msg.get("action", {})
                success, err = game.execute_action(assigned_color, action_data)
                if not success:
                    await websocket.send_json({"type": "error", "message": err})
                else:
                    await broadcast_state(game_id)
                    # Trigger AI chain
                    while game.status == "active" and game.players[game.turn_index]["is_ai"]:
                        game.run_ai_turn()
                        await broadcast_state(game_id)
            elif m_type == "forfeit":
                game.status = "finished"
                # Winner is anyone else alive
                alive = [p["color"] for p in game.players if p["alive"] and p["color"] != assigned_color]
                game.winner = alive[0] if alive else None
                game._calculate_ranking()
                await broadcast_state(game_id)
    except WebSocketDisconnect:
        conn.pop(websocket, None)
        await broadcast_state(game_id)

async def broadcast_state(game_id: str):
    if game_id not in active_games:
        return
    game = active_games[game_id]
    conn = connections[game_id]
    msg = {"type": "state", "state": game.to_dict()}
    for ws in conn:
        try:
            await ws.send_json(msg)
        except Exception:
            pass
```

- [ ] **Step 3b: Wire to `app/main.py`**

Open `app/main.py` and modify imports and router mounting:
```python
# add import
from games.colony_hex.routes import router as colony_hex_router

# In app router section:
app.include_router(colony_hex_router)

# Mount specific play route:
@app.get("/play/colony_hex")
async def play_colony_hex():
    return FileResponse("games/colony_hex/static/index.html")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_colony_hex_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add games/colony_hex/routes.py tests/test_colony_hex_api.py app/main.py
git commit -m "feat: implement API and WebSocket endpoints for Colony Hex"
```

---

### Task 4: Frontend HTML, Canvas and Logic

**Files:**
- Create: `games/colony_hex/static/index.html`
- Create: `games/colony_hex/static/board.js`
- Create: `games/colony_hex/static/logic.js`

**Interfaces:**
- Consumes: WebSocket endpoints `/games/colony_hex/ws/{id}`
- Produces: Hex grid visual board, lobby panel, actions buttons panel.

- [ ] **Step 1: Create static/index.html**

Create `games/colony_hex/static/index.html`:
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Colônia Hex — GameHub</title>
  <link rel="stylesheet" href="/static/styles.css">
  <style>
    .game-area { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 20px; }
    .colony-panel { background: var(--bg-secondary); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); min-width: 250px; }
    .hud-row { display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.9rem; }
    .action-btn { background: var(--accent); color: var(--on-accent); padding: 8px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background var(--transition); }
    .action-btn:hover { background: var(--accent-hover); }
    .action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  </style>
</head>
<body class="page active">
  <header class="game-header">
    <a href="/" class="btn-back" aria-label="Voltar para a seleção de jogos">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
    </a>
    <div class="game-status">
      <span id="turn-indicator" aria-live="polite">Conectando ao lobby...</span>
      <span id="timer">Turno 1/20</span>
    </div>
    <div class="game-menu">
      <button id="btn-forfeit" class="btn-danger">Desistir</button>
    </div>
  </header>
  <main class="game-container">
    <div class="game-area">
      <div class="board-wrapper" style="flex: 1; min-height: 450px;">
        <canvas id="colony-canvas" width="500" height="500"></canvas>
      </div>
      <aside class="sidebar">
        <section class="colony-panel">
          <h4>Seu Painel</h4>
          <div class="hud-row"><span>Sua Cor:</span><span id="hud-my-color" style="font-weight:bold">-</span></div>
          <div class="hud-row"><span>Ações:</span><span id="hud-actions">-</span></div>
          <div class="hud-row"><span>Folhas (🍃):</span><span id="hud-leaves" style="color:var(--gold); font-weight:bold">-</span></div>
        </section>
        <section class="colony-panel" style="margin-top: 15px;">
          <h4>Ações Rápidas</h4>
          <div style="display:grid; gap: 8px;">
            <button id="btn-recruit-worker" class="action-btn">Recrutar Operária (2 🍃)</button>
            <button id="btn-recruit-soldier" class="action-btn">Recrutar Soldado (5 🍃)</button>
            <button id="btn-end-turn" class="btn-secondary" style="padding: 8px 16px;">Encerrar Turno</button>
          </div>
        </section>
        <section id="lobby-panel" class="colony-panel" style="margin-top: 15px;">
          <h4>Lobby</h4>
          <button id="btn-start-game" class="btn-primary" style="display:none;">Iniciar Partida</button>
          <div id="lobby-slots"></div>
        </section>
      </aside>
    </div>
  </main>
  
  <!-- ===== GAME OVER OVERLAY ===== -->
  <div id="game-over-overlay" class="play-gate hidden" role="dialog" aria-modal="true">
    <div class="play-gate-inner">
      <h2 id="game-over-title">Vitória!</h2>
      <p id="game-over-message" style="color: var(--text-secondary); margin-bottom: 1rem;"></p>
      <a href="/" class="btn-secondary" style="text-decoration:none;">Voltar para a Landing</a>
    </div>
  </div>

  <script type="module" src="logic.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create static/board.js**

Create `games/colony_hex/static/board.js`:
```js
// Axial hex grid canvas rendering
const COLOR_MAP = {
  red: "#e94560",
  blue: "#4a90e2",
  green: "#4ade80",
  yellow: "#ffd700",
  neutral: "#2a2a4a",
  rock: "#444"
};

export class HexBoard {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    this.hexRadius = 26;
    this.cells = [];
    this.units = [];
    this.selectedCell = null;
    this.onCellSelected = null;
  }

  update(cells, units) {
    this.cells = cells;
    this.units = units;
    this.render();
  }

  getHexCorner(center, size, i) {
    let angle_deg = 60 * i;
    let angle_rad = Math.PI / 180 * angle_deg;
    return {
      x: center.x + size * Math.cos(angle_rad),
      y: center.y + size * Math.sin(angle_rad)
    };
  }

  hexToPixel(q, r) {
    let x = this.hexRadius * (Math.sqrt(3) * q + Math.sqrt(3)/2 * r);
    let y = this.hexRadius * (3./2 * r);
    return { x: x + this.canvas.width / 2, y: y + this.canvas.height / 2 };
  }

  pixelToHex(x, y) {
    let px = x - this.canvas.width / 2;
    let py = y - this.canvas.height / 2;
    let q = (Math.sqrt(3)/3 * px - 1./3 * py) / this.hexRadius;
    let r = (2./3 * py) / this.hexRadius;
    return this.hexRound(q, r);
  }

  hexRound(fractional_q, fractional_r) {
    let s = -fractional_q - fractional_r;
    let q = Math.round(fractional_q);
    let r = Math.round(fractional_r);
    let s_round = Math.round(s);
    let q_diff = Math.abs(q - fractional_q);
    let r_diff = Math.abs(r - fractional_r);
    let s_diff = Math.abs(s_round - s);
    if (q_diff > r_diff && q_diff > s_diff) {
      q = -r - s_round;
    } else if (r_diff > s_diff) {
      r = -q - s_round;
    }
    return { q, r };
  }

  drawHex(center, color, fill = true, stroke = true, width = 1) {
    this.ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      let corner = this.getHexCorner(center, this.hexRadius - 1, i);
      if (i === 0) this.ctx.moveTo(corner.x, corner.y);
      else this.ctx.lineTo(corner.x, corner.y);
    }
    this.ctx.closePath();
    if (fill) {
      this.ctx.fillStyle = color;
      this.ctx.fill();
    }
    if (stroke) {
      this.ctx.strokeStyle = "#2a2a4a";
      this.ctx.lineWidth = width;
      this.ctx.stroke();
    }
  }

  render() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Draw cells
    for (let cell of this.cells) {
      let center = this.hexToPixel(cell.q, cell.r);
      let color = COLOR_MAP.neutral;
      if (cell.terrain === "rock") color = COLOR_MAP.rock;
      else if (cell.owner) color = COLOR_MAP[cell.owner];
      
      // Selected outline
      let isSelected = this.selectedCell && this.selectedCell.q === cell.q && this.selectedCell.r === cell.r;
      this.drawHex(center, color, true, true, isSelected ? 3 : 1);
      
      if (isSelected) {
        this.ctx.strokeStyle = "#e94560";
        this.ctx.stroke();
      }

      // Draw leaves icon
      if (cell.terrain === "leaf") {
        this.ctx.fillStyle = "#4ade80";
        this.ctx.font = "12px sans-serif";
        this.ctx.fillText("🍃", center.x - 7, center.y + 4);
      }
    }

    // Draw units
    for (let u of this.units) {
      let center = this.hexToPixel(u.q, u.r);
      // Unit color boundary circle
      this.ctx.beginPath();
      this.ctx.arc(center.x, center.y, 14, 0, 2 * Math.PI);
      this.ctx.fillStyle = COLOR_MAP[u.owner];
      this.ctx.fill();
      this.ctx.lineWidth = 2;
      this.ctx.strokeStyle = "#fff";
      this.ctx.stroke();
      
      // Unit type emoji
      this.ctx.fillStyle = "#fff";
      this.ctx.font = "14px sans-serif";
      this.ctx.fillText(u.type === "worker" ? "🐜" : "🪖", center.x - 7, center.y + 5);
    }
  }

  bindEvents() {
    this.canvas.addEventListener("click", (e) => {
      let rect = this.canvas.getBoundingClientRect();
      let clickX = e.clientX - rect.left;
      let clickY = e.clientY - rect.top;
      let target = this.pixelToHex(clickX, clickY);
      
      let matchedCell = this.cells.find(c => c.q === target.q && c.r === target.r);
      if (matchedCell) {
        this.selectedCell = matchedCell;
        this.render();
        if (this.onCellSelected) this.onCellSelected(matchedCell);
      }
    });
  }
}
```

- [ ] **Step 3: Create static/logic.js**

Create `games/colony_hex/static/logic.js`:
```js
import { HexBoard } from './board.js';

let board = new HexBoard("colony-canvas");
board.bindEvents();

let gameId = location.pathname.split("/").pop();
let wsProtocol = location.protocol === "https:" ? "wss" : "ws";
let ws = new WebSocket(`${wsProtocol}://${location.host}/games/colony_hex/ws/${gameId}`);

let myColor = null;
let gameState = null;

const turnIndicator = document.getElementById("turn-indicator");
const lobbyPanel = document.getElementById("lobby-panel");
const lobbySlots = document.getElementById("lobby-slots");
const btnStart = document.getElementById("btn-start-game");
const btnForfeit = document.getElementById("btn-forfeit");

const hudColor = document.getElementById("hud-my-color");
const hudActions = document.getElementById("hud-actions");
const hudLeaves = document.getElementById("hud-leaves");

const btnRecruitWorker = document.getElementById("btn-recruit-worker");
const btnRecruitSoldier = document.getElementById("btn-recruit-soldier");
const btnEndTurn = document.getElementById("btn-end-turn");

ws.onmessage = (event) => {
  let msg = JSON.parse(event.data);
  if (msg.type === "welcome") {
    myColor = msg.seat;
    hudColor.textContent = myColor.toUpperCase();
    hudColor.style.color = getPlayerColorHex(myColor);
    updateState(msg.state);
  } else if (msg.type === "state") {
    updateState(msg.state);
  } else if (msg.type === "error") {
    alert(msg.message);
  }
};

function getPlayerColorHex(color) {
  const map = { red: "#e94560", blue: "#4a90e2", green: "#4ade80", yellow: "#ffd700" };
  return map[color] || "#fff";
}

function updateState(state) {
  gameState = state;
  board.update(state.map, state.units);
  
  let activePlayer = state.players[state.turn_index];
  let myPlayerInfo = state.players.find(p => p.color === myColor);
  
  if (myPlayerInfo) {
    hudActions.textContent = state.turn_index === state.players.indexOf(myPlayerInfo) ? state.actions_left : "0";
    hudLeaves.textContent = myPlayerInfo.leaves;
  }
  
  if (state.status === "lobby") {
    lobbyPanel.style.display = "block";
    turnIndicator.textContent = "Aguardando início da partida no lobby...";
    lobbySlots.innerHTML = state.players.map(p => `
      <div style="color: ${getPlayerColorHex(p.color)}">
        Slot ${p.color.toUpperCase()} ${p.is_ai ? "(IA)" : "(Humano)"}
      </div>
    `).join("");
    if (myColor === "red") {
      btnStart.style.display = "block";
    }
  } else if (state.status === "active") {
    lobbyPanel.style.display = "none";
    let isMyTurn = activePlayer.color === myColor;
    turnIndicator.textContent = isMyTurn ? "Sua vez de jogar!" : `Vez do jogador ${activePlayer.color.toUpperCase()}...`;
    document.getElementById("timer").textContent = `Turno ${state.turn_number}/20`;
  } else if (state.status === "finished") {
    let overlay = document.getElementById("game-over-overlay");
    let msgEl = document.getElementById("game-over-message");
    document.getElementById("game-over-title").textContent = state.winner === myColor ? "Vitória!" : "Fim de Jogo";
    msgEl.textContent = state.winner === myColor ? "Parabéns, você dominou o formigueiro!" : `O jogador ${state.winner?.toUpperCase()} venceu.`;
    overlay.classList.remove("hidden");
  }
}

btnStart.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "start" }));
});

btnForfeit.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "forfeit" }));
});

btnEndTurn.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "action", action: { kind: "end_turn" } }));
});

btnRecruitWorker.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "action", action: { kind: "recruit", unit_type: "worker" } }));
});

btnRecruitSoldier.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "action", action: { kind: "recruit", unit_type: "soldier" } }));
});

// Canvas cell click moves & attacks
board.onCellSelected = (cell) => {
  if (!gameState || gameState.status !== "active") return;
  let activePlayer = gameState.players[gameState.turn_index];
  if (activePlayer.color !== myColor) return;
  
  // Is there a selection?
  // If clicked own territory empty cell -> Option to expand
  if (cell.owner === null && cell.terrain !== "rock") {
    // Expand action
    ws.send(JSON.stringify({
      type: "action",
      action: { kind: "expand", q: cell.q, r: cell.r }
    }));
  } else {
    // Check if clicked cell contains own unit to select
    let ownUnit = gameState.units.find(u => u.q === cell.q && u.r === cell.r && u.owner === myColor);
    if (ownUnit) {
      board.selectedUnit = ownUnit;
    } else if (board.selectedUnit) {
      // Clicked adjacent target with selected unit -> Move or Attack
      let targetUnit = gameState.units.find(u => u.q === cell.q && u.r === cell.r);
      let isEnemyUnit = targetUnit && targetUnit.owner !== myColor;
      let isEnemyTerritory = cell.owner !== null && cell.owner !== myColor;
      
      if (isEnemyUnit || isEnemyTerritory) {
        // Attack
        ws.send(JSON.stringify({
          type: "action",
          action: {
            kind: "attack",
            unit_id: board.selectedUnit.id,
            to_q: cell.q,
            to_r: cell.r
          }
        }));
      } else {
        // Move
        ws.send(JSON.stringify({
          type: "action",
          action: {
            kind: "move",
            unit_id: board.selectedUnit.id,
            to_q: cell.q,
            to_r: cell.r
          }
        }));
      }
      board.selectedUnit = null;
    }
  }
};
```

- [ ] **Step 4: Commit**

```bash
git add games/colony_hex/static/index.html games/colony_hex/static/board.js games/colony_hex/static/logic.js
git commit -m "feat: implement frontend hex board rendering and WebSocket interface"
```

---

### Task 5: Wiring into Hub Shell

**Files:**
- Modify: `static/games.js`
- Modify: `static/play-url.js`
- Test: `tests/test_games_list.py`

**Interfaces:**
- Consumes: `colony_hex` metadata
- Produces: Play card on landing, play-url parse recognition.

- [ ] **Step 1: Wire play-url playable games list**

Open `static/play-url.js` and modify `PLAYABLE_GAMES`:
```js
export const PLAYABLE_GAMES = [
  'checkers',
  'wordsearch',
  'crossword',
  'snake',
  'ant_defense',
  'tower_defense',
  'colony_hex', // Add colony_hex
];
```

- [ ] **Step 2: Add gameCard definition in `static/games.js`**

Add `colony_hex` to `GAMES` in `static/games.js`:
```js
  colony_hex: {
    id: 'colony_hex',
    title: 'Colônia Hex',
    desc: 'Jogo de estratégia 4X por turnos. Expanda seu território em um mapa hexagonal, recrute operárias/soldados e conquiste ninhos inimigos.',
    shortDesc: 'Estratégia hexagonal de formigas. Solo ou multiplayer.',
    players: '2–4',
    modes: ['Solo', 'IA', 'Online'],
    category: ['estrategia', 'tabuleiro'],
    collections: ['treine-sua-mente'],
    duration: '10–20 min',
    difficulty: ['Médio'],
    rating: 4.8,
    plays: 54000,
    featured: true,
    badge: 'novo',
    thumbnail: '🐜',
    icon: '🐜',
    rules: [
      'Controle ninhos de formigas em grade hexagonal (raio 4)',
      'Gere 1 folha por turno para cada célula de território dominado',
      'Ações: expandir território, recrutar unidades (operária/soldado) ou mover/atacar',
      'Soldados atacam e capturam unidades ou territórios oponentes',
      'Capture o ninho adversário para eliminá-lo. Vence quem sobrar ou tiver maior pontuação'
    ]
  }
```

- [ ] **Step 3: Run the tests to check catalog integration**

Run: `pytest tests/test_games_list.py -v`
Expected: FAIL (because result expects 6 games instead of 7)

- [ ] **Step 4: Update tests/test_games_list.py**

Modify `test_exports_exactly_the_six_games` to include `colony_hex`:
```python
def test_exports_exactly_the_seven_games(result):
    assert set(result["ids"]) == {
        "checkers", "wordsearch", "crossword", "snake", "ant_defense", "tower_defense", "colony_hex"
    }
```
And similarly adjust `test_all_games_has_each_id_exactly_once` to expect length 7.

- [ ] **Step 5: Run tests and make sure they pass**

Run: `pytest tests/test_games_list.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add static/games.js static/play-url.js tests/test_games_list.py
git commit -m "chore: integrate Colony Hex into landing catalog and play URL router"
```
