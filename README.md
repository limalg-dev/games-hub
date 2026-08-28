# GameHub

A lightweight web game platform built with **FastAPI** and **WebSockets**. Play **6 games** online — free, no login required.

- **Damas (Checkers)** – classic 8×8 draughts. Play against a built-in minimax AI or a friend over WebSocket.
- **Caça-Palavras (Word Search)** – find hidden words across categories and difficulty levels, with a timer and local leaderboard.
- **Palavras Cruzadas (Crossword)** – crosswords generated dynamically on the server (backtracking), solved solo or collaboratively online via WebSocket.
- **Snake** – classic snake game with real-time WebSocket support.
- **Tower Defense (Ant-themed)** – defend the anthill against waves of bugs. Place and upgrade towers across 15 progressive waves.
- **Super Bomberman** – procedural map generation, power-ups, battle and arcade modes.

## Tech Stack

- **Python 3.11+** – language
- **FastAPI** – web framework (REST + WebSocket)
- **SQLModel** – ORM for SQLite persistence
- **Uvicorn** – ASGI server
- **Pytest + httpx** – testing
- **Minimax** – checkers AI algorithm
- **Docker / docker-compose** – containerized deployment

## Project Structure

```
├── app/
│   ├── main.py         # FastAPI routes, static mounts, seeding & server init
│   ├── models.py       # DB models (Game, PlayerRating)
│   ├── schemas.py      # Pydantic response schemas
│   ├── database.py     # SQLAlchemy engine & init
│   ├── elo.py          # ELO rating system for checkers AI
│   └── websocket.py    # ConnectionManager & WS handler (checkers + crossword)
├── games/
│   ├── checkers/
│   │   ├── game.py     # Checkers board logic
│   │   ├── ai.py       # Minimax AI
│   │   ├── static/     # Canvas board UI
│   │   └── tests/
│   ├── crossword/
│   │   ├── models.py   # Word model
│   │   ├── words.py    # 150-word seed dictionary (5 categories)
│   │   ├── generator.py# Backtracking crossword generator
│   │   ├── static/     # Grid + clues UI
│   │   └── tests/
│   ├── wordsearch/
│   │   └── static/     # Client-side grid game + timer
│   ├── snake/
│   │   ├── logic.py    # Snake game logic
│   │   ├── routes.py   # REST + WebSocket routes
│   │   └── static/     # Game UI
│   ├── tower_defense/
│   │   ├── logic.py    # Tower defense game engine
│   │   ├── routes.py   # REST + WebSocket routes
│   │   └── static/     # Game UI
│   └── bomberman/
│       ├── logic.py    # Map generation & high-score manager
│       ├── routes.py   # REST routes
│       ├── static/     # Game UI
│       └── tests/
├── static/             # Shared SPA shell (index.html, app.js, styles.css)
├── docs/
│   └── archify/        # Runtime architecture diagram (frontend/backend/security)
├── tests/              # API, WebSocket & integration suites
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt
```

## Quick Start

1. **Create a virtual environment** and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

   Or with Docker:
   ```bash
   docker compose up --build
   ```

