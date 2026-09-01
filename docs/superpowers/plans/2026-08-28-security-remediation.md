# Security Audit Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remediate all 10 vulnerabilities identified in the security audit report (`docs/security-audit/relatorio-auditoria-seguranca.pdf`): eliminate Stored XSS across all frontend clients and backend APIs, enforce IP validation, add HTTP defense headers (CSP, X-Frame-Options, nosniff), validate default credentials on startup, protect `/api/words`, and secure session deletion.

**Architecture:** Two decoupled workstreams:
- **Workstream A (Backend: Agent 1):** IP validation in `boletos.py`, security headers middleware in `main.py`, HTML escaping & validation on `POST /api/words`, highscore name sanitization in Bomberman/TD/Hex routes, snake session token guard, and startup checks.
- **Workstream B (Frontend: Agent 2):** DOM hardening (replacing dangerous `innerHTML` concatenations with `textContent` / `document.createElement` / `escapeHTML`) across `boletos.html`, `crossword/board.js`, `bomberman/game.js`, `tower_defense/index.html`, and `colonia_hex/index.html`.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, Pytest, Vanilla JavaScript.

---

## WORKSTREAM A — BACKEND HARDENING (Owner: Agent 1)

### Task A1: IP Validation & Startup Secret Guard (`app/boletos.py`, `app/main.py`)

**Files:**
- Modify: `app/boletos.py`
- Modify: `app/main.py`
- Test: `tests/test_security_remediation.py` (create)

- [ ] **Step 1: Write test for IP validation and secret warnings**

```python
import ipaddress
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_x_forwarded_for_sanitized_ip():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Malicious IP header
        headers = {"X-Forwarded-For": "<script>alert(1)</script>"}
        resp = await ac.post("/boletos/api/login", json={"username": "bad", "password": "bad"}, headers=headers)
        # Should not crash and should record a fallback/safe IP, not raw payload
```

- [ ] **Step 2: Implement IP validation in `app/boletos.py`**
In `_get_client_ip(request: Request) -> str`:
```python
import ipaddress

def _get_client_ip(request: Request) -> str:
    raw_ip = ""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        candidate = forwarded.split(",")[0].strip()
        try:
            ipaddress.ip_address(candidate)
            raw_ip = candidate
        except ValueError:
            raw_ip = "invalido"
    elif request.client and request.client.host:
        try:
            ipaddress.ip_address(request.client.host)
            raw_ip = request.client.host
        except ValueError:
            raw_ip = "desconhecido"
    return raw_ip or "desconhecido"
```

- [ ] **Step 3: Add Startup Secret Warning in `app/main.py` lifespan**
If `os.getenv("ENVIRONMENT") == "production"` and `os.getenv("BOLETOS_PASS") in ("change-me", "123456secreta", None)`:
Log a high-severity security warning at startup.

---

### Task A2: Security HTTP Headers Middleware (`app/main.py`)

**Files:**
- Modify: `app/main.py`
- Test: `tests/test_security_remediation.py`

- [ ] **Step 1: Write test for security headers**

```python
@pytest.mark.asyncio
async def test_security_headers_present():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/")
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert "Content-Security-Policy" in resp.headers
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
```

- [ ] **Step 2: Update middleware in `app/main.py`**

Add headers:
- `X-Frame-Options = "DENY"`
- `X-Content-Type-Options = "nosniff"`
- `Referrer-Policy = "strict-origin-when-cross-origin"`
- `Content-Security-Policy = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data:; connect-src 'self' ws: wss:;"`

---

### Task A3: Backend Sanitization for Words & Highscores (`app/main.py`, `games/*/routes.py`)

**Files:**
- Modify: `app/main.py` (`create_word`)
- Modify: `games/bomberman/routes.py`
- Modify: `games/tower_defense/routes.py`
- Modify: `games/colonia_hex/routes.py`
- Modify: `games/snake/routes.py`

- [ ] **Step 1: Sanitize and validate `POST /api/words`**
In `app/main.py:138`:
- `import html`
- `clean_word = html.escape(word_in.word.strip()[:30])`
- `clean_hint = html.escape(word_in.hint.strip()[:100])`
- Validate non-empty.

- [ ] **Step 2: Sanitize Highscore names across all game routers**
In `bomberman/routes.py`, `tower_defense/routes.py`, `colonia_hex/routes.py`:
- Sanitize player name using `html.escape(name.strip()[:15])`.

- [ ] **Step 3: Secure Snake DELETE endpoint (`games/snake/routes.py`)**
Ensure `DELETE /snake/{game_id}` validates game existence and handles safely.

- [ ] **Step 4: Commit Workstream A**

```bash
git add app/boletos.py app/main.py games/ tests/test_security_remediation.py
git commit -m "feat(security): implement backend IP validation, security headers, word sanitization, and highscore protection"
```

---

## WORKSTREAM B — FRONTEND XSS REMEDIATION & DOM HARDENING (Owner: Agent 2)

### Task B1: Boletos Logs DOM Hardening (`static/boletos.html`)

**Files:**
- Modify: `static/boletos.html`

- [ ] **Step 1: Replace innerHTML with textContent / DOM methods in `renderLogs`**
In `static/boletos.html:407-410`:
Use `document.createElement('div')`, create spans and set `.textContent = l.ip`, `.textContent = l.action`, `.textContent = l.details`, `.textContent = l.timestamp`.

---

### Task B2: Crossword Clues DOM Hardening (`games/crossword/static/board.js`)

**Files:**
- Modify: `games/crossword/static/board.js`

- [ ] **Step 1: Safe rendering of clues in `renderClues`**
In `games/crossword/static/board.js:117,131`:
Instead of raw template literal in `innerHTML`, create `li`, set dataset attributes, create `span.clue-number` with `.textContent = clue.number`, `span.clue-text` with `.textContent = clue.clue`, and append to `acrossList` / `downList`.

---

### Task B3: Highscore Tables DOM Hardening (`bomberman`, `tower_defense`, `colonia_hex`)

**Files:**
- Modify: `games/bomberman/static/game.js`
- Modify: `games/tower_defense/static/index.html`
- Modify: `games/colonia_hex/static/index.html`

- [ ] **Step 1: Implement or use `escapeHTML` helper in all three frontends**
Add helper:
```javascript
function escapeHTML(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
```
Apply to all highscore name renders (`s.name`).

- [ ] **Step 2: Commit Workstream B**

```bash
git add static/boletos.html games/crossword/static/board.js games/bomberman/static/game.js games/tower_defense/static/index.html games/colonia_hex/static/index.html
git commit -m "feat(security): eliminate Stored XSS in boletos logs, crossword clues, and highscore tables"
```

---

## Task 6: Full Suite Verification

- [ ] **Step 1: Run full pytest suite**
Run: `venv/bin/pytest -q`
Expected: 100% pass.
