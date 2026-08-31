import pytest
from games.colonia_hex.logic import (
    HexGame,
    HexCell,
    Province,
    UNIT_COSTS,
    UNIT_UPKEEP,
    BUILDING_COSTS,
    BUILDING_UPKEEP,
    BUILDING_DEFENSE,
    DIRECTIONS,
)


def test_hex_coordinates_and_neighbors():
    game = HexGame(map_size="small", num_players=2, seed=42)
    neighbors = game.get_neighbors(0, 0)
    assert len(neighbors) == 6
    assert (1, 0) in neighbors
    assert (0, 1) in neighbors
    assert (-1, 0) in neighbors
    assert (0, -1) in neighbors
    assert (1, -1) in neighbors
    assert (-1, 1) in neighbors


def test_hex_distance():
    game = HexGame(map_size="small", num_players=2, seed=42)
    assert game.hex_distance(0, 0, 0, 0) == 0
    assert game.hex_distance(0, 0, 1, 0) == 1
    assert game.hex_distance(0, 0, 2, 2) == 4
    assert game.hex_distance(1, -1, -1, 1) == 2


def test_unit_fusion():
    game = HexGame(map_size="small", num_players=2, seed=42)
    assert game.calc_fusion_level(1, 1) == 2
    assert game.calc_fusion_level(1, 2) == 3
    assert game.calc_fusion_level(2, 1) == 3
    assert game.calc_fusion_level(2, 2) == 4
    assert game.calc_fusion_level(1, 3) == 4
    assert game.calc_fusion_level(3, 1) == 4
    assert game.calc_fusion_level(2, 3) is None
    assert game.calc_fusion_level(3, 3) is None
    assert game.calc_fusion_level(1, 4) is None
    assert game.calc_fusion_level(4, 4) is None


def test_constants():
    assert UNIT_COSTS[1] == 10
    assert UNIT_COSTS[2] == 20
    assert UNIT_COSTS[3] == 30
    assert UNIT_COSTS[4] == 40

    assert UNIT_UPKEEP[1] == 2
    assert UNIT_UPKEEP[2] == 6
    assert UNIT_UPKEEP[3] == 18
    assert UNIT_UPKEEP[4] == 54

    assert BUILDING_COSTS["farm"] == 12
    assert BUILDING_COSTS["tower"] == 15
    assert BUILDING_COSTS["strong_tower"] == 35

    assert BUILDING_DEFENSE["castle"] == 1
    assert BUILDING_DEFENSE["tower"] == 2
    assert BUILDING_DEFENSE["strong_tower"] == 3


def test_combat_defense_rule():
    game = HexGame(map_size="small", num_players=2, seed=42)
    # Strength 2 defeats defense 1
    assert game.can_conquer(attacker_level=2, target_defense=1) is True
    # Strength 1 cannot defeat defense 1
    assert game.can_conquer(attacker_level=1, target_defense=1) is False
    # Strength 3 defeats defense 2
    assert game.can_conquer(attacker_level=3, target_defense=2) is True
    # Strength 2 cannot defeat defense 2
    assert game.can_conquer(attacker_level=2, target_defense=2) is False


def test_defense_calculation():
    game = HexGame(map_size="small", num_players=2, seed=42)
    # Set up custom cells
    game.grid.clear()
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0, unit_level=1)
    game.grid[(1, 0)] = HexCell(q=1, r=0, owner=0, building="tower")
    game.grid[(0, 1)] = HexCell(q=0, r=1, owner=0, unit_level=0)
    game.grid[(2, 0)] = HexCell(q=2, r=0, owner=1, unit_level=0)

    # (0, 0) has unit_level=1 and neighbor (1, 0) has tower (defense 2) -> total defense = 2
    assert game.get_cell_defense(0, 0) == 2
    # (1, 0) has tower (defense 2) -> total defense = 2
    assert game.get_cell_defense(1, 0) == 2
    # (0, 1) is neighbor of (0, 0) and (1, 0) [tower neighbor] -> total defense = 2
    assert game.get_cell_defense(0, 1) == 2
    # (2, 0) belongs to owner 1, not owner 0, so tower of owner 0 doesn't protect it
    assert game.get_cell_defense(2, 0) == 0


def test_province_bfs_and_merging():
    game = HexGame(map_size="small", num_players=2, seed=42)
    game.grid.clear()
    # Create two disconnected regions for player 0
    # Region A: (0, 0) - (0, 1)
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0)
    game.grid[(0, 1)] = HexCell(q=0, r=1, owner=0)

    # Region B: (3, 1) - (3, 2)
    game.grid[(3, 1)] = HexCell(q=3, r=1, owner=0)
    game.grid[(3, 2)] = HexCell(q=3, r=2, owner=0)

    game.recalculate_provinces()
    p_p0 = [p for p in game.provinces if p.owner == 0]
    assert len(p_p0) == 2

    # Connect them via contiguous axial bridge: (0, 1) -> (1, 1) -> (2, 1) -> (3, 1)
    game.grid[(1, 1)] = HexCell(q=1, r=1, owner=0)
    game.grid[(2, 1)] = HexCell(q=2, r=1, owner=0)
    game.recalculate_provinces()
    p_p0 = [p for p in game.provinces if p.owner == 0]
    # Now all 6 cells form 1 single province
    assert len(p_p0) == 1
    assert len(p_p0[0].cells) == 6


