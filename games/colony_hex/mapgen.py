from typing import List, Dict, Any

NEST_COORDS = [(-4, 0), (0, -4), (4, 0), (0, 4)]
ROCK_COORDS = {(1, 1), (-1, -1), (2, -2), (-2, 2)}
LEAF_COORDS = {(-2, 1), (2, -1), (1, -2), (-1, 2)}

def generate_map(nests_count: int) -> List[Dict[str, Any]]:
    cells = []
    for q in range(-4, 5):
        for r in range(-4, 5):
            if abs(-q - r) <= 4:
                coord = (q, r)
                terrain = "plain"
                if coord in ROCK_COORDS:
                    terrain = "rock"
                elif coord in LEAF_COORDS:
                    terrain = "leaf"
                cells.append({
                    "q": q,
                    "r": r,
                    "terrain": terrain,
                    "owner": None
                })
    return cells
