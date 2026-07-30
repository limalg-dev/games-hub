# Project Restructure Design Spec

## Overview
Reorganize monolithic project into clean folder hierarchy: `static/` for platform shell, `games/checkers/` and `games/wordsearch/` as self-contained game modules. Each game folder contains its own logic, rendering, and tests.

## Architecture

```
/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── app/                      ← Platform backend (FastAPI)
│   ├── main.py               ← Routes: /, /games, /ws (mounts game routers)
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── __init__.py
├── static/                   ← Platform frontend
│   ├── index.html            ← Landing page
│   ├── app.js                ← SPA router (loads game modules)
│   └── styles.css            ← Shared CSS (variables, layout)
├── games/                    ← Game modules
│   ├── checkers/
│   │   ├── __init__.py
│   │   ├── logic.py          ← Board logic (move validation)
│   │   ├── ai.py             ← AI opponent
│   │   ├── game.py           ← Game model
│   │   ├── router.py         ← /games/checkers/ API endpoints
│   │   ├── websocket.py      ← WebSocket handler
│   │   └── static/
│   │       ├── board.js      ← Canvas rendering
│   │       ├── logic.js      ← Client-side logic
│   │       └── preview.js    ← Modal preview
│   └── wordsearch/
│       ├── __init__.py
│       ├── logic.py          ← Grid generation
│       ├── static/
│       │   ├── board.js      ← Table/Canvas rendering
│       │   ├── logic.js      ← Grid gen (client)
│       │   ├── preview.js    ← Modal preview
│       │   ├── timer.js      ← Timer + leaderboard
│       │   └── words.js      ← Word lists
│       └── tests/
│           └── test_logic.py
├── tests/                    ← Integration tests
│   ├── test_api.py
│   └── test_project_structure.py
└── docs/superpowers/
    ├── plans/
    └── specs/
```

## Changes

### 1. Move Checkers backend files
- `app/ai.py` → `games/checkers/ai.py`
- `app/game.py` → `games/checkers/game.py`
- Not moving: `app/websocket.py`, `app/main.py` (platform stays shared)

### 2. Update imports
- `app/main.py` → imports from `games.checkers`
- `app/websocket.py` → imports from `games.checkers`
- `static/app.js` → all game imports updated to `../games/checkers/...`
- `static/index.html` → link paths unchanged (still /static/)

### 3. Test paths
- `tests/test_ai.py` → `games/checkers/tests/test_ai.py`
- `tests/test_checkers.py` → `games/checkers/tests/test_checkers.py`
- `tests/test_game_logic.py` → `games/checkers/tests/test_game_logic.py`
- Remaining tests stay in `tests/`

### 4. Fix known bugs
- Word search board.js: uses `container` instead of canvas, fix to render in board-wrapper
- app.js: wordsearch imports need explicit paths
- timer.js: localStorage key consistency

## Acceptance Criteria
- [ ] Project starts without import errors
- [ ] Checkers game works (create game, WebSocket, play)
- [ ] Word search works (generate grid, select words, timer)
- [ ] Landing page shows both games
- [ ] All tests pass
- [ ] Docker build succeeds