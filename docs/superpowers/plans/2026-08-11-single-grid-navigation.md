# Single-Grid Landing Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the duplicated featured/collections landing sections with a single game grid showing all 6 games exactly once, filterable by category, with no highlight badges.

**Architecture:** Extract pure game data/filtering/rendering logic from `static/app.js` into a new ES module `static/games.js`, testable via Node (mirroring `tests/test_play_url.py`). `app.js` consumes the module, rendering category tabs dynamically and a badge-free grid. `static/index.html` drops the featured and collections sections; orphaned CSS rules are removed.

**Tech Stack:** Vanilla ES modules (frontend), FastAPI/SQLModel (backend, unchanged), Python 3.14 + pytest (test runner), Node (module harness tests).

## Global Constraints

- The 6 game ids must remain exactly: `checkers`, `wordsearch`, `crossword`, `snake`, `ant_defense`, `tower_defense`.
- `allGames()` must return each id exactly once (no duplication).
- Grid cards must render **without** badges (no `game-badges` / `badge` / `Novo` / `Popular` / `Em Destaque`).
- Category tabs render only categories actually present in `GAMES`, plus an "all" tab; empty categories produce no tab.
- Do not alter backend, `/play/{game}`, the modal, or in-game flow.
- `GAMES` data (titles, ratings, players, categories, collections, etc.) is copied verbatim from `static/app.js:65-212` — do not change values.
- Category tab order: `acao`, `tabuleiro`, `palavras`, `estrategia`, `classicos` (matching the current static tabs).
- Run tests with `.venv/bin/python -m pytest`.

---

### Task 1: `static/games.js` — game data + filter + card rendering

**Files:**
- Create: `static/games.js`
- Test: `tests/test_games_list.py`

**Interfaces:**
- Consumes: nothing (standalone ES module).
- Produces (consumed by Task 2 and the test harness):
  - `GAMES` — object keyed by game id (verbatim copy from `app.js:65-212`).
  - `allGames()` → `Game[]`, values of `GAMES` sorted by `rating` descending.
  - `categories()` → `string[]`, keys of `CATEGORY_LABELS` that appear in at least one game, in order `acao, tabuleiro, palavras, estrategia, classicos`.
  - `gamesByCategory(category)` → `Game[]`; `category === 'all'` returns `allGames()`, otherwise games whose `category` array includes it; unknown category returns `[]`.
  - `gameCard(game)` → `string`, HTML `<article class="game-card">` with thumbnail, info, and hover overlay — **no badge markup**.

- [ ] **Step 1: Write the failing test**

Create `tests/test_games_list.py`:

