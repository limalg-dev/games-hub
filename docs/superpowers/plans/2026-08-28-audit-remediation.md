# Audit Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the real defects surfaced by the 2026-08-28 code audit (`Auditoria agent2`), make the 62 orphaned unit tests actually run, and correct/clarify the docs — without re-architecting the intentionally in-memory platform.

**Architecture:** Two disjoint workstreams. **Code** (agent1): a genuine global-PRNG bug in bomberman, 62 unit tests that pytest never collects because they are named `tests.py` (and collide on basename), plus a fragile HTML handler. **Docs** (agent2): README/PRODUCT drift. The multi-worker global-state findings are **not bugs** — in-memory state is a documented product design choice — so they are addressed by documenting the single-worker deployment constraint, not by adding Redis/locks.

**Tech Stack:** Python 3.11+, FastAPI, pytest 8.4.0 + pytest-asyncio 1.4.0, stdlib `random`.

## Global Constraints

- Do NOT re-architect in-memory state (no Redis, no DB for game sessions, no threading locks). PRODUCT.md: "Board/puzzle state held in memory by the connection manager" is intentional.
- Do NOT run project-wide linters/formatters. Run only the pytest commands specified.
- pytest default collection is `test_*.py`; unit-test modules MUST be named `test_*.py` with a unique basename across the repo.
- Current implementation is the source of truth for behavior/balance where a never-run test disagrees (integration tests that DO run agree with the code).
- Portuguese for user-facing copy; English acceptable in internal READMEs following existing file's language.

---

## WORKSTREAM A — CODE (owner: agent1)

### Task A1: Fix global-PRNG mutation in bomberman map generation

**Files:**
- Modify: `games/bomberman/logic.py:90-151` (function `generate_map`)
- Test: `games/bomberman/tests/test_logic.py` (existing package dir — add tests here)

**Interfaces:**
- Consumes: nothing.
- Produces: `generate_map(..., seed: Optional[int] = None)` unchanged signature; behavior change = deterministic per-call RNG that never touches the module-global `random` state.

Root cause: `games/bomberman/logic.py:90-91` calls `random.seed(seed)`, mutating the process-global PRNG. `seed` is client-reachable via `GET /api/bomberman/map?seed=` (`games/bomberman/routes.py:52`), so any request reseeds the global RNG, making all later `random.*` deterministic and corrupting concurrent requests.

- [ ] **Step 1: Write the failing test**

Add to `games/bomberman/tests/test_logic.py`:

```python
import random
from games.bomberman.logic import generate_map


def test_generate_map_is_deterministic_per_seed():
    a = generate_map(seed=123)
    b = generate_map(seed=123)
    assert a["grid"] == b["grid"]
    assert a["powerups"] == b["powerups"]


def test_generate_map_does_not_mutate_global_rng():
    random.seed(999)
    baseline = [random.random() for _ in range(3)]
    random.seed(999)
    generate_map(seed=42)  # must NOT consume/alter the global stream
    after = [random.random() for _ in range(3)]
    assert baseline == after
```

- [ ] **Step 2: Run and verify it fails**

Run: `venv/bin/pytest games/bomberman/tests/test_logic.py -q`
Expected: `test_generate_map_does_not_mutate_global_rng` FAILS (global stream consumed by the current `random.*` calls).

- [ ] **Step 3: Implement — use a local RNG instance**

In `games/bomberman/logic.py`, edit `generate_map`:

Replace lines 90-91:
```python
    if seed is not None:
        random.seed(seed)
```
with:
```python
    rng = random.Random(seed)
```

Then within the function replace the three module-global calls with the local `rng`:
- line 124: `if random.random() < crate_density:` → `if rng.random() < crate_density:`
- line 141: `random.shuffle(candidate_tiles)` → `rng.shuffle(candidate_tiles)`
- line 150: `if random.random() < 0.40:` → `if rng.random() < 0.40:`
- line 151: `powerup_map[r][c] = random.choice(powerup_pool)` → `powerup_map[r][c] = rng.choice(powerup_pool)`

(`random.Random(None)` seeds from OS entropy, so unseeded calls stay random.)

- [ ] **Step 4: Run and verify it passes**

