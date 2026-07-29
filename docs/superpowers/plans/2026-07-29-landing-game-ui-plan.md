# Landing Page & Game UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the minimal index.html with a modern landing page (hero, game grid, detail modal) and an enhanced Checkers game UI (canvas board, animations, sidebar with captured pieces & move history).

**Architecture:** SPA-style single `index.html` with three sections (landing, modal, game view) toggled via `app.js`. Static files only — FastAPI serves `/` → `index.html` and `/static/*`. Game logic in `static/games/checkers/`.

**Tech Stack:** HTML5, CSS3 (Grid, Flexbox, Custom Properties), Vanilla ES6+ JS (Canvas API, WebSocket), FastAPI static files.

## Global Constraints
- Tag must be `games:latest`.
- Use existing `python:3.11-slim` base image for both Docker stages.
- Runtime command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- No additional OS packages unless required.
- Dark theme only (CSS variables ready for light).
- No external JS frameworks; vanilla ES6 modules.
- Responsive: mobile (375px), tablet (768px), desktop (1440px).
- Accessibility: ARIA labels, keyboard navigation, focus visible.

---

### Task 1: Create project structure and CSS variables

**Files:**
- Create: `static/styles.css`
- Create: `static/games/checkers/board.js`
- Create: `static/games/checkers/logic.js`
- Create: `static/games/checkers/preview.js`
- Modify: `static/index.html` (replace entirely)

**Interfaces:**
- Produces: File scaffold, CSS variables, empty module exports

- [ ] **Step 1: Create CSS variables file**
```css
/* static/styles.css */
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-card: #0f3460;
  --accent: #e94560;
  --accent-hover: #ff6b6b;
  --text-primary: #eaeaea;
  --text-secondary: #a0a0b0;
  --border: #2a2a4a;
  --gold: #ffd700;
  --wood-light: #f0d9b5;
  --wood-dark: #b58863;
  --piece-white: #ffffff;
  --piece-black: #1a1a1a;
  --shadow: 0 4px 24px rgba(0,0,0,0.4);
  --radius: 12px;
  --transition: 0.2s ease;
  --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-mono: "SF Mono", "Fira Code", monospace;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; font-family: var(--font-sans); background: var(--bg-primary); color: var(--text-primary); line-height: 1.5; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
button { font-family: inherit; cursor: pointer; border: none; background: none; color: inherit; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
```

- [ ] **Step 2: Create empty game modules**
```js
// static/games/checkers/logic.js
export const COLS = 8, ROWS = 8;
export const EMPTY = null;
export const COLORS = { WHITE: 'w', BLACK: 'b' };

export function createInitialBoard() { ... }
export function getLegalMoves(board, color) { ... }
export function applyMove(board, from, to) { ... }
export function isValidMove(board, from, to, color) { ... }
export function getPieceAt(board, pos) { ... }
export function algebraic(pos) { ... }
```

```js
// static/games/checkers/board.js
export function drawBoard(ctx, board, options = {}) { ... }
export function drawPiece(ctx, x, y, radius, color, isKing) { ... }
export function animateMove(ctx, board, from, to, onComplete) { ... }
export function highlightSquares(ctx, squares, color) { ... }
```

```js
// static/games/checkers/preview.js
import { createInitialBoard } from './logic.js';
import { drawBoard } from './board.js';
export function renderPreview(canvasId) { ... }
```

- [ ] **Step 3: Verify files exist and syntax is valid**
```bash
ls -la static/styles.css static/games/checkers/*.js
```

- [ ] **Step 4: Commit**
```bash
git add static/styles.css static/games/checkers/
git commit -m "feat: add CSS variables and game module scaffolds"
```

---

### Task 2: Build Landing Page HTML structure

**Files:**
- Modify: `static/index.html` (replace with full landing + modal + game view structure)

**Interfaces:**
- Consumes: CSS variables from Task 1
- Produces: Semantic HTML with three sections (landing, modal, game-view)

- [ ] **Step 1: Write complete index.html**
```html
<!-- static/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>GameHub — Play Classic Games Online</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <!-- ===== LANDING PAGE ===== -->
  <section id="landing" class="page active" aria-label="Game selection">
    <header class="hero">
      <h1>GameHub</h1>
      <p class="hero-tagline">Play classic board games online — free, no install.</p>
    </header>
    <main class="game-grid" id="game-grid" role="list"></main>
  </section>

  <!-- ===== GAME DETAIL MODAL ===== -->
  <div id="game-modal" class="modal hidden" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <div class="modal-backdrop" tabindex="-1"></div>
    <div class="modal-content">
      <button class="modal-close" aria-label="Close modal">&times;</button>
      <div class="modal-visual">
        <canvas id="modal-board-preview" width="320" height="320" aria-label="Checkers board preview"></canvas>
      </div>
      <div class="modal-info">
        <h2 id="modal-title"></h2>
        <p id="modal-desc"></p>
        <dl class="modal-specs" id="modal-specs"></dl>
        <div class="modal-rules" id="modal-rules"></div>
        <button class="btn-primary btn-play-large" id="modal-play-btn">Play Now</button>
      </div>
    </div>
  </div>

  <!-- ===== GAME VIEW ===== -->
  <section id="game-view" class="page hidden" aria-label="Game in progress">
    <header class="game-header">
      <button class="btn-back" id="btn-back-to-landing" aria-label="Back to game selection">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
      </button>
      <div class="game-status">
        <span id="turn-indicator" aria-live="polite">White to move</span>
        <span id="timer" class="hidden" aria-live="off">00:00</span>
      </div>
      <div class="game-menu">
        <button id="btn-new-game" class="btn-secondary">New Game</button>
        <button id="btn-resign" class="btn-danger">Resign</button>
      </div>
    </header>
    <main class="game-main">
      <aside class="sidebar" id="sidebar" aria-label="Game info">
        <button class="sidebar-toggle" id="sidebar-toggle" aria-label="Toggle sidebar" aria-expanded="false">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="18" x2="20" y2="18"/></svg>
        </button>
        <section class="panel captured" id="captured-white">
          <h4>Captured (White)</h4>
          <div class="pieces" id="captured-white-pieces"></div>
        </section>
        <section class="panel history" id="move-history">
          <h4>Move History</h4>
          <ol id="history-list"></ol>
        </section>
        <section class="panel captured" id="captured-black">
          <h4>Captured (Black)</h4>
          <div class="pieces" id="captured-black-pieces"></div>
        </section>
      </aside>
      <div class="board-wrapper">
        <canvas id="board-canvas" width="640" height="640" aria-label="Checkers game board"></canvas>
        <div class="board-overlay" id="board-overlay" aria-hidden="true"></div>
      </div>
    </main>
  </section>

  <script type="module" src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Verify HTML loads without JS errors**
```bash
# Start container and check console
docker run --rm -d -p 8000:8000 --name test-ui games:latest
sleep 3
curl -s http://localhost:8000/ | head -30
docker stop test-ui
```

- [ ] **Step 3: Commit**
```bash
git add static/index.html
git commit -m "feat: add landing, modal, and game view HTML structure"
```

---

### Task 3: Style Landing Page (Hero + Game Grid + Cards)

**Files:**
- Modify: `static/styles.css` (add landing, hero, grid, card styles)

**Interfaces:**
- Consumes: HTML from Task 2
- Produces: Styled landing page matching spec

- [ ] **Step 1: Add landing page styles**
```css
/* static/styles.css - append */

