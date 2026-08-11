# Colônia Hex — Design Spec

## Overview

Add a turn-based light 4X strategy game to GameHub: **Colônia Hex** (ant colonies expand territory on a hexagonal map, collect leaves, and fight for dominance).

| Constraint | Choice |
|------------|--------|
| Genre | Territory + economy (4X light) |
| Theme | Ants / insects (shared universe with Ant Defense) |
| Players | 2–4 (online WebSocket, hotseat, or AI fill) |
| Match length | ~10–20 minutes (~20 turns) |
| Platform fit | Self-contained module under `games/colony_hex/`, same pattern as Snake / Ant Defense |

**Out of MVP (YAGNI):** tech tree, fog of war, diplomacy, procedural multi-map set, global leaderboard, chat, long-lived DB persistence of full replays.

---

## Goals

1. Fill the hub gap for multiplayer strategy beyond 1v1 checkers and real-time tower defense.
2. Keep rules teachable in under a minute; sessions fit casual `/play` usage.
3. Server is source of truth; all actions validated server-side.
4. Reuse GameHub conventions: FastAPI router, static play page, in-memory active games, pytest for logic.

---

## Architecture

Do **not** extend the legacy `app/websocket.py` ConnectionManager (2-color checkers/crossword only). Colony Hex gets its own router and connection map, like Ant Defense / Snake.

```
games/colony_hex/
  __init__.py
  logic.py          # GameState, rules, combat, win
  mapgen.py         # Fixed hex layout (axial coords)
  routes.py         # REST create/join/list + WebSocket
  static/
    index.html      # Served at /play/colony_hex
    board.js        # Hex canvas render + input
    logic.js        # Lobby, HUD, hotseat, WS client
  tests/
    test_logic.py
    test_mapgen.py
```

**Platform wiring (`app/main.py`):**

- `include_router(colony_hex_router, prefix=...)` consistent with existing games (Ant Defense uses `/games`; Snake uses `/api` — prefer **`/games`** prefix and paths under `/games/colony_hex/...` for clarity).
- `GET /play/colony_hex` → `FileResponse` for `games/colony_hex/static/index.html` (or package `index.html` like Snake if preferred; static assets mounted via existing `games/*/static` loop).
- Landing card + play-url entry for `colony_hex`.

**Runtime:**

```
Client(s)  --WS JSON-->  routes.py  -->  logic.GameState (memory)
                              |
                              +--> optional AI greedy after human turn
```

Persistence: in-memory `active_games` dict only for MVP (same as Ant Defense). Optional later: snapshot JSON on `Game` row if platform game table is reused.

---

## Game rules (MVP)

### Map

- Axial hex coordinates `(q, r)`.
- Fixed layout: **hexagon of radius 4** (61 cells). No alternate map shapes in MVP.
- Terrain:
  - `plain` — claimable
  - `leaf` — claimable; cosmetic only (same income as plain)
  - `rock` — blocked, never claimable
- **4 nest positions** near opposite edges/corners for seats 0–3. With 2–3 players, only assigned seats spawn nests; unused nest hexes become plain.

### Players

- Seats: `red`, `blue`, `green`, `yellow` (max 4).
- Each player: `leaves`, `alive`, `is_ai`, `nest {q,r}`.
- Start: **10 leaves**, **1 worker** on nest hex; nest hex owned by player.

### Turn structure

1. **Income** at turn start: **1 leaf per owned hex** (including nest).
2. **Action budget:** **2 actions** per turn.
3. Actions (each costs **1 action**; `end_turn` costs all remaining actions):
   - **Expand** — claim empty non-rock hex that **shares an edge with a hex you already own**; cost **3 leaves**. No unit required on the border. Target must have no unit.
   - **Recruit** — spawn **worker** (2 leaves) or **soldier** (5 leaves) on your nest hex. Nest hex must be **empty** (no unit). One unit per hex everywhere.
   - **Move** — move own unit to an adjacent hex that is owned by you **or** empty claimable (plain/leaf with no owner). Empty hex entered by move does **not** auto-claim. Cannot enter rock, enemy-owned hex, or occupied hex.
   - **Attack** — only **soldiers**. Target adjacent hex:
     - **Enemy unit:** resolve combat — soldier always beats worker; soldier vs soldier → **attacker wins** (fast MVP, attacker advantage). Defender removed; attacker moves to target hex; **owner of hex = attacker**.
     - **Enemy-owned empty hex:** soldier moves in and claims.
     - If the captured hex is the defender’s **nest**, defender is eliminated (`alive=false`): all their units removed; their other hexes become neutral (`owner=null`).
   - **End turn** — set `actions_left = 0` and advance.
4. When `actions_left` hits 0 → next alive player; that player receives **income** then `actions_left = 2`. When the seat after the last player in the round would play, `turn_number += 1` first (or equivalently: increment round when turn wraps to seat 0).
5. **max_turns = 20**. After the last player finishes their turn on turn 20, compute ranking and set `status=finished`.

### Units

| Type | Recruit cost | Role |
|------|--------------|------|
| Worker | 2 leaves | Presence for adjacency; no attack |
| Soldier | 5 leaves | Attack / capture |

Only **one unit per hex**.

### Victory

