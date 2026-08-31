# Super Bomberman Gameplay & Combat Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement SNES-grade game feel and combat mechanics for Super Bomberman: corner-assist navigation, dynamic bomb heartbeat pulse, chiptune BGM music generator, 3 tactical power-ups (Pierce, Punch, Skull), Revenge Cart mechanic, and custom match settings (Best of 1, 3, 5 rounds).

**Architecture:**
- `games/bomberman/logic.py`: backend power-up constants (`POWERUP_PIERCE=7`, `POWERUP_PUNCH=8`, `POWERUP_SKULL=9`) and procedural map generation distribution.
- `games/bomberman/static/audio.js`: procedural chiptune BGM synthesizer + new SFX for punch, curse, pierce.
- `games/bomberman/static/game.js`: corner-sliding algorithm, bomb pulsing & scorch marks, 3 new power-ups, Revenge Cart system, and match settings round logic.
- `games/bomberman/static/index.html` & `style.css`: BGM toggle button, punch action button, and match settings UI.

**Tech Stack:** Python 3.11+, FastAPI, Pytest, Vanilla JavaScript (Canvas 2D + Web Audio API).

## Global Constraints

- Audio MUST be 100% procedurally synthesized in Web Audio API. Zero external `.mp3` or `.wav` files.
- All existing tests in `games/bomberman/tests/` and `tests/` MUST pass without regressions.
- No project-wide linters/formatters.

---

### Task 1: Backend Power-up Constants & Map Generator (`logic.py`)

**Files:**
- Modify: `games/bomberman/logic.py`
- Test: `games/bomberman/tests/test_logic.py`

**Interfaces:**
- `POWERUP_PIERCE = 7`, `POWERUP_PUNCH = 8`, `POWERUP_SKULL = 9`
- `generate_map()` includes all 9 power-up types in its generation pool.

- [ ] **Step 1: Write test for new powerup types in `test_logic.py`**

Add to `games/bomberman/tests/test_logic.py`:

```python
def test_all_powerup_types_defined_and_generated():
    from games.bomberman.logic import (
        POWERUP_NONE, POWERUP_BOMB, POWERUP_FIRE, POWERUP_SPEED,
        POWERUP_KICK, POWERUP_SHIELD, POWERUP_REMOTE,
        POWERUP_PIERCE, POWERUP_PUNCH, POWERUP_SKULL,
        generate_map
    )
    assert POWERUP_PIERCE == 7
    assert POWERUP_PUNCH == 8
    assert POWERUP_SKULL == 9

    # Generate maps and verify powerup pool works
    m = generate_map(seed=42)
    assert "powerups" in m
    assert len(m["powerups"]) == 13
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest games/bomberman/tests/test_logic.py -q`
Expected: FAIL (ImportError for POWERUP_PIERCE).

- [ ] **Step 3: Implement new power-ups in `logic.py`**

In `games/bomberman/logic.py`:
1. Add constants:
```python
POWERUP_PIERCE = 7   # Pierce Bomb (destroys whole line of crates)
POWERUP_PUNCH = 8    # Boxing Glove (punches bombs over walls)
POWERUP_SKULL = 9    # Curse (10s chaos status effect)
```
2. Update `powerup_pool` inside `generate_map`:
```python
    powerup_pool = [
        POWERUP_BOMB, POWERUP_BOMB,
        POWERUP_FIRE, POWERUP_FIRE,
        POWERUP_SPEED, POWERUP_SPEED,
        POWERUP_KICK,
        POWERUP_SHIELD,
        POWERUP_REMOTE,
        POWERUP_PIERCE,
        POWERUP_PUNCH,
        POWERUP_SKULL,
    ]
```

- [ ] **Step 4: Run tests to verify pass**

Run: `venv/bin/pytest games/bomberman/tests/ -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add games/bomberman/logic.py games/bomberman/tests/test_logic.py
git commit -m "feat(bomberman): add Pierce, Punch, and Skull powerup definitions and map pool"
```

---

### Task 2: Chiptune BGM Generator & Extended SFX (`audio.js`)

**Files:**
- Modify: `games/bomberman/static/audio.js`

- [ ] **Step 1: Implement `ChiptuneBGM` class in `audio.js`**

Add chiptune 8-bit BGM synthesizer:
- 16-step looping arcade melody (Square wave oscillator at 135 BPM with low-pass filter).
- Walking bassline (Triangle wave).
- Snare/hi-hat white noise pulses.
- `startBGM()`, `stopBGM()`, `toggleBGM()`.
- Add SFX: `playPunch()`, `playCurse()`, `playPierce()`.

- [ ] **Step 2: Test audio methods in browser context**

---

### Task 3: Corner-Assistance Navigation & Bomb Heartbeat Pulse (`game.js`)

**Files:**
- Modify: `games/bomberman/static/game.js`

- [ ] **Step 1: Implement Corner-Assistance in `updatePlayerMovement`**

When player moves against an obstacle corner with an offset $\le 14\text{px}$ from tile center:
- Automatically slide the player towards the open corridor center.

- [ ] **Step 2: Implement Bomb Heartbeat Pulse & Scorch Marks**

In `drawBombs`:
- Calculate heartbeat pulse: `scale = 1.0 + 0.18 * Math.sin(t * (4 + (3 - fuse) * 3))`.
- Draw animated sparks on bomb fuse.
- Store explosion tiles in `this.scorchMarks` and render subtle fading dark marks.

---

### Task 4: Three New Tactical Power-ups (`game.js`)

**Files:**
- Modify: `games/bomberman/static/game.js`

- [ ] **Step 1: Implement Pierce Bomb (`PWR_PIERCE = 7`)**
  - Explosions continue through soft crates along the line instead of stopping at the first crate.

- [ ] **Step 2: Implement Boxing Glove Punch (`PWR_PUNCH = 8`)**
  - Key `[F]` or Punch button punches a bomb in front of the player, launching it 3 tiles forward over obstacles.

- [ ] **Step 3: Implement Skull Curse (`PWR_SKULL = 9`)**
  - 10-second random affliction: Inverted controls, Bomb diarrhea, 30% speed, or mini fire.
  - Floating status text + purple curse aura on player.

---

### Task 5: Revenge Cart & Match Format Settings (`game.js`, `index.html`, `style.css`)

**Files:**
- Modify: `games/bomberman/static/game.js`, `index.html`, `style.css`

- [ ] **Step 1: Implement Match Settings (Best of 1, 3, 5 rounds)**
  - Add match format selector buttons to start screen.
  - Track `roundWins` and display trophy icons in HUD.

- [ ] **Step 2: Implement Revenge Cart on Player Elimination**
  - In Battle Mode: player moves around the perimeter track and can launch bombs into the arena with `[Space]` (cooldown 4s).

- [ ] **Step 3: UI Buttons for Punch & BGM Toggle**
  - Add Punch button `[F]` on mobile/desktop HUD.
  - Add BGM toggle button `🎵 Música: ON/OFF`.

---

### Task 6: Full Suite Verification

- [ ] **Step 1: Run all tests**

Run: `venv/bin/pytest -q`
Expected: 100% pass across all tests.
