"""
Integration tests for Super Bomberman API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_bomberman_info():
    res = client.get("/api/bomberman/info")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "bomberman"
    assert "15x13" in data["grid_size"]
    assert "battle" in data["modes"]

def test_bomberman_stages():
    res = client.get("/api/bomberman/stages")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5

def test_bomberman_map_generation():
    res = client.get("/api/bomberman/map?mode=battle&difficulty=medium")
    assert res.status_code == 200
    data = res.json()
    assert data["cols"] == 15
    assert data["rows"] == 13
    assert len(data["spawns"]) == 4

def test_bomberman_arcade_map():
    res = client.get("/api/bomberman/map?mode=arcade&stage=1")
    assert res.status_code == 200
    data = res.json()
    assert data["exit_door"] is not None
    assert "stage_info" in data

def test_bomberman_highscores():
    res = client.get("/api/bomberman/highscores")
    assert res.status_code == 200
    scores = res.json()
    assert isinstance(scores, list)
    assert len(scores) >= 1

    post_res = client.post("/api/bomberman/highscores", json={
        "name": "HERO",
        "score": 12345,
        "mode": "arcade",
        "difficulty": "hard"
    })
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["status"] == "success"
    assert post_data["entry"]["name"] == "HERO"

def test_play_bomberman_route():
    res = client.get("/play/bomberman")
    assert res.status_code == 200
    assert "Super Bomberman" in res.text
    assert "gameCanvas" in res.text
