# Checkers Platform Design (FastAPI + WebSockets)

## Overview
A lightweight web platform hosting multiple board games (starting with Checkers). No user authentication; anyone can start a game or join via a short URL. The server is built with **FastAPI**, uses **WebSockets** for real‑time move exchange, and persists game state in a **SQLite** database. An AI opponent runs a simple minimax algorithm.

## Architecture
```
Client (HTML/JS) <--WebSocket--> FastAPI Server
                                   |
                                   |-- SQLite DB (games, moves)
                                   |
                                   `-- AI module (minimax)
```
- **FastAPI** provides HTTP routes for game creation, joining, and static assets, and a WebSocket endpoint for move broadcasting.
- **SQLite** stores `games` (id, player1, player2, status) and `moves` (game_id, move_number, from, to, timestamp).
- **AI** runs in a separate coroutine when a player selects "play vs computer"; it reads the current board from DB, computes the best move, and pushes it via the same WebSocket.
- **No login**: game IDs are UUIDs; the URL `/game/{uuid}` is enough to identify the session.

## Data Model
```sql
CREATE TABLE games (
    id TEXT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    player1 TEXT,
    player2 TEXT,
    status TEXT CHECK(status IN ('waiting','active','finished'))
);

CREATE TABLE moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT REFERENCES games(id),
    move_number INTEGER,
    from_square TEXT,
    to_square TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints
- `POST /games` – create a new game, returns UUID.
- `GET /games/{id}` – retrieve game metadata.
- `GET /static/{file}` – serve HTML/JS client.
- `WebSocket /ws/{game_id}` – bi‑directional stream of JSON messages `{type: "move", from:..., to:...}`.

## Client Flow
1. Load `index.html` → fetch game list or create new.
2. Connect to WebSocket at `/ws/{game_id}`.
3. Send/receive move messages; UI updates board.
4. If playing vs AI, after opponent move the server triggers AI and pushes its move.

## Scaling Considerations
- For a single‑node deployment, SQLite suffices.
- To scale horizontally, replace SQLite with a shared DB (PostgreSQL) and use Redis Pub/Sub for WebSocket broadcast across instances.

## Extensibility
- New games can be added by implementing a game‑logic module exposing `initial_state`, `legal_moves`, `apply_move`, and `evaluate` for AI.
- Client can load game‑specific JS modules dynamically.

## Testing
- Unit tests for game logic (move validation, win detection).
- Integration tests using `httpx` and `websockets` to simulate two players.

## Security & Performance
- No authentication, so limit game creation rate via simple IP‑based throttling.
- Keep WebSocket messages lightweight JSON.
- Run FastAPI with `uvicorn --workers 4` for concurrency.

---
*Design approved by user on 2024‑07‑29.*