/* ===== PAGE VISIBILITY ===== */
.page { display: none; }
.page.active { display: block; animation: fadeIn 0.3s var(--transition); }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

/* ===== HERO ===== */
.hero { text-align: center; padding: 4rem 2rem 2rem; background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%); border-bottom: 1px solid var(--border); }
.hero h1 { font-size: clamp(2.5rem, 6vw, 4rem); font-weight: 700; margin-bottom: 0.5rem; background: linear-gradient(135deg, var(--text-primary), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-tagline { font-size: clamp(1rem, 2.5vw, 1.25rem); color: var(--text-secondary); max-width: 600px; margin: 0 auto; }

/* ===== GAME GRID ===== */
.game-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; padding: 2rem; max-width: 1200px; margin: 0 auto; }
.game-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.5rem; display: flex; flex-direction: column; transition: transform var(--transition), box-shadow var(--transition), border-color var(--transition); position: relative; overflow: hidden; }
.game-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--accent), var(--gold)); opacity: 0; transition: opacity var(--transition); }
.game-card:hover { transform: translateY(-4px); box-shadow: var(--shadow); border-color: var(--accent); }
.game-card:hover::before { opacity: 1; }
.game-thumb { width: 100%; aspect-ratio: 1; border-radius: calc(var(--radius) - 4px); background: linear-gradient(135deg, var(--wood-dark), var(--wood-light)); display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; position: relative; overflow: hidden; }
.checkers-preview { width: 80%; height: 80%; }
.game-info { flex: 1; display: flex; flex-direction: column; }
.game-info h3 { font-size: 1.25rem; margin-bottom: 0.5rem; }
.game-desc { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1rem; flex: 1; }
.game-meta { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; }
.badge { font-size: 0.7rem; padding: 0.25rem 0.5rem; border-radius: 999px; background: var(--bg-secondary); color: var(--text-secondary); border: 1px solid var(--border); text-transform: uppercase; letter-spacing: 0.05em; }
.badge.ai { background: rgba(233, 69, 96, 0.15); color: var(--accent); border-color: var(--accent); }
.btn-play { width: 100%; padding: 0.75rem; background: var(--accent); color: white; border-radius: calc(var(--radius) - 4px); font-weight: 600; font-size: 1rem; transition: background var(--transition), transform 0.1s; }
.btn-play:hover { background: var(--accent-hover); transform: scale(1.02); }
.btn-play:active { transform: scale(0.98); }
```

- [ ] **Step 2: Add Checkers preview SVG to HTML (inline in Task 2 HTML or via JS)**
   - In `app.js` Task 5, we'll inject the preview SVG. For now, add a placeholder style:
```css
.checkers-preview { display: block; }
```

- [ ] **Step 3: Test landing page renders**
```bash
docker build -t games:latest . && docker run --rm -d -p 8000:8000 --name test-ui games:latest
sleep 3
curl -s http://localhost:8000/ | grep -c "GameHub"
docker stop test-ui
```

- [ ] **Step 4: Commit**
```bash
git add static/styles.css
git commit -m "feat: style landing page hero, grid, and game cards"
```

---

### Task 4: Style Game Detail Modal

**Files:**
- Modify: `static/styles.css` (add modal styles)

**Interfaces:**
- Consumes: Modal HTML from Task 2
- Produces: Accessible, animated modal with preview canvas

- [ ] **Step 1: Add modal styles**
```css
/* static/styles.css - append */

