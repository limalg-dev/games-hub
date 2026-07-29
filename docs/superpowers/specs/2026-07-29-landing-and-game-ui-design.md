# Landing Page & Game UI Design Spec

## Overview
Modernize the Checkers platform with a polished landing page (game discovery) and an enhanced in-game UI. Single-page app architecture using existing FastAPI static serving.

## Architecture
- **SPA-style**: `index.html` contains landing, modal, and game container sections; `app.js` toggles visibility
- **Static files only**: No server-side routing changes; FastAPI continues to serve `/` → `index.html` and `/static/*`
- **Game modules**: `static/games/checkers/` for board rendering, move logic, WebSocket handling
- **Shared theme**: CSS variables for colors, spacing, typography

---

## 1. Landing Page (`/`)

### Structure
```html
<section id="landing" class="page active">
  <header class="hero">
    <h1>GameHub</h1>
    <p>Play classic board games online — free, no install.</p>
  </header>
  <main class="game-grid" id="game-grid"></main>
</section>
```

### Hero
- Centered, dark background with subtle pattern
- Title: "GameHub" (or "Checkers Platform" if single-game)
- Subtitle: "Play classic board games online — free, no install."
- CTA button (optional): "Explore Games" → scrolls to grid

### Game Grid
- Responsive CSS Grid: `repeat(auto-fit, minmax(280px, 1fr))`
- Gap: 1.5rem; padding: 2rem
- Each card: `GameCard` component (see below)

### GameCard Component
```html
<article class="game-card" data-game="checkers">
  <div class="game-thumb">
    <!-- SVG illustration or canvas preview -->
    <svg class="checkers-preview" viewBox="0 0 80 80">...</svg>
  </div>
  <div class="game-info">
    <h3>Checkers</h3>
    <p class="game-desc">Classic 8×8 draughts. Play vs AI or friend.</p>
    <div class="game-meta">
      <span class="badge">2 Players</span>
      <span class="badge ai">AI Opponent</span>
      <span class="badge">~10 min</span>
    </div>
  </div>
  <button class="btn-play" data-game="checkers">Play</button>
</article>
```
- Hover: subtle lift + border glow
- Click "Play" → opens `GameDetailModal`

---

## 2. Game Detail Modal

### Trigger
- Click "Play" on any `GameCard`
- ESC or backdrop click → close

### Structure
```html
<div id="game-modal" class="modal hidden" role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <div class="modal-backdrop"></div>
  <div class="modal-content">
    <button class="modal-close" aria-label="Close">&times;</button>
    <div class="modal-visual">
      <!-- Large board illustration / screenshot -->
      <canvas id="modal-board-preview" width="320" height="320"></canvas>
    </div>
    <div class="modal-info">
      <h2 id="modal-title">Checkers</h2>
      <p id="modal-desc">Classic 8×8 English draughts. Capture all opponent pieces or block them.</p>
      <dl class="modal-specs">
        <dt>Players</dt><dd>2</dd>
        <dt>Mode</dt><dd>Local / AI / Online (WebSocket)</dd>
        <dt>Est. time</dt><dd>5–15 min</dd>
        <dt>Difficulty</dt><dd>Easy / Medium / Hard (AI)</dd>
      </dl>
      <div class="modal-rules">
        <h4>Rules Summary</h4>
        <ul>
          <li>Move diagonally forward on dark squares</li>
          <li>Capture by jumping over opponent piece</li>
          <li>Multiple jumps allowed in one turn</li>
          <li>Reach back row → King (moves backward too)</li>
          <li>Win by capturing all or blocking opponent</li>
        </ul>
      </div>
      <button class="btn-primary btn-play-large" data-game="checkers">Play Now</button>
    </div>
  </div>
</div>
```

### Modal Board Preview
- Canvas rendering a static mid-game position (or animated idle)
- Reuses checkers rendering module (read-only)

---

## 3. Checkers Game View (`#game-view`)

### Layout
```html
<section id="game-view" class="page hidden">
  <header class="game-header">
    <button class="btn-back" id="btn-back-to-landing" aria-label="Back to games">←</button>
    <div class="game-status">
      <span id="turn-indicator">White to move</span>
      <span id="timer" class="hidden">00:00</span>
    </div>
    <div class="game-menu">
      <button id="btn-new-game">New Game</button>
      <button id="btn-resign">Resign</button>
    </div>
  </header>
  <main class="game-main">
    <aside class="sidebar" id="sidebar">
      <section class="panel captured" id="captured-white">
        <h4>Captured (White)</h4>
        <div class="pieces"></div>
      </section>
      <section class="panel history" id="move-history">
        <h4>Move History</h4>
        <ol id="history-list"></ol>
      </section>
      <section class="panel captured" id="captured-black">
        <h4>Captured (Black)</h4>
        <div class="pieces"></div>
      </section>
    </aside>
    <div class="board-wrapper">
      <canvas id="board-canvas" width="640" height="640"></canvas>
      <div class="board-overlay" id="board-overlay"></div>
    </div>
  </main>
</section>
```

