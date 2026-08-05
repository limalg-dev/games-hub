from __future__ import annotations
import json
from typing import Dict, List, Optional, Tuple
from fastapi import WebSocket, WebSocketDisconnect
from games.checkers.game import Board
from games.checkers.ai import choose_move
from app.models import Game
from sqlmodel import Session, select
from app.database import engine

class ConnectionManager:
    def __init__(self):
        self.boards: Dict[str, Board] = {}  # for checkers
        self.turn: Dict[str, str] = {}  # game_id -> "w" or "b"
        self.crossword_state: Dict[str, dict] = {}  # game_id -> state dict
        self.clients: Dict[str, Dict[int, dict]] = {}  # game_id -> {ws_id: {"ws": WebSocket, "color": str}}

    async def connect(self, game_id: str, websocket: WebSocket) -> str | None:
        await websocket.accept()
        ws_id = id(websocket)
        self.clients.setdefault(game_id, {})
        conn = self.clients[game_id]
        if game_id not in self.boards and game_id not in self.crossword_state:
            # First connection for this game: initialize state based on game type
            with Session(engine) as session:
                game = session.exec(select(Game).where(Game.id == game_id)).first()
                if not game:
                    await websocket.close(code=4004, reason="Game not found")
                    return None
                if game.game_type == "checkers":
                    self.boards[game_id] = Board()
                    self.turn[game_id] = "w"
                elif game.game_type == "crossword":
                    # Initialize crossword state from puzzle_data
                    if game.puzzle_data:
                        data = json.loads(game.puzzle_data)
                        self.crossword_state[game_id] = self._init_crossword_state(data)
                    else:
                        # Should not happen if game was created with puzzle data
                        await websocket.close(code=4000, reason="Puzzle data missing")
                        return None
                else:
                    # Unknown game type
                    await websocket.close(code=4000, reason="Unsupported game type")
                    return None
        if len(conn) == 0:
            color = "w"
        elif len(conn) == 1:
            color = "b"
        else:
            return None
        conn[ws_id] = {"ws": websocket, "color": color}
        return color

    def _init_crossword_state(self, data: dict) -> dict:
        size = data["size"]
        solution = data["grid"]  # list of list of str or None
        across_clues = data["clues"]["across"]
        down_clues = data["clues"]["down"]
        # Compute clue numbers grid
        num_grid = [[None for _ in range(size)] for __ in range(size)]
        for clue in across_clues + down_clues:
            r, c, n = clue["row"], clue["col"], clue["number"]
            if num_grid[r][c] is None or n < num_grid[r][c]:
                num_grid[r][c] = n
        # Initialize filled grid: False for all cells
        filled = [[False for _ in range(size)] for __ in range(size)]
        # Black cells (where solution is None) are considered already filled? Actually, they are not playable.
        # We'll mark them as True in filled so that we don't allow moves there, but we might want to distinguish.
        # Instead, we'll check during move validation: if solution cell is None, reject.
        # For simplicity, we can set filled to True for black cells to skip them in completion check.
        for r in range(size):
            for c in range(size):
                if solution[r][c] is None:
                    filled[r][c] = True
        return {
            "solution": solution,
            "filled": filled,
            "across_clues": across_clues,
            "down_clues": down_clues,
            "num_grid": num_grid,
            "size": size,
        }

    def disconnect(self, game_id: str, websocket: WebSocket):
        ws_id = id(websocket)
        if game_id in self.clients:
            self.clients[game_id].pop(ws_id, None)
            if not self.clients[game_id]:
                del self.clients[game_id]
                if game_id in self.boards:
                    del self.boards[game_id]
                    del self.turn[game_id]
                if game_id in self.crossword_state:
                    del self.crossword_state[game_id]

    async def broadcast(self, game_id: str, message: dict, exclude: WebSocket | None = None):
        for data in self.clients.get(game_id, {}).values():
            if exclude and data["ws"] is exclude:
                continue
            await data["ws"].send_json(message)

    async def send_personal(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, game_id: str):
    with Session(engine) as session:
        db_game = session.exec(select(Game).where(Game.id == game_id)).first()
        if not db_game:
            await websocket.close(code=4004, reason="Game not found")
            return
    color = await manager.connect(game_id, websocket)
    if color is None:
        await websocket.close(code=4003, reason="Game full")
        return
    # update player fields in DB
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
    # Send initial state based on game type
    with Session(engine) as session:
        game = session.exec(select(Game).where(Game.id == game_id)).first()
        if game.game_type == "checkers":
            await manager.send_personal(websocket, {"type": "color", "color": color})
            await manager.broadcast(game_id, {"type": "board", "board": manager.boards[game_id].board})
        elif game.game_type == "crossword":
            state = manager.crossword_state[game_id]
            await manager.send_personal(websocket, {"type": "color", "color": color})
            # Send initial crossword state: clues and empty filled grid
            await manager.send_personal(websocket, {
                "type": "crossword_init",
                "size": state["size"],
                "num_grid": state["num_grid"],
                "across_clues": state["across_clues"],
                "down_clues": state["down_clues"],
                "filled": state["filled"]
            })
            # Also broadcast to others? Actually, we want each player to get the same init.
            # But we already sent to the connecting player. We'll broadcast to others in the loop? 
            # For simplicity, we'll broadcast the init to everyone when a new player connects? 
            # However, the init is the same for all. We'll send to the new player only; 
            # the other players already got their init when they connected.
            # Alternatively, we can broadcast the init to all when the game starts.
            # We'll do that when the second player connects? Actually, we can broadcast the init 
            # to all connected clients when we initialize the state (when first player connects).
            # But we don't have the websockets of other players at that moment? 
            # We'll handle by sending the init to each player as they connect.
            # For now, we'll just send to the connecting player.
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") not in ("move", "input"):
                continue
            if game.game_type == "checkers":
                # Existing checkers move handling
                if manager.turn.get(game_id) != color:
                    await manager.send_personal(websocket, {"type": "error", "message": "Not your turn"})
                    continue
                fr = tuple(msg["from"])
                to = tuple(msg["to"])
                board = manager.boards[game_id]
                piece = board.board[fr[0]][fr[1]]
                if not piece or piece.lower() != color:
                    await manager.send_personal(websocket, {"type": "error", "message": "Invalid piece"})
                    continue
                legal_moves = board.legal_moves(color)
                if fr not in [m[0] for m in legal_moves] or to not in [m[1] for m in legal_moves if m[0] == fr]:
                    await manager.send_personal(websocket, {"type": "error", "message": "Illegal move"})
                    continue
                board.apply_move(fr, to)
                manager.turn[game_id] = "b" if color == "w" else "w"
                await manager.broadcast(game_id, {"type": "board", "board": board.board})
                # check win
                for c in ("w", "b"):
                    if not board.legal_moves(c):
                        winner = "b" if c == "w" else "w"
                        await manager.broadcast(game_id, {"type": "game_over", "winner": winner})
                        break
                else:
                    # AI opponent
                    with Session(engine) as session:
                        g = session.exec(select(Game).where(Game.id == game_id)).first()
                        if g and not g.player2:
                            ai_color = "b" if color == "w" else "w"
                            ban = manager.boards.get(game_id)
                            if ban:
                                ai_move = choose_move(ban, ai_color)
                                if ai_move:
                                    ban.apply_move(*ai_move)
                                    manager.turn[game_id] = color
                                    await manager.broadcast(game_id, {"type": "board", "board": ban.board})
                                    for c in ("w", "b"):
                                        if not ban.legal_moves(c):
                                            winner = "b" if c == "w" else "w"
                                            await manager.broadcast(game_id, {"type": "game_over", "winner": winner})
                                            break
            elif game.game_type == "crossword":
                if msg.get("type") == "input":
                    row = msg.get("row")
                    col = msg.get("col")
                    letter = msg.get("letter")
                    if row is None or col is None or letter is None:
                        await manager.send_personal(websocket, {"type": "error", "message": "Invalid input format"})
                        continue
                    if not (0 <= row < manager.crossword_state[game_id]["size"] and 0 <= col < manager.crossword_state[game_id]["size"]):
                        await manager.send_personal(websocket, {"type": "error", "message": "Cell out of bounds"})
                        continue
                    state = manager.crossword_state[game_id]
                    solution_letter = state["solution"][row][col]
                    if solution_letter is None:
                        await manager.send_personal(websocket, {"type": "error", "message": "Cannot fill this cell"})
                        continue
                    if state["filled"][row][col]:
                        await manager.send_personal(websocket, {"type": "error", "message": "Cell already filled"})
                        continue
                    if letter.upper() != solution_letter:
                        await manager.send_personal(websocket, {"type": "incorrect", "row": row, "col": col})
                        continue
                    state["filled"][row][col] = True
                    await manager.send_personal(websocket, {"type": "correct", "row": row, "col": col})
                    await manager.broadcast(game_id, {
                        "type": "opponent_input",
                        "row": row,
                        "col": col,
                        "letter": letter.upper(),
                        "sender_color": color
                    }, exclude=websocket)
                    all_filled = True
                    for r in range(state["size"]):
                        for c in range(state["size"]):
                            if state["solution"][r][c] is not None and not state["filled"][r][c]:
                                all_filled = False
                                break
                        if not all_filled:
                            break
                    if all_filled:
                        await manager.broadcast(game_id, {"type": "complete"})
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
