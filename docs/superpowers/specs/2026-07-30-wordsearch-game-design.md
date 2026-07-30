# Word Search Game Design Spec

## Overview
Add a classic Word Search (Caça-Palavras) game to the GameHub platform. Single-player, client-side only, with configurable difficulty, categories, timer, hints, and touch support.

## Architecture
- **Client-side only**: All logic runs in browser (grid generation, word placement, selection, timer, leaderboard via localStorage)
- **Static files only**: No backend changes; FastAPI continues to serve `/` → `index.html` and `/static/*`
- **Module structure**: Follows existing `static/games/checkers/` pattern
- **SPA integration**: Reuses existing modal system and navigation in `app.js`

---

## 1. Game Data (`static/games/wordsearch/words.js`)

### Categories
```js
export const CATEGORIES = {
  animals: { name: 'Animais', words: ['CACHORRO', 'GATO', 'ELEFANTE', 'GIRAFA', 'LEAO', 'MACACO', 'PAPAGAIO', 'TARTARUGA', 'ZEBRA', 'COBRA'] },
  countries: { name: 'Países', words: ['BRASIL', 'ARGENTINA', 'CANADA', 'FRANCA', 'ALEMANHA', 'ITALIA', 'JAPAO', 'MEXICO', 'PORTUGAL', 'ESPANHA'] },
  tech: { name: 'Tecnologia', words: ['COMPUTADOR', 'INTERNET', 'SOFTWARE', 'HARDWARE', 'PYTHON', 'JAVASCRIPT', 'DATABASE', 'ALGORITMO', 'SERVIDOR', 'ROTEADOR'] },
  food: { name: 'Comida', words: ['PIZZA', 'HAMBURGUER', 'SUSHI', 'CHURRASCO', 'LASANHA', 'SALADA', 'SOBREMESA', 'CHOCOLATE', 'FRUTAS', 'VEGETAIS'] },
  sports: { name: 'Esportes', words: ['FUTEBOL', 'BASQUETE', 'VOLEI', 'NATACAO', 'TENIS', 'CORRIDA', 'CICLISMO', 'BOXE', 'GOLFE', 'SURFE'] },
  random: { name: 'Aleatório', words: [] } // Filled from all categories
};
```

### Difficulty Config
```js
export const DIFFICULTIES = {
  easy:   { gridSize: 10, wordCount: 6,  directions: 4,  name: 'Fácil',   timeBonus: 300 },
  medium: { gridSize: 12, wordCount: 10, directions: 8,  name: 'Médio',   timeBonus: 180 },
  hard:   { gridSize: 15, wordCount: 15, directions: 8,  name: 'Difícil', timeBonus: 120 }
};
// directions: 4 = H/V only, 8 = all 8 directions
```

---

## 2. Game Logic (`static/games/wordsearch/logic.js`)

### Exports
- `createGrid(config)` → `{ grid: string[][], placedWords: PlacedWord[] }`
- `getWordAt(grid, r, c, dr, dc, length)` → string
- `checkWordFound(grid, word, placedWords)` → boolean
- `getAllWords(grid, placedWords)` → string[]

### PlacedWord Type
```js
{ word: string, start: [r,c], end: [r,c], direction: [dr,dc], found: boolean }
```

### Grid Generation Algorithm
1. Create empty `gridSize x gridSize` array filled with `null`
2. For each word (shuffled, take `wordCount`):
   - Try up to 100 random positions + directions
   - Check if word fits (bounds + no conflicts with different letters)
   - Place word, record `PlacedWord`
   - If fails after 100 tries → reduce word count, continue
3. Fill remaining `null` cells with random letters (A-Z)
4. Return grid + placedWords

### Directions (8 total)
```js
const DIRS_4 = [[0,1], [1,0], [0,-1], [-1,0]]; // H + V
const DIRS_8 = [...DIRS_4, [1,1], [1,-1], [-1,1], [-1,-1]]; // + diagonals
```

---

## 3. Board Rendering (`static/games/wordsearch/board.js`)

### Class: `WordSearchGame`
```js
constructor(canvasId) { ... }
async init(config) { ... }  // config: { category, difficulty, grid, placedWords }
render() { ... }
handlePointerDown(e) { ... }
handlePointerMove(e) { ... }
handlePointerUp(e) { ... }
checkSelection() { ... }
updateUI() { ... }
```

### Visual Spec
- **Canvas**: Square, responsive (max 600px), cells = canvasSize / gridSize
- **Cells**: White background, dark border, centered letter (font: monospace, size = cell * 0.6)
- **Selection**: Blue semi-transparent overlay on dragged cells
- **Found words**: Green permanent highlight on word cells + strikethrough in word list
- **Current selection**: Blue highlight
- **Hover (desktop)**: Light highlight on cell under cursor

