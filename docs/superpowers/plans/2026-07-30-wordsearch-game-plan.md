# Word Search Game Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a classic Word Search (Caça-Palavras) game to GameHub with configurable difficulty, categories, timer, hints, and touch support — all client-side.

**Architecture:** Client-side only vanilla ES6 modules following existing `static/games/checkers/` pattern. SPA integration via existing `app.js` navigation and modal system. No backend changes.

**Tech Stack:** HTML5 Canvas, Vanilla ES6+ JS (modules), CSS3 (Grid, Flexbox, Custom Properties), localStorage for leaderboard.

## Global Constraints
- Tag must be `games:latest`.
- Use existing `python:3.11-slim` base image for both Docker stages.
- Runtime command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- No additional OS packages unless required.
- Dark theme only (CSS variables ready for light).
- No external JS frameworks; vanilla ES6 modules.
- Responsive: mobile (375px), tablet (768px), desktop (1440px).
- Accessibility: ARIA labels, keyboard navigation, focus visible.
- Follow existing file structure: `static/games/wordsearch/` with logic.js, board.js, preview.js, words.js, timer.js.

---

### Task 1: Create Word Search module scaffolds and word lists

**Files:**
- Create: `static/games/wordsearch/words.js`
- Create: `static/games/wordsearch/logic.js`
- Create: `static/games/wordsearch/board.js`
- Create: `static/games/wordsearch/preview.js`
- Create: `static/games/wordsearch/timer.js`

**Interfaces:**
- Produces: Module scaffolds with exports matching spec

- [ ] **Step 1: Create words.js with categories and difficulties**
```js
// static/games/wordsearch/words.js
export const CATEGORIES = {
  animals: { name: 'Animais', words: ['CACHORRO', 'GATO', 'ELEFANTE', 'GIRAFA', 'LEAO', 'MACACO', 'PAPAGAIO', 'TARTARUGA', 'ZEBRA', 'COBRA', 'TIGRE', 'URSO', 'LOBO', 'RAPOSA', 'COELHO'] },
  countries: { name: 'Países', words: ['BRASIL', 'ARGENTINA', 'CANADA', 'FRANCA', 'ALEMANHA', 'ITALIA', 'JAPAO', 'MEXICO', 'PORTUGAL', 'ESPANHA', 'CHINA', 'INDIA', 'AUSTRALIA', 'EGITO', 'NORUEGA'] },
  tech: { name: 'Tecnologia', words: ['COMPUTADOR', 'INTERNET', 'SOFTWARE', 'HARDWARE', 'PYTHON', 'JAVASCRIPT', 'DATABASE', 'ALGORITMO', 'SERVIDOR', 'ROTEADOR', 'FIREWALL', 'CLOUD', 'SOCKET', 'API', 'FRAMEWORK'] },
  food: { name: 'Comida', words: ['PIZZA', 'HAMBURGUER', 'SUSHI', 'CHURRASCO', 'LASANHA', 'SALADA', 'SOBREMESA', 'CHOCOLATE', 'FRUTAS', 'VEGETAIS', 'PASTEL', 'TORTA', 'BOLO', 'SORVETE', 'CAFE'] },
  sports: { name: 'Esportes', words: ['FUTEBOL', 'BASQUETE', 'VOLEI', 'NATACAO', 'TENIS', 'CORRIDA', 'CICLISMO', 'BOXE', 'GOLFE', 'SURFE', 'SKATE', 'HIPISMO', 'REMO', 'VELA', 'ESGRIMA'] }
};

export function getRandomCategory() {
  const cats = Object.keys(CATEGORIES).filter(k => k !== 'random');
  return cats[Math.floor(Math.random() * cats.length)];
}

export function getWordsForCategory(category, count) {
  if (category === 'random') {
    const cat = getRandomCategory();
    return getWordsForCategory(cat, count);
  }
  const words = [...CATEGORIES[category].words];
  // Shuffle and take count
  for (let i = words.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [words[i], words[j]] = [words[j], words[i]];
  }
  return words.slice(0, count);
}

export const DIFFICULTIES = {
  easy:   { gridSize: 10, wordCount: 6,  directions: 4,  name: 'Fácil',   timeBonus: 300 },
  medium: { gridSize: 12, wordCount: 10, directions: 8,  name: 'Médio',   timeBonus: 180 },
  hard:   { gridSize: 15, wordCount: 15, directions: 8,  name: 'Difícil', timeBonus: 120 }
};

export const DIRS_4 = [[0,1], [1,0], [0,-1], [-1,0]];
export const DIRS_8 = [[0,1], [1,0], [0,-1], [-1,0], [1,1], [1,-1], [-1,1], [-1,-1]];
```

