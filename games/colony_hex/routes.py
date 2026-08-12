import json
from uuid import uuid4
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict
from games.colony_hex.logic import GameState

router = APIRouter(prefix="/games/colony_hex")

active_games: Dict[str, GameState] = {}
connections: Dict[str, Dict[WebSocket, str]] = {}  # game_id -> {ws: color}

SEATS = ["red", "blue", "green", "yellow"]

@router.post("")
async def create_game(body: dict = None):
    body = body or {}
    max_players = body.get("max_players", 2)
    fill_ai = body.get("fill_ai", True)
    
    game_id = str(uuid4())
    players_setup = []
    # Host is red
    players_setup.append({"color": "red", "is_ai": False})
    
    # Fill remaining seats
    for i in range(1, max_players):
        players_setup.append({"color": SEATS[i], "is_ai": fill_ai})
        
    game_state = GameState(game_id, players_setup)
    active_games[game_id] = game_state
    connections[game_id] = {}
    
    return {"game_id": game_id, "state": game_state.to_dict()}

@router.get("")
async def list_games():
    return [
        {
            "game_id": gid,
            "status": g.status,
            "players": [p["color"] for p in g.players if not p["is_ai"]]
        }
        for gid, g in active_games.items()
    ]

@router.get("/{game_id}")
async def get_game(game_id: str):
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return active_games[game_id].to_dict()

@router.websocket("/ws/{game_id}")
async def ws_endpoint(websocket: WebSocket, game_id: str):
    if game_id not in active_games:
        await websocket.close(code=4004, reason="Jogo não encontrado")
        return
    await websocket.accept()
    game = active_games[game_id]
    
    # Assign color
    conn = connections[game_id]
    assigned_color = None
    for p in game.players:
        if not p["is_ai"] and p["color"] not in conn.values():
            assigned_color = p["color"]
            break
            
    if not assigned_color:
        await websocket.close(code=4003, reason="Jogo cheio")
        return
        
    conn[websocket] = assigned_color
    await websocket.send_json({"type": "welcome", "seat": assigned_color, "state": game.to_dict()})
    
    # Broadcast current connections state
    await broadcast_state(game_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            m_type = msg.get("type")
            
            if m_type == "start":
                if assigned_color == "red" and game.status == "lobby":
                    game.start_game()
                    await broadcast_state(game_id)
            elif m_type == "action":
                if game.status != "active":
                    await websocket.send_json({"type": "error", "message": "Jogo não está ativo"})
                    continue
                action_data = msg.get("action", {})
                success, err = game.execute_action(assigned_color, action_data)
                if not success:
                    await websocket.send_json({"type": "error", "message": err})
                else:
                    await broadcast_state(game_id)
                    # Trigger AI chain
                    while game.status == "active" and game.players[game.turn_index]["is_ai"]:
                        game.run_ai_turn()
                        await broadcast_state(game_id)
            elif m_type == "forfeit":
                game.status = "finished"
                # Winner is anyone else alive
                alive = [p["color"] for p in game.players if p["alive"] and p["color"] != assigned_color]
                game.winner = alive[0] if alive else None
                game._calculate_ranking()
                await broadcast_state(game_id)
    except WebSocketDisconnect:
        conn.pop(websocket, None)
        await broadcast_state(game_id)

async def broadcast_state(game_id: str):
    if game_id not in active_games:
        return
    game = active_games[game_id]
    conn = connections[game_id]
    msg = {"type": "state", "state": game.to_dict()}
    for ws in conn:
        try:
            await ws.send_json(msg)
        except Exception:
            pass
