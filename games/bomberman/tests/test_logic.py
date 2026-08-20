"""
Unit tests for Super Bomberman logic and map generation
"""
import pytest
from games.bomberman.logic import (
    generate_map,
    STAGE_CONFIGS,
    high_score_manager,
    GRID_COLS,
    GRID_ROWS,
    CELL_WALL,
    CELL_EMPTY,
    CELL_CRATE,
    SPAWN_CORNERS,
)

def test_map_dimensions():
    arena = generate_map(seed=42)
    assert arena["cols"] == GRID_COLS
    assert arena["rows"] == GRID_ROWS
    assert len(arena["grid"]) == GRID_ROWS
    assert all(len(row) == GRID_COLS for row in arena["grid"])

def test_map_outer_walls_and_pillars():
    arena = generate_map(seed=42)
    grid = arena["grid"]
    
    # Outer walls
    for c in range(GRID_COLS):
        assert grid[0][c] == CELL_WALL
        assert grid[GRID_ROWS - 1][c] == CELL_WALL
    for r in range(GRID_ROWS):
        assert grid[r][0] == CELL_WALL
        assert grid[r][GRID_COLS - 1] == CELL_WALL
        
    # Pillars at even row and col
    for r in range(2, GRID_ROWS - 2, 2):
        for c in range(2, GRID_COLS - 2, 2):
            assert grid[r][c] == CELL_WALL

def test_safe_spawns_are_not_blocked():
    arena = generate_map(mode="battle", seed=100)
    grid = arena["grid"]
    
    for r_s, c_s in SPAWN_CORNERS:
        assert grid[r_s][c_s] == CELL_EMPTY
        # Neighbors around spawn must not have crates so player is not boxed in
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r_s + dr, c_s + dc
            if 0 < nr < GRID_ROWS - 1 and 0 < nc < GRID_COLS - 1:
                assert grid[nr][nc] != CELL_CRATE

def test_arcade_mode_has_exit_door():
    arena = generate_map(mode="arcade", seed=123)
    assert arena["exit_door"] is not None
    r, c = arena["exit_door"]
    assert arena["grid"][r][c] == CELL_CRATE

def test_highscore_manager():
    initial_count = len(high_score_manager.get_scores())
    new_entry = high_score_manager.add_score("TEST_BOMBER", 99999, "battle", "hard")
    assert new_entry["name"] == "TEST_BOMBER"
    assert new_entry["score"] == 99999
    
    top = high_score_manager.get_scores(limit=1)[0]
    assert top["name"] == "TEST_BOMBER"
    assert top["score"] == 99999

def test_stage_configs_valid():
    assert len(STAGE_CONFIGS) == 5
    for stage in STAGE_CONFIGS:
        assert "stage" in stage
        assert "name" in stage
        assert "enemies" in stage
        assert "time_seconds" in stage
        assert stage["time_seconds"] > 0