- [ ] **Step 2: Create logic.js scaffold with exports**
```js
// static/games/wordsearch/logic.js
import { DIRS_4, DIRS_8 } from './words.js';

export function createGrid(config) { ... }
export function getWordAt(grid, r, c, dr, dc, length) { ... }
export function checkWordFound(grid, word, placedWords) { ... }
export function getAllWords(grid, placedWords) { ... }
```

- [ ] **Step 3: Create board.js scaffold**
```js
// static/games/wordsearch/board.js
export class WordSearchGame { ... }
```

- [ ] **Step 4: Create preview.js scaffold**
```js
// static/games/wordsearch/preview.js
export function renderPreview(canvasId) { ... }
```

- [ ] **Step 5: Create timer.js scaffold**
```js
// static/games/wordsearch/timer.js
export function startTimer() { ... }
export function stopTimer() { ... }
export function getTime() { ... }
export function saveScore(config, time) { ... }
export function getLeaderboard(difficulty) { ... }
export function renderLeaderboard(containerId, difficulty) { ... }
```

- [ ] **Step 6: Verify files exist**
```bash
ls -la static/games/wordsearch/
```

- [ ] **Step 7: Commit**
```bash
git add static/games/wordsearch/
git commit -m "feat: add wordsearch module scaffolds and word lists"
```

---

### Task 2: Implement grid generation logic

**Files:**
- Modify: `static/games/wordsearch/logic.js` (full implementation)

**Interfaces:**
- Consumes: `words.js` (DIRS_4, DIRS_8)
- Produces: `createGrid(config)` returning `{ grid, placedWords }`

- [ ] **Step 1: Implement createGrid**
```js
// static/games/wordsearch/logic.js
import { DIRS_4, DIRS_8 } from './words.js';

export function createGrid(config) {
  const { gridSize, wordCount, directions } = config;
  const dirs = directions === 4 ? DIRS_4 : DIRS_8;
  
  // Empty grid
  const grid = Array(gridSize).fill(null).map(() => Array(gridSize).fill(null));
  const placedWords = [];
  const words = config.words; // Already selected and shuffled
  
  for (const word of words) {
    let placed = false;
    let attempts = 0;
    
    while (!placed && attempts < 100) {
      attempts++;
      const dir = dirs[Math.floor(Math.random() * dirs.length)];
      const [dr, dc] = dir;
      const len = word.length;
      
      // Calculate valid start range
      let minR = 0, maxR = gridSize - 1;
      let minC = 0, maxC = gridSize - 1;
      
      if (dr === 1) maxR = gridSize - len;
      else if (dr === -1) minR = len - 1;
      if (dc === 1) maxC = gridSize - len;
      else if (dc === -1) minC = len - 1;
      
      if (minR > maxR || minC > maxC) continue;
      
      const r = Math.floor(Math.random() * (maxR - minR + 1)) + minR;
      const c = Math.floor(Math.random() * (maxC - minC + 1)) + minC;
      
      // Check if word fits
      let fits = true;
      for (let i = 0; i < len; i++) {
        const nr = r + dr * i;
        const nc = c + dc * i;
        const existing = grid[nr][nc];
        if (existing && existing !== word[i]) {
          fits = false;
          break;
        }
      }
      
      if (fits) {
        // Place word
        for (let i = 0; i < len; i++) {
          const nr = r + dr * i;
          const nc = c + dc * i;
          grid[nr][nc] = word[i];
        }
        placedWords.push({
          word,
          start: [r, c],
          end: [r + dr * (len - 1), c + dc * (len - 1)],
          direction: dir,
          found: false
        });
        placed = true;
      }
    }
    
    if (!placed) {
      console.warn(`Could not place word: ${word}`);
    }
  }
  
  // Fill empty cells with random letters
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {
      if (!grid[r][c]) {
        grid[r][c] = letters[Math.floor(Math.random() * letters.length)];
      }
    }
  }
  
  return { grid, placedWords };
}

export function getWordAt(grid, r, c, dr, dc, length) {
  let word = '';
  for (let i = 0; i < length; i++) {
    const nr = r + dr * i;
    const nc = c + dc * i;
    if (nr < 0 || nr >= grid.length || nc < 0 || nc >= grid[0].length) return null;
    word += grid[nr][nc];
  }
  return word;
}

export function checkWordFound(grid, word, placedWords) {
  const placed = placedWords.find(p => p.word === word && !p.found);
  if (placed) {
    placed.found = true;
    return true;
  }
  return false;
}

export function getAllWords(grid, placedWords) {
  return placedWords.map(p => p.word);
}
```

