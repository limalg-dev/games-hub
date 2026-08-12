import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_colony_hex_lobby():
    resp = client.post("/games/colony_hex", json={"max_players": 2, "fill_ai": True})
    assert resp.status_code == 200
    data = resp.json()
    assert "game_id" in data
    assert data["state"]["status"] == "lobby"

def test_get_colony_hex_lobby():
    resp_create = client.post("/games/colony_hex", json={"max_players": 2, "fill_ai": True})
    game_id = resp_create.json()["game_id"]
    
    resp_get = client.get(f"/games/colony_hex/{game_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == game_id

def test_list_colony_hex_lobbies():
    client.post("/games/colony_hex", json={"max_players": 2, "fill_ai": True})
    resp_list = client.get("/games/colony_hex")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) >= 1

def test_websocket_colony_hex():
    resp_create = client.post("/games/colony_hex", json={"max_players": 2, "fill_ai": True})
    game_id = resp_create.json()["game_id"]
    
    with client.websocket_connect(f"/games/colony_hex/ws/{game_id}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "welcome"
        assert data["seat"] == "red"
        
        # In connection phase, websocket also receives the first broadcasted state:
        welcome_broadcast = websocket.receive_json()
        assert welcome_broadcast["type"] == "state"
        
        # Test start message
        websocket.send_json({"type": "start"})
        state_data = websocket.receive_json()
        assert state_data["type"] == "state"
        assert state_data["state"]["status"] == "active"
        
        # Test action error response
        websocket.send_json({
            "type": "action",
            "action": {
                "kind": "recruit",
                "unit_type": "worker"
            }
        })
        resp = websocket.receive_json()
        assert resp["type"] == "error"
        assert resp["message"] == "Ninho ocupado"

        # Now let's try a valid action: end turn
        websocket.send_json({
            "type": "action",
            "action": {
                "kind": "end_turn"
            }
        })
        
        # This will trigger AI turn(s) since the other player is an AI and it's their turn
        # The endpoint loops and broadcasts the state for each AI turn
        # Let's receive the broadcasted states until the status is finished or it's our turn again
        # (or just receive at least one state broadcast indicating state update)
        resp_turn = websocket.receive_json()
        assert resp_turn["type"] == "state"