/* ===== MODAL ===== */
.modal { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; padding: 1rem; }
.modal.hidden { display: none; }
.modal-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,0.7); animation: fadeIn 0.2s var(--transition); }
.modal-content { position: relative; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: var(--radius); max-width: 720px; width: 100%; max-height: 90vh; overflow-y: auto; display: grid; grid-template-columns: 1fr; animation: slideUp 0.3s var(--transition); }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: none; } }
@media (min-width: 640px) { .modal-content { grid-template-columns: 320px 1fr; } }
.modal-close { position: absolute; top: 1rem; right: 1rem; width: 36px; height: 36px; border-radius: 50%; background: var(--bg-card); border: 1px solid var(--border); color: var(--text-secondary); font-size: 1.5rem; display: flex; align-items: center; justify-content: center; z-index: 1; transition: all var(--transition); }
.modal-close:hover { background: var(--accent); color: white; border-color: var(--accent); }
.modal-visual { background: var(--bg-primary); border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: center; padding: 1.5rem; }
@media (min-width: 640px) { .modal-visual { border-bottom: none; border-right: 1px solid var(--border); min-height: 400px; } }
#modal-board-preview { max-width: 100%; height: auto; }
.modal-info { padding: 1.5rem 2rem; }
.modal-info h2 { font-size: 1.75rem; margin-bottom: 0.5rem; }
#modal-desc { color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6; }
.modal-specs { display: grid; grid-template-columns: auto 1fr; gap: 0.5rem 1.5rem; margin-bottom: 1.5rem; font-size: 0.9rem; }
.modal-specs dt { color: var(--text-secondary); }
.modal-specs dd { font-weight: 500; }
.modal-rules { background: var(--bg-card); border: 1px solid var(--border); border-radius: calc(var(--radius) - 4px); padding: 1rem; margin-bottom: 1.5rem; }
.modal-rules h4 { margin-bottom: 0.75rem; font-size: 0.95rem; }
.modal-rules ul { list-style: none; display: grid; gap: 0.4rem; }
.modal-rules li { position: relative; padding-left: 1.5rem; font-size: 0.85rem; color: var(--text-secondary); }
.modal-rules li::before { content: '→'; position: absolute; left: 0; color: var(--accent); }
.btn-primary { width: 100%; padding: 1rem; background: linear-gradient(135deg, var(--accent), #c0392b); color: white; border-radius: calc(var(--radius) - 4px); font-weight: 600; font-size: 1.1rem; transition: transform var(--transition), box-shadow var(--transition); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(233, 69, 96, 0.4); }
.btn-primary:active { transform: translateY(0); }
```

- [ ] **Step 2: Test modal opens/closes (will wire in Task 6)**
```bash
# Visual test after Task 6
```

- [ ] **Step 3: Commit**
```bash
git add static/styles.css
git commit -m "feat: style game detail modal with preview and specs"
```

---

### Task 5: Style Game View (Header, Sidebar, Board Wrapper)

**Files:**
- Modify: `static/styles.css` (add game view styles)

**Interfaces:**
- Consumes: Game view HTML from Task 2
- Produces: Responsive game layout with collapsible sidebar

- [ ] **Step 1: Add game view styles**
```css
/* static/styles.css - append */

/* ===== GAME VIEW ===== */
.game-header { display: flex; align-items: center; gap: 1rem; padding: 1rem 1.5rem; background: var(--bg-secondary); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 10; }
.btn-back { width: 40px; height: 40px; border-radius: 50%; background: var(--bg-card); border: 1px solid var(--border); color: var(--text-secondary); display: flex; align-items: center; justify-content: center; transition: all var(--transition); }
.btn-back:hover { background: var(--accent); color: white; border-color: var(--accent); }
.game-status { flex: 1; text-align: center; }
#turn-indicator { font-weight: 600; font-size: 1.1rem; }
#turn-indicator.white { color: var(--piece-white); }
#turn-indicator.black { color: var(--gold); }
#timer { font-family: var(--font-mono); font-size: 1.25rem; color: var(--accent); }
.game-menu { display: flex; gap: 0.5rem; }
.btn-secondary, .btn-danger { padding: 0.5rem 1rem; border-radius: calc(var(--radius) - 4px); font-weight: 500; font-size: 0.875rem; transition: all var(--transition); }
.btn-secondary { background: var(--bg-card); border: 1px solid var(--border); color: var(--text-primary); }
.btn-secondary:hover { background: var(--border); }
.btn-danger { background: rgba(233, 69, 96, 0.15); border: 1px solid var(--accent); color: var(--accent); }
.btn-danger:hover { background: var(--accent); color: white; }

.game-main { display: flex; flex: 1; overflow: hidden; }
.sidebar { width: 280px; background: var(--bg-secondary); border-right: 1px solid var(--border); display: flex; flex-direction: column; overflow-y: auto; transition: transform 0.3s var(--transition); }
.sidebar-toggle { display: none; width: 100%; padding: 0.75rem; background: var(--bg-card); border: none; border-bottom: 1px solid var(--border); color: var(--text-primary); justify-content: center; }
.panel { padding: 1.5rem; border-bottom: 1px solid var(--border); }
.panel:last-child { border-bottom: none; }
.panel h4 { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem; }
.captured .pieces { display: flex; flex-wrap: wrap; gap: 0.4rem; justify-content: center; min-height: 60px; }
.captured-piece { width: 32px; height: 32px; border-radius: 50%; background: radial-gradient(circle at 30% 30%, var(--piece-white) 0%, var(--piece-black) 100%); box-shadow: 0 2px 4px rgba(0,0,0,0.3); position: relative; }
.captured-piece.black { background: radial-gradient(circle at 30% 30%, #444 0%, var(--piece-black) 100%); }
.history ol { display: grid; gap: 0.3rem; }
.history li { font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary); padding: 0.25rem 0.5rem; background: var(--bg-card); border-radius: 4px; transition: all var(--transition); cursor: pointer; }
.history li:hover { background: var(--border); color: var(--text-primary); }
.history li.current { background: var(--accent); color: white; }

.board-wrapper { flex: 1; display: flex; align-items: center; justify-content: center; padding: 2rem; background: var(--bg-primary); position: relative; }
#board-canvas { max-width: 100%; height: auto; box-shadow: var(--shadow); border-radius: 8px; background: var(--wood-dark); }
.board-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; }

/* ===== RESPONSIVE ===== */
@media (max-width: 1024px) {
  .sidebar { position: fixed; top: 0; left: 0; bottom: 0; z-index: 20; transform: translateX(-100%); box-shadow: var(--shadow); }
  .sidebar.open { transform: translateX(0); }
  .sidebar-toggle { display: flex; }
  .game-header { padding: 1rem; }
}
@media (max-width: 768px) {
  .hero { padding: 3rem 1rem 1.5rem; }
  .game-grid { padding: 1rem; gap: 1rem; }
  .modal-content { margin: 1rem; }
  .board-wrapper { padding: 1rem; }
  .panel { padding: 1rem; }
}
@media (max-width: 480px) {
  .hero h1 { font-size: 2rem; }
  .btn-play { padding: 0.6rem; font-size: 0.9rem; }
  .game-menu { display: none; } /* Could move to dropdown */
}
```

- [ ] **Step 2: Commit**
```bash
git add static/styles.css
git commit -m "feat: style game view header, sidebar, board wrapper responsive"
```

---

### Task 6: Implement SPA Navigation in app.js

**Files:**
- Create: `static/app.js` (replace existing)

**Interfaces:**
- Consumes: HTML sections from Task 2, CSS from Tasks 3-5
- Produces: View switching functions, modal open/close, game start flow

- [ ] **Step 1: Write app.js with navigation**
```js
// static/app.js
import { renderPreview } from '/static/games/checkers/preview.js';
import { CheckersGame } from '/static/games/checkers/board.js';

// ===== STATE =====
const STATE = {
  currentView: 'landing',
  selectedGame: null,
  game: {
    id: null,
    ws: null,
    myColor: null,
    board: null,
    history: [],
    captured: { w: [], b: [] },
    turn: 'w',
    status: 'waiting'
  }
};

// ===== DOM REFS =====
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const landing = $('#landing');
const modal = $('#game-modal');
const gameView = $('#game-view');
const gameGrid = $('#game-grid');
const modalTitle = $('#modal-title');
const modalDesc = $('#modal-desc');
const modalSpecs = $('#modal-specs');
const modalRules = $('#modal-rules');
const modalPlayBtn = $('#modal-play-btn');
const modalClose = $('.modal-close');
const modalBackdrop = $('.modal-backdrop');
const turnIndicator = $('#turn-indicator');
const timerEl = $('#timer');
const btnBack = $('#btn-back-to-landing');
const btnNewGame = $('#btn-new-game');
const btnResign = $('#btn-resign');
const sidebar = $('#sidebar');
const sidebarToggle = $('#sidebar-toggle');
const historyList = $('#history-list');
const capturedWhite = $('#captured-white-pieces');
const capturedBlack = $('#captured-black-pieces');
const boardCanvas = $('#board-canvas');
const boardOverlay = $('#board-overlay');

// ===== GAME DATA =====
const GAMES = {
  checkers: {
    id: 'checkers',
    title: 'Checkers',
    desc: 'Classic 8×8 English draughts. Capture all opponent pieces or block them completely.',
    shortDesc: 'Classic 8×8 draughts. Play vs AI or friend.',
    players: 2,
    modes: ['Local', 'AI', 'Online'],
    duration: '5–15 min',
    difficulty: ['Easy', 'Medium', 'Hard'],
    rules: [
      'Move diagonally forward on dark squares only',
      'Capture by jumping over an adjacent opponent piece',
      'Multiple jumps allowed in a single turn',
      'Reach the back row → become a King (moves backward too)',
      'Win by capturing all enemy pieces or blocking all moves'
    ]
  }
};

// ===== VIEW MANAGEMENT =====
function showView(view) {
  [landing, modal, gameView].forEach(v => v.classList.remove('active'));
  STATE.currentView = view;
  if (view === 'landing') landing.classList.add('active');
  else if (view === 'modal') modal.classList.remove('hidden');
  else if (view === 'game') gameView.classList.add('active');
}

function openModal(gameId) {
  const game = GAMES[gameId];
  if (!game) return;
  STATE.selectedGame = gameId;
  modalTitle.textContent = game.title;
  modalDesc.textContent = game.desc;
  modalSpecs.innerHTML = `
    <dt>Players</dt><dd>${game.players}</dd>
    <dt>Modes</dt><dd>${game.modes.join(', ')}</dd>
    <dt>Duration</dt><dd>${game.duration}</dd>
    <dt>AI Difficulty</dt><dd>${game.difficulty.join(' / ')}</dd>
  `;
  modalRules.innerHTML = `
    <h4>Rules Summary</h4>
    <ul>${game.rules.map(r => `<li>${r}</li>`).join('')}</ul>
  `;
  // Render preview
  renderPreview('modal-board-preview');
  showView('modal');
}

function closeModal() {
  modal.classList.add('hidden');
  showView('landing');
  STATE.selectedGame = null;
}

async function startGame(gameId) {
  closeModal();
  showView('game');
  STATE.game.id = gameId;
  // Create game on server
  const resp = await fetch('/games', { method: 'POST' });
  const data = await resp.json();
  STATE.game.id = data.id;
  connectWebSocket();
}

function backToLanding() {
  if (STATE.game.ws) {
    STATE.game.ws.close();
  }
  STATE.game = { id: null, ws: null, myColor: null, board: null, history: [], captured: { w: [], b: [] }, turn: 'w', status: 'waiting' };
  showView('landing');
}

// ===== EVENT LISTENERS =====
// Landing: game cards (delegated)
gameGrid.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-game]');
  if (btn) openModal(btn.dataset.game);
});

