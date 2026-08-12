import pytest
from games.colony_hex.logic import GameState

def test_initial_state():
    players = [
        {"color": "red", "is_ai": False},
        {"color": "blue", "is_ai": True}
    ]
    state = GameState("g1", players)
    data = state.to_dict()
    assert data["status"] == "lobby"
    assert len(data["players"]) == 2
    assert data["players"][0]["leaves"] == 10
    assert data["players"][0]["alive"] is True
    # Nest owned
    nest_cell = next(c for c in data["map"] if c["q"] == -4 and c["r"] == 0)
    assert nest_cell["owner"] == "red"

def test_execute_invalid_action():
    players = [{"color": "red", "is_ai": False}, {"color": "blue", "is_ai": False}]
    state = GameState("g1", players)
    state.status = "active"
    # Expand to non-adjacent
    success, err = state.execute_action("red", {"kind": "expand", "q": 0, "r": 0})
    assert success is False
    assert err is not None

def test_start_game():
    # Only 1 player
    players = [{"color": "red", "is_ai": False}]
    state = GameState("g1", players)
    success, err = state.start_game()
    assert success is False
    assert state.status == "lobby"

    # 2 players
    players = [{"color": "red", "is_ai": False}, {"color": "blue", "is_ai": True}]
    state = GameState("g1", players)
    success, err = state.start_game()
    assert success is True
    assert state.status == "active"

def test_turn_and_income():
    players = [{"color": "red", "is_ai": False}, {"color": "blue", "is_ai": False}]
    state = GameState("g1", players)
    state.start_game()
    
    # Red starts, gets income (10 + 1 owned nest = 11)
    assert state.turn_index == 0
    assert state.players[0]["leaves"] == 11
    assert state.actions_left == 2
    
    # Red ends turn
    success, err = state.execute_action("red", {"kind": "end_turn"})
    assert success is True
    
    # Blue starts, gets income (10 + 1 owned nest = 11)
    assert state.turn_index == 1
    assert state.players[1]["leaves"] == 11
    assert state.actions_left == 2
    
    # Blue ends turn
    success, err = state.execute_action("blue", {"kind": "end_turn"})
    assert success is True
    
    # Back to Red, turn_number increases to 2
    assert state.turn_index == 0
    assert state.turn_number == 2
    assert state.players[0]["leaves"] == 12

def test_expand_action():
    players = [{"color": "red", "is_ai": False}, {"color": "blue", "is_ai": False}]
    state = GameState("g1", players)
    state.start_game()
    
    # Starting leaves: 11. Actions: 2. Nest: (-4, 0).
    # Let's expand to adjacent (-3, 0).
    success, err = state.execute_action("red", {"kind": "expand", "q": -3, "r": 0})
    assert success is True
    assert err is None
    
    # State verification:
    # 1. Leaves reduced by 3 (11 - 3 = 8)
    assert state.players[0]["leaves"] == 8
    # 2. Actions reduced by 1 (2 - 1 = 1)
    assert state.actions_left == 1
    # 3. Cell owner set to "red"
    cell = next(c for c in state.map if c["q"] == -3 and c["r"] == 0)
    assert cell["owner"] == "red"
    
    # Try to expand to the same cell again (already owned)
    success, err = state.execute_action("red", {"kind": "expand", "q": -3, "r": 0})
    assert success is False
    assert err is not None
    assert state.actions_left == 1
    
    # Try to expand to a rock cell.
    # From spec: ROCK_COORDS = {(1, 1), (-1, -1), (2, -2), (-2, 2)}
    # Let's find a rock cell or manually set a cell to rock.
    # Actually, we can just try to expand to (-1, -1) which is a rock (if adjacent - wait, it's not adjacent to red territory yet).
    # Let's make an adjacent cell a rock cell for testing, or check if any adjacent is rock.
    # None of the immediately adjacent to (-4,0) are rocks. Let's make (-4, 1) a rock cell for the test.
    cell_to_rock = next(c for c in state.map if c["q"] == -4 and c["r"] == 1)
    original_terrain = cell_to_rock["terrain"]
    cell_to_rock["terrain"] = "rock"
    success, err = state.execute_action("red", {"kind": "expand", "q": -4, "r": 1})
    assert success is False
    assert err is not None
    cell_to_rock["terrain"] = original_terrain # restore
    
    # Try to expand to a cell containing a unit
    # Worker is at (-4, 0). Let's see if we can expand to (-4, 0)
    success, err = state.execute_action("red", {"kind": "expand", "q": -4, "r": 0})
    assert success is False
    assert err is not None
    
    # Try to expand to a non-adjacent cell
    success, err = state.execute_action("red", {"kind": "expand", "q": 0, "r": 0})
    assert success is False
    assert err is not None
    
    # Try to expand with insufficient leaves.
    # Set leaves to 2.
    state.players[0]["leaves"] = 2
    success, err = state.execute_action("red", {"kind": "expand", "q": -3, "r": 1})
    assert success is False
    assert err is not None