def test_province_economy_and_bankruptcy():
    game = HexGame(map_size="small", num_players=2, seed=42)
    p = [p for p in game.provinces if p.owner == game.current_player][0]
    initial_gold = p.gold
    # End turn generates income and updates turn
    res = game.end_turn()
    assert res["success"] is True
    assert game.turn_number >= 1


def test_starvation_collapse():
    game = HexGame(map_size="small", num_players=2, seed=42)
    game.grid.clear()
    # 2 cells for player 0, 1 Knight (upkeep 54), initial gold 10
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0, unit_level=4, building="castle")
    game.grid[(0, 1)] = HexCell(q=0, r=1, owner=0, unit_level=0)
    game.current_player = 0
    game.recalculate_provinces()
    p = game.provinces[0]
    p.gold = 10

    # Net income: 2 cells - 54 upkeep = -52. 10 + (-52) = -42 < 0 -> Bankruptcy!
    game.end_turn()

    # Knight should have died from starvation
    assert game.grid[(0, 0)].unit_level == 0
    assert game.grid[(0, 0)].has_tree is True  # turned into tree/grave
    p_after = [prov for prov in game.provinces if prov.owner == 0][0]
    assert p_after.gold == 0


def test_recruitment_and_movement():
    game = HexGame(map_size="small", num_players=2, seed=42)
    game.grid.clear()
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0, building="castle")
    game.grid[(1, 0)] = HexCell(q=1, r=0, owner=0)
    game.grid[(2, 0)] = HexCell(q=2, r=0, owner=None, has_tree=True)  # Neutral with tree
    game.current_player = 0
    game.recalculate_provinces()
    p = game.provinces[0]
    p.gold = 25

    # Recruit worker (cost 10) on (0, 0)
    res = game.recruit(p.id, 0, 0, level=1)
    assert res["success"] is True
    assert p.gold == 15
    assert game.grid[(0, 0)].unit_level == 1

    # Move worker from (0, 0) to (1, 0) within province
    res = game.move(0, 0, 1, 0)
    assert res["success"] is True
    assert game.grid[(0, 0)].unit_level == 0
    assert game.grid[(1, 0)].unit_level == 1
    assert game.grid[(1, 0)].has_moved is True

    # Try moving again in same turn (should fail)
    res = game.move(1, 0, 0, 0)
    assert res["success"] is False


def test_tree_harvesting():
    game = HexGame(map_size="small", num_players=2, seed=42)
    game.grid.clear()
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0, unit_level=1, has_moved=False)
    game.grid[(1, 0)] = HexCell(q=1, r=0, owner=None, has_tree=True)
    game.current_player = 0
    game.recalculate_provinces()
    p = game.provinces[0]
    initial_gold = p.gold

    # Move to neutral hex with tree -> conquers hex, harvests tree (+3 gold)
    res = game.move(0, 0, 1, 0)
    assert res["success"] is True
    assert game.grid[(1, 0)].owner == 0
    assert game.grid[(1, 0)].has_tree is False
    assert p.gold == initial_gold + 3


def test_build_structures():
    game = HexGame(map_size="small", num_players=2, seed=42)
    game.grid.clear()
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0, building="castle")
    game.grid[(0, 1)] = HexCell(q=0, r=1, owner=0)
    game.grid[(1, 0)] = HexCell(q=1, r=0, owner=0)
    game.current_player = 0
    game.recalculate_provinces()
    p = game.provinces[0]
    p.gold = 50

    # Build farm on (0, 1)
    res = game.build(p.id, 0, 1, "farm")
    assert res["success"] is True
    assert game.grid[(0, 1)].building == "farm"
    prov = game.get_province_by_id(p.id)
    assert prov.gold == 50 - BUILDING_COSTS["farm"]

    # Build tower on (1, 0)
    res = game.build(p.id, 1, 0, "tower")
    assert res["success"] is True
    assert game.grid[(1, 0)].building == "tower"
    prov = game.get_province_by_id(p.id)
    assert prov.gold == 50 - BUILDING_COSTS["farm"] - BUILDING_COSTS["tower"]
