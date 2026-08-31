# Tower Defense Map & 3x Zoom Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul the map path and strategic build slots in `games/tower_defense/logic.py` for maximum tactical depth, and upgrade the camera zoom in `games/tower_defense/static/index.html` to support up to 3.0x (300%) zoom with smooth scaling.

**Architecture:**
- `games/tower_defense/logic.py`: updated Catmull-Rom waypoints and balanced 44 strategic build slots categorized into curve pockets, central gauntlet chokepoints, and last stand base slots.
- `games/tower_defense/test_tower_defense_logic.py`: tests verifying slot validity, path continuity, and terrain codes.
- `games/tower_defense/static/index.html`: `WorldCamera.maxZoom = 3.0`, refined zoom steps, and minimap bounds.

**Tech Stack:** Python 3.11+, Pytest, Vanilla JS / Canvas 2D.

---

### Task 1: Backend Map Geometry & Strategic Build Slots (`logic.py`)

**Files:**
- Modify: `games/tower_defense/logic.py`
- Test: `games/tower_defense/test_tower_defense_logic.py`

**Interfaces:**
- `TowerDefenseGame.BUILD_SLOT_LAYOUTS`: 44 strategic (x, y) coordinates.
- `TowerDefenseGame.OBSTACLE_LAYOUTS`: thematic obstacles.
- `TowerDefenseGame._generate_organic_path()`: refined Catmull-Rom path.

- [ ] **Step 1: Write tests for new map path and slot placements in `test_tower_defense_logic.py`**

Add/update in `games/tower_defense/test_tower_defense_logic.py`:

```python
def test_map_path_continuity_and_build_slots():
    game = TowerDefenseGame()
    assert len(game.path) > 30
    assert len(game.build_slots) >= 35

    # Check that every build slot is strictly on terrain type 1 and not on path (0) or obstacle (2)
    for bx, by in game.build_slots:
        assert game.terrain[by][bx] == 1
        assert (bx, by) not in game.path
        # Verify placement succeeds on build slot
        can_place, msg = game.can_place_tower(bx, by, TowerType.ARCHER)
        assert can_place is True or "crystals" in msg
```

- [ ] **Step 2: Run test to verify it passes/fails**

Run: `venv/bin/pytest games/tower_defense/test_tower_defense_logic.py -q`

- [ ] **Step 3: Implement new waypoints and 44 build slots in `logic.py`**

Update `_generate_organic_path` waypoints:
```python
        waypoints = [
            (-1.0, 4.0),   # Entry
            (4.0, 4.0),
            (9.0, 2.5),    # High Ridge
            (16.0, 3.0),
            (23.0, 4.5),   # Top Turn
            (27.0, 7.5),   # Drop
            (22.0, 9.5),   # Loop Alpha (Chokepoint)
            (13.0, 8.5),   # Westbound
            (6.0, 10.5),   # Drop
            (3.0, 14.0),   # Turn East
            (11.0, 14.0),  # Central Gauntlet
            (20.0, 13.5),
            (27.0, 15.5),  # East Turn
            (25.0, 19.0),  # Drop & Loop Back
            (17.0, 18.5),  # Westbound
            (8.0, 19.5),   # Lower Pocket
            (3.0, 22.0),   # Final Hairpin
            (12.0, 22.5),  # Base Approach
            (22.0, 22.0),  # Final Straight
            (28.0, 21.0),
            (31.0, 21.0),  # Anthill Colony Exit
        ]
```

Update `BUILD_SLOT_LAYOUTS` (44 tactical slots covering curve apexes, chokepoint dual-coverage, and base defense):
```python
    BUILD_SLOT_LAYOUTS = [
        # ── Zone 1: Entry & High Ridge (North) ──
        (2, 3), (4, 2), (6, 2), (9, 4), (11, 4), (14, 4), (16, 1), (18, 2),
        (21, 3), (24, 3), (25, 6), (28, 6),
        # ── Zone 2: Loop Alpha & Chokepoint (Mid-North) ──
        (25, 9), (21, 8), (17, 7), (13, 7), (10, 6), (8, 9), (5, 9),
        # ── Zone 3: Central Gauntlet (Dual-Coverage Corridor) ──
        (2, 12), (5, 12), (8, 12), (12, 12), (16, 12), (20, 11), (22, 12),
        (26, 13), (28, 14), (28, 17),
        # ── Zone 4: Lower Loop & Chokepoint Beta (Mid-South) ──
        (24, 17), (20, 17), (16, 16), (12, 17), (8, 17), (5, 18), (2, 20),
        # ── Zone 5: Last Stand & Anthill Base Perimeter (South) ──
        (5, 23), (8, 23), (12, 21), (15, 21), (18, 21), (21, 20), (25, 22), (27, 23),
    ]
```

Update `OBSTACLE_LAYOUTS`:
```python
    OBSTACLE_LAYOUTS = [
        (1, 1, 'pebble'), (12, 1, 'leaf'), (20, 1, 'twig'),
        (28, 3, 'moss'), (29, 9, 'water'),
        (16, 9, 'pebble'), (1, 8, 'twig'),
        (7, 14, 'leaf'), (15, 14, 'moss'),
        (1, 16, 'water'), (29, 18, 'pebble'),
        (12, 19, 'leaf'), (1, 23, 'twig'),
        (29, 23, 'water'), (18, 23, 'moss'),
    ]
```

- [ ] **Step 4: Run test suite**

Run: `venv/bin/pytest games/tower_defense/test_tower_defense_logic.py -q`
Expected: PASS (all tests pass).

- [ ] **Step 5: Commit**

```bash
git add games/tower_defense/logic.py games/tower_defense/test_tower_defense_logic.py
git commit -m "feat(tower_defense): overhaul map pathing and implement 44 strategic build slots"
```

---

### Task 2: Frontend Camera 3.0x Max Zoom & Visual Alignment (`index.html`)

**Files:**
- Modify: `games/tower_defense/static/index.html`

- [ ] **Step 1: Update `WorldCamera` in `index.html`**

In `WorldCamera` constructor:
- Set `this.maxZoom = 3.0;` (was 2.0).
- Set `this.minZoom = 0.35;` (was 0.3).
- In `zoomAt`: use factor `1.10` for smooth zooming.

- [ ] **Step 2: Verify minimap and range circles at 3.0x zoom**

- Minimap viewport indicator correctly bounds to viewport with 3.0x zoom.
- Zoom percentage indicator in HUD accurately displays up to `300%`.

- [ ] **Step 3: Commit**

```bash
git add games/tower_defense/static/index.html
git commit -m "feat(tower_defense): support up to 3.0x max zoom with smooth scaling"
```

---

### Task 3: Full Suite Verification

- [ ] **Step 1: Run entire test suite**

Run: `venv/bin/pytest -q`
Expected: 100% pass across all tests.
