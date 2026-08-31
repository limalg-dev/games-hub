"""
Colônia Hex - API Routes
Endpoints for creating games, fetching state, executing actions,
submitting highscores, and serving the HTML5 canvas client.
"""

from __future__ import annotations
import os
import time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.responses import FileResponse, JSONResponse

from .logic import HexGame

router = APIRouter(prefix="/colonia-hex", tags=["colonia_hex"])

# In-memory storage for active games
active_games: Dict[str, HexGame] = {}
_game_created: Dict[str, float] = {}
_GAME_TTL = 3600  # 1 hour


def _cleanup_expired() -> None:
    now = time.time()
    expired = [gid for gid, ts in _game_created.items() if now - ts > _GAME_TTL]
    for gid in expired:
        active_games.pop(gid, None)
        _game_created.pop(gid, None)


class NewGameRequest(BaseModel):
    map_size: str = Field(default="small")
    num_players: int = Field(default=2, ge=2, le=4)
    difficulty: str = Field(default="medium")
    seed: Optional[int] = None


class ActionRequest(BaseModel):
    game_id: str
    action_type: str  # "recruit", "move", "build", "end_turn"
    province_id: Optional[str] = None
    from_q: Optional[int] = None
    from_r: Optional[int] = None
    to_q: Optional[int] = None
    to_r: Optional[int] = None
    q: Optional[int] = None
    r: Optional[int] = None
    level: Optional[int] = 1
    building: Optional[str] = None


class ScoreSubmission(BaseModel):
    player_name: str = Field(..., max_length=20)
    score: int = Field(..., ge=0)
    difficulty: str = Field(default="medium")
    turns: int = Field(default=0, ge=0)
    map_size: str = Field(default="small")
    won: bool = Field(default=True)


class ColoniaHexHighScoreManager:
    def __init__(self):
        self.scores: List[Dict[str, Any]] = [
            {"name": "COLONY_MASTER", "score": 2400, "difficulty": "hard", "turns": 12, "map_size": "medium", "won": True},
            {"name": "HEX_QUEEN", "score": 1850, "difficulty": "medium", "turns": 15, "map_size": "small", "won": True},
            {"name": "ANT_COMMANDER", "score": 1320, "difficulty": "medium", "turns": 18, "map_size": "small", "won": True},
            {"name": "LEAF_STRATEGIST", "score": 950, "difficulty": "easy", "turns": 22, "map_size": "small", "won": True},
            {"name": "TERRITORY_CHAMP", "score": 600, "difficulty": "easy", "turns": 25, "map_size": "small", "won": True},
        ]

    def get_scores(self, limit: int = 10) -> List[Dict[str, Any]]:
        return sorted(self.scores, key=lambda x: x["score"], reverse=True)[:limit]

    def add_score(
        self,
        name: str,
        score: int,
        difficulty: str = "medium",
        turns: int = 0,
        map_size: str = "small",
        won: bool = True,
    ) -> Dict[str, Any]:
        entry = {
            "name": (name or "ANON")[:15].upper(),
            "score": max(0, int(score)),
            "difficulty": difficulty,
            "turns": turns,
            "map_size": map_size,
            "won": won,
        }
        self.scores.append(entry)
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:50]
        return entry


high_score_manager = ColoniaHexHighScoreManager()


@router.post("/api/new")
async def create_new_game(req: NewGameRequest = NewGameRequest()):
    """Create a new Colonia Hex game session."""
    _cleanup_expired()
    game = HexGame(
        map_size=req.map_size,
        num_players=req.num_players,
        difficulty=req.difficulty,
        seed=req.seed,
    )
    active_games[game.game_id] = game
    _game_created[game.game_id] = time.time()
    return {
        "status": "success",
        "game_id": game.game_id,
        "state": game.to_dict(),
    }


@router.get("/api/state/{game_id}")
async def get_game_state(game_id: str):
    """Retrieve full board and province state for a game."""
    _cleanup_expired()
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found")
    return {
        "status": "success",
        "state": game.to_dict(),
    }


@router.post("/api/action")
async def execute_action(action: ActionRequest):
    """Execute a gameplay action (recruit, move, build, end_turn)."""
    _cleanup_expired()
    game = active_games.get(action.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game session not found")

    action_type = action.action_type.lower()
    if action_type == "recruit":
        if not action.province_id or action.q is None or action.r is None:
            raise HTTPException(status_code=400, detail="Missing province_id, q, or r for recruitment")
        result = game.recruit(
            province_id=action.province_id,
            q=action.q,
            r=action.r,
            level=action.level or 1,
        )
    elif action_type == "move":
        if action.from_q is None or action.from_r is None or action.to_q is None or action.to_r is None:
            raise HTTPException(status_code=400, detail="Missing from_q, from_r, to_q, or to_r for movement")
        result = game.move(
            from_q=action.from_q,
            from_r=action.from_r,
            to_q=action.to_q,
            to_r=action.to_r,
        )
    elif action_type == "build":
        if not action.province_id or action.q is None or action.r is None or not action.building:
            raise HTTPException(status_code=400, detail="Missing province_id, q, r, or building for construction")
        result = game.build(
            province_id=action.province_id,
            q=action.q,
            r=action.r,
            building=action.building,
        )
    elif action_type == "end_turn":
        result = game.end_turn()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action type: {action.action_type}")

    if not result.get("success", False):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "reason": result.get("reason", "Action failed"),
                "state": game.to_dict(),
            },
        )

    return {
        "status": "success",
        "result": result,
        "state": game.to_dict(),
    }


@router.get("/api/highscores")
async def get_highscores(limit: int = Query(default=10, ge=1, le=50)):
    """Retrieve top highscore entries."""
    return high_score_manager.get_scores(limit=limit)


@router.post("/api/highscores")
async def submit_highscore(submission: ScoreSubmission):
    """Submit a highscore entry."""
    entry = high_score_manager.add_score(
        name=submission.player_name,
        score=submission.score,
        difficulty=submission.difficulty,
        turns=submission.turns,
        map_size=submission.map_size,
        won=submission.won,
    )
    return {"status": "success", "entry": entry}


@router.get("/play")
async def play_colonia_hex_redirect():
    """Serves the standalone Colonia Hex web client."""
    static_html = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_html):
        return FileResponse(static_html)
    return FileResponse("static/index.html")