```python
"""Guard the landing game data and filtering logic using the real module.

The harness runs the actual browser script (static/games.js) under Node,
so these checks track the module the browser loads — not a reimplementation.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

HARNESS = """
import { GAMES, allGames, categories, gamesByCategory, gameCard } from './games.js';

const GAME_IDS = Object.keys(GAMES);
const games = allGames();

const results = {
  ids: GAME_IDS,
  games,
  categoryList: categories(),
  byAll: gamesByCategory('all'),
  byUnknown: gamesByCategory('inexistente'),
  cards: Object.fromEntries(GAME_IDS.map(id => [id, gameCard(GAMES[id])])),
  groupedByCategory: Object.fromEntries(
    categories().map(cat => [cat, gamesByCategory(cat).map(g => g.id)])
  ),
};

// Duplication check: every category group must have unique ids.
results.byCategoryHasDuplicates = Object.fromEntries(
  categories().map(cat => {
    const ids = gamesByCategory(cat).map(g => g.id);
    return [cat, new Set(ids).size !== ids.length];
  })
);

// Badge/featured/collection leakage check on rendered cards.
results.cardLeaks = Object.fromEntries(
  GAME_IDS.map(id => ({
    badge: /game-badges|badge-novo|badge-popular|badge-destaque|Novo|Popular|Em Destaque/.test(gameCard(GAMES[id])),
    featured: /featured/.test(gameCard(GAMES[id])),
    collection: /collection/.test(gameCard(GAMES[id])),
  }))
);

console.log(JSON.stringify(results));
"""


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    work = tmp_path_factory.mktemp("games_list")
    shutil.copy(STATIC / "games.js", work / "games.js")
    (work / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    (work / "harness.mjs").write_text(HARNESS, encoding="utf-8")

    proc = subprocess.run(
        [node, "harness.mjs"], cwd=work, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_exports_exactly_the_six_games(result):
    assert set(result["ids"]) == {
        "checkers", "wordsearch", "crossword", "snake", "ant_defense", "tower_defense",
    }


def test_all_games_has_each_id_exactly_once(result):
    ids = [g["id"] for g in result["games"]]
    assert len(ids) == 6
    assert len(set(ids)) == 6


def test_all_games_sorted_by_rating_descending(result):
    ratings = [g["rating"] for g in result["games"]]
    assert ratings == sorted(ratings, reverse=True)


def test_categories_cover_every_game_category(result):
    used = {c for g in result["games"] for c in g["category"]}
    assert set(result["categoryList"]) == used


def test_by_all_returns_every_game(result):
    assert len(result["byAll"]) == 6
    assert set(g["id"] for g in result["byAll"]) == set(result["ids"])


def test_by_unknown_category_is_empty(result):
    assert result["byUnknown"] == []


def test_each_category_has_unique_games(result):
    assert all(not v for v in result["byCategoryHasDuplicates"].values())


def test_every_game_belongs_to_a_known_category(result):
    known = set(result["categoryList"])
    for g in result["games"]:
        assert set(g["category"]).issubset(known)


def test_cards_have_no_badge_featured_or_collection_markup(result):
    for id, leaks in result["cardLeaks"].items():
        assert not leaks["badge"], f"{id} leaked badge markup"
        assert not leaks["featured"], f"{id} leaked featured markup"
        assert not leaks["collection"], f"{id} leaked collection markup"


def test_each_card_references_its_own_game_once(result):
    for id, html in result["cards"].items():
        assert html.count(f'data-game="{id}"') == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_games_list.py -q`
Expected: FAIL — `harness failed` with `Cannot find module ... games.js` (file does not exist yet).

- [ ] **Step 3: Create `static/games.js`**

