"""
Ant Defense - Tower Defense Game
Rotas API e WebSocket para o jogo Ant Defense
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from typing import Dict, List, Optional
import asyncio
import time
import json

from .logic import GameState, TowerType, EnemyType, create_game

router = APIRouter()

# Armazena estados de jogos ativos: game_id -> GameState
active_games: Dict[str, GameState] = {}
# Conexões WebSocket ativas: game_id -> list of websockets
game_connections: Dict[str, List[WebSocket]] = {}


@router.post("/games/ant_defense")
async def create_ant_defense_game() -> Dict:
    """Cria um novo jogo Ant Defense"""
    game_id = f"ant_defense_{int(time.time() * 1000)}"
    game_state = create_game()
    active_games[game_id] = game_state
    game_connections[game_id] = []
    
    return {
        "game_id": game_id,
        "game_type": "ant_defense",
        "status": "created",
        "initial_state": game_state.to_dict()
    }


@router.get("/games/ant_defense")
async def list_ant_defense_games() -> Dict:
    """Lista todos os jogos Ant Defense ativos"""
    games = []
    for game_id, game_state in active_games.items():
        games.append({
            "game_id": game_id,
            "wave_number": game_state.wave_number,
            "score": game_state.score,
            "lives": game_state.lives,
            "gold": game_state.gold,
            "game_over": game_state.game_over
        })
    
    return {"games": games, "count": len(games)}


@router.get("/games/ant_defense/{game_id}")
async def get_ant_defense_game(game_id: str) -> Dict:
    """Obtém estado atual de um jogo Ant Defense"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    game_state = active_games[game_id]
    return {
        "game_id": game_id,
        "state": game_state.to_dict()
    }


@router.post("/games/ant_defense/{game_id}/tower")
async def place_tower(
    game_id: str,
    grid_x: int = Query(...),
    grid_y: int = Query(...),
    tower_type: str = Query(...)
) -> Dict:
    """Coloca uma torre no grid"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    # Valida tipo de torre
    try:
        tower_type_enum = TowerType(tower_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de torre inválido. Opções: {[t.value for t in TowerType]}"
        )
    
    game_state = active_games[game_id]
    success, message = game_state.place_tower(grid_x, grid_y, tower_type_enum)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Notifica conexões WebSocket
    await broadcast_game_state(game_id, game_state)
    
    return {
        "success": True,
        "message": message,
        "remaining_gold": game_state.gold,
        "state": game_state.to_dict()
    }


@router.post("/games/ant_defense/{game_id}/wave")
async def start_wave(game_id: str, wave_number: int = Query(...)) -> Dict:
    """Inicia uma nova onda de inimigos"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    game_state = active_games[game_id]
    
    if game_state.wave_active:
        raise HTTPException(status_code=400, detail="Onda já em andamento")
    
    game_state.start_wave(wave_number)
    
    # Notifica conexões WebSocket
    await broadcast_game_state(game_id, game_state)
    
    return {
        "success": True,
        "wave_number": wave_number,
        "state": game_state.to_dict()
    }


@router.post("/games/ant_defense/{game_id}/pause")
async def toggle_pause(game_id: str) -> Dict:
    """Pausa/retoma o jogo"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    game_state = active_games[game_id]
    game_state.paused = not game_state.paused
    
    await broadcast_game_state(game_id, game_state)
    
    return {
        "success": True,
        "paused": game_state.paused,
        "state": game_state.to_dict()
    }


@router.delete("/games/ant_defense/{game_id}")
async def delete_ant_defense_game(game_id: str) -> Dict:
    """Deleta um jogo Ant Defense"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    del active_games[game_id]
    if game_id in game_connections:
        # Fecha todas as conexões WebSocket
        for ws in game_connections[game_id]:
            try:
                await ws.close()
            except:
                pass
        del game_connections[game_id]
    
    return {"success": True, "message": "Jogo deletado"}


@router.websocket("/ws/ant_defense/{game_id}")
async def ant_defense_websocket(websocket: WebSocket, game_id: str):
    """WebSocket para updates em tempo real do jogo Ant Defense"""
    await websocket.accept()
    
    if game_id not in active_games:
        await websocket.send_json({"error": "Jogo não encontrado"})
        await websocket.close()
        return
    
    # Adiciona conexão à lista do jogo
    if game_id not in game_connections:
        game_connections[game_id] = []
    game_connections[game_id].append(websocket)
    
    # Envia estado inicial
    game_state = active_games[game_id]
    await websocket.send_json({
        "type": "init",
        "state": game_state.to_dict()
    })
    
    try:
        while True:
            # Recebe comandos do cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            
            command = message.get("command")
            
            if command == "place_tower":
                grid_x = message.get("grid_x")
                grid_y = message.get("grid_y")
                tower_type = message.get("tower_type")
                
                if grid_x is None or grid_y is None or tower_type is None:
                    await websocket.send_json({
                        "error": "Dados inválidos para place_tower"
                    })
                    continue
                
                try:
                    tower_type_enum = TowerType(tower_type)
                    game_state = active_games[game_id]
                    success, msg = game_state.place_tower(grid_x, grid_y, tower_type_enum)
                    
                    await websocket.send_json({
                        "type": "tower_placed",
                        "success": success,
                        "message": msg,
                        "state": game_state.to_dict()
                    })
                    
                    if success:
                        await broadcast_game_state(game_id, game_state, exclude=websocket)
                
                except ValueError as e:
                    await websocket.send_json({"error": str(e)})
            
            elif command == "start_wave":
                wave_number = message.get("wave_number", 1)
                game_state = active_games[game_id]
                
                if not game_state.wave_active:
                    game_state.start_wave(wave_number)
                    await broadcast_game_state(game_id, game_state)
            
            elif command == "pause":
                game_state = active_games[game_id]
                game_state.paused = not game_state.paused
                await broadcast_game_state(game_id, game_state)
            
            elif command == "get_state":
                game_state = active_games[game_id]
                await websocket.send_json({
                    "type": "state_update",
                    "state": game_state.to_dict()
                })
            
            else:
                await websocket.send_json({"error": f"Comando desconhecido: {command}"})
    
    except WebSocketDisconnect:
        pass
    finally:
        # Remove conexão da lista
        if game_id in game_connections and websocket in game_connections[game_id]:
            game_connections[game_id].remove(websocket)


async def broadcast_game_state(game_id: str, game_state: GameState, exclude: WebSocket = None):
    """Envia estado atualizado para todas as conexões WebSocket do jogo"""
    if game_id not in game_connections:
        return
    
    state_dict = game_state.to_dict()
    
    for ws in game_connections[game_id]:
        if ws != exclude:
            try:
                await ws.send_json({
                    "type": "state_update",
                    "state": state_dict
                })
            except:
                pass  # Ignora erros de envio


# Loop de atualização do jogo (roda em background)
async def game_update_loop():
    """Atualiza todos os jogos ativos periodicamente"""
    while True:
        dt = 0.033  # ~30 FPS
        
        for game_id, game_state in list(active_games.items()):
            if not game_state.paused and not game_state.game_over:
                events = game_state.update(dt)
                
                # Se houve mudanças significativas, notifica clientes
                if events["enemies_killed"] or events["base_hit"] or events["wave_complete"]:
                    await broadcast_game_state(game_id, game_state)
        
        await asyncio.sleep(dt)


# Inicia o loop de atualização quando o módulo é carregado
@router.on_event("startup")
async def start_game_loop():
    """Inicia o loop de atualização de jogos em background"""
    asyncio.create_task(game_update_loop())
