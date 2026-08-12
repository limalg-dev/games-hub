import pytest
from games.colony_hex.mapgen import generate_map

def test_generate_map_structure():
    hex_map = generate_map(4)
    assert len(hex_map) == 61
    for cell in hex_map:
        assert "q" in cell
        assert "r" in cell
        assert cell["terrain"] in ("plain", "leaf", "rock")
        assert cell["owner"] is None
        # Coords constraint: q + r + s = 0 where s = -q-r
        s = -cell["q"] - cell["r"]
        assert max(abs(cell["q"]), abs(cell["r"]), abs(s)) <= 4

def test_fixed_terrain_features():
    hex_map = generate_map(4)
    rocks = {(c["q"], c["r"]) for c in hex_map if c["terrain"] == "rock"}
    assert (1, 1) in rocks
    assert (-1, -1) in rocks
    assert (2, -2) in rocks
    assert (-2, 2) in rocks

    leaves = {(c["q"], c["r"]) for c in hex_map if c["terrain"] == "leaf"}
    assert (-2, 1) in leaves
    assert (2, -1) in leaves
