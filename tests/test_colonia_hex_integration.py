import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_new_game():
    response = client.post(
        "/colonia-hex/api/new",
        json={"map_size": "small", "num_players": 2, "difficulty": "medium"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "game_id" in data
    assert "state" in data
    state = data["state"]
    assert state["map_size"] == "small"
    assert state["num_players"] == 2
    assert state["turn_number"] == 1
    assert len(state["provinces"]) >= 2
    assert len(state["grid"]) > 0


def test_get_game_state():
    # Create game
    create_res = client.post(
        "/colonia-hex/api/new",
        json={"map_size": "small", "num_players": 2, "difficulty": "easy"},
    )
    game_id = create_res.json()["game_id"]

    # Get state
    res = client.get(f"/colonia-hex/api/state/{game_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["state"]["game_id"] == game_id

    # 404 for unknown game
    res_404 = client.get("/colonia-hex/api/state/non_existent_game_999")
    assert res_404.status_code == 404


def test_execute_actions():
    # Create game
    create_res = client.post(
        "/colonia-hex/api/new",
        json={"map_size": "small", "num_players": 2, "difficulty": "medium", "seed": 42},
    )
    game_id = create_res.json()["game_id"]
    state = create_res.json()["state"]

    p0 = [p for p in state["provinces"] if p["owner"] == 0][0]
    p0_cells = [tuple(map(int, k.split(","))) for k, v in state["grid"].items() if v["owner"] == 0]

    # End turn action
    end_turn_res = client.post(
        "/colonia-hex/api/action",
        json={"game_id": game_id, "action_type": "end_turn"},
    )
    assert end_turn_res.status_code == 200
    end_data = end_turn_res.json()
    assert end_data["status"] == "success"
    assert "state" in end_data
    assert end_data["state"]["turn_number"] >= 1


def test_highscores():
    # Get highscores
    res = client.get("/colonia-hex/api/highscores")
    assert res.status_code == 200
    scores = res.json()
    assert isinstance(scores, list)
    assert len(scores) > 0

    # Submit highscore
    post_res = client.post(
        "/colonia-hex/api/highscores",
        json={
            "player_name": "AntStrategist",
            "score": 1250,
            "difficulty": "hard",
            "turns": 14,
            "map_size": "medium",
            "won": True,
        },
    )
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "success"
    assert post_res.json()["entry"]["name"] == "ANTSTRATEGIST"
    assert post_res.json()["entry"]["score"] == 1250


def test_invalid_action():
    create_res = client.post(
        "/colonia-hex/api/new",
        json={"map_size": "small", "num_players": 2},
    )
    game_id = create_res.json()["game_id"]

    # Invalid action type
    res = client.post(
        "/colonia-hex/api/action",
        json={"game_id": game_id, "action_type": "invalid_magic_move"},
    )
    assert res.status_code == 400

    # Action on non-existent game
    res_404 = client.post(
        "/colonia-hex/api/action",
        json={"game_id": "ghost_game_123", "action_type": "end_turn"},
    )
    assert res_404.status_code == 404

def test_recruit_move_build_api():
    create_res = client.post(
        "/colonia-hex/api/new",
        json={"map_size": "small", "num_players": 2, "seed": 42},
    )
    assert create_res.status_code == 200
    game_id = create_res.json()["game_id"]
    state = create_res.json()["state"]
    p0 = [p for p in state["provinces"] if p["owner"] == 0][0]

    # Find cell in province without unit/building
    target_cell = None
    for cell_coords in p0["cells"]:
        key = f"{cell_coords[0]},{cell_coords[1]}"
        if state["grid"][key]["unit_level"] == 0 and state["grid"][key]["building"] is None:
            target_cell = cell_coords
    if target_cell:
        # Recruit worker (cost 10, starting gold 10)
        recruit_res = client.post(
            "/colonia-hex/api/action",
            json={
                "game_id": game_id,
                "action_type": "recruit",
                "province_id": p0["id"],
                "q": target_cell[0],
                "r": target_cell[1],
                "level": 1,
            },
        )
        assert recruit_res.status_code == 200
        assert recruit_res.json()["status"] == "success"
def test_play_routes():
    res1 = client.get("/play/colonia_hex")
    assert res1.status_code == 200

    res2 = client.get("/colonia-hex/play")
    assert res2.status_code == 200