// Modal
modalClose?.addEventListener('click', closeModal);
modalBackdrop?.addEventListener('click', closeModal);
modalPlayBtn?.addEventListener('click', () => startGame(STATE.selectedGame));
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !modal.classList.contains('hidden')) closeModal(); });

// Game view
btnBack?.addEventListener('click', backToLanding);
btnNewGame?.addEventListener('click', () => startGame(STATE.game.id));
btnResign?.addEventListener('click', () => { /* TODO: resign logic */ });
sidebarToggle?.addEventListener('click', () => sidebar.classList.toggle('open'));

// ===== INIT =====
function init() {
  renderGameGrid();
}
function renderGameGrid() {
  gameGrid.innerHTML = Object.values(GAMES).map(game => `
    <article class="game-card" data-game="${game.id}">
      <div class="game-thumb">
        <svg class="checkers-preview" viewBox="0 0 80 80" width="80" height="80">
          ${generateCheckersPreviewSVG()}
        </svg>
      </div>
      <div class="game-info">
        <h3>${game.title}</h3>
        <p class="game-desc">${game.shortDesc}</p>
        <div class="game-meta">
          <span class="badge">${game.players} Players</span>
          <span class="badge ai">AI Opponent</span>
          <span class="badge">${game.duration}</span>
        </div>
      </div>
      <button class="btn-play" data-game="${game.id}">Play</button>
    </article>
  `).join('');
}

function generateCheckersPreviewSVG() {
  // Simple 8x8 preview with a few pieces
  let svg = '';
  const square = 10;
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      if ((r + c) % 2 === 0) {
        svg += `<rect x="${c*square}" y="${r*square}" width="${square}" height="${square}" fill="#b58863"/>`;
      }
    }
  }
  // Place a few pieces
  const pieces = [
    {r:1,c:1,col:'w'},{r:1,c:3,col:'w'},{r:1,c:5,col:'w'},{r:1,c:7,col:'w'},
    {r:6,c:0,col:'b'},{r:6,c:2,col:'b'},{r:6,c:4,col:'b'},{r:6,c:6,col:'b'},
    {r:3,c:3,col:'w'},{r:4,c:4,col:'b'}
  ];
  pieces.forEach(p => {
    const cx = p.c*square + square/2;
    const cy = p.r*square + square/2;
    const col = p.col === 'w' ? '#fff' : '#111';
    svg += `<circle cx="${cx}" cy="${cy}" r="3.5" fill="${col}" stroke="#333" stroke-width="0.5"/>`;
  });
  return svg;
}