```js
// static/games.js
export const GAMES = {
  checkers: {
    id: 'checkers',
    title: 'Checkers',
    desc: 'Classic 8×8 English draughts. Capture all opponent pieces or block them completely.',
    shortDesc: 'Classic 8×8 draughts. Play vs AI or friend.',
    players: 2,
    modes: ['Local', 'AI', 'Online'],
    category: ['tabuleiro', 'estrategia', 'classicos'],
    collections: ['2-jogadores', 'classicos-atemporais'],
    duration: '5–15 min',
    difficulty: ['Easy', 'Medium', 'Hard'],
    rating: 4.8,
    plays: 125000,
    featured: true,
    badge: 'destaque',
    thumbnail: '',
    rules: [
      'Move diagonally forward on dark squares only',
      'Capture by jumping over an adjacent opponent piece',
      'Multiple jumps allowed in a single turn',
      'Reach the back row → become a King (moves backward too)',
      'Win by capturing all enemy pieces or blocking all moves'
    ]
  },
  wordsearch: {
    id: 'wordsearch',
    title: 'Caça-Palavras',
    desc: 'Encontre palavras escondidas na grade. Múltiplas categorias e níveis de dificuldade.',
    shortDesc: 'Encontre palavras na grade. Várias categorias.',
    players: 1,
    modes: ['Solo', 'Timer', 'Ranking'],
    category: ['palavras', 'classicos'],
    collections: ['treine-sua-mente', 'classicos-atemporais'],
    duration: '5–20 min',
    difficulty: ['Fácil', 'Médio', 'Difícil'],
    rating: 4.5,
    plays: 98000,
    featured: false,
    badge: 'popular',
    thumbnail: '',
    rules: [
      'Palavras podem estar horizontais, verticais ou diagonais',
      'Podem ser lidas da esquerda para direita ou vice-versa',
      'Arraste para selecionar letras da palavra',
      'Palavras encontradas ficam marcadas na lista',
      'Complete todas as palavras para vencer'
    ]
  },
  crossword: {
    id: 'crossword',
    title: 'Palavras Cruzadas',
    desc: 'Resolva palavras cruzadas geradas dinamicamente pelo servidor. Dicas across/down e multijogador.',
    shortDesc: 'Cruza palavras com dicas. Solo ou online.',
    players: '1–2',
    modes: ['Solo', 'Online'],
    category: ['palavras', 'classicos'],
    collections: ['treine-sua-mente'],
    duration: '5–25 min',
    difficulty: ['Fácil', 'Médio', 'Difícil'],
    rating: 4.7,
    plays: 64000,
    featured: false,
    badge: 'novo',
    thumbnail: '',
    rules: [
      'Clique numa dica ou célula para selecionar a palavra',
      'Digite a letra em cada célula; letras corretas ficam verdes',
      'Setas alternam entre horizontal e vertical',
      'Células pretas são blocos (não preenchíveis)',
      'Complete todo o grid para vencer. Dois jogadores podem resolver juntos'
    ]
  },
  snake: {
    id: 'snake',
    title: 'Snake',
    desc: 'Jogo da cobrinha moderno. Coma maçãs para crescer sem colidir com as paredes ou consigo mesmo.',
    shortDesc: 'Coma maçãs, cresça e não colida!',
    players: 1,
    modes: ['Solo', 'High Score'],
    category: ['acao', 'classicos'],
    collections: ['acao-pura', 'classicos-atemporais'],
    duration: '2–10 min',
    difficulty: ['Fácil', 'Médio', 'Difícil'],
    rating: 4.6,
    plays: 150000,
    featured: true,
    badge: 'popular',
    thumbnail: '',
    rules: [
      'Use setas ou WASD para controlar a cobrinha',
      'Coma maçãs vermelhas para crescer e ganhar pontos',
      'Não colida com as paredes ou com o próprio corpo',
      'A velocidade aumenta progressivamente',
      'Pause/Resume a qualquer momento'
    ]
  },
  tower_defense: {
    id: 'tower_defense',
    title: '🏰 Tower Defense',
    desc: 'Tower Defense estratégico onde formigas defendem o formigueiro contra invasores. Posicione torres estrategicamente!',
    shortDesc: 'Defenda o formigueiro com torres estratégicas!',
    players: 1,
    modes: ['Solo', 'Ondas Infinitas'],
    category: ['estrategia', 'acao'],
    collections: ['treine-sua-mente', 'acao-pura'],
    duration: '10–30 min',
    difficulty: ['Fácil', 'Médio', 'Difícil'],
    rating: 4.8,
    plays: 75000,
    featured: true,
    badge: 'novo',
    thumbnail: '🏰',
    icon: '🏰',
    rules: [
      'Posicione torres nas células marcadas do grid',
      'Cada torre custa ouro - derrote inimigos para ganhar mais',
      'Torres: Arqueiro (rápido), Bomba (área), Gelo (desacelera)',
      'Inimigos vêm em ondas - não deixe nenhum passar!',
      'Gerencie bem seu ouro para maximizar a defesa'
    ]
  },
  ant_defense: {
    id: 'ant_defense',
    title: '🐜 Ant Defense',
    desc: 'Defenda o formigueiro real contra invasores usando torres de formigas especializadas. Estratégia pura!',
    shortDesc: 'Formigas defendem o formigueiro!',
    players: 1,
    modes: ['Solo', 'Sobrevivência'],
    category: ['estrategia', 'acao'],
    collections: ['treine-sua-mente', 'acao-pura'],
    duration: '15–40 min',
    difficulty: ['Médio', 'Difícil', 'Expert'],
    rating: 4.9,
    plays: 45000,
    featured: true,
    badge: 'destaque',
    thumbnail: '🐜',
    icon: '🐜',
    rules: [
      'Construa torres de formigas ao longo do caminho',
      'Formiga Soldado: dano alto | Formiga Operária: rápido | Formiga Ácida: veneno',
      'Proteja a rainha no centro do formigueiro',
      'Invasores: Besouros (tanques), Moscas (rápidos), Lagartas (muita vida)',
      'Use estratégias combinadas para máxima eficiência'
    ]
  }
};

const CATEGORY_LABELS = {
  acao: 'Ação',
  tabuleiro: 'Tabuleiro',
  palavras: 'Palavras',
  estrategia: 'Estratégia',
  classicos: 'Clássicos',
};

export function allGames() {
  return Object.values(GAMES).sort((a, b) => b.rating - a.rating);
}

export function categories() {
  return Object.keys(CATEGORY_LABELS).filter(cat =>
    Object.values(GAMES).some(g => g.category && g.category.includes(cat))
  );
}

export function gamesByCategory(category) {
  if (category === 'all') return allGames();
  if (!category) return [];
  return Object.values(GAMES).filter(g => g.category && g.category.includes(category));
}

function formatPlays(plays) {
  if (plays >= 1000000) return (plays / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (plays >= 1000) return (plays / 1000).toFixed(0) + 'K';
  return String(plays);
}

function renderThumbnail(game) {
  if (game.icon) {
    return `<div class="game-icon-real">${game.icon}</div>`;
  }
  if (game.thumbnail) {
    return `<img src="${game.thumbnail}" alt="${game.title}">`;
  }
  return `<svg class="game-preview" viewBox="0 0 80 80" width="80" height="80">${generateGamePreviewSVG(game.id)}</svg>`;
}

function gameHoverOverlay(game) {
  return `
    <div class="game-hover-overlay">
      <h3>${game.title}</h3>
      <p class="game-desc">${game.shortDesc}</p>
      <div class="game-hover-meta">
        <span>★ <span class="val">${game.rating.toFixed(1)}</span></span>
        <span><span class="val">${formatPlays(game.plays)}</span> plays</span>
      </div>
      <button class="btn-play" data-game="${game.id}">Jogar</button>
    </div>
  `;
}

export function gameCard(game) {
  return `
    <article class="game-card" data-game="${game.id}">
      <div class="game-thumb">
        ${renderThumbnail(game)}
      </div>
      <div class="game-info">
        <h3>${game.title}</h3>
        <p class="game-desc">${game.shortDesc}</p>
        <div class="game-meta">
          <span class="badge">${game.players} Players</span>
          <span class="badge">${game.duration}</span>
        </div>
      </div>
      <button class="btn-play" data-game="${game.id}">Jogar Agora</button>
      ${gameHoverOverlay(game)}
    </article>
  `;
}

function generateGamePreviewSVG(gameId) {
  const square = 10;
  if (gameId === 'crossword') {
    const letters = { '1,1':'A','1,2':'P','1,3':'I','1,4':'O','1,5':'D','3,1':'C','4,1':'O','5,1':'D','5,2':'O','5,3':'M','5,4':'E','5,5':'S','2,3':'T','3,3':'A','4,3':'E' };
    let svg = '';
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const x = c * square, y = r * square;
        const key = `${r},${c}`;
        if (letters[key]) {
          svg += `<rect x="${x}" y="${y}" width="${square}" height="${square}" fill="#fff" stroke="#b58863" stroke-width="0.75"/>`;
          svg += `<text x="${x+5}" y="${y+6.5}" font-size="6" fill="#0f3460" text-anchor="middle" font-family="monospace">${letters[key]}</text>`;
        } else {
          svg += `<rect x="${x}" y="${y}" width="${square}" height="${square}" fill="#0f3460"/>`;
        }
      }
    }
    return svg;
  }
  if (gameId === 'wordsearch') {
    let svg = '';
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const x = c*square, y = r*square;
        svg += `<rect x="${x}" y="${y}" width="${square}" height="${square}" fill="#0f3460" stroke="#2a2a4a" stroke-width="0.5"/>`;
        const letter = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[(r*8+c) % 26];
        svg += `<text x="${x+5}" y="${y+7}" font-size="7" fill="#eaeaea" text-anchor="middle" font-family="monospace">${letter}</text>`;
      }
    }
    return svg;
  }
  let svg = '';
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      if ((r + c) % 2 === 0) {
        svg += `<rect x="${c*square}" y="${r*square}" width="${square}" height="${square}" fill="#b58863"/>`;
      }
    }
  }
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
```