def test_recruit_action():
    players = [{"color": "red", "is_ai": False}, {"color": "blue", "is_ai": False}]
    state = GameState("g1", players)
    state.start_game()
    
    # Starting leaves: 11. Actions: 2. Nest: (-4, 0).
    # Try recruiting a worker on occupied nest (-4, 0) -> should fail
    success, err = state.execute_action("red", {"kind": "recruit", "unit_type": "worker"})
    assert success is False
    assert err is not None
    
    # Move unit away from nest to make it free.
    # Unit 0 is at (-4, 0). Let's move it to (-3, 0)
    # But wait, we can only move to cells we own or empty plain/leaf hex.
    # (-3, 0) is empty plain hex, so we can move there.
    # Unit ID of first unit is "u_red_0"
    success, err = state.execute_action("red", {"kind": "move", "unit_id": "u_red_0", "to_q": -3, "to_r": 0})
    assert success is True
    
    # Now nest (-4, 0) is empty. Leaves: 11. Actions: 1.
    # Try recruiting worker. Cost is 2.
    success, err = state.execute_action("red", {"kind": "recruit", "unit_type": "worker"})
    assert success is True
    assert err is None
    assert state.players[0]["leaves"] == 9
    assert state.turn_index == 1 # Red turn ended, advanced to Blue.
    assert state.actions_left == 2 # Resets to 2.
    
    # Verify a new unit was created on the nest
    # Units list contains unit 0 and the new unit
    new_unit = next(u for u in state.units if u["q"] == -4 and u["r"] == 0)
    assert new_unit["owner"] == "red"
    assert new_unit["type"] == "worker"
    
    # Wait, it's now Blue's turn! Blue gets income (11 leaves, nest at (0, -4))
    # Let's move Blue's starting unit "u_blue_0" at (0, -4) to (0, -3) to free Blue's nest.
    assert state.turn_index == 1
    success, err = state.execute_action("blue", {"kind": "move", "unit_id": "u_blue_0", "to_q": 0, "to_r": -3})
    assert success is True
    
    # Now Blue recruits a soldier. Cost is 5.
    success, err = state.execute_action("blue", {"kind": "recruit", "unit_type": "soldier"})
    assert success is True
    assert state.players[1]["leaves"] == 6 # 11 - 5
    
    # Verify new soldier on Blue nest
    soldier_unit = next(u for u in state.units if u["q"] == 0 and u["r"] == -4)
    assert soldier_unit["owner"] == "blue"
    assert soldier_unit["type"] == "soldier"
    
    # Try recruiting with insufficient leaves
    # Back to Red turn. Let's end Blue's turn if there's any action left.
    # Wait, Blue had 2 actions. 1 move, 1 recruit. So Blue's turn is already ended!
    # Back to Red. Turn 2. Red gets income (9 + 2 owned cells = 11).
    assert state.turn_index == 0
    # Red nest has worker. Let's move it to (-4, 1) to free the nest.
    # Red units are: "u_red_0" at (-3, 0) and the new recruit (ID: "u_red_1") at (-4, 0).
    # Let's move "u_red_1" to (-4, 1)
    success, err = state.execute_action("red", {"kind": "move", "unit_id": "u_red_2", "to_q": -4, "to_r": 1})
    # Wait, what was the ID of the new unit? Let's check how logic.py assigns IDs:
    # "id": f"u_{color}_{len(self.units)}"
    # Since self.units initially has 2 elements ("u_red_0", "u_blue_0"),
    # when Red recruited, len(self.units) was 2, so the ID is "u_red_2".
    # When Blue recruited, len(self.units) was 3, so the ID is "u_blue_3".
    # Let's verify this. Yes, success should be True.
    assert success is True
    
    # Red leaves: 11. Let's set Red leaves to 1.
    state.players[0]["leaves"] = 1
    # Try to recruit a worker (cost 2) -> should fail
    success, err = state.execute_action("red", {"kind": "recruit", "unit_type": "worker"})
    assert success is False
    assert err is not None