init();
```

- [ ] **Step 2: Test navigation works (landing → modal → game view)**
```bash
docker build -t games:latest . && docker run --rm -d -p 8000:8000 --name test-ui games:latest
sleep 3
# Manual browser test: open http://localhost:8000/, click Play, verify modal opens, click Play Now
docker stop test-ui
```

- [ ] **Step 3: Commit**
```bash
git add static/app.js
git commit -m "feat: implement SPA navigation (landing, modal, game view)"
```

---

### Task 7: Implement Checkers Board Rendering (Canvas)

**Files:**
- Modify: `static/games/checkers/board.js` (full implementation)

**Interfaces:**
- Consumes: Board state array[8][8], CSS variables
- Produces: `drawBoard(ctx, board, options)`, `drawPiece()`, `animateMove()`, `highlightSquares()`

- [ ] **Step 1: Implement board.js**
```js
// static/games/checkers/board.js
const SQUARE_SIZE = 80;
const BOARD_SIZE = 8;
const PIECE_RADIUS = 30;
const PIECE_STROKE = 2;
const ANIMATION_DURATION = 150; // ms

// Wood texture cache
let woodPattern = null;

function createWoodPattern(ctx) {
  if (woodPattern) return woodPattern;
  const canvas = document.createElement('canvas');
  canvas.width = 256; canvas.height = 256;
  const c = canvas.getContext('2d');
  // Base
  const gradient = c.createLinearGradient(0, 0, 256, 256);
  gradient.addColorStop(0, '#e8c58a');
  gradient.addColorStop(0.5, '#d4a574');
  gradient.addColorStop(1, '#c4945a');
  c.fillStyle = gradient;
  c.fillRect(0, 0, 256, 256);
  // Noise
  const imgData = c.getImageData(0, 0, 256, 256);
  const data = imgData.data;
  for (let i = 0; i < data.length; i += 4) {
    const noise = (Math.random() - 0.5) * 20;
    data[i] = Math.max(0, Math.min(255, data[i] + noise));
    data[i+1] = Math.max(0, Math.min(255, data[i+1] + noise));
    data[i+2] = Math.max(0, Math.min(255, data[i+2] + noise));
  }
  c.putImageData(imgData, 0, 0);
  woodPattern = ctx.createPattern(canvas, 'repeat');
  return woodPattern;
}

export function drawBoard(ctx, board, options = {}) {
  const { selectedSquare, validMoves = [], lastMove, animateFrom, animateTo, animateProgress, kingPromotion } = options;
  const width = ctx.canvas.width;
  const height = ctx.canvas.height;
  const squareSize = width / BOARD_SIZE;
  const radius = squareSize * 0.375;

  // Clear
  ctx.clearRect(0, 0, width, height);

  // Wood background
  ctx.fillStyle = createWoodPattern(ctx);
  ctx.fillRect(0, 0, width, height);

  // Squares
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      const x = c * squareSize;
      const y = r * squareSize;
      const isDark = (r + c) % 2 === 0;

      // Dark squares
      if (isDark) {
        ctx.fillStyle = '#b58863';
        ctx.fillRect(x, y, squareSize, squareSize);
      }

      // Highlights
      if (selectedSquare && selectedSquare[0] === r && selectedSquare[1] === c) {
        ctx.fillStyle = 'rgba(233, 69, 96, 0.3)';
        ctx.fillRect(x, y, squareSize, squareSize);
      }
      if (validMoves.some(([vr, vc]) => vr === r && vc === c)) {
        // Pulsing dot
        const pulse = 0.5 + 0.5 * Math.sin(Date.now() / 200);
        ctx.fillStyle = `rgba(255, 215, 0, ${0.4 + 0.3 * pulse})`;
        ctx.beginPath();
        ctx.arc(x + squareSize/2, y + squareSize/2, squareSize * 0.15, 0, Math.PI * 2);
        ctx.fill();
      }
      if (lastMove && ((lastMove.from[0] === r && lastMove.from[1] === c) || (lastMove.to[0] === r && lastMove.to[1] === c))) {
        ctx.fillStyle = 'rgba(255, 215, 0, 0.25)';
        ctx.fillRect(x, y, squareSize, squareSize);
      }
    }
  }

  // Border
  ctx.strokeStyle = '#8b6b4a';
  ctx.lineWidth = 4;
  ctx.strokeRect(2, 2, width - 4, height - 4);

  // Pieces
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      const piece = board[r][c];
      if (!piece) continue;

      // Skip animating piece
      if (animateFrom && animateFrom[0] === r && animateFrom[1] === c) continue;

      const x = c * squareSize + squareSize / 2;
      const y = r * squareSize + squareSize / 2;
      drawPiece(ctx, x, y, radius, piece.color, piece.king);
    }
  }

  // Animating piece
  if (animateFrom && animateTo && animateProgress !== undefined) {
    const piece = board[animateFrom[0]][animateFrom[1]];
    if (piece) {
      const sx = animateFrom[1] * squareSize + squareSize / 2;
      const sy = animateFrom[0] * squareSize + squareSize / 2;
      const tx = animateTo[1] * squareSize + squareSize / 2;
      const ty = animateTo[0] * squareSize + squareSize / 2;
      const x = sx + (tx - sx) * animateProgress;
      const y = sy + (ty - sy) * animateProgress;
      // Lift effect
      const lift = Math.sin(animateProgress * Math.PI) * 20;
      drawPiece(ctx, x, y - lift, radius, piece.color, piece.king);
    }
  }

  // King promotion animation
  if (kingPromotion) {
    const { r, c, progress } = kingPromotion;
    const x = c * squareSize + squareSize / 2;
    const y = r * squareSize + squareSize / 2;
    const scale = 1 + 0.5 * Math.sin(progress * Math.PI);
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(scale, scale);
    drawPiece(ctx, 0, 0, radius, 'w', true); // crown preview
    ctx.restore();
  }
}

