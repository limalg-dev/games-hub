# Boletos Decouple + Dependency Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the optional `boletos` PDF feature unable to break the platform or the game test suite when its dependency (`reportlab`) is absent, remove the hardcoded credential literal, and re-sync the venv with the declared dependencies.

**Architecture:** `app/main.py` currently imports `boletos_router` unconditionally at module scope (`app/main.py:19`), so a missing `reportlab` raises `ModuleNotFoundError` while importing `app.main` — which every game test does. We move the boletos wiring behind a small, testable helper that swallows `ModuleNotFoundError` and registers the router only when its dependency is importable. Credentials become environment-overridable with the current values kept as defaults so the live instance keeps working.

**Tech Stack:** Python 3.11+, FastAPI, pytest + httpx (ASGITransport / TestClient), reportlab (optional runtime dep of boletos only).

## Global Constraints

- Python version floor: `>=3.11` (from `pyproject.toml`).
- Dependency pins are exact and MUST stay in sync across `requirements.txt`, `requirements-prod.txt`, and `pyproject.toml`: `fastapi==0.115`, `uvicorn[standard]==0.30`, `sqlmodel==0.0.21`, `reportlab==5.0.1`, `pytest==8.2`, `pytest-asyncio==1.4.0`, `httpx==0.27`.
- No login/auth/accounts is the platform default; boletos is an off-product test feature and MUST NOT gain platform status (no game card, no `/play/*` entry).
- New games ship as self-contained modules; do NOT extend the legacy 2-color WebSocket `ConnectionManager`. (Not touched here; stated so the implementer does not "improve" it.)
- UI copy standardizes to Portuguese. (No UI copy changes in this plan.)
- Tests MUST be deterministic and full-suite-safe (each test that touches the DB already resets `SQLModel.metadata` per existing fixtures — follow that pattern).

---

### Task 1: Make the boletos router optional in `app/main.py`

**Files:**
- Modify: `app/main.py:19` (remove the unconditional `from app.boletos import router as boletos_router`) and `app/main.py:51-52` (the `app.include_router(boletos_router)` block)
- Test: `tests/test_boletos_optional.py` (create)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `app.main._include_optional_boletos(app: FastAPI) -> bool` — attempts `from app.boletos import router`; on `ModuleNotFoundError` returns `False` without registering anything; on success calls `app.include_router(router)` and returns `True`. Later tasks and tests rely on this exact name and signature.

- [ ] **Step 1: Write the failing test**

Create `tests/test_boletos_optional.py`:

```python
import sys
import pytest
from fastapi import FastAPI

import app.main as main


def test_include_optional_boletos_registers_when_dependency_present():
    fresh = FastAPI()
    assert main._include_optional_boletos(fresh) is True
    paths = {route.path for route in fresh.routes}
    assert "/boletos/api/login" in paths


def test_include_optional_boletos_skips_when_module_unimportable(monkeypatch):
    # Setting the sys.modules entry to None forces `import app.boletos`
    # to raise ImportError (documented CPython behavior), simulating a
    # missing optional dependency like reportlab.
    monkeypatch.setitem(sys.modules, "app.boletos", None)
    fresh = FastAPI()
    assert main._include_optional_boletos(fresh) is False
    paths = {route.path for route in fresh.routes}
    assert not any(p.startswith("/boletos") for p in paths)


def test_app_module_imports_without_boletos(monkeypatch):
    # Importing app.main must never fail because boletos is unavailable.
    monkeypatch.setitem(sys.modules, "app.boletos", None)
    import importlib
    reloaded = importlib.reload(main)
    assert hasattr(reloaded, "app")
    # restore a clean module for later tests in the session
    importlib.reload(reloaded)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_boletos_optional.py -v`
Expected: FAIL — `AttributeError: module 'app.main' has no attribute '_include_optional_boletos'`.

- [ ] **Step 3: Write minimal implementation**

