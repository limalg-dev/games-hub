# Crossword Game — Design Spec

## Overview

Add a crossword puzzle game (palavras cruzadas) to GameHub. Backend generates the grid dynamically via backtracking algorithm, client renders it as DOM. Supports single-player and multiplayer modes.

## Architecture

```
┌─────────────────────────────────────────────┐
│                 Backend (FastAPI)            │
│  POST /api/words     → CRUD de palavras     │
│  POST /games         → Criar jogo crossword  │
│  GET  /games/{id}    → Estado do jogo        │
│  WS   /ws/{game_id}  → Multiplayer tempo     │
│                                              │
│  crossword/generator.py → Algoritmo grid     │
│  crossword/words.py     → Seed do banco      │
│  crossword/models.py    → Modelo Word        │
└──────────────┬──────────────────────────────┘
               │ JSON / WebSocket
┌──────────────▼──────────────────────────────┐
│              Frontend (JS/HTML/CSS)          │
│  crossword/board.js    → Renderiza grid DOM  │
│  crossword/logic.js    → Valida input, timer │
│  crossword/preview.js  → Preview no modal    │
│  crossword/timer.js    → Timer + leaderboard │
└─────────────────────────────────────────────┘
```

## Backend

### Models (SQLModel)

```python
# games/crossword/models.py
class Word(SQLModel, table=True):
    id: Optional[int] = pk()
    word: str           # "PYTHON"
    hint: str           # "Linguagem de programação"
    category: str       # "tech"
    difficulty: int     # 1=easy, 2=medium, 3=hard
```

Existing `Game` model gains `game_type: str = "checkers"` field (default for backward compatibility).

### Word Seed

- ~150 hardcoded words across 5 categories: animals, countries, tech, food, sports
- 3 difficulty levels per category
- Seeded via FastAPI `lifespan` on first startup (insert if table empty)
- API endpoint `POST /api/words` allows adding more words

### Grid Generator (`games/crossword/generator.py`)

- Backtracking algorithm that places words on an N×N grid
- First word placed at center, subsequent words try to cross existing words at common letters
- Returns JSON: `grid[][]` (letters or null for black cells), `clues` (across/down with position, number, hint), `size`
- Difficulty levels:
  - Easy: 8×8 grid, 8-10 words
  - Medium: 12×12 grid, 12-15 words
  - Hard: 15×15 grid, 18-22 words

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/words` | Add a word |
| GET | `/api/words` | List words (filter by category/difficulty) |
| POST | `/games` | Create crossword game (body: `{game_type: "crossword", difficulty: "easy"}`) |
| GET | `/games/{id}` | Get game state |

### WebSocket Protocol

- `connect` → server sends full puzzle (grid, clues, size)
- `input` → client sends `{row, col, letter}`, server validates against grid
- `correct` / `incorrect` → server responds with validation
- `complete` → server checks if puzzle is finished, computes score

## Frontend

### Grid Rendering (DOM-based)

- Grid rendered as `<div>` CSS grid — each cell is an `<input maxlength="1">`
- Black cells rendered as solid `<div>` blocks
- Sidebar with clue lists (Across / Down) — clicking a clue focuses the corresponding cell
- Color scheme: black = block, white = editable, green = correct, red = incorrect

### Game Modes

- **Solo**: Timer runs, leaderboard stored in localStorage
- **Multiplayer**: WebSocket sync, same puzzle, first to complete wins

### Modules

| File | Purpose |
|------|---------|
| `crossword/board.js` | `CrosswordGame` class — render, input handling, WebSocket |
| `crossword/logic.js` | Pure functions — validate input, check completion |
| `crossword/preview.js` | `renderPreview(canvasId)` — small preview for modal |
| `crossword/timer.js` | Timer + localStorage leaderboard |

## Tests

### Unit Tests — `games/crossword/tests/`

| File | Tests |
|------|-------|
| `test_generator.py` | Grid generation, valid intersections, difficulty sizes, no duplicates |
| `test_words.py` | Seed logic, word CRUD, category/difficulty filtering |

### Unit Tests — Existing (update)

| File | Tests |
|------|-------|
| `games/checkers/tests/*.py` | All existing tests must still pass |

### API Tests — `tests/test_api.py` (extend)

- POST `/api/words` — create word
- GET `/api/words` — list/filter
- POST `/games` — create crossword game
- GET `/games/{id}` — get crossword state

### WebSocket Tests — `tests/test_websocket.py` (extend)

- Connect to crossword game
- Receive puzzle data
- Send input, receive validation
- Complete puzzle

### Integration Tests — `tests/test_integration.py` (new)

- Full flow: seed words → create game → play → complete
- Multiplayer flow: two connections → both receive puzzle → one completes

## Files to Create

```
games/crossword/
├── __init__.py
├── models.py          # Word SQLModel
├── generator.py       # Grid generation algorithm
├── words.py           # Seed data
├── static/
│   ├── board.js       # CrosswordGame class
│   ├── logic.js       # Validation functions
│   ├── preview.js     # Modal preview
│   └── timer.js       # Timer + leaderboard
└── tests/
    ├── __init__.py
    ├── test_generator.py
    └── test_words.py
```

## Files to Modify

- `app/main.py` — add lifespan word seed, add `/api/words` endpoints, update `POST /games`
- `app/models.py` — add `game_type` field to `Game`
- `app/websocket.py` — add crossword game support alongside checkers
- `static/app.js` — register crossword in `GAMES`, add modal/start/cleanup handlers
- `static/styles.css` — crossword-specific styles
- `tests/test_api.py` — extend with crossword tests
- `tests/test_websocket.py` — extend with crossword tests