- [ ] **Step 2: Commit**
```bash
git add static/games/wordsearch/logic.js
git commit -m "feat: implement wordsearch grid generation logic"
```

---

### Task 3: Implement board rendering and selection

**Files:**
- Modify: `static/games/wordsearch/board.js` (full implementation)

**Interfaces:**
- Consumes: `logic.js` (for validation if needed)
- Produces: `WordSearchGame` class with render, pointer handling

- [ ] **Step 1: Implement WordSearchGame class**
```js
// static/games/wordsearch/board.js
export class WordSearchGame {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.grid = null;
    this.placedWords = [];
    this.config = null;
    this.cellSize = 0;
    this.selecting = false;
    this.selectionStart = null;
    this.selectionEnd = null;
    this.currentWord = '';
    this.foundWords = new Set();
    this.hintUsed = false;
    
    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.canvas.addEventListener('pointerdown', (e) => this.handlePointerDown(e));
    this.canvas.addEventListener('pointermove', (e) => this.handlePointerMove(e));
    this.canvas.addEventListener('pointerup', (e) => this.handlePointerUp(e));
    this.canvas.addEventListener('pointerleave', (e) => this.handlePointerUp(e));
    this.render();
  }
  
  resize() {
    const wrapper = this.canvas.parentElement;
    const maxSize = Math.min(wrapper.clientWidth - 40, wrapper.clientHeight - 40, 600);
    this.canvas.width = maxSize;
    this.canvas.height = maxSize;
    if (this.grid) this.cellSize = this.canvas.width / this.grid.length;
    this.render();
  }
  
  async init(config) {
    this.config = config;
    const { createGrid } = await import('./logic.js');
    const result = createGrid(config);
    this.grid = result.grid;
    this.placedWords = result.placedWords;
    this.cellSize = this.canvas.width / this.grid.length;
    this.foundWords.clear();
    this.hintUsed = false;
    this.render();
    this.updateWordList();
  }
  
  render() {
    if (!this.grid) return;
    const ctx = this.ctx;
    const size = this.canvas.width;
    const gs = this.grid.length;
    const cs = this.cellSize;
    
    // Clear
    ctx.clearRect(0, 0, size, size);
    
    // Background
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, size, size);
    
    // Draw cells
    for (let r = 0; r < gs; r++) {
      for (let c = 0; c < gs; c++) {
        const x = c * cs;
        const y = r * cs;
        
        // Cell background
        const isSelected = this.isCellSelected(r, c);
        const isFound = this.isCellFound(r, c);
        
        if (isFound) {
          ctx.fillStyle = 'rgba(74, 222, 128, 0.3)';
        } else if (isSelected) {
          ctx.fillStyle = 'rgba(233, 69, 96, 0.4)';
        } else {
          ctx.fillStyle = '#0f3460';
        }
        ctx.fillRect(x, y, cs, cs);
        
        // Border
        ctx.strokeStyle = '#2a2a4a';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, cs, cs);
        
        // Letter
        ctx.fillStyle = '#eaeaea';
        ctx.font = `bold ${cs * 0.55}px monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.grid[r][c], x + cs/2, y + cs/2 + 2);
      }
    }
    
    // Draw selection line
    if (this.selecting && this.selectionStart && this.selectionEnd) {
      ctx.strokeStyle = '#e94560';
      ctx.lineWidth = 4;
      ctx.lineCap = 'round';
      ctx.beginPath();
      const sx = this.selectionStart[1] * cs + cs/2;
      const sy = this.selectionStart[0] * cs + cs/2;
      const ex = this.selectionEnd[1] * cs + cs/2;
      const ey = this.selectionEnd[0] * cs + cs/2;
      ctx.moveTo(sx, sy);
      ctx.lineTo(ex, ey);
      ctx.stroke();
    }
  }
  
  isCellSelected(r, c) {
    if (!this.selecting || !this.selectionStart || !this.selectionEnd) return false;
    const [sr, sc] = this.selectionStart;
    const [er, ec] = this.selectionEnd;
    const dr = Math.sign(er - sr);
    const dc = Math.sign(ec - sc);
    // Check if (r,c) is on the line between start and end
    if (dr === 0 && dc === 0) return r === sr && c === sc;
    if (r < Math.min(sr, er) || r > Math.max(sr, er) || c < Math.min(sc, ec) || c > Math.max(sc, ec)) return false;
    return (r - sr) * dc === (c - sc) * dr;
  }
  
  isCellFound(r, c) {
    for (const pw of this.placedWords) {
      if (pw.found) {
        const [sr, sc] = pw.start;
        const [er, ec] = pw.end;
        const dr = Math.sign(er - sr);
        const dc = Math.sign(ec - sc);
        for (let i = 0; ; i++) {
          const cr = sr + dr * i;
          const cc = sc + dc * i;
          if (cr === r && cc === c) return true;
          if (cr === er && cc === ec) break;
        }
      }
    }
    return false;
  }
  
  getCellFromEvent(e) {
    const rect = this.canvas.getBoundingClientRect();
    const cs = this.cellSize;
    const c = Math.floor((e.clientX - rect.left) / cs);
    const r = Math.floor((e.clientY - rect.top) / cs);
    if (r < 0 || r >= this.grid.length || c < 0 || c >= this.grid.length) return null;
    return [r, c];
  }
  
  handlePointerDown(e) {
    const cell = this.getCellFromEvent(e);
    if (!cell) return;
    this.selecting = true;
    this.selectionStart = cell;
    this.selectionEnd = cell;
    this.currentWord = this.grid[cell[0]][cell[1]];
    this.render();
  }
  
  handlePointerMove(e) {
    if (!this.selecting) return;
    const cell = this.getCellFromEvent(e);
    if (!cell) return;
    this.selectionEnd = cell;
    // Build current word from start to end
    this.buildCurrentWord();
    this.render();
  }
  
  handlePointerUp(e) {
    if (!this.selecting) return;
    this.selecting = false;
    this.checkSelection();
    this.selectionStart = null;
    this.selectionEnd = null;
    this.currentWord = '';
    this.render();
  }
  
  buildCurrentWord() {
    if (!this.selectionStart || !this.selectionEnd) return;
    const [sr, sc] = this.selectionStart;
    const [er, ec] = this.selectionEnd;
    const dr = Math.sign(er - sr);
    const dc = Math.sign(ec - sc);
    let word = '';
    for (let r = sr, c = sc; ; r += dr, c += dc) {
      word += this.grid[r][c];
      if (r === er && c === ec) break;
    }
    this.currentWord = word;
  }
  
  checkSelection() {
    if (!this.currentWord || this.currentWord.length < 2) return;
    // Check both directions
    const reversed = this.currentWord.split('').reverse().join('');
    for (const pw of this.placedWords) {
      if (!pw.found && (pw.word === this.currentWord || pw.word === reversed)) {
        pw.found = true;
        this.foundWords.add(pw.word);
        this.updateWordList();
        this.checkWin();
        break;
      }
    }
  }
  
  checkWin() {
    if (this.foundWords.size === this.placedWords.length) {
      this.onWin?.();
    }
  }
  
  updateWordList() {
    const list = document.getElementById('word-list');
    if (!list) return;
    list.innerHTML = this.placedWords.map(pw => `
      <li class="${pw.found ? 'found' : ''}" data-word="${pw.word}">
        ${pw.word}
      </li>
    `).join('');
  }
  
  useHint() {
    if (this.hintUsed) return;
    const unfound = this.placedWords.filter(pw => !pw.found);
    if (unfound.length === 0) return;
    const random = unfound[Math.floor(Math.random() * unfound.length)];
    const [r, c] = random.start;
    // Briefly highlight the first letter
    this.hintUsed = true;
    this.render();
    // Could show a toast or highlight the cell
    setTimeout(() => this.render(), 2000);
  }
  
  onWin() {
    // Override in app.js
  }
}
```

- [ ] **Step 2: Commit**
```bash
git add static/games/wordsearch/board.js
git commit -m "feat: implement wordsearch board rendering and selection"
```

---

### Task 4: Implement timer and leaderboard

**Files:**
- Modify: `static/games/wordsearch/timer.js` (full implementation)

**Interfaces:**
- Produces: Timer functions, leaderboard localStorage management

- [ ] **Step 1: Implement timer.js**
```js
// static/games/wordsearch/timer.js
let timerInterval = null;
let startTime = 0;
let elapsed = 0;