export function drawPiece(ctx, x, y, radius, color, isKing) {
  // Shadow
  ctx.shadowColor = 'rgba(0,0,0,0.4)';
  ctx.shadowBlur = 8;
  ctx.shadowOffsetY = 4;

  // Piece body
  const grad = ctx.createRadialGradient(x - radius*0.3, y - radius*0.3, radius*0.1, x, y, radius);
  if (color === 'w') {
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.5, '#f0f0f0');
    grad.addColorStop(1, '#d0d0d0');
  } else {
    grad.addColorStop(0, '#333333');
    grad.addColorStop(0.5, '#1a1a1a');
    grad.addColorStop(1, '#000000');
  }
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();

  // Stroke
  ctx.shadowColor = 'transparent';
  ctx.strokeStyle = color === 'w' ? '#aaa' : '#000';
  ctx.lineWidth = PIECE_STROKE;
  ctx.stroke();

  // King crown
  if (isKing) {
    ctx.fillStyle = '#ffd700';
    ctx.strokeStyle = '#b8860b';
    ctx.lineWidth = 1.5;
    const crownSize = radius * 0.55;
    ctx.beginPath();
    ctx.moveTo(x - crownSize, y + crownSize * 0.3);
    ctx.lineTo(x - crownSize * 0.5, y - crownSize * 0.3);
    ctx.lineTo(x, y + crownSize * 0.2);
    ctx.lineTo(x + crownSize * 0.5, y - crownSize * 0.3);
    ctx.lineTo(x + crownSize, y + crownSize * 0.3);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    // Cross on top
    ctx.beginPath();
    ctx.moveTo(x, y - crownSize * 0.3);
    ctx.lineTo(x, y - crownSize * 0.6);
    ctx.moveTo(x - crownSize * 0.2, y - crownSize * 0.45);
    ctx.lineTo(x + crownSize * 0.2, y - crownSize * 0.45);
    ctx.stroke();
  }
}

export function animateMove(board, from, to, onComplete) {
  const startTime = performance.now();
  function frame(now) {
    const progress = Math.min(1, (now - startTime) / ANIMATION_DURATION);
    const eased = 1 - Math.pow(1 - progress, 3); // cubic ease-out
    // Redraw with animation
    // This will be called from game controller with requestAnimationFrame
    onComplete(eased);
    if (progress < 1) requestAnimationFrame(frame);
    else onComplete(1);
  }
  requestAnimationFrame(frame);
}

export function highlightSquares(ctx, squares, color) {
  // Used by preview
}
```

- [ ] **Step 2: Commit**
```bash
git add static/games/checkers/board.js
git commit -m "feat: implement checkers board canvas rendering with wood texture, pieces, animations"
```

---

### Task 8: Implement Checkers Game Logic (Client-side)

**Files:**
- Modify: `static/games/checkers/logic.js` (full implementation)

**Interfaces:**
- Consumes: Board array, move coordinates
- Produces: `createInitialBoard()`, `getLegalMoves()`, `applyMove()`, `isValidMove()`, `algebraic()`

- [ ] **Step 1: Implement logic.js**
```js
// static/games/checkers/logic.js
export const COLS = 8, ROWS = 8;
export const EMPTY = null;
export const COLORS = { WHITE: 'w', BLACK: 'b' };

export function createInitialBoard() {
  const board = Array(ROWS).fill(null).map(() => Array(COLS).fill(EMPTY));
  // White pieces (bottom, rows 5-7)
  for (let r = 5; r < 8; r++) {
    for (let c = 0; c < COLS; c++) {
      if ((r + c) % 2 === 0) board[r][c] = { color: 'w', king: false };
    }
  }
  // Black pieces (top, rows 0-2)
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < COLS; c++) {
      if ((r + c) % 2 === 0) board[r][c] = { color: 'b', king: false };
    }
  }
  return board;
}

export function cloneBoard(board) {
  return board.map(row => row.map(p => p ? {...p} : null));
}

export function getPieceAt(board, [r, c]) {
  if (r < 0 || r >= ROWS || c < 0 || c >= COLS) return null;
  return board[r][c];
}

export function getLegalMoves(board, color) {
  const moves = [];
  const dirs = color === 'w' ? [[-1,-1],[-1,1]] : [[1,-1],[1,1]];
  const kingDirs = [[-1,-1],[-1,1],[1,-1],[1,1]];

  // First pass: captures (mandatory)
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const piece = board[r][c];
      if (!piece || piece.color !== color) continue;
      const pieceMoves = piece.king ? kingDirs : dirs;
      findCaptures(board, r, c, piece, pieceMoves, [], moves);
    }
  }
  if (moves.length) return moves;

  // Second pass: normal moves
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const piece = board[r][c];
      if (!piece || piece.color !== color) continue;
      const pieceMoves = piece.king ? kingDirs : dirs;
      for (const [dr, dc] of pieceMoves) {
        const nr = r + dr, nc = c + dc;
        if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS && !board[nr][nc]) {
          moves.push({ from: [r,c], to: [nr,nc], capture: false });
        }
      }
    }
  }
  return moves;
}

function findCaptures(board, r, c, piece, dirs, path, moves) {
  let found = false;
  for (const [dr, dc] of dirs) {
    const midR = r + dr, midC = c + dc;
    const landR = r + 2*dr, landC = c + 2*dc;
    if (landR < 0 || landR >= ROWS || landC < 0 || landC >= COLS) continue;
    const midPiece = board[midR][midC];
    const landPiece = board[landR][landC];
    if (midPiece && midPiece.color !== piece.color && !landPiece) {
      found = true;
      // Simulate capture
      board[midR][midC] = null;
      board[landR][landC] = piece;
      board[r][c] = null;
      const newPath = [...path, [midR, midC]];
      findCaptures(board, landR, landC, piece, dirs, newPath, moves);
      // Undo
      board[r][c] = piece;
      board[landR][landC] = null;
      board[midR][midC] = midPiece;
    }
  }
  if (!found && path.length > 0) {
    moves.push({ from: path[0].slice(0,2), to: [r,c], capture: true, captured: path });
  }
}

export function applyMove(board, from, to) {
  const [fr, fc] = from;
  const [tr, tc] = to;
  const piece = board[fr][fc];
  if (!piece) return false;

  board[tr][tc] = piece;
  board[fr][fc] = null;

  // King promotion
  if (!piece.king && ((piece.color === 'w' && tr === 0) || (piece.color === 'b' && tr === ROWS-1))) {
    piece.king = true;
  }
  return true;
}

export function isValidMove(board, from, to, color) {
  const moves = getLegalMoves(board, color);
  return moves.some(m => m.from[0]===from[0] && m.from[1]===from[1] && m.to[0]===to[0] && m.to[1]===to[1]);
}

export function algebraic([r, c]) {
  const files = 'abcdefgh';
  const ranks = '87654321'; // White at bottom (rank 1 = row 7)
  return `${files[c]}${ranks[r]}`;
}