### Touch Support
- `pointerdown` / `pointermove` / `pointerup` (works for mouse + touch)
- Drag to select letters in straight line
- Auto-detect direction from first two points
- Visual feedback during drag

### Word List Sidebar (reuses captured panels)
- Left panel: Word list with checkboxes
- Found words: `text-decoration: line-through`, green color
- Scrollable if many words

---

## 4. Timer & Leaderboard (`static/games/wordsearch/timer.js`)

### Timer
- Count-up from 00:00
- Display in game header (reuses `#timer` element)
- Starts on first interaction, stops when all words found
- Format: `MM:SS`

### Leaderboard (localStorage)
```js
// Key: 'wordsearch_leaderboard'
// Value: [{ difficulty, category, time, date, gridSize, wordCount }, ...]
// Max 10 entries per difficulty
```

### Functions
- `startTimer()` / `stopTimer()` / `getTime()`
- `saveScore(config, time)` → updates leaderboard
- `getLeaderboard(difficulty)` → top 10
- `renderLeaderboard(containerId, difficulty)` → HTML table

---

## 5. Modal Preview (`static/games/wordsearch/preview.js`)

```js
export function renderPreview(canvasId) { ... }
```
- Renders a small static grid (8x8) with 3-4 sample words
- Uses same rendering logic as board.js (simplified)

---

## 6. SPA Integration (`static/app.js` modifications)

### Add to GAMES object
```js
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

### Dynamic Modal for Word Search
- When `gameId === 'wordsearch'`:
  - Show difficulty selector (radio buttons)
  - Show category selector (dropdown)
  - "Play Now" passes config to `startGame()`

### Game View Routing
```js
async function startGame(gameId) {
  if (gameId === 'wordsearch') {
    // Collect config from modal
    const config = getWordSearchConfig();
    await startWordSearch(config);
    return;
  }
  // ... existing checkers logic
}
```

---

## 7. File Structure
```
static/
├── index.html          # (existing, unchanged)
├── app.js              # (modified: add wordsearch to GAMES, startWordSearch)
├── styles.css          # (add wordsearch-specific styles)
└── games/
    ├── checkers/       # (existing)
    └── wordsearch/
        ├── logic.js    # Grid generation, word placement
        ├── board.js    # Canvas rendering, selection, touch
        ├── preview.js  # Modal preview
        ├── words.js    # Word lists, categories, difficulties
        └── timer.js    # Timer, leaderboard
```

---

## 8. CSS Additions (`static/styles.css`)

### Word Search Specific
```css
/* Word list in sidebar */
.word-list { list-style: none; display: grid; gap: 0.3rem; }
.word-list li { padding: 0.4rem 0.6rem; background: var(--bg-card); border-radius: 4px; font-family: var(--font-mono); font-size: 0.85rem; transition: all var(--transition); }
.word-list li.found { text-decoration: line-through; color: #4ade80; background: rgba(74, 222, 128, 0.1); }
.word-list li.current { background: var(--accent); color: white; }

/* Difficulty/category selectors in modal */
.config-group { margin-bottom: 1rem; }
.config-group label { display: block; margin-bottom: 0.3rem; font-size: 0.85rem; color: var(--text-secondary); }
.config-group select, .config-group input { width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: calc(var(--radius) - 4px); color: var(--text-primary); }
.config-group input[type="radio"] { width: auto; margin-right: 0.5rem; }

/* Canvas grid lines (for debugging) */
.ws-cell { /* cell styles handled in canvas */ }
```

---

## 9. Acceptance Criteria

- [ ] Landing page shows "Caça-Palavras" card alongside Checkers
- [ ] Click "Play" → modal opens with difficulty + category selectors
- [ ] Click "Play Now" → game view loads with grid
- [ ] Grid renders correctly at selected size (10/12/15)
- [ ] Words placed in correct directions (4 for easy, 8 for med/hard)
- [ ] Mouse drag selects letters in straight line
- [ ] Touch swipe selects letters on mobile
- [ ] Valid word found → highlighted green, crossed off list
- [ ] Invalid selection → clears on release
- [ ] Timer starts on first selection, stops when complete
- [ ] Completion shows modal with time + "Save Score" + "Play Again"
- [ ] Leaderboard shows top 10 per difficulty (localStorage)
- [ ] Hint button reveals first letter of a random unfound word
- [ ] Responsive: works on mobile (375px), tablet (768px), desktop (1440px)
- [ ] Docker build succeeds, container runs at `localhost:8000`

---

## 10. Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Game type | Classic word search grid |
| Multiplayer | Single player only |
| Difficulty | Configurable (Easy/Medium/Hard) |
| Word lists | Themed categories + Random |
| Directions | 8 directions (4 for Easy) |
| Features | Timer, leaderboard, hints, touch support |
| Architecture | Client-side only (Approach 1) |