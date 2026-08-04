# Crossword WebSocket Support — Implementation Plan

## Goal

Add WebSocket multiplayer support for crossword puzzles alongside existing checkers functionality.

## Current State

- `app/websocket.py` — Only handles checkers games
- `app/models.py` — `Game` model without `game_type` field
- `games/crossword/` — Has `models.py` (Word) and `words.py` (seed data), but NO `generator.py`
- Existing tests pass for checkers

## Dependencies (Must Complete First)

### 1. Create `games/crossword/generator.py`

The crossword generator doesn't exist yet. Based on the design spec, it needs:
- Backtracking algorithm to place words on N×N grid
- Difficulty levels: Easy (8×8), Medium (12×12), Hard (15×15)
- Returns: `{grid, clues, size, words_placed}`
- Grid is `List[List[Optional[str]]]` — letters or None for black cells

**Code from existing plan:**
```python
# games/crossword/generator.py
import random
from typing import List, Optional, Dict, Any

DIFFICULTY_CONFIG = {
    1: {"max_size": 8, "min_words": 6, "max_words": 10},
    2: {"max_size": 12, "min_words": 10, "max_words": 15},
    3: {"max_size": 15, "min_words": 15, "max_words": 22},
}

class CrosswordGrid:
    def __init__(self, size: int):
        self.size = size
        self.grid: List[List[Optional[str]]] = [[None for _ in range(size)] for _ in range(size)]
        self.placed_words: List[Dict[str, Any]] = []

    def can_place_word(self, word: str, row: int, col: int, direction: str) -> bool:
        dr = 1 if direction == "down" else 0
        dc = 1 if direction == "across" else 0
        end_row = row + dr * (len(word) - 1)
        end_col = col + dc * (len(word) - 1)
        if end_row >= self.size or end_col >= self.size:
            return False
        if row < 0 or col < 0:
            return False
        for i, letter in enumerate(word):
            r = row + dr * i
            c = col + dc * i
            existing = self.grid[r][c]
            if existing is not None and existing != letter:
                return False
        return True

    def place_word(self, word: str, row: int, col: int, direction: str, hint: str, number: int):
        dr = 1 if direction == "down" else 0
        dc = 1 if direction == "across" else 0
        for i, letter in enumerate(word):
            r = row + dr * i
            c = col + dc * i
            self.grid[r][c] = letter
        self.placed_words.append({
            "word": word, "row": row, "col": col,
            "direction": direction, "hint": hint, "number": number,
        })

    def get_intersections(self, word: str) -> List[Dict[str, Any]]:
        intersections = []
        for placed in self.placed_words:
            for i, letter in enumerate(word):
                dr = 1 if placed["direction"] == "down" else 0
                dc = 1 if placed["direction"] == "across" else 0
                for j, placed_letter in enumerate(placed["word"]):
                    if placed_letter == letter:
                        new_dir = "across" if placed["direction"] == "down" else "down"
                        new_row = placed["row"] + dr * j - (1 if new_dir == "down" else 0) * i
                        new_col = placed["col"] + dc * j - (1 if new_dir == "across" else 0) * i
                        if self.can_place_word(word, new_row, new_col, new_dir):
                            intersections.append({
                                "row": new_row, "col": new_col, "direction": new_dir,
                            })
        return intersections


def generate_crossword(words: List[Dict[str, str]], difficulty: int = 1) -> Dict[str, Any]:
    config = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG[1])
    max_size = config["max_size"]
    max_words = min(len(words), config["max_words"])
    sorted_words = sorted(words, key=lambda w: len(w["word"]), reverse=True)
    selected = sorted_words[:max_words]
    crossword = CrosswordGrid(max_size)
    word_number = 1
    if selected:
        first = selected[0]
        start_row = max_size // 2
        start_col = (max_size - len(first["word"])) // 2
        crossword.place_word(
            first["word"].upper(), start_row, start_col, "across",
            first.get("hint", ""), word_number
        )
        word_number += 1
    for word_data in selected[1:]:
        word = word_data["word"].upper()
        hint = word_data.get("hint", "")
        intersections = crossword.get_intersections(word)
        random.shuffle(intersections)
        placed = False
        for inter in intersections:
            if crossword.can_place_word(word, inter["row"], inter["col"], inter["direction"]):
                crossword.place_word(word, inter["row"], inter["col"], inter["direction"], hint, word_number)
                word_number += 1
                placed = True
                break
        if not placed:
            for direction in random.sample(["across", "down"], 2):
                for r in range(max_size):
                    for c in range(max_size):
                        if crossword.can_place_word(word, r, c, direction):
                            crossword.place_word(word, r, c, direction, hint, word_number)
                            word_number += 1
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break
    clues = {"across": [], "down": []}
    for pw in crossword.placed_words:
        clue_entry = {
            "number": pw["number"], "row": pw["row"], "col": pw["col"],
            "clue": pw["hint"], "length": len(pw["word"]),
        }
        clues[pw["direction"]].append(clue_entry)
    clues["across"].sort(key=lambda c: (c["row"], c["col"]))
    clues["down"].sort(key=lambda c: (c["row"], c["col"]))
    return {
        "grid": crossword.grid, "clues": clues, "size": max_size,
        "words_placed": len(crossword.placed_words),
    }
```

