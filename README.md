# Checkers Platform

A lightweight web‑based checkers platform built with **FastAPI** and **WebSockets**. Supports both multiplayer (online via WebSocket) and single‑player against a built‑in AI opponent. No login required.

## Tech Stack

- **Python 3.11+** – language
- **FastAPI** – web framework
- **SQLModel** – ORM for SQLite persistence
- **Uvicorn** – ASGI server
- **Pytest** – testing
- **httpx** – HTTP test client
- **Minimax** – AI algorithm

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI routes & server init
│   ├── models.py       # DB models (Game, Move)
│   ├── schemas.py      # Pydantic response schemas
│   ├── database.py     # SQLAlchemy engine & init
│   ├── game.py         # Checkers board logic
│   ├── ai.py           # Minimax AI
│   └── websocket.py    # WebSocket manager & handler
├── static/
│   ├── index.html      # Client UI
│   └── app.js          # Client JS (board, WS, controls)
├── tests/
│   └── ...             # Test suites
├── pyproject.toml
└── requirements.txt
```

## Quick Start

1. **Clone or navigate** to the project root.

2. **Create a virtual environment** and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Open** [http://localhost:8000](http://localhost:8000) in your browser.

5. Click **New Game** to create a game. Share the URL to let another player join, or play locally against the AI.

## API Endpoints

| Method | Path             | Description                    |
|--------|------------------|--------------------------------|
| POST   | `/games`         | Create a new game, returns UUID |
| GET    | `/games/{id}`    | Get game status                |
| WS     | `/ws/{id}`       | WebSocket for real‑time moves  |
| GET    | `/`              | Serves the client UI           |

## WebSocket Protocol

Messages are JSON:

- **Client → Server**: `{"type": "move", "from": [r,c], "to": [r,c]}`
- **Server → Client**: `{"type": "board", "board": [8][8]}` state after every move
- **Server → Client**: `{"type": "game_over", "winner": "w"|"b"}`
- **Server → Client**: `{"type": "error", "message": "..."}`

## Architecture

The platform follows a simple hub‑and‑spoke model:

1. **FastAPI** serves HTTP endpoints and a WebSocket route.
2. **SQLite** persists game metadata (players, status).
3. **Board** state is stored in‑memory by the `ConnectionManager`.
4. **AI** runs as a synchronous minimax inside the WebSocket event loop; for multiplayer, moves are relayed between connected clients.
5. **Client** is a single‑page HTML/JS app that renders the board and handles user interactions.

## Running Tests

```bash
source .venv/bin/activate
pytest -v
```

## License

MIT