3. **Open** [http://localhost:8000](http://localhost:8000) in your browser.

4. Pick a game card, choose the difficulty, and play. For online checkers/crossword, the game runs over a WebSocket.

## API Endpoints

### Platform

| Method | Path              | Description                                          |
|--------|-------------------|------------------------------------------------------|
| POST   | `/games`          | Create a game (`game_type`: `checkers`\|`crossword`, `difficulty`: `easy`\|`medium`\|`hard`, default `easy`) |
| GET    | `/games/{id}`     | Get game status                                      |
| POST   | `/api/words`      | Add a word to the dictionary (`difficulty`: int `1`–`3`) |
| GET    | `/api/words`      | List words (filters: `category`, `difficulty`: int `1`–`3`) |
| GET    | `/api/ratings/{player_id}` | Get ELO ratings for a player (query: `game_type`) |
| WS     | `/ws/{id}`        | WebSocket for real-time moves (checkers + crossword) |
| GET    | `/`               | Serves the client UI                                 |

### Snake (`/api` prefix)

| Method | Path              | Description                                          |
|--------|-------------------|------------------------------------------------------|
| GET    | `/api/snake`      | Snake game info                                      |
| POST   | `/api/snake/new`  | Create a new snake game                              |
| GET    | `/api/snake/{id}` | Get game state                                       |
| POST   | `/api/snake/{id}/direction` | Set snake direction                          |
| POST   | `/api/snake/{id}/update`   | Advance game state (move snake)             |
| POST   | `/api/snake/{id}/pause`    | Toggle pause                             |
| DELETE | `/api/snake/{id}` | Delete a game                                        |
| WS     | `/api/ws/snake/{id}` | Real-time snake game updates                    |

### Tower Defense

| Method | Path              | Description                                          |
|--------|-------------------|------------------------------------------------------|
| GET    | `/tower-defense/` | Game info and difficulty config                      |
| POST   | `/tower-defense/games/create` | Create a new game                        |
| GET    | `/tower-defense/games/{id}`  | Get game state                         |
| POST   | `/tower-defense/games/{id}/place-tower`  | Place a tower on the grid      |
| POST   | `/tower-defense/games/{id}/sell-tower`   | Sell a tower                  |
| POST   | `/tower-defense/games/{id}/upgrade-tower`| Upgrade a tower               |
| POST   | `/tower-defense/games/{id}/start-wave`   | Start an enemy wave           |
| GET    | `/tower-defense/play` | Serve the game HTML page                         |
| WS     | `/tower-defense/ws/{id}` | Real-time tower defense updates              |

### Super Bomberman

| Method | Path              | Description                                          |
|--------|-------------------|------------------------------------------------------|
| GET    | `/api/bomberman/info`      | Game metadata and modes                   |
| GET    | `/api/bomberman/stages`    | Arcade stage configurations               |
| GET    | `/api/bomberman/map`       | Generate a procedural map (query: `mode`, `difficulty`, `stage`, `seed`) |
| GET    | `/api/bomberman/highscores`| Top highscores                             |
| POST   | `/api/bomberman/highscores`| Submit a highscore entry                   |
| GET    | `/play/bomberman`          | Serve the game HTML page                   |

### Play Pages

| Path              | Game                                         |
|-------------------|----------------------------------------------|
| `/play/checkers`  | Checkers (shared SPA shell)                  |
| `/play/wordsearch`| Word Search (shared SPA shell)               |
| `/play/crossword` | Crossword (shared SPA shell)                 |
| `/play/snake`     | Snake (dedicated page)                       |
| `/play/tower_defense` | Tower Defense / Ant Defense (dedicated page) |
| `/play/bomberman` | Super Bomberman (dedicated page)             |

## WebSocket Protocol

Messages are JSON. The payload type depends on the game:

**Checkers** (`/ws/{game_id}`)
- **Client → Server**: `{"type": "move", "from": [r,c], "to": [r,c]}`
- **Server → Client**: `{"type": "board", "board": [8][8]}` after every move
- **Server → Client**: `{"type": "game_over", "winner": "w"|"b"}`

**Crossword** (`/ws/{game_id}`)
- **Server → Client** (on connect): `{"type": "crossword_init", "size", "num_grid", "across_clues", "down_clues", "filled"}`
- **Client → Server**: `{"type": "input", "row", "col", "letter"}` (validated server-side against the solution)
- **Server → Client**: `{"type": "opponent_input", "row", "col", "letter", "sender_color"}` broadcast to other players
- **Server → Client**: `{"type": "complete"}` when all cells are filled

**Snake** (`/api/ws/snake/{game_id}`)
- **Client → Server**: `{"action": "direction", "direction": "UP"|"DOWN"|"LEFT"|"RIGHT"}`
- **Client → Server**: `{"action": "pause"}` / `{"action": "reset"}`
- **Server → Client**: `{"type": "init", "state": {...}}` / `{"type": "direction_changed", ...}` / `{"type": "pause_toggled", ...}`

**Tower Defense** (`/tower-defense/ws/{game_id}`)
- **Client → Server**: `{"command": "place_tower", "x": int, "y": int, "tower_type": "archer"|"bomb"|"ice"}`
- **Client → Server**: `{"command": "start_wave"}` / `{"command": "sell_tower", "tower_id": str}` / `{"command": "upgrade_tower", "tower_id": str}`
- **Client → Server**: `{"command": "set_speed", "scale": 1|2|4}` / `{"command": "toggle_auto_wave"}`
- **Server → Client**: `{"type": "state_update", "state": {...}}` / `{"type": "command_result", ...}`

**Common**
- **Server → Client**: `{"type": "error", "message": "..."}`
- **Server → Client** (checkers/crossword): `{"type": "color", "color": "w"|"b"}` player assignment (max 2 per game)

## Architecture

The platform follows a hub-and-spoke model:

1. **FastAPI** serves static assets, REST endpoints, and a WebSocket route.
2. **SQLite** persists games, moves, and the word dictionary via SQLModel (150 words seeded on startup).
3. **Board / puzzle state** is held in-memory by the `ConnectionManager`; crossword puzzles are generated by `games/crossword/generator.py` and validated letter-by-letter on the server.
4. **Checkers AI** runs as synchronous minimax inside the WebSocket event loop.
5. **Client** is a single-page app (per-game modules under `games/*/static/`) that renders the board/grid and handles interactions.

An interactive runtime diagram (frontend, backend, and security/trust boundaries) is available at
[`docs/archify/gamehub-runtime.architecture.html`](docs/archify/gamehub-runtime.architecture.html)
(source: [`gamehub-runtime.architecture.json`](docs/archify/gamehub-runtime.architecture.json)).

![GameHub Runtime Architecture](docs/archify/gamehub-runtime-sharecard.png)

## Running Tests

```bash
source .venv/bin/activate
pytest -v
```

Covers the API, WebSocket flow (checkers + crossword), crossword generator/word logic, and overall project structure.

## Deployment

Game/session state is held **entirely in memory** — the `ConnectionManager` (boards, turns, crossword state), per-game `active_games` dicts (snake, tower defense), and the bomberman high-score table are not persisted to disk or a shared store. This is an intentional design choice for a zero-config casual platform.

**The server MUST run as a single worker.** Do not use `uvicorn --workers N` or multiple replicas. Multiple workers fragment state: a game created in one worker is invisible to others, and WebSocket sessions are lost across workers.

```bash
# ✅ Correct — single worker
uvicorn app.main:app --host 0.0.0.0 --port 8000

# ❌ Wrong — fragments in-memory state
uvicorn app.main:app --workers 4
```

## License

MIT

---
_Repo: limalg-dev/games-hub_