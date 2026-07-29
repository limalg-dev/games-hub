from __future__ import annotations
import json
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Tuple
from app.game import Board
from app.models import Game
from app.ai import choose_move
from sqlmodel import Session, select
from app.database import engine

class ConnectionManager:
    def __init__(self):
        self.boards: Dict[str, Board] = {}
        self.turn: Dict[str, str] = {}  # game_id -> "w" or "b"
        self.clients: Dict[str, Dict[int, dict]] = {}  # game_id -> {ws_id: {"ws": WebSocket, "color": str}}

    async def connect(self, game_id: str, websocket: WebSocket) -> str | None:
        await websocket.accept()
        ws_id = id(websocket)
        self.clients.setdefault(game_id, {})
        conn = self.clients[game_id]
        if game_id not in self.boards:
            self.boards[game_id] = Board()
            self.turn[game_id] = "w"
        if len(conn) == 0:
            color = "w"
        elif len(conn) == 1:
            color = "b"
        else:
            return None
        conn[ws_id] = {"ws": websocket, "color": color}
        return color

    def disconnect(self, game_id: str, websocket: WebSocket):
        ws_id = id(websocket)
        if game_id in self.clients:
            self.clients[game_id].pop(ws_id, None)
            if not self.clients[game_id]:
                del self.clients[game_id]
                del self.boards[game_id]
                del self.turn[game_id]

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
    await manager.send_personal(websocket, {"type": "color", "color": color})
    await manager.broadcast(game_id, {"type": "board", "board": manager.boards[game_id].board})
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") != "move":
                continue
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
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