def test_move_action():
    players = [{"color": "red", "is_ai": False}, {"color": "blue", "is_ai": False}]
    state = GameState("g1", players)
    state.start_game()
    
    # Red turn. Red unit 0 at (-4, 0).
    # Move to adjacent empty plain hex (-3, 0)
    success, err = state.execute_action("red", {"kind": "move", "unit_id": "u_red_0", "to_q": -3, "to_r": 0})
    assert success is True
    
    # Verify unit is moved, cell (-3, 0) owner is STILL None (move does not auto-claim)
    unit = next(u for u in state.units if u["id"] == "u_red_0")
    assert unit["q"] == -3 and unit["r"] == 0
    cell = next(c for c in state.map if c["q"] == -3 and c["r"] == 0)
    assert cell["owner"] is None
    
    # Move to non-adjacent (e.g. back to (-4, 0) is adjacent, but let's try (-1, 0))
    success, err = state.execute_action("red", {"kind": "move", "unit_id": "u_red_0", "to_q": -1, "to_r": 0})
    assert success is False
    assert err is not None
    
    # Let's make an adjacent cell owned by opponent (blue) and try moving there.
    # Cell (-4, 1) owned by blue:
    opp_cell = next(c for c in state.map if c["q"] == -4 and c["r"] == 1)
    opp_cell["owner"] = "blue"
    # Try to move unit 0 from (-3, 0) to (-4, 1) which is adjacent.
    success, err = state.execute_action("red", {"kind": "move", "unit_id": "u_red_0", "to_q": -4, "to_r": 1})
    assert success is False
    assert err is not None
    opp_cell["owner"] = None # restore
    
    # Try to move enemy unit
    success, err = state.execute_action("red", {"kind": "move", "unit_id": "u_blue_0", "to_q": 0, "to_r": -3})
    assert success is False
    assert err is not None