In `app/main.py`, delete line 19 (`from app.boletos import router as boletos_router`).

Replace the boletos include block (currently `app/main.py:51-52`):

```python
# Include Boletos test routes
app.include_router(boletos_router)
```

with a helper defined before the include calls and invoked in place:

```python
def _include_optional_boletos(app: FastAPI) -> bool:
    """Register the optional boletos test router.

    Boletos is an off-product PDF test feature whose only heavy dependency
    (reportlab) is optional. A missing dependency must degrade gracefully:
    the platform and its game test suite must still import and run.
    Returns True when the router was registered, False otherwise.
    """
    try:
        from app.boletos import router as boletos_router
    except ModuleNotFoundError:
        return False
    app.include_router(boletos_router)
    return True
```

Then, where the other routers are included, replace the deleted include with:

```python
# Include Boletos test routes (optional: skipped if reportlab is absent)
_include_optional_boletos(app)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_boletos_optional.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Run the full suite to confirm no regressions**

Run: `pytest -q`
Expected: all tests pass (baseline is 260 passed, 1 skipped with reportlab installed; boletos routes still registered so no existing behavior changes).

- [ ] **Step 6: Commit**

```bash
git add app/main.py tests/test_boletos_optional.py
git commit -m "fix: make boletos router optional so missing reportlab can't break the platform"
```

---

### Task 2: Make boletos credentials environment-overridable

**Files:**
- Modify: `app/boletos.py:8-15` (imports — add `import os`) and `app/boletos.py:29-30` (the `TEST_USER` / `TEST_PASS` literals)
- Test: `tests/test_boletos_optional.py` (add one test)

**Interfaces:**
- Consumes: nothing.
- Produces: `app.boletos.TEST_USER` and `app.boletos.TEST_PASS` module attributes read from `BOLETOS_USER` / `BOLETOS_PASS` env vars at import time, defaulting to `"user-boleto"` and `"change-me"` respectively.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_boletos_optional.py`:

```python
def test_boletos_credentials_default_and_override(monkeypatch):
    import importlib
    import app.boletos as boletos

    # Defaults when env unset.
    monkeypatch.delenv("BOLETOS_USER", raising=False)
    monkeypatch.delenv("BOLETOS_PASS", raising=False)
    reloaded = importlib.reload(boletos)
    assert reloaded.TEST_USER == "user-boleto"
    assert reloaded.TEST_PASS == "change-me"

    # Env override wins.
    monkeypatch.setenv("BOLETOS_USER", "alice")
    monkeypatch.setenv("BOLETOS_PASS", "s3cr3t")
    reloaded = importlib.reload(boletos)
    assert reloaded.TEST_USER == "alice"
    assert reloaded.TEST_PASS == "s3cr3t"

    # Restore module defaults for the rest of the session.
    monkeypatch.delenv("BOLETOS_USER", raising=False)
    monkeypatch.delenv("BOLETOS_PASS", raising=False)
    importlib.reload(boletos)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_boletos_optional.py::test_boletos_credentials_default_and_override -v`
Expected: FAIL — `assert 'change-me' == '123456secreta'` (current hardcoded value) or an env-override assertion failure.

- [ ] **Step 3: Write minimal implementation**

In `app/boletos.py`, add `import os` to the stdlib import block (near line 10, alongside `import io` / `import random`).

Replace lines 29-30:

```python
TEST_USER = "user-boleto"
TEST_PASS = "123456secreta"
```

with:

```python
TEST_USER = os.getenv("BOLETOS_USER", "user-boleto")
TEST_PASS = os.getenv("BOLETOS_PASS", "change-me")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_boletos_optional.py::test_boletos_credentials_default_and_override -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `pytest -q`
Expected: all pass (the `login` route at `app/boletos.py:412-419` still reads `TEST_USER`/`TEST_PASS`, now sourced from env with defaults).

- [ ] **Step 6: Commit**

```bash
git add app/boletos.py tests/test_boletos_optional.py
git commit -m "fix: source boletos test credentials from env vars, drop hardcoded password"
```

---

### Task 3: Re-sync the virtualenv with declared dependencies

**Files:**
- No source changes. This task reconciles the running environment with `requirements.txt`.
- Verify: `requirements.txt`, `requirements-prod.txt`, `pyproject.toml` (read-only confirmation the pins already match; no edits expected).

**Interfaces:**
- Consumes: the guard from Task 1 (so the suite is green even before reportlab is present).
- Produces: nothing for later tasks; this is the environment-integrity gate.

- [ ] **Step 1: Confirm the pins are already consistent (no edit)**

Run: `grep -nE "reportlab|pytest-asyncio" requirements.txt requirements-prod.txt pyproject.toml`
Expected: `reportlab==5.0.1` in `requirements.txt`, `requirements-prod.txt`, `pyproject.toml`; `pytest-asyncio==1.4.0` in `requirements.txt` and `pyproject.toml`. If any diverge, align them to these exact values and commit separately.

- [ ] **Step 2: Reproduce the clean-env failure mode (evidence)**

Run: `venv/bin/python -c "import app.main; print('imports OK')"`
Expected AFTER Task 1: `imports OK` even if reportlab were absent. (If reportlab is currently installed, uninstall in a scratch check only if you want to observe the guard: `pip uninstall -y reportlab` then rerun the import, then reinstall in Step 3. Optional.)

- [ ] **Step 3: Install/sync all declared dependencies**

Run:
```bash
source venv/bin/activate
pip install -r requirements.txt
```
Expected: `reportlab-5.0.1` present and `pytest-asyncio` upgraded to `1.4.0`.

- [ ] **Step 4: Verify environment matches declarations**

Run: `pip list | grep -iE "reportlab|pytest-asyncio|fastapi|sqlmodel|httpx|uvicorn"`
Expected: `reportlab 5.0.1`, `pytest-asyncio 1.4.0`, `fastapi 0.115.0`, `sqlmodel 0.0.21`, `httpx 0.27.0`.

- [ ] **Step 5: Run the full suite on the synced environment**

Run: `pytest -q`
Expected: all pass (target: 263 passed / 1 skipped — the prior 260 passed/1 skipped plus the 3 new boletos-optional tests and 1 credentials test; adjust the exact count to what the suite reports).

- [ ] **Step 6: Commit any pin reconciliation (only if Step 1 required edits)**

```bash
git add requirements.txt requirements-prod.txt pyproject.toml
git commit -m "chore: reconcile dependency pins (reportlab, pytest-asyncio)"
```

---

## Out of Scope (explicitly not corrected here)

- **pytest-asyncio deprecation warnings** on Python 3.14 (`asyncio.get_event_loop_policy` deprecated). These are upstream warnings, already partially filtered in `pyproject.toml` `filterwarnings`; not a defect in this codebase. No fix planned.
- **Removing boletos entirely.** Rejected in favor of decoupling (user decision 2026-08-28). Revisit only if boletos is confirmed dead.
- **Fictional metrics** in `static/games.js` (`plays`, `rating`). Product-copy concern, not a correction.

## Self-Review

- **Spec coverage:** Root cause (unconditional boletos import → whole suite dies on missing reportlab) → Task 1. Secondary defect (hardcoded credential literal) → Task 2. Environment/pin divergence (reportlab uninstalled; pytest-asyncio 0.24.0 vs declared 1.4.0) → Task 3. All three diagnosed causes are covered.
- **Placeholder scan:** No TBD/TODO; every code step shows exact content and exact file:line anchors.
- **Type consistency:** `_include_optional_boletos(app: FastAPI) -> bool` is defined in Task 1 and consumed by the Task 1 tests; `TEST_USER`/`TEST_PASS` attrs defined in Task 2 and asserted in the Task 2 test. Names consistent across tasks.
