"""
🐜 Ant Defense - Rotas API e WebSocket para Tower Defense
Integração com a plataforma Checkers-Platform
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import json
import asyncio
import time
from datetime import datetime

from games.tower_defense.logic import (
    TowerDefenseGame, 
    TowerType, EnemyType,
    GameState, Difficulty, DIFFICULTY_CONFIGS
)
import logging

logger = logging.getLogger(__name__)

# Router paraTower Defense
router = APIRouter(prefix="/tower-defense", tags=["tower_defense"])

# Armazenamento de jogos em memória (em produção usar banco de dados/Redis)
active_games: Dict[str, TowerDefenseGame] = {}
game_websockets: Dict[str, List[WebSocket]] = {}
_game_created: Dict[str, float] = {}
_GAME_TTL = 3600  # 1 hour


def _cleanup_expired():
    """Remove games older than _GAME_TTL seconds."""
    now = time.time()
    expired = [gid for gid, ts in _game_created.items() if now - ts > _GAME_TTL]
    for gid in expired:
        active_games.pop(gid, None)
        game_websockets.pop(gid, None)
        _game_created.pop(gid, None)


class PlaceTowerRequest(BaseModel):
    x: int
    y: int
    tower_type: str  # "archer", "bomb", "ice"


class UpgradeTowerRequest(BaseModel):
    tower_id: str
    branch: Optional[str] = None


class SellTowerRequest(BaseModel):
    tower_id: str


class StartWaveRequest(BaseModel):
    pass


class CreateGameRequest(BaseModel):
    difficulty: str = "normal"  # "easy", "normal", "hard"


class TowerDefenseHighScoreRequest(BaseModel):
    name: str
    score: int
    difficulty: str = "normal"
    waves_cleared: int = 0
    victory: bool = False


class TowerDefenseHighScoreManager:
    """In-memory highscore keeper with initial classic arcade scores for Tower Defense."""
    def __init__(self):
        self._scores: List[Dict[str, Any]] = [
            {"name": "COMMANDER_ANT", "score": 30000, "difficulty": "normal", "waves_cleared": 15, "victory": True, "date": "2026-08-28"},
            {"name": "SCOUT_ANT", "score": 20000, "difficulty": "normal", "waves_cleared": 12, "victory": False, "date": "2026-08-28"},
            {"name": "COLONY_GUARD", "score": 15000, "difficulty": "easy", "waves_cleared": 15, "victory": True, "date": "2026-08-28"},
            {"name": "QUEEN_DEFENDER", "score": 45000, "difficulty": "hard", "waves_cleared": 15, "victory": True, "date": "2026-08-28"},
            {"name": "INSANE_SURVIVOR", "score": 60000, "difficulty": "insane", "waves_cleared": 15, "victory": True, "date": "2026-08-28"},
        ]

    def get_scores(self, difficulty: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        filtered = self._scores
        if difficulty:
            filtered = [s for s in filtered if s.get("difficulty") == difficulty]
        filtered = sorted(filtered, key=lambda s: s.get("score", 0), reverse=True)
        return filtered[:limit]

    def add_score(self, name: str, score: int, difficulty: str = "normal", waves_cleared: int = 0, victory: bool = False) -> Dict[str, Any]:
        entry = {
            "name": name.strip().upper()[:16] or "ANON_ANT",
            "score": int(score),
            "difficulty": difficulty,
            "waves_cleared": int(waves_cleared),
            "victory": bool(victory),
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        self._scores.append(entry)
        self._scores.sort(key=lambda s: s["score"], reverse=True)
        return entry


td_high_score_manager = TowerDefenseHighScoreManager()


@router.get("/")
async def get_tower_defense_info():
    """Informações sobre o jogo Tower Defense"""
    return {
        "name": "Ant Defense",
        "description": "Jogo Tower Defense onde formigas defendem o formigueiro",
        "version": "1.0.0",
        "game_modes": ["single_player"],
        "max_players": 1,
        "grid_size": "30x25",
        "tower_types": ["archer", "bomb", "ice"],
        "enemy_types": ["fly", "beetle", "sky_bug"],
        "difficulties": {
            d.value: {
                "label": cfg["label"],
                "description": cfg["description"],
                "start_crystals": cfg["start_crystals"],
                "start_lives": cfg["start_lives"],
            }
            for d, cfg in DIFFICULTY_CONFIGS.items()
        }
    }


@router.get("/highscores")
async def get_tower_defense_highscores(difficulty: Optional[str] = None, limit: int = 10):
    """Retorna a lista de recordes do Tower Defense"""
    return td_high_score_manager.get_scores(difficulty=difficulty, limit=limit)


@router.post("/highscores")
async def post_tower_defense_highscores(request: TowerDefenseHighScoreRequest):
    """Registra uma nova pontuação no Tower Defense"""
    entry = td_high_score_manager.add_score(
        name=request.name,
        score=request.score,
        difficulty=request.difficulty,
        waves_cleared=request.waves_cleared,
        victory=request.victory,
    )
    return {"status": "success", "entry": entry}


@router.post("/games/create")
async def create_game(request: CreateGameRequest = CreateGameRequest()):
    """Cria um novo jogo de Tower Defense"""
    _cleanup_expired()
    game_id = f"td_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"

    # Map difficulty string to enum
    diff_map = {
        "easy": Difficulty.EASY, "normal": Difficulty.NORMAL,
        "hard": Difficulty.HARD, "insane": Difficulty.INSANE,
    }
    difficulty = diff_map.get(request.difficulty, Difficulty.NORMAL)

    game = TowerDefenseGame(game_id=game_id, difficulty=difficulty)
    active_games[game_id] = game
    game_websockets[game_id] = []
    _game_created[game_id] = time.time()
    
    return {
        "success": True,
        "game_id": game_id,
        "initial_state": game.get_state()
    }


@router.get("/games/{game_id}")
async def get_game(game_id: str):
    """Obtém o estado atual do jogo"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    game = active_games[game_id]
    return game.get_state()


