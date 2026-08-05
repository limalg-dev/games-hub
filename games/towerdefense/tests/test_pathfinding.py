from games.towerdefense.pathfinding import astar

def test_astar_finds_path():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    path = astar(grid, (0, 0), (4, 4))
    assert path is not None
    assert len(path) > 0
    assert path[0] == (0, 0)
    assert path[-1] == (4, 4)

def test_astar_no_path():
    grid = [
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0],
    ]
    path = astar(grid, (0, 0), (0, 4))
    assert path is None

def test_astar_straight_line():
    grid = [[0, 0, 0, 0, 0]]
    path = astar(grid, (0, 0), (0, 4))
    assert path == [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]

def test_astar_start_equals_end():
    grid = [[0, 0], [0, 0]]
    path = astar(grid, (0, 0), (0, 0))
    assert path == [(0, 0)]

def test_astar_around_obstacle():
    grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    path = astar(grid, (0, 0), (2, 2))
    assert path is not None
    assert len(path) == 5