Run: `venv/bin/pytest games/bomberman/tests/test_logic.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add games/bomberman/logic.py games/bomberman/tests/test_logic.py
git commit -m "fix(bomberman): use local RNG in generate_map to stop global PRNG mutation"
```

---

### Task A2: Make the snake unit tests discoverable

**Files:**
- Rename: `games/snake/tests.py` → `games/snake/test_snake_logic.py` (11 tests, all currently pass when run explicitly)

**Interfaces:** none.

- [ ] **Step 1: Confirm current pass state (explicit run)**

Run: `venv/bin/pytest games/snake/tests.py -q`
Expected: `11 passed`.

- [ ] **Step 2: Rename via git**

```bash
git mv games/snake/tests.py games/snake/test_snake_logic.py
```

- [ ] **Step 3: Verify collection + pass under default discovery**

Run: `venv/bin/pytest games/snake/test_snake_logic.py -q`
Expected: `11 passed`.

- [ ] **Step 4: Commit**

```bash
git add -A games/snake/
git commit -m "test(snake): rename tests.py to test_snake_logic.py so pytest collects it"
```

---

### Task A3: Make the tower_defense unit tests discoverable and fix 3 stale assertions

**Files:**
- Rename: `games/tower_defense/tests.py` → `games/tower_defense/test_tower_defense_logic.py` (51 tests; 48 pass, 3 stale)
- Modify: the 3 stale assertions in that file

**Interfaces:** none.

Context: three assertions drifted from the current (intended) implementation because the module never ran. The behavioral assertions in each already pass; only wording/balance literals are stale. Match the code.

- [ ] **Step 1: Rename via git**

```bash
git mv games/tower_defense/tests.py games/tower_defense/test_tower_defense_logic.py
```

- [ ] **Step 2: Run to see the 3 failures**

Run: `venv/bin/pytest games/tower_defense/test_tower_defense_logic.py -q`
Expected: `3 failed, 48 passed` — `test_place_tower_on_path_fails`, `test_place_tower_blocked_terrain`, `test_archer_stats`.

- [ ] **Step 3: Fix the 3 stale assertions to match current behavior**

In `games/tower_defense/test_tower_defense_logic.py`:

1. `test_place_tower_on_path_fails` — current message is `"obstructed by obstacle"`. Change the assertion:
```python
    assert "obstacle" in message.lower() or "obstáculo" in message.lower()
```
(keep the preceding `assert success is False` / `assert tower is None`).

2. `test_place_tower_blocked_terrain` — current message is `"no build slot here"`. Change the assertion:
```python
    assert "slot" in message.lower() or "build" in message.lower()
```

3. `test_archer_stats` — current archer range is `2.8`. Change:
```python
    assert tower.range == 2.8
```

- [ ] **Step 4: Run to verify all pass**

Run: `venv/bin/pytest games/tower_defense/test_tower_defense_logic.py -q`
Expected: `51 passed`.

- [ ] **Step 5: Commit**

```bash
git add -A games/tower_defense/
git commit -m "test(tower_defense): collect unit tests and align 3 stale assertions with current logic"
```

---

### Task A4: Harden tower_defense HTML handler

**Files:**
- Modify: `games/tower_defense/routes.py:407-421` (`play_tower_defense`)

**Interfaces:** none.

- [ ] **Step 1: Implement — use FileResponse with a clean fallback**

Replace the body of `play_tower_defense` (`games/tower_defense/routes.py:409-421`):
```python
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    return HTMLResponse(
        content="<h1>Tower Defense - Em Desenvolvimento</h1><p>Interface HTML ainda não disponível.</p>",
        status_code=200,
    )
```
(`FileResponse` and `HTMLResponse` are already imported at `games/tower_defense/routes.py:7`.)

- [ ] **Step 2: Verify the route still serves**

