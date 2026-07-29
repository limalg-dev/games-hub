from __future__ import annotations
import json
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from app.game import Board
from app.models import Game, Move
from app.ai import choose_move
from sqlmodel import Session, select
from app.database import engine

class ConnectionManager:
    def __init__(self):
        self.games: Dict[str, list[WebSocket]] = {}
        self.boards: Dict[str, Board] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        await websocket.accept()
        self.games.setdefault(game_id, []).append(websocket)
        if game_id not in self.boards:
            self.boards[game_id] = Board()

    def disconnect(self, game_id: str, websocket: WebSocket):
        if game_id in self.games:
            self.games[game_id].remove(websocket)
            if not self.games[game_id]:
                del self.games[game_id]

    async def broadcast(self, game_id: str, message: dict):
        for ws in self.games.get(game_id, []):
            await ws.send_json(message)

    async def send_personal(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, game_id: str):
    with Session(engine) as session:
        game = session.exec(select(Game).where(Game.id == game_id)).first()
        if not game:
            await websocket.close(code=4004, reason="Game not found")
            return
    if game_id not in manager.games:
        await manager.connect(game_id, websocket)
    elif len(manager.games[game_id]) < 2:
        await manager.connect(game_id, websocket)
    else:
        await websocket.close(code=4003, reason="Game full")
        return
    await manager.broadcast(game_id, {"type": "board", "board": manager.boards[game_id].board})
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "move":
                fr = tuple(msg["from"])
                to = tuple(msg["to"])
                board = manager.boards[game_id]
                if fr not in [m[0] for m in board.legal_moves(board.board[fr[0]][fr[1]].lower())]:
                    await manager.send_personal(websocket, {"type": "error", "message": "Invalid move"})
                    continue
                board.apply_move(fr, to)
                await manager.broadcast(game_id, {"type": "board", "board": board.board})
                # check win
                if not board.legal_moves("w") or not board.legal_moves("b"):
                    await manager.broadcast(game_id, {"type": "game_over", "winner": "b" if not board.legal_moves("w") else "w"})
                    continue
                # AI opponent: if player2 is None or game AI
                with Session(engine) as session:
                    db_game = session.exec(select(Game).where(Game.id == game_id)).first()
                    if db_game and not db_game.player2:
                        al_move = choose_move(board, "b")
                        if al_move:
                            board.apply_move(*al_move)
                            await manager.broadcast(game_id, {"type": "board", "board": board.board})
                            if not board.legal_moves("w"):
                                await manager.broadcast(game_id, {"type": "game_over", "winner": "b"})
    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