### 2. Add `game_type` to Game Model

```python
# app/models.py — add field
class Game(SQLModel, table=True):
    id: str = Field(primary_key=True)
    player1: Optional[str] = None
    player2: Optional[str] = None
    status: str = Field(default="waiting")
    game_type: str = Field(default="checkers")  # NEW
```

### 3. Update `app/main.py`

- Import `Word`, `SEED_WORDS`, `generate_crossword`
- Add lifespan to seed words on startup
- Update `POST /games` to accept `game_type` and `difficulty`
- Add `POST /api/words` and `GET /api/words` endpoints

---

## Main Task: WebSocket Crossword Support

### Files to Modify

- `app/websocket.py` — Add crossword game handling

### Files to Create

- `tests/test_crossword_ws.py` — WebSocket tests

### Architecture

The WebSocket handler needs to:
1. **Detect game type** from database on connection
2. **Branch logic** based on game_type:
   - `"checkers"` → Existing checkers logic (unchanged)
   - `"crossword"` → New crossword logic

### Crossword WebSocket State

```python
# In ConnectionManager, add crossword-specific state:
self.puzzles: Dict[str, dict] = {}      # game_id -> generated puzzle
self.user_grids: Dict[str, Dict[str, list]] = {}  # game_id -> {ws_id: [[letter]]}
self.completed: Dict[str, Dict[str, bool]] = {}   # game_id -> {ws_id: completed}
```

### Crossword WebSocket Protocol

**Server → Client:**
```
{"type": "puzzle", "grid": [...], "clues": {...}, "size": 8}
{"type": "correct", "row": 0, "col": 0, "letter": "A"}
{"type": "incorrect", "row": 0, "col": 0}
{"type": "complete", "time": 120, "correct": 45, "total": 50}
{"type": "opponent_input", "row": 0, "col": 0, "letter": "B"}
{"type": "error", "message": "..."}
```

**Client → Server:**
```
{"type": "input", "row": 0, "col": 0, "letter": "A"}
{"type": "connect"}
```

### Implementation Steps

#### Step 1: Add crossword state to ConnectionManager

```python
class ConnectionManager:
    def __init__(self):
        # Existing checkers state
        self.boards: Dict[str, Board] = {}
        self.turn: Dict[str, str] = {}
        self.clients: Dict[str, Dict[int, dict]] = {}
        
        # NEW: Crossword state
        self.puzzles: Dict[str, dict] = {}
        self.user_grids: Dict[str, Dict[str, list]] = {}
        self.completed: Dict[str, Dict[str, bool]] = {}
```

#### Step 2: Update disconnect to clean crossword state