export function parseAlgebraic(str) {
  const files = 'abcdefgh';
  const c = files.indexOf(str[0]);
  const r = 7 - parseInt(str[1], 10);
  return [r, c];
}
```

- [ ] **Step 2: Commit**
```bash
git add static/games/checkers/logic.js
git commit -m "feat: implement checkers game logic (legal moves, captures, promotion, algebraic notation)"
```

---

### Task 9: Implement Modal Preview Renderer

**Files:**
- Modify: `static/games/checkers/preview.js` (full implementation)

**Interfaces:**
- Consumes: Canvas element ID
- Produces: Static board preview for modal

- [ ] **Step 1: Implement preview.js**
```js
// static/games/checkers/preview.js
import { createInitialBoard } from './logic.js';
import { drawBoard } from './board.js';

export function renderPreview(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const board = createInitialBoard();
  // Show a mid-game position for visual interest
  board[3][3] = { color: 'w', king: false };
  board[4][4] = { color: 'b', king: true };
  drawBoard(ctx, board);
}
```

- [ ] **Step 2: Commit**
```bash
git add static/games/checkers/preview.js
git commit -m "feat: implement modal board preview renderer"
```

---

### Task 10: Implement CheckersGame Class & WebSocket Integration

**Files:**
- Modify: `static/games/checkers/board.js` (add CheckersGame class)
- Modify: `static/app.js` (add WebSocket logic, game controller)

**Interfaces:**
- Consumes: WebSocket endpoint `/ws/{gameId}`, board.js, logic.js
- Produces: Full game loop: create game → connect WS → handle messages → render

- [ ] **Step 1: Add CheckersGame class to board.js**
```js
// static/games/checkers/board.js - append at end

export class CheckersGame {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.board = null;
    this.myColor = null;
    this.turn = 'w';
    this.history = [];
    this.captured = { w: [], b: [] };
    this.selectedSquare = null;
    this.validMoves = [];
    this.lastMove = null;
    this.animating = false;
    this.animationStart = 0;
    this.animationFrom = null;
    this.animationTo = null;
    this.ws = null;
    this.gameId = null;

    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.canvas.addEventListener('click', (e) => this.handleClick(e));
    this.render();
  }

  resize() {
    const wrapper = this.canvas.parentElement;
    const size = Math.min(wrapper.clientWidth - 40, wrapper.clientHeight - 40, 640);
    this.canvas.width = size;
    this.canvas.height = size;
    this.render();
  }

  async init(gameId, ws) {
    this.gameId = gameId;
    this.ws = ws;
    this.board = await import('./logic.js').then(m => m.createInitialBoard());
    this.render();
  }

  setMyColor(color) {
    this.myColor = color;
    this.updateTurnIndicator();
  }

  handleMessage(msg) {
    if (msg.type === 'color') {
      this.setMyColor(msg.color);
    } else if (msg.type === 'board') {
      this.animateToBoard(msg.board);
    } else if (msg.type === 'game_over') {
      this.handleGameOver(msg.winner);
    } else if (msg.type === 'error') {
      console.warn('Server error:', msg.message);
    }
  }

  animateToBoard(newBoard) {
    // Find moved piece
    let from = null, to = null;
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const oldP = this.board?.[r]?.[c];
        const newP = newBoard[r][c];
        if (oldP && !newP) from = [r,c];
        if (!oldP && newP) to = [r,c];
      }
    }
    this.lastMove = { from, to };
    if (from && to) {
      this.animateMove(from, to, () => {
        this.board = newBoard;
        this.turn = this.turn === 'w' ? 'b' : 'w';
        this.updateHistory(from, to);
        this.updateCaptured();
        this.render();
      });
    } else {
      this.board = newBoard;
      this.render();
    }
  }

  animateMove(from, to, onComplete) {
    this.animating = true;
    this.animationFrom = from;
    this.animationTo = to;
    this.animationStart = performance.now();
    const animate = (now) => {
      const progress = Math.min(1, (now - this.animationStart) / 150);
      const eased = 1 - Math.pow(1 - progress, 3);
      this.render({ animateFrom: from, animateTo: to, animateProgress: eased });
      if (progress < 1) requestAnimationFrame(animate);
      else {
        this.animating = false;
        this.animationFrom = this.animationTo = null;
        onComplete();
      }
    };
    requestAnimationFrame(animate);
  }

  render(options = {}) {
    if (!this.board) return;
    const { selectedSquare, validMoves, lastMove } = options;
    import('./board.js').then(m => m.drawBoard(this.ctx, this.board, {
      selectedSquare: selectedSquare ?? this.selectedSquare,
      validMoves: validMoves ?? this.validMoves,
      lastMove: lastMove ?? this.lastMove,
      animateFrom: options.animateFrom,
      animateTo: options.animateTo,
      animateProgress: options.animateProgress
    }));
  }

  handleClick(e) {
    if (this.animating || this.turn !== this.myColor) return;
    const rect = this.canvas.getBoundingClientRect();
    const squareSize = this.canvas.width / 8;
    const c = Math.floor((e.clientX - rect.left) / squareSize);
    const r = Math.floor((e.clientY - rect.top) / squareSize);
    if (r < 0 || r >= 8 || c < 0 || c >= 8) return;

    const piece = this.board[r][c];
    if (!this.selectedSquare) {
      if (piece && piece.color === this.myColor) {
        this.selectedSquare = [r, c];
        this.validMoves = this.getValidMovesForPiece(r, c);
        this.render();
      }
    } else {
      if (this.selectedSquare[0] === r && this.selectedSquare[1] === c) {
        this.selectedSquare = null;
        this.validMoves = [];
        this.render();
      } else if (this.validMoves.some(([vr, vc]) => vr === r && vc === c)) {
        this.sendMove(this.selectedSquare, [r, c]);
        this.selectedSquare = null;
        this.validMoves = [];
      } else if (piece && piece.color === this.myColor) {
        this.selectedSquare = [r, c];
        this.validMoves = this.getValidMovesForPiece(r, c);
        this.render();
      }
    }
  }

  getValidMovesForPiece(r, c) {
    const moves = [];
    // Use logic module
    // For now, return all legal moves from this piece
    // Full implementation would filter getLegalMoves
    return moves;
  }

  sendMove(from, to) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'move', from, to }));
    }
  }

  updateTurnIndicator() {
    const el = document.getElementById('turn-indicator');
    if (el) {
      el.textContent = `${this.turn === 'w' ? 'White' : 'Black'} to move`;
      el.className = this.turn;
    }
  }

  updateHistory(from, to) {
    import('./logic.js').then(m => {
      const moveStr = `${m.algebraic(from)}-${m.algebraic(to)}`;
      const moveNum = Math.floor(this.history.length / 2) + 1;
      const entry = `${moveNum}. ${moveStr}`;
      this.history.push(entry);
      const list = document.getElementById('history-list');
      if (list) {
        const li = document.createElement('li');
        li.textContent = entry;
        list.appendChild(li);
        list.scrollTop = list.scrollHeight;
      }
    });
  }

  updateCaptured() {
    // Compare captured pieces count
    // Simplified: count missing pieces from initial
    const initial = { w: 12, b: 12 };
    let wCount = 0, bCount = 0;
    for (const row of this.board) {
      for (const p of row) {
        if (p) { if (p.color === 'w') wCount++; else bCount++; }
      }
    }
    const capturedW = initial.b - bCount;
    const capturedB = initial.w - wCount;
    this.renderCaptured('captured-white-pieces', capturedW, 'w');
    this.renderCaptured('captured-black-pieces', capturedB, 'b');
  }

  renderCaptured(containerId, count, color) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    const maxShow = 12;
    for (let i = 0; i < Math.min(count, maxShow); i++) {
      const div = document.createElement('div');
      div.className = `captured-piece ${color === 'b' ? 'black' : ''}`;
      container.appendChild(div);
    }
    if (count > maxShow) {
      const div = document.createElement('div');
      div.className = 'captured-piece';
      div.textContent = `+${count - maxShow}`;
      div.style.fontSize = '10px';
      div.style.display = 'flex';
      div.style.alignItems = 'center';
      div.style.justifyContent = 'center';
      container.appendChild(div);
    }
  }

  handleGameOver(winner) {
    const won = winner === this.myColor;
    alert(won ? 'You win!' : 'You lose.');
    // Could show a nice modal instead
  }
}
```

- [ ] **Step 2: Update app.js to use CheckersGame**
```js
// static/app.js - replace connectWebSocket and add game instance
let checkersGame = null;