> Note: `badge`, `featured`, `collections`, `icon`, `modes`, `difficulty`, `rules` remain in the `GAMES` objects (some are used by the modal in `app.js`) — the tests assert only that the *rendered card markup* leaks none of these terms.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_games_list.py -q`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add static/games.js tests/test_games_list.py
git commit -m "feat: extract game data, filtering and card rendering to games.js"
```

---

### Task 2: Rewire `app.js` to the extracted module

**Files:**
- Modify: `static/app.js`
- Test: `tests/test_static_js_imports.py`

**Interfaces:**
- Consumes: `GAMES`, `categories`, `gamesByCategory`, `gameCard` from `/static/games.js`.
- Produces: `renderCategoryTabs()` populates `.category-list`; `renderGameGrid(category)` populates `#game-grid` with badge-free cards; category clicks still filter through `activeCategory`.

- [ ] **Step 1: Add imports (already failing if referenced before definition — the test asserts names are exported)**

Change the import block at the top of `static/app.js` (line 6) to add:

```js
import { GAMES, categories, gamesByCategory, gameCard } from '/static/games.js';
```

- [ ] **Step 2: Remove `GAMES` and `COLLECTIONS` local definitions**

Delete from `static/app.js`:
- The entire `const GAMES = {...}` block (lines 64-212).
- The `// ===== COLLECTIONS DATA =====` block with `const COLLECTIONS = {...}` (lines 214-220).

