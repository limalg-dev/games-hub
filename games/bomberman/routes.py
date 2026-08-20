"""
Super Bomberman API Routes
"""
import os
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from starlette.responses import FileResponse

from .logic import (
    generate_map,
    STAGE_CONFIGS,
    high_score_manager,
    GRID_COLS,
    GRID_ROWS
)

router = APIRouter()

class ScoreSubmission(BaseModel):
    name: str = Field(..., max_length=20)
    score: int = Field(..., ge=0)
    mode: str = Field(default="battle")
    difficulty: str = Field(default="medium")


@router.get("/api/bomberman/info")
async def get_bomberman_info():
    """Get metadata about Super Bomberman."""
    return {
        "id": "bomberman",
        "title": "Super Bomberman",
        "version": "1.0.0",
        "grid_size": f"{GRID_COLS}x{GRID_ROWS}",
        "modes": ["battle", "arcade"],
        "difficulties": ["easy", "medium", "hard"],
        "stages_count": len(STAGE_CONFIGS),
    }


@router.get("/api/bomberman/stages")
async def get_stages():
    """Get all arcade stage configurations."""
    return STAGE_CONFIGS


@router.get("/api/bomberman/map")
async def get_map(
    mode: str = Query(default="battle", pattern="^(battle|arcade)$"),
    difficulty: str = Query(default="medium", pattern="^(easy|medium|hard)$"),
    stage: int = Query(default=1, ge=1, le=len(STAGE_CONFIGS)),
    seed: Optional[int] = Query(default=None),
):
    """Generate a procedural Bomberman map/arena."""
    density_map = {"easy": 0.50, "medium": 0.65, "hard": 0.75}
    density = density_map.get(difficulty, 0.65)
    
    if mode == "arcade":
        stage_cfg = STAGE_CONFIGS[stage - 1]
        density = stage_cfg.get("crate_density", density)
        map_data = generate_map(
            cols=GRID_COLS,
            rows=GRID_ROWS,
            crate_density=density,
            mode="arcade",
            seed=seed
        )
        map_data["stage_info"] = stage_cfg
        return map_data

    return generate_map(
        cols=GRID_COLS,
        rows=GRID_ROWS,
        crate_density=density,
        mode="battle",
        seed=seed
    )


@router.get("/api/bomberman/highscores")
async def get_highscores(limit: int = Query(default=10, ge=1, le=50)):
    """Retrieve top highscores."""
    return high_score_manager.get_scores(limit=limit)


@router.post("/api/bomberman/highscores")
async def submit_highscore(submission: ScoreSubmission):
    """Submit a highscore entry."""
    entry = high_score_manager.add_score(
        name=submission.name,
        score=submission.score,
        mode=submission.mode,
        difficulty=submission.difficulty,
    )
    return {"status": "success", "entry": entry}


@router.get("/play/bomberman")
async def play_bomberman():
    """Serves the standalone Super Bomberman game client."""
    static_html = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if not os.path.exists(static_html):
        raise HTTPException(status_code=404, detail="Game page not found")
    return FileResponse(static_html)
