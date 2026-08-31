# Tower Defense Gameplay & Feature Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the full suite of gameplay improvements for Ant Defense: WebAudio procedural sound synthesizer, targeting priorities, wave preview, pause control, 2 active player spells (Acid Strike & Frost Nova), Level 4 branching tower specializations, and highscore ranking.

**Architecture:** 
- `games/tower_defense/logic.py`: core game logic extensions (targeting engine, spell cooldown/cast engine, L4 branching stats, time_scale pause, wave preview serialization).
- `games/tower_defense/routes.py`: WebSocket message handlers (`set_target_mode`, `cast_spell`, `upgrade_tower` with branch) and REST endpoints for `/tower-defense/highscores`.
- `games/tower_defense/static/index.html`: WebAudio `SoundSystem`, spell UI buttons with cooldown indicators + targeting cursor, tower panel controls (targeting selector + L4 branch choices), pause button, and wave preview banner.

**Tech Stack:** Python 3.11+, FastAPI (REST + WebSocket), Pytest, Vanilla JavaScript (HTML5 Canvas 2D + Web Audio API).

## Global Constraints

- Do NOT use external `.mp3` or `.wav` sound files. Audio MUST be 100% procedurally synthesized via Web Audio API oscillators/noise/gain nodes.
- Maintain backwards compatibility: existing endpoints and routes (`/play/tower_defense`, `/tower-defense/play`, `/play/ant_defense`) MUST continue functioning seamlessly.
- State is held in-memory (per documented single-worker architecture).
- All unit tests MUST reside in `games/tower_defense/test_tower_defense_logic.py` and integration tests in `tests/test_tower_defense_integration.py`.
- Run only the target pytest commands. Do not run global linters.

---

### Task 1: Backend Logic — Targeting Priorities, Pause & Wave Preview (`logic.py`)

**Files:**
- Modify: `games/tower_defense/logic.py`
- Test: `games/tower_defense/test_tower_defense_logic.py`

**Interfaces:**
- `Tower.target_mode: str = "first"` (options: `"first"`, `"last"`, `"strongest"`, `"weakest"`, `"closest"`)
- `TowerDefenseGame.set_target_mode(tower_id: str, mode: str) -> Tuple[bool, str]`
- `TowerDefenseGame.set_time_scale(scale: int) -> Tuple[bool, str]` (supports `scale in (0, 1, 2, 4)`)
- `GameState.next_wave: Optional[Dict[str, Any]]` serialized in `get_state()`

- [ ] **Step 1: Write failing tests for targeting, pause, and wave preview**

Add to `games/tower_defense/test_tower_defense_logic.py`:

```python
def test_target_modes_first_last_strongest_weakest():
    game = TowerDefenseGame()
    # Place an archer at (5, 4)
    success, _, tower = game.place_tower(4, 4, TowerType.ARCHER)
    assert success is True
    
    # Spawn 3 enemies with varying distance_traveled and hp
    e_near_exit = Enemy(id="e1", enemy_type=EnemyType.FLY, x=4.0, y=4.5, hp=20, max_hp=20, speed=1.0, base_speed=1.0, reward=5, distance_traveled=100.0)
    e_strong = Enemy(id="e2", enemy_type=EnemyType.TANK, x=4.0, y=4.2, hp=200, max_hp=200, speed=1.0, base_speed=1.0, reward=10, distance_traveled=50.0)
    e_weak = Enemy(id="e3", enemy_type=EnemyType.SPRINTER, x=4.0, y=4.1, hp=5, max_hp=5, speed=1.0, base_speed=1.0, reward=2, distance_traveled=20.0)
    game.enemies = [e_near_exit, e_strong, e_weak]

    # Mode: FIRST (highest distance_traveled -> e1)
    game.set_target_mode(tower.id, "first")
    targets = game._find_targets(tower)
    assert targets[0].id == "e1"

    # Mode: LAST (lowest distance_traveled -> e3)
    game.set_target_mode(tower.id, "last")
    targets = game._find_targets(tower)
    assert targets[0].id == "e3"

    # Mode: STRONGEST (highest hp -> e2)
    game.set_target_mode(tower.id, "strongest")
    targets = game._find_targets(tower)
    assert targets[0].id == "e2"

    # Mode: WEAKEST (lowest hp -> e3)
    game.set_target_mode(tower.id, "weakest")
    targets = game._find_targets(tower)
    assert targets[0].id == "e3"


def test_pause_time_scale():
    game = TowerDefenseGame()
    ok, msg = game.set_time_scale(0)
    assert ok is True
    assert game.state.time_scale == 0
    
    # Update with dt should not advance enemies when paused
    enemy = Enemy(id="e1", enemy_type=EnemyType.FLY, x=1.0, y=1.0, hp=20, max_hp=20, speed=2.0, base_speed=2.0, reward=5)
    game.enemies = [enemy]
    game.update(0.1)
    assert enemy.x == 1.0  # did not move


def test_wave_preview_in_state():
    game = TowerDefenseGame()
    state = game.get_state()
    assert "next_wave_preview" in state["state"]
    assert state["state"]["next_wave_preview"]["wave_number"] == 1
    assert len(state["state"]["next_wave_preview"]["enemies"]) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest games/tower_defense/test_tower_defense_logic.py::test_target_modes_first_last_strongest_weakest -q`