```python
def disconnect(self, game_id: str, websocket: WebSocket):
    ws_id = id(websocket)
    if game_id in self.clients:
        self.clients[game_id].pop(ws_id, None)
        if not self.clients[game_id]:
            del self.clients[game_id]
            # Clean checkers state
            self.boards.pop(game_id, None)
            self.turn.pop(game_id, None)
            # Clean crossword state
            self.puzzles.pop(game_id, None)
            self.user_grids.pop(game_id, None)
            self.completed.pop(game_id, None)
```

#### Step 3: Update websocket_endpoint to detect game type

```python
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    with Session(engine) as session:
        db_game = session.exec(select(Game).where(Game.id == game_id)).first()
        if not db_game:
            await websocket.close(code=4004, reason="Game not found")
            return
    
    game_type = getattr(db_game, 'game_type', 'checkers')
    
    if game_type == "crossword":
        await handle_crossword_ws(websocket, game_id, db_game)
    else:
        await handle_checkers_ws(websocket, game_id)
```

#### Step 4: Implement handle_crossword_ws

```python
async def handle_crossword_ws(websocket: WebSocket, game_id: str, db_game):
    color = await manager.connect(game_id, websocket)
    if color is None:
        await websocket.close(code=4003, reason="Game full")
        return
    
    # Update player fields
    with Session(engine) as session:
        game = session.exec(select(Game).where(Game.id == game_id)).first()
        if color == "w":
            game.player1 = "connected"
            if not game.player2:
                game.status = "active"
        else:
            game.player2 = "connected"
            game.status = "active"
        session.add(game)
        session.commit()
    
    # Generate puzzle if not exists
    if game_id not in manager.puzzles:
        with Session(engine) as session:
            words = session.exec(select(Word)).all()
            word_dicts = [{"word": w.word, "hint": w.hint} for w in words]
        difficulty = getattr(db_game, 'difficulty', 1) if hasattr(db_game, 'difficulty') else 1
        puzzle = generate_crossword(word_dicts, difficulty)
        manager.puzzles[game_id] = puzzle
        manager.user_grids[game_id] = {}
        manager.completed[game_id] = {}
    
    ws_id = str(id(websocket))
    puzzle = manager.puzzles[game_id]
    manager.user_grids[game_id][ws_id] = [[None for _ in range(puzzle["size"])] for _ in range(puzzle["size"])]
    manager.completed[game_id][ws_id] = False
    
    # Send puzzle to client
    await manager.send_personal(websocket, {
        "type": "puzzle",
        "grid": puzzle["grid"],
        "clues": puzzle["clues"],
        "size": puzzle["size"],
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "input":
                row = msg.get("row")
                col = msg.get("col")
                letter = msg.get("letter", "").upper()
                
                # Validate input
                if not (0 <= row < puzzle["size"] and 0 <= col < puzzle["size"]):
                    await manager.send_personal(websocket, {"type": "error", "message": "Invalid position"})
                    continue
                
                if not letter or len(letter) != 1 or not letter.isalpha():
                    await manager.send_personal(websocket, {"type": "error", "message": "Invalid letter"})
                    continue
                
                # Check if cell is black
                if puzzle["grid"][row][col] is None:
                    await manager.send_personal(websocket, {"type": "error", "message": "Cannot input in black cell"})
                    continue
                
                # Update user grid
                manager.user_grids[game_id][ws_id][row][col] = letter
                
                # Validate against solution
                if puzzle["grid"][row][col] == letter:
                    await manager.send_personal(websocket, {"type": "correct", "row": row, "col": col, "letter": letter})
                else:
                    await manager.send_personal(websocket, {"type": "incorrect", "row": row, "col": col})
                
                # Broadcast to opponent
                await manager.broadcast(game_id, {
                    "type": "opponent_input",
                    "row": row,
                    "col": col,
                    "letter": letter,
                }, exclude=websocket)
                
                # Check completion
                user_grid = manager.user_grids[game_id][ws_id]
                if is_puzzle_complete(puzzle["grid"], user_grid):
                    manager.completed[game_id][ws_id] = True
                    correct = sum(1 for r in range(puzzle["size"]) for c in range(puzzle["size"]) 
                                 if puzzle["grid"][r][c] is not None and user_grid[r][c] == puzzle["grid"][r][c])
                    total = sum(1 for r in range(puzzle["size"]) for c in range(puzzle["size"]) 
                               if puzzle["grid"][r][c] is not None)
                    await manager.broadcast(game_id, {
                        "type": "complete",
                        "correct": correct,
                        "total": total,
                    })
    
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)


def is_puzzle_complete(solution: list, user_grid: list) -> bool:
    for r in range(len(solution)):
        for c in range(len(solution[r])):
            if solution[r][c] is not None and user_grid[r][c] != solution[r][c]:
                return False
    return True
```

