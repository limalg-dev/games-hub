# Crossword WebSocket Support — Focused Plan

## Current State Summary

**Already Implemented:**
- ✅ `games/crossword/generator.py` — Grid generation algorithm
- ✅ `games/crossword/models.py` — Word model
- ✅ `games/crossword/words.py` — Seed data (150 words)
- ✅ `app/models.py` — `game_type` field added to Game
- ✅ `app/schemas.py` — `GameCreate`, `WordCreate`, `WordRead` schemas
- ✅ `app/main.py` — Lifespan, word endpoints, game creation with puzzle
- ✅ `tests/test_crossword_api.py` — API tests

**Not Yet Implemented:**
- ❌ `app/websocket.py` — Still only handles checkers
- ❌ `tests/test_crossword_ws.py` — WebSocket tests

## Task: Update `app/websocket.py`

### Changes Required

1. **Add crossword state to ConnectionManager**
2. **Detect game type in websocket_endpoint**
3. **Implement handle_crossword_ws function**
4. **Rename existing checkers logic to handle_checkers_ws**
5. **Clean up crossword state on disconnect**

### Implementation Details

#### 1. Update ConnectionManager.__init__

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

#### 2. Update disconnect method

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

#### 3. Update websocket_endpoint to branch by game_type

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

#### 4. Implement handle_crossword_ws

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
        difficulty = 1
        if hasattr(db_game, 'difficulty') and db_game.difficulty:
            DIFFICULTY_MAP = {"easy": 1, "medium": 2, "hard": 3}
            difficulty = DIFFICULTY_MAP.get(db_game.difficulty, 1)
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

#### 5. Rename existing checkers logic

```python
async def handle_checkers_ws(websocket: WebSocket, game_id: str):
    # Move ALL existing checkers logic here (lines 60-126)
    color = await manager.connect(game_id, websocket)
    # ... rest of existing code
```

## Task: Create `tests/test_crossword_ws.py`

### Test Cases

1. **test_crossword_game_creates** — Verify crossword game creation via API
2. **test_crossword_ws_connect** — Verify WebSocket connection and puzzle receipt
3. **test_crossword_ws_input** — Verify input validation and correct/incorrect responses
4. **test_crossword_ws_opponent_input** — Verify opponent input broadcast
5. **test_crossword_ws_completion** — Verify puzzle completion detection

### Test Code

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

def test_crossword_ws_opponent_input():
    resp = client.post("/games", json={"game_type": "crossword"})
    game_id = resp.json()["id"]
    with client.websocket_connect(f"/ws/{game_id}") as ws1:
        puzzle1 = json.loads(ws1.receive_text())
        with client.websocket_connect(f"/ws/{game_id}") as ws2:
            puzzle2 = json.loads(ws2.receive_text())
            grid = puzzle1["grid"]
            for r in range(len(grid)):
                for c in range(len(grid[r])):
                    if grid[r][c] is not None:
                        ws1.send_text(json.dumps({"type": "input", "row": r, "col": c, "letter": grid[r][c]}))
                        # ws1 gets correct response
                        result1 = json.loads(ws1.receive_text())
                        assert result1["type"] == "correct"
                        # ws2 gets opponent_input
                        result2 = json.loads(ws2.receive_text())
                        assert result2["type"] == "opponent_input"
                        return
```

## Execution Order

1. **Update `app/websocket.py`** with crossword support
2. **Create `tests/test_crossword_ws.py`** with test cases
3. **Run existing tests** to verify no regression
4. **Run new tests** to verify crossword works

## Verification

```bash
# Run all existing tests
python -m pytest tests/ games/checkers/tests/ -v

# Run new crossword WebSocket tests
python -m pytest tests/test_crossword_ws.py -v
```