### Board Rendering (Canvas)
- **Size**: 640×640 (80px squares), scaled via CSS `max-width: 100%`
- **Wood texture**: Procedural gradient or embedded pattern
- **Squares**: Alternating `#f0d9b5` (light) / `#b58863` (dark)
- **Pieces**: Circles with radial gradient for 3D look
  - White: `#ffffff` → `#e0e0e0` with subtle shadow
  - Black: `#222222` → `#000000`
  - King: Gold crown icon (Unicode ♔/♕ or drawn)
- **Animations** (CSS + JS):
  - Piece slide: 150ms ease-out
  - Capture fade: 200ms opacity + scale
  - King promotion: pulse + crown appear
  - Valid move highlight: pulsing dot on target squares

### Sidebar Panels
1. **Captured Pieces** — small piece icons stacked (max 12 visible, "+N" overflow)
2. **Move History** — algebraic notation (e.g., "1. e3-f4  e6-f5"), click to replay (future)
3. **Captured Pieces** — mirrored for opponent

### Responsive
- Desktop (>1024px): Sidebar left (280px), board center
- Tablet (768–1024px): Sidebar collapsible (hamburger), board larger
- Mobile (<768px): Sidebar hidden by default, slide-in drawer; board fills width

---

## 4. State Management (`app.js`)

### Sections
```js
const STATE = {
  currentView: 'landing', // 'landing' | 'modal' | 'game'
  selectedGame: null,
  game: {
    id: null,
    ws: null,
    myColor: null,
    board: null,
    history: [],
    captured: { w: [], b: [] },
    turn: 'w',
    status: 'waiting' // waiting | active | over
  }
};
```

### Navigation Functions
```js
function showLanding() { ... }
function openModal(gameId) { ... }
function closeModal() { ... }
function startGame(gameId) { ... }
function showGameView() { ... }
function backToLanding() { ... }
```

### WebSocket Integration
- Reuse existing `websocket_endpoint` logic
- On `color` message → set `myColor`, show board
- On `board` message → animate to new position, update history/captured
- On `game_over` → show modal with result, offer "Play Again"

---

## 5. CSS Architecture

### Variables (`:root`)
```css
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
}
```

### Component Classes
- `.page` — section visibility (`active` / `hidden`)
- `.game-card`, `.game-thumb`, `.game-info`, `.badge`, `.btn-play`
- `.modal`, `.modal-backdrop`, `.modal-content`, `.modal-visual`, `.modal-specs`
- `.game-header`, `.game-status`, `.game-menu`
- `.game-main`, `.sidebar`, `.panel`, `.board-wrapper`, `#board-canvas`

---

## 6. File Structure
```
static/
├── index.html          # Landing + Modal + Game View (all sections)
├── app.js              # SPA controller, navigation, WS glue
├── styles.css          # All styles (variables, components, responsive)
├── games/
│   └── checkers/
│       ├── board.js    # Canvas rendering, animations
│       ├── logic.js    # Move validation, legal moves (mirror of Python)
│       └── preview.js  # Modal board preview renderer
```

---

## 7. Implementation Phases

| Phase | Deliverable |
|-------|-------------|
| 1 | Landing page HTML/CSS + GameCard grid (static data) |
| 2 | GameDetailModal with preview canvas |
| 3 | GameView layout + board canvas rendering (static position) |
| 4 | Piece animations (slide, capture, promote) |
| 5 | Sidebar: captured pieces + move history |
| 6 | WebSocket integration: create game, join, moves, AI |
| 7 | Responsive polish, accessibility (ARIA, keyboard) |
| 8 | Build Docker image, verify |

---

## 8. Open Questions (Resolved in Spec)

| Question | Decision |
|----------|----------|
| Single vs multi-page | SPA (Approach 1) |
| Routing | Hash-based optional later; no router v1 |
| AI difficulty selector | In modal specs; default "Medium" |
| Timer | Optional; hidden by default |
| Sound effects | Not in v1 |
| Themes (light/dark) | Dark only v1; CSS vars ready for light |

---

## 9. Acceptance Criteria

- [ ] Landing loads at `/` with hero + at least 1 game card (Checkers)
- [ ] Click "Play" → modal opens with preview, rules, "Play Now"
- [ ] "Play Now" → game view shows board, sidebar, header
- [ ] Board renders correctly with wood texture, pieces, kings
- [ ] Valid moves highlighted on piece selection
- [ ] Piece animates smoothly to target square
- [ ] Captured pieces appear in sidebar
- [ ] Move history updates in algebraic notation
- [ ] WebSocket: create game, connect, receive color, make move, see opponent/AI move
- [ ] Game over modal shows winner, "Play Again" works
- [ ] Responsive: works on mobile (375px), tablet (768px), desktop (1440px)
- [ ] Docker build succeeds, container runs, accessible at `localhost:8000`