@router.post("/games/{game_id}/place-tower")
async def place_tower(game_id: str, request: PlaceTowerRequest):
    """Coloca uma torre no grid"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    game = active_games[game_id]
    
    # Mapeia tipo de torre
    tower_type_map = {
        "archer": TowerType.ARCHER,
        "bomb": TowerType.BOMB,
        "ice": TowerType.ICE
    }
    
    if request.tower_type not in tower_type_map:
        raise HTTPException(status_code=400, detail=f"Tipo de torre inválido: {request.tower_type}")
    
    tower_type = tower_type_map[request.tower_type]
    success, message, tower = game.place_tower(request.x, request.y, tower_type)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Notifica websockets conectados
    await broadcast_game_state(game_id)
    
    return {
        "success": True,
        "message": message,
        "tower": tower.to_dict() if tower else None,
        "state": game.get_state()
    }


@router.post("/games/{game_id}/sell-tower")
async def sell_tower(game_id: str, request: SellTowerRequest):
    """Vende uma torre"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    game = active_games[game_id]
    success, message, sell_value = game.sell_tower(request.tower_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    await broadcast_game_state(game_id)
    
    return {
        "success": True,
        "message": message,
        "sell_value": sell_value,
        "state": game.get_state()
    }


@router.post("/games/{game_id}/upgrade-tower")
async def upgrade_tower(game_id: str, request: UpgradeTowerRequest):
    """Faz upgrade de uma torre"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    game = active_games[game_id]
    success, message = game.upgrade_tower(request.tower_id, branch=request.branch)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    await broadcast_game_state(game_id)
    
    return {
        "success": True,
        "message": message,
        "state": game.get_state()
    }


@router.post("/games/{game_id}/start-wave")
async def start_wave(game_id: str, request: StartWaveRequest):
    """Inicia uma nova onda de inimigos"""
    if game_id not in active_games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    game = active_games[game_id]
    success, message = game.start_wave()
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    await broadcast_game_state(game_id)
    
    return {
        "success": True,
        "message": message,
        "state": game.get_state()
    }


@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """WebSocket para updates em tempo real do jogo"""
    await websocket.accept()
    
    if game_id not in active_games:
        await websocket.send_json({"error": "Jogo não encontrado"})
        await websocket.close()
        return
    
    # Adiciona websocket à lista do jogo
    if game_id not in game_websockets:
        game_websockets[game_id] = []
    game_websockets[game_id].append(websocket)
    
    # Envia estado inicial
    game = active_games[game_id]
    await websocket.send_json({
        "type": "init",
        "state": game.get_state()
    })
    
    try:
        # Mantém conexão aberta e recebe comandos
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Processa comandos do cliente
            command = message.get("command")
            
            if command == "place_tower":
                tower_type_map = {
                    "archer": TowerType.ARCHER,
                    "bomb": TowerType.BOMB,
                    "ice": TowerType.ICE
                }
                x = message.get("x")
                y = message.get("y")
                tower_type_str = message.get("tower_type")
                
                if x is not None and y is not None and tower_type_str in tower_type_map:
                    tower_type = tower_type_map[tower_type_str]
                    success, msg, _ = game.place_tower(x, y, tower_type)
                    await websocket.send_json({
                        "type": "command_result",
                        "command": "place_tower",
                        "success": success,
                        "message": msg
                    })
                    await broadcast_game_state(game_id)
            
            elif command == "start_wave":
                success, msg = game.start_wave()
                await websocket.send_json({
                    "type": "command_result",
                    "command": "start_wave",
                    "success": success,
                    "message": msg
                })
                await broadcast_game_state(game_id)
            
            elif command == "sell_tower":
                tower_id = message.get("tower_id")
                if tower_id:
                    success, msg, value = game.sell_tower(tower_id)
                    await websocket.send_json({
                        "type": "command_result",
                        "command": "sell_tower",
                        "success": success,
                        "message": msg,
                        "sell_value": value
                    })
                    await broadcast_game_state(game_id)
            
            elif command == "upgrade_tower":
                tower_id = message.get("tower_id")
                branch = message.get("branch")
                if tower_id:
                    success, msg = game.upgrade_tower(tower_id, branch=branch)
                    await websocket.send_json({
                        "type": "command_result",
                        "command": "upgrade_tower",
                        "success": success,
                        "message": msg
                    })
                    await broadcast_game_state(game_id)

            elif command == "set_target_mode":
                tower_id = message.get("tower_id")
                target_mode = message.get("target_mode")
                if tower_id and target_mode:
                    success, msg = game.set_target_mode(tower_id, target_mode)
                    await websocket.send_json({
                        "type": "command_result",
                        "command": "set_target_mode",
                        "success": success,
                        "message": msg
                    })
                    await broadcast_game_state(game_id)

            elif command == "cast_spell":
                spell = message.get("spell")
                x = float(message.get("x", 0.0))
                y = float(message.get("y", 0.0))
                if spell:
                    success, msg, data = game.cast_spell(spell, x, y)
                    await websocket.send_json({
                        "type": "command_result",
                        "command": "cast_spell",
                        "success": success,
                        "message": msg,
                        "data": data
                    })
                    await broadcast_game_state(game_id)

            elif command == "set_speed":
                scale = message.get("scale", 1)
                success, msg = game.set_time_scale(int(scale))
                await websocket.send_json({
                    "type": "command_result",
                    "command": "set_speed",
                    "success": success,
                    "message": msg
                })
                await broadcast_game_state(game_id)

            elif command == "toggle_auto_wave":
                success, msg = game.toggle_auto_wave()
                await websocket.send_json({
                    "type": "command_result",
                    "command": "toggle_auto_wave",
                    "success": success,
                    "message": msg
                })
                await broadcast_game_state(game_id)
    
    except WebSocketDisconnect:
        pass
    finally:
        # Remove websocket da lista
        if game_id in game_websockets and websocket in game_websockets[game_id]:
            game_websockets[game_id].remove(websocket)


async def broadcast_game_state(game_id: str):
    """Envia estado atual do jogo para todos os websockets conectados"""
    if game_id not in active_games or game_id not in game_websockets:
        return
    
    game = active_games[game_id]
    state = game.get_state()
    
    disconnected = []
    for ws in game_websockets[game_id]:
        try:
            await ws.send_json({
                "type": "state_update",
                "state": state
            })
        except Exception as exc:
            logger.debug("Failed to broadcast to WS: %s", exc)
            disconnected.append(ws)
    
    # Remove websockets desconectados
    for ws in disconnected:
        game_websockets[game_id].remove(ws)


async def game_loop_task():
    """Task que roda o game loop continuamente"""
    _cleanup_counter = 0
    BASE_DT = 0.033  # ~30 FPS server tick rate
    while True:
        dt = BASE_DT
        
        # Periodic cleanup every ~60 seconds
        _cleanup_counter += 1
        if _cleanup_counter % 1800 == 0:
            _cleanup_expired()
        
        for game_id, game in list(active_games.items()):
            if not game.state.game_over and not game.state.victory:
                result = game.update(dt)
                
                # Broadcast em qualquer gameplay ativa: onda rodando, inimigos andando, projéteis, ataques ou mudanças
                should_broadcast = (
                    game.wave_active
                    or len(game.enemies) > 0
                    or len(game.projectiles) > 0
                    or bool(result["attacks"])
                    or bool(result["enemies_destroyed"])
                    or bool(result["state_changes"])
                )
                if should_broadcast:
                    await broadcast_game_state(game_id)

        # Sleep less when time is scaled up (e.g. 4x → sleep 4x less)
        max_scale = 1
        for game in active_games.values():
            if game.state.time_scale > max_scale:
                max_scale = game.state.time_scale
        await asyncio.sleep(dt / max_scale)


# Função para iniciar o game loop
def start_game_loop():
    """Inicia o game loop em background"""
    asyncio.create_task(game_loop_task())


# Serve o arquivo HTML do jogo
@router.get("/play", response_class=HTMLResponse)
async def play_tower_defense():
    """Serve a interface do jogo Tower Defense"""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    return HTMLResponse(
        content="<h1>Tower Defense - Em Desenvolvimento</h1><p>Interface HTML ainda não disponível.</p>",
        status_code=200,
    )