- [ ] **Step 3: Remove featured and collections rendering + helpers**

Delete from `static/app.js`:
- `getBadgeLabel` (666-669), `getBadgeClass` (671-674), `renderBadge` (676-679).
- `renderThumbnail` (681-690), `renderHoverOverlay` (692-704), `formatPlays` (660-664).
- `renderFeaturedSpotlight` (706-733), `renderFeaturedSecondary` (735-764).
- The `featuredSection` listener (767-771).
- `// ===== COLLECTIONS =====` block: `collectionsContainer`, `activeCollectionFilteredGames`, `gamesForCollection`, `renderCollections`, and the `collectionsContainer` click listener (773-837).
- `renderGameGrid` (839-859) implementation — replaced in Step 4.
- `generateGamePreviewSVG` (861-914) — now lives in `games.js`.

Keep the modal helpers used by `openModal` (`renderPreview` import from checkers, describe title/specs/rules HTML) intact.

- [ ] **Step 4: Rebuild tab rendering and grid**

Replace the category-nav wiring section (lines 566-583) with:

```js
// ===== LANDING CATEGORY NAV =====
let activeCategory = 'all';
const categoryList = $('.category-list');
const categoryToggle = $('.category-toggle');

function renderCategoryTabs() {
  if (!categoryList) return;
  const tabs = [
    `<li><button class="category-tab active" data-category="all">Todos os Jogos</button></li>`,
    ...categories().map(cat =>
      `<li><button class="category-tab" data-category="${cat}">${cat}</button></li>`
    ),
  ].join('');
  categoryList.innerHTML = tabs;
  categoryList.querySelectorAll('.category-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      activeCategory = tab.dataset.category;
      categoryList.querySelectorAll('.category-tab').forEach(t => t.classList.toggle('active', t === tab));
      renderGameGrid(activeCategory);
      if (window.innerWidth <= 768) {
        categoryList.classList.remove('open');
        categoryToggle?.setAttribute('aria-expanded', 'false');
      }
    });
  });
}

categoryToggle?.addEventListener('click', () => {
  const open = categoryList.classList.toggle('open');
  categoryToggle?.setAttribute('aria-expanded', String(open));
});
```

Replace `renderGameGrid` (839-859) with:

```js
function renderGameGrid(category) {
  const games = gamesByCategory(category || activeCategory);
  gameGrid.innerHTML = games.map(gameCard).join('');
}
```

Update `init()` to call `renderCategoryTabs()` before `renderGameGrid()`:

```js
function init() {
  renderCategoryTabs();
  renderGameGrid('all');

  const play = parsePlayUrl(location.pathname, location.search);
  if (play) void openPlayGate(play);
}
```

Remove `const categoryTabs = $$('.category-tab');` (was line 568) — tabs are now bound inside `renderCategoryTabs`.

- [ ] **Step 5: Run tests**

Run: `.venv/bin/python -m pytest tests/test_static_js_imports.py tests/test_games_list.py tests/test_play_url.py -q`
Expected: PASS.

> `test_static_js_imports.py` reads every `import ... from` and asserts the target exports those names; `GAMES`, `categories`, `gamesByCategory`, `gameCard` are all exported by `games.js`.

- [ ] **Step 6: Commit**

```bash
git add static/app.js
git commit -m "feat: render landing from games.js module without badges"
```

---

### Task 3: Strip featured and collections sections from `index.html`

**Files:**
- Modify: `static/index.html`

**Interfaces:**
- Consumes: `renderCategoryTabs()` now writes the tabs inside `.category-list`; `renderGameGrid()` writes into `#game-grid`.
- Produces: landing markup containing only hero, `.category-nav`, and `#game-grid`.