Run: `venv/bin/pytest tests/test_tower_defense_integration.py -q`
Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add games/tower_defense/routes.py
git commit -m "fix(tower_defense): serve index.html via FileResponse instead of manual open()"
```

---

### Task A5: Full-suite gate

- [ ] **Step 1: Run the entire suite (default discovery now includes the renamed modules)**

Run: `venv/bin/pytest -q`
Expected: previous 264 passed + 11 (snake) + 51 (tower_defense) + 2 (bomberman new) = ~328 passed, 1 skipped, 0 failed. Report the exact numbers.

- [ ] **Step 2: If any collision/error appears** (e.g. duplicate basename), STOP and report — do not delete tests to make it pass.

---

## WORKSTREAM B — DOCS (owner: agent2)

### Task B1: Update README.md to reflect all 6 games, endpoints, and structure

**Files:**
- Modify: `README.md`

**Interfaces:** none.

- [ ] **Step 1: Games intro** — extend the top list (currently Checkers/Word Search/Crossword) to include Snake, Tower Defense (ant-themed), and Super Bomberman, one line each, matching PRODUCT.md wording.

- [ ] **Step 2: Project Structure** — add `app/elo.py` (ELO rating system) and the `games/snake/`, `games/tower_defense/`, `games/bomberman/` module dirs (`logic.py`, `routes.py`, `tests`/`test_*_logic.py`, `static/`).

- [ ] **Step 3: API Endpoints table** — add the game routers' endpoints:
  - Bomberman: `GET /api/bomberman/info`, `GET /api/bomberman/stages`, `GET /api/bomberman/map`, `GET /api/bomberman/highscores`, `POST /api/bomberman/highscores`, `GET /play/bomberman`
  - Snake: `POST /api/snake/new`, `GET /api/snake/{id}`, `POST /api/snake/{id}/direction`, `POST /api/snake/{id}/update`, `POST /api/snake/{id}/pause`, `DELETE /api/snake/{id}`, `WS /api/ws/snake/{id}` (snake router mounted with `prefix=/api`)
  - Tower Defense: `POST /tower-defense/games/create`, `GET /tower-defense/games/{id}`, `POST /tower-defense/games/{id}/place-tower`, `GET /tower-defense/play`, `WS /tower-defense/ws/{id}`
  (Verify exact paths by reading `games/*/routes.py` before writing — do not guess.)

- [ ] **Step 4: Deployment constraint** — add a short "Deployment" note: the platform holds game/session state in memory (ConnectionManager, per-game `active_games` dicts, bomberman highscores), so it MUST run as a **single worker** (`uvicorn app.main:app` without `--workers N`); multiple workers fragment state and lose sessions on restart. This is by design; there is no shared store.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs(readme): document all 6 games, game endpoints, elo.py, single-worker constraint"
```

### Task B2: Clarify Ant Defense vs Tower Defense in PRODUCT.md

**Files:**
- Modify: `PRODUCT.md` (Capabilities section and any list treating them as separate games)

- [ ] **Step 1:** Add one clarifying clause where Ant Defense and Tower Defense are listed: they are the **same module** (`games/tower_defense/`); `/play/ant_defense` redirects to the unified tower_defense page (`app/main.py:78-85`). Keep the shared ant/invasor theming note.

- [ ] **Step 2: Commit**

```bash
git add PRODUCT.md
git commit -m "docs(product): clarify Ant Defense and Tower Defense are the same module"
```

---

## Explicitly NOT changed (design choices, not defects)

- **HighScoreManager thread-safety** (audit 3.2): FastAPI async routes share one event loop; `add_score` has no `await` between append and sort, so it is effectively atomic. No lock needed.
- **Global `active_games` / `game_websockets` / `ConnectionManager`** (audit 3.3/3.4): intentional in-memory design (PRODUCT.md). Addressed via the single-worker doc note (Task B1 Step 4), not re-architecture.
- **`app/main.py` relative paths** (audit 3.6): server is expected to run from project root; covered by the deployment note.
- **wordsearch unit tests** (audit 4.4): logic is client-side; API-level tests already exist in `tests/`.

## Self-Review

- **Coverage:** ALTA 3.1→A1, 4.1/4.2 (orphan tests)→A2/A3; BAIXA 3.5→A4; MÉDIA 5.1/5.2/5.3→B1; BAIXA 5.4→B2; MÉDIA 3.2/3.3/3.4 + BAIXA 3.6/4.4 → documented as design (B1 Step 4 + "NOT changed"). All audit rows accounted for.
- **Placeholder scan:** every code step has exact file:line and literal code; endpoint list flagged "verify before writing" because router paths must be read, not guessed.
- **Consistency:** renamed modules use unique basenames (`test_snake_logic.py`, `test_tower_defense_logic.py`); no collision with root `tests/`.