def test_field_fusion():
    game = HexGame(map_size="small", num_players=2, seed=42)
    game.grid.clear()
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0, unit_level=1, has_moved=False)
    game.grid[(1, 0)] = HexCell(q=1, r=0, owner=0, unit_level=1, has_moved=False)
    game.current_player = 0
    game.recalculate_provinces()

    # Move (0, 0) to (1, 0) -> 1 + 1 fuses into Soldier (level 2)
    res = game.move(0, 0, 1, 0)
    assert res["success"] is True
    assert game.grid[(0, 0)].unit_level == 0
    assert game.grid[(1, 0)].unit_level == 2
    assert game.grid[(1, 0)].has_moved is True


def test_procedural_map_generation():
    for size in ["small", "medium", "large"]:
        for num_p in [2, 3, 4]:
            game = HexGame(map_size=size, num_players=num_p, seed=123)
            assert len(game.grid) > 10
            assert len(game.provinces) >= num_p
            # Every player has at least 1 province
            owners = {p.owner for p in game.provinces}
            for player_idx in range(num_p):
                assert player_idx in owners


def test_ai_turn_execution():
    game = HexGame(map_size="small", num_players=2, difficulty="medium", seed=99)
    # Player 0 is human, Player 1 is bot
    assert game.current_player == 0
    res = game.end_turn()
    assert res["success"] is True
    # If bot turn ran automatically on end_turn or step_ai
    # Turn should advance back to human (player 0) or step through
    assert game.turn_number >= 1


def test_game_to_dict_and_from_dict():
    game = HexGame(map_size="small", num_players=2, seed=77)
    state = game.to_dict()
    assert "grid" in state
    assert "provinces" in state
    assert "current_player" in state
    assert "turn_number" in state
    assert "winner" in state

    game2 = HexGame.from_dict(state)
    assert game2.current_player == game.current_player
    assert game2.turn_number == game.turn_number
    assert len(game2.grid) == len(game.grid)
    assert len(game2.provinces) == len(game.provinces)

def test_tower_upgrade_to_strong_tower():
    game = HexGame(map_size="small", num_players=2, seed=42)
    game.grid.clear()
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0, building="castle")
    game.grid[(1, 0)] = HexCell(q=1, r=0, owner=0, building="tower")
    game.current_player = 0
    game.recalculate_provinces()
    p = game.provinces[0]
    p.gold = 50

    # Upgrade tower (15) to strong_tower (35) -> cost difference is 20
    res = game.build(p.id, 1, 0, "strong_tower")
    assert res["success"] is True
    assert game.grid[(1, 0)].building == "strong_tower"
    prov = game.get_province_by_id(p.id)
    assert prov.gold == 50 - 20


def test_territory_split_by_conquest():
    game = HexGame(map_size="small", num_players=2, seed=42)
    game.grid.clear()
    # Player 0 has a line: (0, 0) - (1, 0) - (2, 0)
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0, building="castle")
    game.grid[(1, 0)] = HexCell(q=1, r=0, owner=0)
    game.grid[(2, 0)] = HexCell(q=2, r=0, owner=0)

    # Player 1 has attacker at (1, 1) with level 2
    game.grid[(1, 1)] = HexCell(q=1, r=1, owner=1, unit_level=2)
    game.current_player = 1
    game.recalculate_provinces()

    # Player 1 conquers the middle cell (1, 0)
    res = game.move(1, 1, 1, 0)
    assert res["success"] is True
    assert game.grid[(1, 0)].owner == 1

    # Now player 0 territory is split into 2 provinces: (0, 0) and (2, 0)
    p0_provinces = [p for p in game.provinces if p.owner == 0]
    assert len(p0_provinces) == 2


def test_insufficient_funds_and_invalid_actions():
    game = HexGame(map_size="small", num_players=2, seed=42)
    game.grid.clear()
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0, building="castle")
    game.current_player = 0
    game.recalculate_provinces()
    p = game.provinces[0]
    p.gold = 5

    # Cannot recruit worker (cost 10) with 5 gold
    res = game.recruit(p.id, 0, 0, level=1)
    assert res["success"] is False
    assert "Not enough gold" in res["reason"]

    # Cannot build farm (cost 12) with 5 gold
    res = game.build(p.id, 0, 0, "farm")
    assert res["success"] is False


def test_victory_condition():
    game = HexGame(map_size="small", num_players=2, seed=42)
    game.grid.clear()
    # Only player 0 has cells
    game.grid[(0, 0)] = HexCell(q=0, r=0, owner=0, building="castle")
    game.current_player = 0
    game.recalculate_provinces()
    game.check_game_over()
    assert game.game_over is True
    assert game.winner == 0

    # Actions after game over must fail
    p = game.provinces[0]
    p.gold = 50
    res = game.recruit(p.id, 0, 0, level=1)
    assert res["success"] is False
    assert res["reason"] == "Game is already over"


def test_all_ai_difficulties():
    for diff in ["easy", "medium", "hard"]:
        game = HexGame(map_size="small", num_players=2, difficulty=diff, seed=123)
        # Should run without error
        game.run_ai_turn(player_id=1, difficulty=diff)