- [ ] **Step 1: Remove static category tabs**

Replace the `<ul class="category-list">...</ul>` in `static/index.html` (lines 17-24) with an empty list:

```html
      <ul class="category-list"></ul>
```

- [ ] **Step 2: Remove featured and collections sections**

Delete from `static/index.html`:
- The `<section class="featured" ...>...</section>` block (lines 27-30).
- The `<section class="collections" ...><!-- collection slots rendered by JS --></section>` block (lines 31-33).

The landing remains: `<header class="hero">`, `<nav class="category-nav">` (with empty `.category-list` and the `.category-toggle` button), and `<main class="game-grid" id="game-grid">`.

- [ ] **Step 3: Verify landing renders**

Start the server, load the landing, and confirm it renders with tabs + all 6 cards:

```bash
.venv/bin/python -m uvicorn app.main:app --port 8123 >/tmp/games_server.log 2>&1 &
echo $! > /tmp/games_server.pid
sleep 3
curl -s http://127.0.0.1:8123/ | rg -c 'game-card|category-nav'
```

Run: `.venv/bin/python -m pytest tests/test_static_js_imports.py tests/test_games_list.py -q`
Expected: PASS.

Kill the server afterward: `kill $(cat /tmp/games_server.pid)`.

- [ ] **Step 4: Commit**

```bash
git add static/index.html
git commit -m "feat: remove featured and collections sections from landing"
```

---

### Task 4: Remove orphaned CSS

**Files:**
- Modify: `static/styles.css`

**Interfaces:**
- Consumes: final landing markup (no `.featured*`, `.collections*`, `collection-*` elements).
- Produces: stylesheet with no dead rules for removed sections.

- [ ] **Step 1: Locate orphaned rules**

Run: `.venv/bin/python - <<'PY'
from pathlib import Path
css = Path("static/styles.css").read_text()
for i, line in enumerate(css.splitlines(), 1):
    if any(k in line for k in (".featured", ".collections", ".collection-", ".featured-spotlight", ".featured-secondary")):
        print(f"{i}: {line}")
PY`
Expected: lines referencing `.featured*`, `.collections*`, `.collection-*`.

- [ ] **Step 2: Delete orphaned blocks**

For each selector listed whose *whole rule block* is now dead (features/collections only), remove the entire rule. Keep any shared rules still used by `.game-card`, `.badge`, `.btn-play`, `.game-hover-overlay`, `.game-thumb`, `.game-info`, `.game-meta` (badges like `.badge-novo`, `.badge-popular`, `.badge-destaque`, `.game-badges` are now unused — remove those blocks too).

- [ ] **Step 3: Verify CSS sanity + tests**

Run: `.venv/bin/python -m pytest tests/test_static_js_imports.py tests/test_games_list.py -q`
Expected: PASS.

Also confirm no HTML file still references removed classes:
Run: rg -n 'featured|collection' static/index.html
Expected: no matches in `static/index.html`.

- [ ] **Step 4: Commit**

```bash
git add static/styles.css
git commit -m "chore: drop CSS for removed featured and collections sections"
```

---

### Task 5: Full validation

**Files:**
- Test: full suite + live server smoke test

- [ ] **Step 1: Run the full test suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all passing (188 + 7 new = 195 passed, 1 skipped).

- [ ] **Step 2: Live smoke test**

```bash
.venv/bin/python -m uvicorn app.main:app --port 8123 >/tmp/games_server.log 2>&1 &
echo $! > /tmp/games_server.pid
sleep 3
for route in snake ant_defense tower_defense checkers; do
  echo "/play/$route -> $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8123/play/$route)"
done
curl -s http://127.0.0.1:8123/ | rg -c 'game-card'
kill $(cat /tmp/games_server.pid)
```

Expected: each `/play/*` → 200; the landing contains at least 6 `game-card` occurrences (spotlight/secondary/collections no longer contribute cards).

- [ ] **Step 3: Final commit if any straggler diffs exist**

```bash
git add -A
git commit -m "chore: finalize single-grid landing navigation"
```

(If there are no diff changes, skip this commit gracefully with `git diff --quiet || git commit ...`.)

- [ ] **Step 4: Push to main**

```bash
git push origin main
```