1. **Elimination:** when only one player has `alive=true`, that player wins immediately (`game_over`).
2. **Domination (turn limit):** highest score = `(owned_hex_count * 10) + leaves`. Tie-break: more soldiers, then more workers, then lower seat index.

### AI (MVP)

Greedy priority each action:

1. Attack adjacent enemy if soldier available and profitable (enemy worker or empty enemy hex).
2. Expand to empty adjacent if leaves ≥ 3.
3. Recruit soldier if any adjacent threat and leaves ≥ 5; else recruit worker if leaves ≥ 2 and nest free.
4. Move soldier toward nearest enemy border.
5. End turn.

AI runs server-side when `is_ai` seat is current turn; broadcast state after each AI action or once per full AI turn (prefer **one broadcast per action** for spectators).

---

## Data model

```text
Hex:    { q, r, terrain: plain|leaf|rock, owner: color|null }
Unit:   { id, owner, type: worker|soldier, q, r }
Player: { id/seat, color, leaves, alive, is_ai, nest: {q,r} }
GameState: {
  id,
  status: lobby | active | finished,
  map: Hex[],
  units: Unit[],
  players: Player[],   # length 2–4
  turn_index,          # index into players
  turn_number,         # 1..max_turns
  max_turns: 20,
  actions_left: 0..2,
  winner: color|null,
  ranking: [{color, score, ...}]|null
}
```

Public `to_dict()` for REST/WS. No hidden info in MVP (full map visible).

---

## API & WebSocket

### REST

| Method | Path | Description |
|--------|------|-------------|
| POST | `/games/colony_hex` | Create lobby; body optional `{ max_players: 2..4, fill_ai: bool }` → `{ game_id, state }` |
| GET | `/games/colony_hex` | List active lobbies/games (id, status, seats) |
| GET | `/games/colony_hex/{id}` | Snapshot state |
| POST | `/games/colony_hex/{id}/start` | Optional REST mirror of WS `start` |

**Seat assignment:** on WebSocket connect only (no REST join in MVP). Host = first connected human. Start requires ≥2 participants counting AI seats marked `is_ai`.

### WebSocket `/games/colony_hex/ws/{game_id}`

**Server → Client**

| type | payload |
|------|---------|
| `welcome` | `{ seat/color, state }` |
| `state` | full `GameState` dict |
| `error` | `{ message }` |
| `game_over` | `{ winner, ranking, state }` |

**Client → Server**

| type | payload |
|------|---------|
| `start` | `{}` (host only, lobby) |
| `set_ai` | `{ seat, is_ai }` (host, lobby) |
| `action` | `{ kind: expand\|recruit\|move\|attack\|end_turn, q?, r?, to_q?, to_r?, unit_type? }` |
| `forfeit` | `{}` |

Validation: reject if not `active`, not your turn, illegal coords, insufficient leaves, etc. On success, apply, maybe run AI chain, broadcast `state` / `game_over`.

### Hotseat

Single client holds all human seats: UI shows current color; actions sent with server trusting seat = current turn (no extra auth). Optional client message `hotseat: true` at create so one connection drives all non-AI seats.

### Disconnect

- Lobby: free seat.
- Active: **60s** grace via `asyncio` deadline, then forfeit (`alive=false`, units removed, hexes `owner=null`). If implementation cost is high, immediate forfeit is acceptable fallback — document choice in code.

---

## Client UI

- **Lobby:** player slots, AI toggles, Start, shareable game id.
- **Board:** canvas hex grid; owned tint by color; units as emoji/icons (🐜 worker, 🗡️/🪖 soldier); rocks gray; nests marked.
- **HUD:** leaves, actions left, turn N/20, whose turn.
- **Input:** select unit → legal hex highlights → confirm action; toolbar for Recruit type / End turn.
- **Game over:** ranking modal + New game.

No shared SPA shell required if dedicated `/play/colony_hex` page (like Snake). Still add landing card linking to play URL.

---

## Testing

### Unit (`games/colony_hex/tests/`)

- Mapgen: nest count, no owner on rock, radius size.
- Income: leaves += owned count.
- Expand: cost, adjacency, rock blocked.
- Recruit: costs, nest occupancy.
- Move / Attack resolution matrix.
- Elimination on nest loss.
- Turn-limit scoring and ranking.
- Turn order skips dead players.

### Integration

- Create → connect 2 WS → start → one expand → state reflects owner/leaves.
- Illegal action returns `error` without mutation.

### Manual

- 4P hotseat smoke, 1H+AI, full 20-turn finish.

---

## Implementation order (for later plan)

1. `mapgen` + `logic` + unit tests (no HTTP).
2. `routes` REST + WS + AI hook.
3. Static board + lobby + HUD.
4. Wire `main.py` + landing card.
5. Smoke tests + README blurb.

---

## Security & performance

- No auth (platform default); rate-limit create later if needed.
- Cap concurrent colony games in memory (soft cap e.g. 100) optional.
- Messages: full state OK for ~61 hexes; keep JSON small (no replay log in MVP).

---

## Success criteria

- [ ] 2–4 players can finish a game in ≤20 minutes with only Expand/Recruit/Move/Attack/End.
- [ ] Illegal moves never desync clients (server authority).
- [ ] Hotseat and at least one AI opponent work without a second browser.
- [ ] Logic covered by pytest; playable at `/play/colony_hex`.

---

*Design approved in brainstorming session on 2026-08-11.*