export function startTimer() {
  if (timerInterval) return;
  startTime = Date.now() - elapsed;
  timerInterval = setInterval(() => {
    elapsed = Date.now() - startTime;
    updateTimerDisplay();
  }, 100);
}

export function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

export function resetTimer() {
  stopTimer();
  elapsed = 0;
  updateTimerDisplay();
}

export function getTime() {
  return elapsed;
}

export function getFormattedTime() {
  const totalSeconds = Math.floor(elapsed / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function updateTimerDisplay() {
  const el = document.getElementById('timer');
  if (el) el.textContent = getFormattedTime();
}

const LEADERBOARD_KEY = 'wordsearch_leaderboard';

export function saveScore(config, timeMs) {
  const { difficulty, category, gridSize, wordCount } = config;
  const entry = {
    difficulty,
    category,
    time: timeMs,
    formattedTime: formatTime(timeMs),
    date: new Date().toISOString(),
    gridSize,
    wordCount
  };
  
  const board = getLeaderboard(difficulty);
  board.push(entry);
  board.sort((a, b) => a.time - b.time);
  const top10 = board.slice(0, 10);
  localStorage.setItem(`${LEADERBOARD_KEY}_${difficulty}`, JSON.stringify(top10));
}

export function getLeaderboard(difficulty) {
  const data = localStorage.getItem(`${LEADERBOARD_KEY}_${difficulty}`);
  return data ? JSON.parse(data) : [];
}

export function renderLeaderboard(containerId, difficulty) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const board = getLeaderboard(difficulty);
  if (board.length === 0) {
    container.innerHTML = '<p class="text-secondary">Nenhum recorde ainda. Seja o primeiro!</p>';
    return;
  }
  container.innerHTML = `
    <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
      <thead>
        <tr style="border-bottom:1px solid var(--border);">
          <th style="text-align:left; padding:0.5rem;">#</th>
          <th style="text-align:left; padding:0.5rem;">Tempo</th>
          <th style="text-align:left; padding:0.5rem;">Categoria</th>
          <th style="text-align:left; padding:0.5rem;">Data</th>
        </tr>
      </thead>
      <tbody>
        ${board.map((e, i) => `
          <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:0.5rem;">${i+1}</td>
            <td style="padding:0.5rem; font-family:var(--font-mono);">${e.formattedTime}</td>
            <td style="padding:0.5rem;">${e.category}</td>
            <td style="padding:0.5rem; color:var(--text-secondary);">${new Date(e.date).toLocaleDateString()}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function formatTime(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}
```

- [ ] **Step 2: Commit**
```bash
git add static/games/wordsearch/timer.js
git commit -m "feat: implement wordsearch timer and leaderboard"
```

---

### Task 5: Implement modal preview

**Files:**
- Modify: `static/games/wordsearch/preview.js` (full implementation)

**Interfaces:**
- Consumes: `logic.js`, `board.js` (drawBoard equivalent)
- Produces: `renderPreview(canvasId)` for modal

- [ ] **Step 1: Implement preview.js**
```js
// static/games/wordsearch/preview.js
import { createGrid } from './logic.js';
import { DIFFICULTIES } from './words.js';

export function renderPreview(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  // Small preview config
  const config = {
    gridSize: 8,
    wordCount: 4,
    directions: 4,
    words: ['GATO', 'CACHORRO', 'SOL', 'LUA']
  };
  
  const { grid } = createGrid(config);
  const size = canvas.width;
  const gs = grid.length;
  const cs = size / gs;
  
  ctx.clearRect(0, 0, size, size);
  ctx.fillStyle = '#1a1a2e';
  ctx.fillRect(0, 0, size, size);
  
  for (let r = 0; r < gs; r++) {
    for (let c = 0; c < gs; c++) {
      const x = c * cs;
      const y = r * cs;
      ctx.fillStyle = '#0f3460';
      ctx.fillRect(x, y, cs, cs);
      ctx.strokeStyle = '#2a2a4a';
      ctx.lineWidth = 0.5;
      ctx.strokeRect(x, y, cs, cs);
      ctx.fillStyle = '#eaeaea';
      ctx.font = `bold ${cs * 0.5}px monospace`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(grid[r][c], x + cs/2, y + cs/2 + 1);
    }
  }
}
```

- [ ] **Step 2: Commit**
```bash
git add static/games/wordsearch/preview.js
git commit -m "feat: implement wordsearch modal preview"
```

---

### Task 6: Integrate Word Search into SPA (app.js)

**Files:**
- Modify: `static/app.js` (add wordsearch to GAMES, add startWordSearch, dynamic modal config)

**Interfaces:**
- Consumes: All wordsearch modules, existing SPA navigation
- Produces: Word Search playable from landing page

- [ ] **Step 1: Add wordsearch to GAMES object**
```js
// In static/app.js, add to GAMES object:
wordsearch: {
  id: 'wordsearch',
  title: 'Caça-Palavras',
  desc: 'Encontre palavras escondidas na grade. Múltiplas categorias e níveis de dificuldade.',
  shortDesc: 'Encontre palavras na grade. Várias categorias.',
  players: 1,
  modes: ['Solo', 'Timer', 'Ranking'],
  duration: '5–20 min',
  difficulty: ['Fácil', 'Médio', 'Difícil'],
  rules: [
    'Palavras podem estar horizontais, verticais ou diagonais',
    'Podem ser lidas da esquerda para direita ou vice-versa',
    'Arraste (ou clique) para selecionar letras da palavra',
    'Palavras encontradas ficam marcadas na lista',
    'Complete todas as palavras para vencer'
  ]
}
```

- [ ] **Step 2: Modify openModal to show config for wordsearch**
```js
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
    <dt>Difficulty</dt><dd>${game.difficulty.join(' / ')}</dd>
  `;
  modalRules.innerHTML = `
    <h4>Rules Summary</h4>
    <ul>${game.rules.map(r => `<li>${r}</li>`).join('')}</ul>
  `;
  
  if (gameId === 'wordsearch') {
    // Show config selectors
    modalRules.innerHTML += `
      <div class="config-group">
        <label>Dificuldade</label>
        <div>
          <label><input type="radio" name="ws-difficulty" value="easy" checked> Fácil (10×10, 6 palavras)</label>
        </div>
        <div>
          <label><input type="radio" name="ws-difficulty" value="medium"> Médio (12×12, 10 palavras)</label>
        </div>
        <div>
          <label><input type="radio" name="ws-difficulty" value="hard"> Difícil (15×15, 15 palavras)</label>
        </div>
      </div>
      <div class="config-group">
        <label>Categoria</label>
        <select id="ws-category">
          <option value="random">Aleatório</option>
          <option value="animals">Animais</option>
          <option value="countries">Países</option>
          <option value="tech">Tecnologia</option>
          <option value="food">Comida</option>
          <option value="sports">Esportes</option>
        </select>
      </div>
    `;
  }
  
  renderPreview('modal-board-preview');
  showView('modal');
}
```

- [ ] **Step 3: Add startWordSearch and config collection**
```js
async function startGame(gameId) {
  if (gameId === 'wordsearch') {
    const config = getWordSearchConfig();
    await startWordSearch(config);
    return;
  }
  // ... existing checkers logic
}

function getWordSearchConfig() {
  const difficulty = document.querySelector('input[name="ws-difficulty"]:checked')?.value || 'easy';
  const category = document.getElementById('ws-category')?.value || 'random';
  const diff = DIFFICULTIES[difficulty];
  const { getWordsForCategory } = await import('/static/games/wordsearch/words.js');
  const words = getWordsForCategory(category, diff.wordCount);
  return { ...diff, category, words };
}

async function startWordSearch(config) {
  closeModal();
  showView('game');
  STATE.currentGameType = 'wordsearch';
  STATE.game.id = 'wordsearch-' + Date.now(); // Local game ID
  
  // Initialize WordSearchGame
  if (!wordSearchGame) {
    const { WordSearchGame } = await import('/static/games/wordsearch/board.js');
    wordSearchGame = new WordSearchGame('board-canvas');
  }
  await wordSearchGame.init(config);
  
  // Setup timer
  const { startTimer, stopTimer, getTime, saveScore } = await import('/static/games/wordsearch/timer.js');
  wordSearchGame.onWin = () => {
    stopTimer();
    const time = getTime();
    saveScore(config, time);
    showWinModal(time);
  };
  startTimer();
  
  // Update UI for wordsearch mode
  updateGameViewForWordSearch();
}

let wordSearchGame = null;

function updateGameViewForWordSearch() {
  // Replace sidebar with word list
  const sidebar = document.getElementById('sidebar');
  sidebar.innerHTML = `
    <section class="panel word-list-panel">
      <h4>Palavras</h4>
      <ul class="word-list" id="word-list"></ul>
    </section>
    <section class="panel leaderboard-panel">
      <h4>Ranking</h4>
      <div id="leaderboard-container"></div>
    </section>
  `;
  
  // Add hint button to game menu
  const gameMenu = document.querySelector('.game-menu');
  if (gameMenu && !document.getElementById('btn-hint')) {
    const hintBtn = document.createElement('button');
    hintBtn.id = 'btn-hint';
    hintBtn.className = 'btn-secondary';
    hintBtn.textContent = 'Dica';
    hintBtn.addEventListener('click', () => wordSearchGame?.useHint());
    gameMenu.insertBefore(hintBtn, gameMenu.firstChild);
  }
  
  // Render leaderboard
  const { renderLeaderboard } = await import('/static/games/wordsearch/timer.js');
  const diff = document.querySelector('input[name="ws-difficulty"]:checked')?.value || 'easy';
  renderLeaderboard('leaderboard-container', diff);
}

function showWinModal(time) {
  const formatted = formatTime(time);
  alert(`Parabéns! Você completou em ${formatted}!`);
  // Could show a nicer modal with "Play Again" button
}

function formatTime(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}
```

- [ ] **Step 4: Add DIFFICULTIES import to app.js**
```js
// At top of app.js
import { DIFFICULTIES } from '/static/games/wordsearch/words.js';
```

- [ ] **Step 5: Commit**
```bash
git add static/app.js
git commit -m "feat: integrate wordsearch into SPA navigation and modal"
```

---

### Task 7: Add Word Search specific styles

**Files:**
- Modify: `static/styles.css` (add wordsearch styles)

**Interfaces:**
- Consumes: HTML from app.js, board.js rendering
- Produces: Styled word list, config selectors, responsive adjustments

- [ ] **Step 1: Add wordsearch styles**
```css
/* static/styles.css - append */

/* ===== WORD SEARCH SPECIFIC ===== */
.word-list-panel { flex: 1; overflow-y: auto; }
.word-list { list-style: none; display: grid; gap: 0.3rem; padding: 0.5rem; }
.word-list li { 
  padding: 0.5rem 0.75rem; 
  background: var(--bg-card); 
  border-radius: 6px; 
  font-family: var(--font-mono); 
  font-size: 0.9rem; 
  transition: all var(--transition);
  border: 1px solid transparent;
}
.word-list li.found { 
  text-decoration: line-through; 
  color: #4ade80; 
  background: rgba(74, 222, 128, 0.15);
  border-color: rgba(74, 222, 128, 0.3);
}
.word-list li.current { 
  background: var(--accent); 
  color: white; 
}

.leaderboard-panel { padding: 1rem; }
.leaderboard-panel h4 { margin-bottom: 0.75rem; }

/* Config selectors in modal */
.config-group { margin-bottom: 1rem; }
.config-group label { display: block; margin-bottom: 0.3rem; font-size: 0.85rem; color: var(--text-secondary); }
.config-group > label { font-weight: 500; }
.config-group div { margin: 0.3rem 0; }
.config-group input[type="radio"] { width: auto; margin-right: 0.5rem; accent-color: var(--accent); }
.config-group select { 
  width: 100%; 
  padding: 0.5rem; 
  background: var(--bg-card); 
  border: 1px solid var(--border); 
  border-radius: calc(var(--radius) - 4px); 
  color: var(--text-primary); 
  font-family: inherit;
}
.config-group select:focus { outline: 2px solid var(--accent); outline-offset: 2px; }

/* Hint button */
#btn-hint { background: var(--gold); color: var(--bg-primary); }
#btn-hint:hover { background: #e6c200; }

/* Win modal (if needed) */
.win-modal { /* reuse .modal styles */ }

/* Canvas touch action */
#board-canvas { touch-action: none; }

/* Responsive adjustments for wordsearch */
@media (max-width: 768px) {
  .word-list li { font-size: 0.8rem; padding: 0.4rem 0.5rem; }
  .leaderboard-panel { padding: 0.75rem; }
}
```

- [ ] **Step 2: Commit**
```bash
git add static/styles.css
git commit -m "feat: add wordsearch specific styles"
```

---

### Task 8: Build Docker image and verify

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
curl -s http://localhost:8000/ | grep -c "Caça-Palavras"
curl -s http://localhost:8000/static/games/wordsearch/logic.js | head -1
curl -s http://localhost:8000/static/games/wordsearch/board.js | head -1
curl -s http://localhost:8000/static/games/wordsearch/words.js | head -1
curl -s http://localhost:8000/static/games/wordsearch/timer.js | head -1
curl -s http://localhost:8000/static/games/wordsearch/preview.js | head -1
```

- [ ] **Step 3: Manual browser test checklist**
   - [ ] Landing loads at `/` with hero + Checkers + Word Search cards
   - [ ] Click "Play" on Word Search → modal opens with difficulty + category selectors
   - [ ] Select difficulty/category → click "Play Now" → game view loads
   - [ ] Grid renders at correct size (10/12/15)
   - [ ] Words placed in correct directions (4 for easy, 8 for med/hard)
   - [ ] Mouse drag selects letters in straight line
   - [ ] Touch swipe selects letters on mobile (test in DevTools device toolbar)
   - [ ] Valid word found → highlighted green, crossed off list
   - [ ] Invalid selection → clears on release
   - [ ] Timer starts on first selection, stops when complete
   - [ ] Completion shows time + saves to leaderboard
   - [ ] Hint button reveals first letter of unfound word
   - [ ] Leaderboard shows top 10 per difficulty (localStorage persists)
   - [ ] "New Game" button creates fresh grid
   - [ ] Responsive: works on mobile (375px), tablet (768px), desktop (1440px)
   - [ ] Keyboard: Tab navigation, Escape closes modal
   - [ ] Reduced motion: no animations

- [ ] **Step 4: Commit final changes**
```bash
git add -A
git commit -m "feat: complete wordsearch game implementation"
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-07-30-wordsearch-game-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**