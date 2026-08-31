# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are casual, Portuguese-speaking players who open a browser and play a quick game without creating an account. They pick a game, choose difficulty, and play in under a minute. Multiplayer games additionally serve people who want to play with a friend by sharing a play link. Audience copy and community expectations are Portuguese.

## Product Purpose

GameHub is a free, no-login web game platform hosting a growing set of casual games: checkers (vs minimax AI or online), word search, crossword (solo or collaborative online), snake, tower defense (ant-themed), Super Bomberman, and Colônia Hex (turn-based hex territory strategy). Ant Defense and Tower Defense are the **same module** (`games/tower_defense/`); `/play/ant_defense` redirects to the unified tower defense page. Success means a visitor can see a game card, open it, and be playing without friction — and can bring a friend in via a shareable `/play/*` URL.

## Positioning

Free, no-login hub of classic casual games with a server-authoritative multiplayer twist: real-time checkers over WebSocket and a collaborative crossword where both players solve the same grid. Crosswords are generated dynamically on the server. The thing a neighboring clone could not truthfully copy is instant frictionless play plus genuine real-time multiplayer (WebSocket, server as source of truth) as the differentiator.

## Operating Context

Used entirely in a browser. Visitors land on a single-page hub with game cards and category tabs, open a game details modal, choose difficulty (and word-search category), and play; checkers and crossword optionally run over a WebSocket opened by the server. Shareable deep links: `/play/checkers`, `/play/wordsearch`, `/play/crossword`, `/play/snake`, `/play/ant_defense`, `/play/tower_defense`, `/play/bomberman`, `/play/colonia_hex` (legacy games use the shared SPA shell; snake/ant_defense/tower_defense/bomberman/colonia_hex use dedicated pages). Word search runs a client-side timer with a local leaderboard. Deployable via Docker (`docker-compose.yml`, `docker-compose.prod.yml`) and runnable locally with uvicorn.

## Capabilities and Constraints

Confirmed capabilities:

- Checkers: 8×8 English draughts, minimax AI with Easy/Medium/Hard, or two players over WebSocket (server-authoritative).
- Word search (Caça-Palavras): client-side grid, easy/medium/hard, multiple categories, timer, local high scores.
- Crossword (Palavras Cruzadas): server-generated via backtracking from a 150-word seeded dictionary (5 categories), solo or collaborative online over WebSocket, letter-by-letter server validation.
- Snake, Tower Defense / Ant Defense (same module, `games/tower_defense/`; `/play/ant_defense` redirects to `/play/tower_defense`), Super Bomberman, Colônia Hex: self-contained games with dedicated play pages and FastAPI routers.
Constraints and technical facts:

- Stack: Python 3.11+, FastAPI (REST + WebSocket), SQLModel, SQLite persistence (`games.db`), Uvicorn, pytest + httpx; vanilla frontend (shared SPA shell `static/` plus per-game static modules); Docker / docker-compose.
- No login, no auth, no accounts — platform default, repeatedly relied on by routes.
- Board/puzzle state held in memory by the connection manager; checkers AI runs synchronously inside the WebSocket event loop.
- Mixed-language copy today (landing tabs PT, checkers UI EN, word search/crossword PT). Standardize future UI copy to Portuguese.
- Public deployment URL: https://game.ofertasshow.shop.
- WebSocket protocol supports checkers (board/game_over messages) and crossword (init/update/game_over) only in the legacy shell; never extend the legacy 2-color ConnectionManager for new games.

## Brand Commitments

- Name: **GameHub** — confirmed, binding.
- Voice/personality: no explicit commitment beyond name; casual and free ("play classic board games online — free, no install").
- Ant/invasor universe shared between Tower Defense and Ant Defense (same module, design docs) — a durable theming thread to preserve.

## Evidence on Hand

- README.md: full feature + protocol + architecture documentation.
- `docs/archify/gamehub-runtime.architecture.html`: runtime architecture diagram (frontend, backend, security/trust boundaries).
- `games/tower_defense/DESIGN_DOC.md`: ant-themed tower defense design (mechanics, balance tables).
- `docs/superpowers/specs/`: design specs incl. Colônia Hex (2026-08-11), single-grid navigation (2026-08-11), word search, crossword, landing/play-tab improvements.
- `docs/superpowers/plans/`: implementation plans for the above.
- No testimonials, case studies, press, or third-party numbers exist; fictional play counts/ratings in `static/games.js` must not be treated as real usage evidence.

## Product Principles

1. Friction is the enemy — no login, no install, play gated behind one click.
2. Server is the source of truth for any multiplayer state; every move is validated server-side.
3. Ship a new game as a self-contained module (FastAPI router + own static page/tests), never extending the legacy WebSocket shell.
4. The hub discovers games through data (`static/games.js`), so a game is real when it has a card, a `/play/*` entry, and working logic.
5. Casual Portuguese-speaking players must understand the hub and the games without help; UI copy standardizes to Portuguese.