Expected: FAIL.

- [ ] **Step 3: Implement targeting priorities, pause & wave preview in `logic.py`**

1. In `Tower` dataclass:
   - Add field `target_mode: str = "first"`
   - Add `"target_mode": self.target_mode` in `to_dict()`.
2. In `_find_targets(tower)`:
   - Collect all enemies in range.
   - Sort based on `tower.target_mode`:
     - `"first"`: `key=lambda e: -e.distance_traveled`
     - `"last"`: `key=lambda e: e.distance_traveled`
     - `"strongest"`: `key=lambda e: -e.hp`
     - `"weakest"`: `key=lambda e: e.hp`
     - `"closest"`: `key=lambda e: math.sqrt((tower.x - e.x)**2 + (tower.y - e.y)**2)`
3. Implement `set_target_mode(self, tower_id: str, mode: str) -> Tuple[bool, str]`:
   - Validate `mode in ("first", "last", "strongest", "weakest", "closest")`.
   - Update `tower.target_mode = mode`.
4. In `set_time_scale(self, scale: int)`:
   - Allow `scale in (0, 1, 2, 4)`.
   - If `scale == 0`: `f"Game paused"` else `f"Speed set to {scale}x"`.
5. In `get_state()`:
   - Calculate `next_wave_preview`: if `self.state.current_wave < self.state.total_waves`, get wave config for next wave index, returning dict `{ "wave_number": next_wave, "bonus": cfg.bonus, "enemies": [{ "type": etype.value, "count": count }] }`.

- [ ] **Step 4: Run tests to verify all pass**

Run: `venv/bin/pytest games/tower_defense/test_tower_defense_logic.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add games/tower_defense/logic.py games/tower_defense/test_tower_defense_logic.py
git commit -m "feat(tower_defense): implement targeting priorities, pause time_scale, and wave preview"
```

---

### Task 2: Backend Logic — Active Spells & L4 Branching Specializations (`logic.py`)

**Files:**
- Modify: `games/tower_defense/logic.py`
- Test: `games/tower_defense/test_tower_defense_logic.py`

**Interfaces:**
- `Tower.branch: Optional[str] = None`
- `MAX_TOWER_LEVEL = 4`
- `TowerDefenseGame.cast_spell(spell: str, x: float = 0.0, y: float = 0.0) -> Tuple[bool, str, Dict[str, Any]]`
- `TowerDefenseGame.upgrade_tower(tower_id: str, branch: Optional[str] = None) -> Tuple[bool, str]`

- [ ] **Step 1: Write failing tests for Active Spells and L4 Branches**

Add to `games/tower_defense/test_tower_defense_logic.py`:

```python
def test_active_spells_acid_strike_and_frost_nova():
    game = TowerDefenseGame()
    # Spawn enemies
    e1 = Enemy(id="e1", enemy_type=EnemyType.FLY, x=5.0, y=5.0, hp=100, max_hp=100, speed=2.0, base_speed=2.0, reward=5)
    e2 = Enemy(id="e2", enemy_type=EnemyType.FLY, x=20.0, y=20.0, hp=100, max_hp=100, speed=2.0, base_speed=2.0, reward=5)
    game.enemies = [e1, e2]

    # Cast Acid Strike at (5, 5)
    ok, msg, data = game.cast_spell("acid_strike", 5.0, 5.0)
    assert ok is True
    assert e1.hp == 0 or e1.hp < 100  # Took damage
    assert e2.hp == 100  # Out of range

    # Cooldown is active; casting again must fail
    ok2, _, _ = game.cast_spell("acid_strike", 5.0, 5.0)
    assert ok2 is False

    # Cast Frost Nova
    ok_frost, _, _ = game.cast_spell("frost_nova")
    assert ok_frost is True
    assert e2.slowed is True
    assert e2.speed < e2.base_speed


def test_tower_l4_branching_upgrades():
    game = TowerDefenseGame()
    game.state.crystals = 1000
    ok, _, tower = game.place_tower(4, 4, TowerType.ARCHER)
    
    # Upgrade to L2, L3
    game.upgrade_tower(tower.id)
    assert tower.level == 2
    game.upgrade_tower(tower.id)
    assert tower.level == 3

    # Upgrade to L4 without specifying branch should fail or require branch
    # Branch A: sniper
    ok, msg = game.upgrade_tower(tower.id, branch="sniper")
    assert ok is True
    assert tower.level == 4
    assert tower.branch == "sniper"
    assert tower.range >= 4.0  # Sniper has huge range
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest games/tower_defense/test_tower_defense_logic.py::test_active_spells_acid_strike_and_frost_nova -q`
Expected: FAIL.

- [ ] **Step 3: Implement Active Spells & L4 Branching in `logic.py`**

1. Define L4 Stats in `TOWER_STATS` with branches:
   - `archer`: L4 `sniper` (`damage: (75, 110)`, `speed: 1.8`, `range: 4.5`, `cost: 160`) and `gatling` (`damage: (8, 12)`, `speed: 0.18`, `range: 2.8`, `cost: 160`).
   - `bomb`: L4 `toxic_mortar` (`damage: (50, 75)`, `speed: 2.2`, `range: 3.0`, `aoe: 2.0`, `cost: 180`) and `plasma_cannon` (`damage: (90, 140)`, `speed: 2.8`, `range: 2.6`, `aoe: 2.6`, `cost: 180`).
   - `ice`: L4 `blizzard` (`damage: (10, 10)`, `speed: 0.5`, `range: 3.0`, `aura: True`, `cost: 150`) and `permafrost` (`damage: (25, 40)`, `speed: 1.5`, `range: 3.0`, `slow_factor: 0.15`, `cost: 150`).
2. Add `branch: Optional[str] = None` to `Tower`, update `MAX_TOWER_LEVEL = 4`.
3. In `upgrade_tower(tower_id, branch=None)`:
   - If `tower.level == 3`, require `branch in VALID_BRANCHES[tower.tower_type]`. Set `tower.branch = branch`.
4. Spell system:
   - Track `self.spell_cooldowns = {"acid_strike": 0.0, "frost_nova": 0.0}`.
   - Implement `cast_spell(self, spell: str, x: float = 0.0, y: float = 0.0)`:
     - Check cooldown.
     - `acid_strike`: deal 120 damage to all enemies within 2.5 cells of `(x, y)`. Set cooldown = 40.0s.
     - `frost_nova`: apply 70% slow for 5.0s to all current enemies. Set cooldown = 60.0s.
   - In `update(dt)`: decrement spell cooldowns by `scaled_dt`.
   - In `get_state()`: return `spells` with remaining cooldowns.

- [ ] **Step 4: Run tests to verify all pass**

Run: `venv/bin/pytest games/tower_defense/test_tower_defense_logic.py -q`
Expected: PASS (all tests pass).

- [ ] **Step 5: Commit**

```bash
git add games/tower_defense/logic.py games/tower_defense/test_tower_defense_logic.py
git commit -m "feat(tower_defense): implement 2 active player spells and L4 branching tower specializations"
```

---

### Task 3: Backend API & WebSocket Routes (`routes.py`)

**Files:**
- Modify: `games/tower_defense/routes.py`
- Test: `tests/test_tower_defense_integration.py`

**Interfaces:**
- WS command handlers: `set_target_mode`, `cast_spell`, `upgrade_tower` with `branch`.
- REST endpoints: `GET /tower-defense/highscores` and `POST /tower-defense/highscores`.

- [ ] **Step 1: Write integration tests for new commands and highscore endpoints**

Add to `tests/test_tower_defense_integration.py`:

```python
@pytest.mark.asyncio
async def test_tower_defense_highscores_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Get default highscores
        resp = await ac.get("/tower-defense/highscores?difficulty=normal")
        assert resp.status_code == 200
        scores = resp.json()
        assert isinstance(scores, list)
        
        # Post new score
        payload = {"name": "HERO_ANT", "score": 25000, "difficulty": "normal", "waves_cleared": 15, "victory": True}
        post_resp = await ac.post("/tower-defense/highscores", json=payload)
        assert post_resp.status_code == 200
        assert post_resp.json()["status"] == "success"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/test_tower_defense_integration.py -k test_tower_defense_highscores_api -q`
Expected: FAIL (404 Not Found).

- [ ] **Step 3: Implement WS commands and HighScores in `routes.py`**

1. Create `TowerDefenseHighScoreManager` class with in-memory scores per difficulty (Easy, Normal, Hard, Insane).
2. Add routes:
   - `GET /tower-defense/highscores`
   - `POST /tower-defense/highscores`
3. In `websocket_endpoint` command parser:
   - Handle `set_target_mode`: `game.set_target_mode(data["tower_id"], data["target_mode"])`.
   - Handle `cast_spell`: `game.cast_spell(data["spell"], data.get("x", 0.0), data.get("y", 0.0))`.
   - Update `upgrade_tower`: accept `branch=data.get("branch")`.

- [ ] **Step 4: Run integration tests**

Run: `venv/bin/pytest tests/test_tower_defense_integration.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add games/tower_defense/routes.py tests/test_tower_defense_integration.py
git commit -m "feat(tower_defense): add highscore API and WS handlers for targeting, spells, and L4 upgrades"
```

---

### Task 4: Frontend WebAudio Sound Synthesizer & Sound FX (`index.html`)

**Files:**
- Modify: `games/tower_defense/static/index.html`

- [ ] **Step 1: Implement `SoundSystem` in JavaScript**

Create procedural audio synthesizer using `AudioContext`:
- `playShootArcher()`, `playShootBomb()`, `playShootIce()`, `playSpellAcid()`, `playSpellFrost()`, `playWaveStart()`, `playWaveClear()`, `playGameOver()`, `playTowerPlace()`.
- Add Mute button `🔊 / 🔇` with `localStorage` state.

- [ ] **Step 2: Connect audio triggers to game events**

- Call sound methods on:
  - Tower placement
  - Projectiles firing / exploding
  - Spells cast
  - Wave start / wave completion
  - Victory / Defeat

- [ ] **Step 3: Verify no JS console errors**

---

### Task 5: Frontend UI Controls & Canvas Overlays (`index.html`)

**Files:**
- Modify: `games/tower_defense/static/index.html`

- [ ] **Step 1: Implement Pause button & Wave Preview Banner**
  - Add Pause button `⏸️` in time controls; spacebar toggles pause (`speed 0`).
  - Add Wave Preview card displaying incoming enemy icons & count before wave starts.

- [ ] **Step 2: Implement Spell Buttons & AoE Targeting**
  - Add 2 buttons on bottom panel: `💥 Chuva de Ácido [Q]` and `❄️ Névoa Congelante [E]`.
  - Show radial cooldown countdown on buttons.
  - Clicking Acid Strike activates green AoE reticle on canvas to choose target location.

- [ ] **Step 3: Implement Targeting Priority Selector & L4 Branch Upgrades**
  - In Tower Info Panel: add pill buttons for `Primeiro`, `Último`, `Mais Forte`, `Mais Fraco`, `Mais Próximo`.
  - When Tower is Level 3: show 2 distinct upgrade branch buttons (e.g. `[Sniper]` vs `[Gatling]`) with stats preview.

- [ ] **Step 4: Implement Highscores Modal**
  - Highscores button in header + submission prompt on Victory / Game Over.

- [ ] **Step 5: Full verification & Commit**

```bash
git add games/tower_defense/static/index.html
git commit -m "feat(tower_defense): add WebAudio sound synthesizer, spell controls, targeting UI, and L4 upgrade branches"
```

---

### Task 6: Full Suite Verification & Polish

- [ ] **Step 1: Run full pytest suite**

Run: `venv/bin/pytest -q`
Expected: 100% pass across all tests.

- [ ] **Step 2: Commit any final cleanup**