def test_attack_and_elimination():
    players = [{"color": "red", "is_ai": False}, {"color": "blue", "is_ai": False}]
    state = GameState("g1", players)
    state.start_game()
    
    # Let's spawn a soldier for red. We need a free nest and 5 leaves.
    # Move red starting worker from (-4, 0) to (-3, 0)
    state.execute_action("red", {"kind": "move", "unit_id": "u_red_0", "to_q": -3, "to_r": 0})
    # Recruit soldier for red on nest (-4, 0) (Red has 11 - 5 = 6 leaves left)
    success, err = state.execute_action("red", {"kind": "recruit", "unit_type": "soldier"})
    assert success is True
    
    # Red turn ended (2 actions used: move, recruit).
    # Blue turn starts. Let's move Blue worker from (0, -4) to (0, -3).
    # And then Blue recruits a soldier on nest (0, -4).
    state.execute_action("blue", {"kind": "move", "unit_id": "u_blue_0", "to_q": 0, "to_r": -3})
    state.execute_action("blue", {"kind": "recruit", "unit_type": "soldier"})
    
    # Red turn starts again. Red gets income (6 + 2 owned cells = 8 leaves).
    # Red soldier is at (-4, 0).
    # Let's teleport the red soldier to (-2, 0) and the blue worker to (-1, 0) to test combat.
    red_soldier = next(u for u in state.units if u["owner"] == "red" and u["type"] == "soldier")
    blue_worker = next(u for u in state.units if u["owner"] == "blue" and u["type"] == "worker")
    
    red_soldier["q"] = -2
    red_soldier["r"] = 0
    blue_worker["q"] = -1
    blue_worker["r"] = 0
    
    # Try attacking with worker (should fail, only soldiers can attack)
    success, err = state.execute_action("red", {"kind": "attack", "unit_id": "u_red_0", "to_q": -1, "to_r": 0})
    assert success is False
    assert err is not None
    
    # Attack blue worker at (-1, 0) with red soldier from (-2, 0)
    success, err = state.execute_action("red", {"kind": "attack", "unit_id": red_soldier["id"], "to_q": -1, "to_r": 0})
    assert success is True
    assert err is None
    
    # Verify blue worker is removed from units
    assert blue_worker not in state.units
    # Verify red soldier moved to (-1, 0)
    assert red_soldier["q"] == -1 and red_soldier["r"] == 0
    # Verify cell (-1, 0) is owned by red
    cell = next(c for c in state.map if c["q"] == -1 and c["r"] == 0)
    assert cell["owner"] == "red"
    
    # Now let's test Soldier vs Soldier.
    # Teleport blue soldier (on blue nest 0, -4) to (0, 0).
    # Teleport red soldier (at -1, 0) to (0, 1).
    # Wait, (0, 1) is adjacent to (0, 0).
    blue_soldier = next(u for u in state.units if u["owner"] == "blue" and u["type"] == "soldier")
    blue_soldier["q"] = 0
    blue_soldier["r"] = 0
    red_soldier["q"] = 0
    red_soldier["r"] = 1
    
    # Set cell (0, 0) to be owned by blue
    cell_0_0 = next(c for c in state.map if c["q"] == 0 and c["r"] == 0)
    cell_0_0["owner"] = "blue"
    
    # It is Red's turn (actions left: 1). Red soldier attacks blue soldier.
    success, err = state.execute_action("red", {"kind": "attack", "unit_id": red_soldier["id"], "to_q": 0, "to_r": 0})
    assert success is True
    # Attacking soldier wins. Blue soldier should be removed.
    assert blue_soldier not in state.units
    # Red soldier occupies (0, 0)
    assert red_soldier["q"] == 0 and red_soldier["r"] == 0
    # Red owns (0, 0)
    assert cell_0_0["owner"] == "red"
    
    # Now let's test Nest Capture and Elimination.
    # Teleport red soldier to (0, -3) which is adjacent to blue nest (0, -4).
    red_soldier["q"] = 0
    red_soldier["r"] = -3
    
    # Let's give blue another owned hex to verify neutralization.
    extra_blue_cell = next(c for c in state.map if c["q"] == 1 and c["r"] == -4)
    extra_blue_cell["owner"] = "blue"
    
    # Blue nest is at (0, -4). It is owned by "blue".
    nest_cell = next(c for c in state.map if c["q"] == 0 and c["r"] == -4)
    assert nest_cell["owner"] == "blue"
    
    # Red turn ended since it used second action.
    # It advanced to Blue. But wait! Blue has no units left (worker and soldier both dead).
    # Let's check: Blue still has nest and some leaves. Blue can recruit or pass.
    # Wait, Blue's nest (0, -4) is free (no unit on it). Blue has leaves.
    # Let's make Blue end turn.
    state.execute_action("blue", {"kind": "end_turn"})
    
    # Red turn. Red soldier attacks Blue nest (0, -4).
    success, err = state.execute_action("red", {"kind": "attack", "unit_id": red_soldier["id"], "to_q": 0, "to_r": -4})
    assert success is True
    
    # Verify Blue is eliminated
    blue_player = state.players[1]
    assert blue_player["alive"] is False
    # Blue nest owned by red
    assert nest_cell["owner"] == "red"
    # Blue's other hexes are neutralized
    assert extra_blue_cell["owner"] is None
    # All Blue units removed
    assert not any(u["owner"] == "blue" for u in state.units)
    
    # Game should be finished because only Red is alive
    assert state.status == "finished"
    assert state.winner == "red"

def test_turn_skips_dead_players():
    players = [
        {"color": "red", "is_ai": False},
        {"color": "blue", "is_ai": False},
        {"color": "green", "is_ai": False}
    ]
    state = GameState("g1", players)
    state.start_game()
    
    # 3 players active: red (0), blue (1), green (2)
    # Set blue to dead
    state.players[1]["alive"] = False
    
    # Red is active (0). Let's end Red's turn.
    success, err = state.execute_action("red", {"kind": "end_turn"})
    assert success is True
    
    # Turn should advance to green (2), skipping blue (1)
    assert state.turn_index == 2
    assert state.players[state.turn_index]["color"] == "green"

def test_turn_limit_finished():
    players = [
        {"color": "red", "is_ai": False},
        {"color": "blue", "is_ai": False}
    ]
    state = GameState("g1", players)
    state.start_game()
    
    # Fast forward to turn 20, index 1 (Blue's turn)
    state.turn_number = 20
    state.turn_index = 1
    state.actions_left = 1
    
    # Blue ends turn
    success, err = state.execute_action("blue", {"kind": "end_turn"})
    assert success is True
    
    # Turn number should become 21, game should finish
    assert state.turn_number == 21
    assert state.status == "finished"
    assert state.ranking is not None