async function connectWebSocket() {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${protocol}://${location.host}/ws/${STATE.game.id}`);
  STATE.game.ws = ws;

  ws.onopen = () => console.log('WebSocket opened');
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'color') {
      STATE.game.myColor = msg.color;
      // Initialize game UI
      if (!checkersGame) {
        checkersGame = new CheckersGame('board-canvas');
      }
      await checkersGame.init(STATE.game.id, ws);
      checkersGame.setMyColor(msg.color);
    } else if (checkersGame) {
      checkersGame.handleMessage(msg);
    }
  };
  ws.onclose = () => {
    console.log('WebSocket closed');
    document.getElementById('loader').classList.remove('visible');
  };
}

// Update startGame to not call connectWebSocket directly (now in onmessage)
async function startGame(gameId) {
  closeModal();
  showView('game');
  STATE.game.id = gameId;
  const resp = await fetch('/games', { method: 'POST' });
  const data = await resp.json();
  STATE.game.id = data.id;
  // connectWebSocket called after color received
}
```

- [ ] **Step 3: Commit**
```bash
git add static/games/checkers/board.js static/app.js
git commit -m "feat: implement CheckersGame class and WebSocket integration"
```

---

### Task 11: Polish & Accessibility

**Files:**
- Modify: `static/styles.css` (focus states, reduced motion)
- Modify: `static/app.js` (keyboard navigation, ARIA updates)

**Interfaces:**
- Consumes: All previous tasks
- Produces: Accessible, polished UI

- [ ] **Step 1: Add focus/accessibility styles**
```css
/* static/styles.css - append */
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
.modal:focus-within .modal-close { outline: none; }
.game-card:focus-within { box-shadow: 0 0 0 2px var(--accent); }
```

- [ ] **Step 2: Add keyboard navigation to app.js**
```js
// static/app.js - add to init()
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (!modal.classList.contains('hidden')) closeModal();
    else if (STATE.currentView === 'game') backToLanding();
  }
  if (e.key === 'Tab' && STATE.currentView === 'game') {
    // Trap focus in modal when open
  }
});

// ARIA updates in CheckersGame
updateTurnIndicator() {
  const el = document.getElementById('turn-indicator');
  if (el) {
    el.textContent = `${this.turn === 'w' ? 'White' : 'Black'} to move`;
    el.className = this.turn;
    el.setAttribute('aria-live', 'polite');
  }
}
```

- [ ] **Step 3: Commit**
```bash
git add static/styles.css static/app.js
git commit -m "feat: add accessibility (focus, reduced motion, ARIA) and keyboard nav"
```

---

### Task 12: Build Docker Image & Verify

**Files:**
- None (verification)

**Interfaces:**
- Consumes: All previous tasks
- Produces: Working `games:latest` image

- [ ] **Step 1: Build image**
```bash
docker build -t games:latest .
```

- [ ] **Step 2: Run container and test**
```bash
docker run --rm -d -p 8000:8000 --name games-final games:latest
sleep 5
curl -s http://localhost:8000/ | grep -c "GameHub"
curl -s http://localhost:8000/static/app.js | head -1
curl -s http://localhost:8000/static/games/checkers/board.js | head -1
curl -s http://localhost:8000/static/games/checkers/logic.js | head -1
curl -s http://localhost:8000/static/games/checkers/preview.js | head -1
```

- [ ] **Step 3: Manual browser test checklist**
   - [ ] Landing loads at `/` with hero + Checkers card
   - [ ] Click "Play" → modal opens with preview, specs, rules
   - [ ] Click "Play Now" → game view loads
   - [ ] Board renders with wood texture, pieces, kings
   - [ ] Click piece → valid moves highlighted (gold dots)
   - [ ] Click valid square → piece animates smoothly
   - [ ] WebSocket: receive color, see board update
   - [ ] AI moves (if no second player)
   - [ ] Captured pieces appear in sidebar
   - [ ] Move history updates
   - [ ] Game over shows winner
   - [ ] Responsive: test mobile (DevTools device toolbar)
   - [ ] Keyboard: Tab navigation, Escape closes modal
   - [ ] Reduced motion: no animations

- [ ] **Step 4: Commit final changes**
```bash
git add -A
git commit -m "feat: complete landing page and game UI overhaul"
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-07-29-landing-game-ui-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**