#### Step 5: Rename existing checkers handler

```python
async def handle_checkers_ws(websocket: WebSocket, game_id: str):
    # Move existing checkers logic here
    color = await manager.connect(game_id, websocket)
    # ... rest of existing code
```

### Test Plan

Create `tests/test_crossword_ws.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, init_db
from sqlmodel import SQLModel
import json

@pytest.fixture(autouse=True)
def _setup_db():
    init_db()
    yield
    with engine.connect() as conn:
        trans = conn.begin()
        for table in reversed(SQLModel.metadata.sorted_tables):
            conn.execute(table.delete())
        trans.commit()

client = TestClient(app)

def test_crossword_game_creates():
    resp = client.post("/games", json={"game_type": "crossword"})
    assert resp.status_code == 200
    game_id = resp.json()["id"]
    state = client.get(f"/games/{game_id}").json()
    assert state.get("id") == game_id

def test_crossword_ws_connect():
    resp = client.post("/games", json={"game_type": "crossword"})
    game_id = resp.json()["id"]
    with client.websocket_connect(f"/ws/{game_id}") as ws:
        msg = json.loads(ws.receive_text())
        assert msg["type"] == "puzzle"
        assert "grid" in msg
        assert "clues" in msg
        assert "size" in msg

def test_crossword_ws_input():
    resp = client.post("/games", json={"game_type": "crossword"})
    game_id = resp.json()["id"]
    with client.websocket_connect(f"/ws/{game_id}") as ws:
        puzzle_msg = json.loads(ws.receive_text())
        # Find first non-black cell
        grid = puzzle_msg["grid"]
        for r in range(len(grid)):
            for c in range(len(grid[r])):
                if grid[r][c] is not None:
                    ws.send_text(json.dumps({"type": "input", "row": r, "col": c, "letter": grid[r][c]}))
                    result = json.loads(ws.receive_text())
                    assert result["type"] == "correct"
                    return

def test_crossword_ws_incorrect_input():
    resp = client.post("/games", json={"game_type": "crossword"})
    game_id = resp.json()["id"]
    with client.websocket_connect(f"/ws/{game_id}") as ws:
        puzzle_msg = json.loads(ws.receive_text())
        grid = puzzle_msg["grid"]
        for r in range(len(grid)):
            for c in range(len(grid[r])):
                if grid[r][c] is not None:
                    wrong_letter = "Z" if grid[r][c] != "Z" else "A"
                    ws.send_text(json.dumps({"type": "input", "row": r, "col": c, "letter": wrong_letter}))
                    result = json.loads(ws.receive_text())
                    assert result["type"] == "incorrect"
                    return
```

---

## Execution Order

1. **Create `games/crossword/generator.py`** — Grid generation algorithm
2. **Add `game_type` to `app/models.py`** — Database schema update
3. **Update `app/main.py`** — Lifespan, word endpoints, game creation
4. **Update `app/websocket.py`** — Add crossword WebSocket support
5. **Create `tests/test_crossword_ws.py`** — WebSocket tests
6. **Run all tests** — Verify no regression

## Verification

1. Run existing tests: `python -m pytest tests/ games/checkers/tests/ -v`
2. Run new tests: `python -m pytest tests/test_crossword_ws.py -v`
3. Verify checkers still works
4. Verify crossword WebSocket flow works