def test_ai_greedy_turn():
    # 2 players: Red (Human), Blue (AI)
    players = [
        {"color": "red", "is_ai": False},
        {"color": "blue", "is_ai": True}
    ]
    state = GameState("g1", players)
    state.start_game()
    
    # Red starts. Red has 11 leaves.
    # Let's just make Red end their turn so Blue AI gets its turn.
    state.execute_action("red", {"kind": "end_turn"})
    
    # It should be Blue's turn now. Blue gets income (10 + 1 owned nest = 11)
    assert state.turn_index == 1
    assert state.players[1]["leaves"] == 11
    
    # Run the AI turn
    state.run_ai_turn()
    
    # Blue has executed its turn. Since it has 11 leaves and actions_left = 2:
    # 1. Attack adjacent: Blue has no soldiers, so skipped.
    # 2. Expand: Blue has 11 leaves. Expands to an adjacent cell (e.g. (0, -3)).
    #    Leaves become 8, actions_left becomes 1.
    # 3. Expand: Blue has 8 leaves. Expands to another adjacent cell (e.g. (1, -4)).
    #    Leaves become 5, actions_left becomes 0 (which triggers next turn, advancing back to Red).
    # Since actions_left hit 0, turn advanced to Red, which gets income (12 leaves + 1 owned = 13 leaves).
    assert state.turn_index == 0
    assert state.turn_number == 2
    # Verify Blue did expand: Blue should own at least 2 cells on map now
    blue_cells = [c for c in state.map if c["owner"] == "blue"]
    assert len(blue_cells) == 3 # nest + 2 expansions
    
    # Now let's test AI recruitment and threat detection.
    # Teleport Red worker to (-1, -3) which is adjacent to Blue nest (0, -4)
    red_worker = next(u for u in state.units if u["owner"] == "red")
    red_worker["q"] = -1
    red_worker["r"] = -3
    
    # Teleport Blue worker away from its nest to make it free
    blue_worker = next(u for u in state.units if u["owner"] == "blue")
    blue_worker["q"] = 0
    blue_worker["r"] = -3
    
    # Block expansions for Blue:
    from games.colony_hex.logic import get_distance
    blocked_cells = []
    for c in state.map:
        if c["owner"] is None and c["terrain"] != "rock":
            adjacent_to_blue = any(
                owned["owner"] == "blue" and get_distance(c["q"], c["r"], owned["q"], owned["r"]) == 1
                for owned in state.map
            )
            if adjacent_to_blue:
                c["owner"] = "red"
                blocked_cells.append(c)
                
    # End Red's turn to hand it to Blue
    state.execute_action("red", {"kind": "end_turn"})
    
    # Blue starts with 5 leaves + 3 owned cells = 8 leaves.
    # Nest (0, -4) is free, and there is an adjacent threat (Red worker at -1, -3).
    # Since expansions are blocked, Blue will recruit a soldier (cost 5).
    # Then it has 1 action left. It will attack the adjacent Red worker at (-1, -3)!
    state.run_ai_turn()
    
    # Verify Blue recruited a soldier on nest (0, -4) and it then attacked Red worker at (-1, -3)
    blue_soldier = next((u for u in state.units if u["owner"] == "blue" and u["type"] == "soldier"), None)
    assert blue_soldier is not None
    
    # Red worker should be dead (removed from units)
    assert red_worker not in state.units
    # Blue soldier moved to (-1, -3)
    assert blue_soldier["q"] == -1 and blue_soldier["r"] == -3
    
    # Clean up blocked cells
    for c in blocked_cells:
        c["owner"] = None
        
    # Now test AI soldier moving towards enemy nest
    # End Red's turn to hand it to Blue
    state.execute_action("red", {"kind": "end_turn"})
    
    # Set Blue leaves to 0 so it cannot recruit or expand
    state.players[1]["leaves"] = 0
    
    # Run AI turn. Blue should move its soldier closer to Red's nest at (-4, 0).
    # Initially soldier is at (-1, -3).
    # It should make 2 moves: (-1, -3) -> (-2, -2) -> (-3, -1)
    state.run_ai_turn()
    
    # Verify Blue soldier is at (-3, -1)
    assert blue_soldier["q"] == -3 and blue_soldier["r"] == -1











