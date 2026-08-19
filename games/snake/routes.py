"""
Snake Game API Routes
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import Dict, Optional
import asyncio
import json
import time

from .logic import SnakeGame, Direction

router = APIRouter()

# Store active games with timestamps for TTL expiry
active_games: Dict[str, SnakeGame] = {}
_game_created: Dict[str, float] = {}
_GAME_TTL = 3600  # 1 hour


def _cleanup_expired():
    """Remove games older than _GAME_TTL seconds."""
    now = time.time()
    expired = [gid for gid, ts in _game_created.items() if now - ts > _GAME_TTL]
    for gid in expired:
        active_games.pop(gid, None)
        _game_created.pop(gid, None)


@router.get("/snake")
async def get_snake_info():
    """Get snake game information"""
    return {
        "name": "Snake",
        "description": "Classic snake game with modern features",
        "grid_size": "20x20",
        "controls": "Arrow keys or WASD"
    }


@router.post("/snake/new")
async def create_snake_game():
    """Create a new snake game"""
    import uuid
    _cleanup_expired()
    game_id = str(uuid.uuid4())
    game = SnakeGame()
    active_games[game_id] = game
    _game_created[game_id] = time.time()
    return {"game_id": game_id, "state": game.get_state()}


@router.get("/snake/{game_id}")
async def get_snake_game(game_id: str):
    """Get current state of a snake game"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = active_games[game_id]
    return {"game_id": game_id, "state": game.get_state()}


@router.post("/snake/{game_id}/direction")
async def set_snake_direction(game_id: str, direction: str):
    """Set snake direction"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        dir_enum = Direction[direction.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid direction: {direction}")
    
    game = active_games[game_id]
    game.set_direction(dir_enum)
    return {"success": True, "direction": direction}


@router.post("/snake/{game_id}/update")
async def update_snake_game(game_id: str):
    """Update snake game state (move snake)"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = active_games[game_id]
    continues = game.update()
    
    return {
        "success": True,
        "state": game.get_state(),
        "game_over": not continues
    }


@router.post("/snake/{game_id}/pause")
async def toggle_snake_pause(game_id: str):
    """Toggle pause state"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = active_games[game_id]
    game.toggle_pause()
    return {"success": True, "paused": game.paused}


@router.delete("/snake/{game_id}")
async def delete_snake_game(game_id: str):
    """Delete a snake game"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    del active_games[game_id]
    return {"success": True}


@router.websocket("/ws/snake/{game_id}")
async def snake_websocket(websocket: WebSocket, game_id: str):
    """WebSocket for real-time snake game updates"""
    await websocket.accept()
    
    if game_id not in active_games:
        await websocket.close(code=4004, reason="Game not found")
        return
    
    game = active_games[game_id]
    
    try:
        # Send initial state
        await websocket.send_json({"type": "init", "state": game.get_state()})
        
        while True:
            # Receive commands from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            
            if action == "direction":
                direction = message.get("direction")
                try:
                    dir_enum = Direction[direction.upper()]
                    game.set_direction(dir_enum)
                    await websocket.send_json({
                        "type": "direction_changed",
                        "direction": direction
                    })
                except KeyError:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Invalid direction: {direction}"
                    })
            
            elif action == "pause":
                game.toggle_pause()
                await websocket.send_json({
                    "type": "pause_toggled",
                    "paused": game.paused
                })
            
            elif action == "reset":
                game.reset()
                await websocket.send_json({
                    "type": "reset",
                    "state": game.get_state()
                })
            
            # Auto-send game state updates in a separate task
            # This would be better handled with a game loop
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
