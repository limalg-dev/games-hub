// static/app.js
import { renderPreview } from '/games/checkers/static/preview.js';
import { CheckersGame } from '/games/checkers/static/board.js';
import { CrosswordGame } from '/games/crossword/static/board.js';
import { DIFFICULTIES } from '/games/wordsearch/static/words.js';

// ===== STATE =====
const STATE = {
  currentView: 'landing',
  selectedGame: null,
  currentGameType: null,
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
const boardWrapper = $('#board-wrapper');

// Save original board/sidebar HTML for restoration after wordsearch
const ORIGINAL_BOARD_HTML = boardWrapper ? boardWrapper.innerHTML : '';
const ORIGINAL_SIDEBAR_HTML = sidebar ? sidebar.innerHTML : '';

function restoreBoard() {
  if (boardWrapper) boardWrapper.innerHTML = ORIGINAL_BOARD_HTML;
  if (sidebar) sidebar.innerHTML = ORIGINAL_SIDEBAR_HTML;
}

// ===== GAME DATA =====
const GAMES = {
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
  }
};

// ===== COLLECTIONS DATA =====
const COLLECTIONS = {
  'treine-sua-mente':      { title: 'Treine sua Mente',    desc: 'Desafios que exercitam o cérebro' },
  'acao-pura':             { title: 'Ação Pura',           desc: 'Jogos rápidos e intensos' },
  '2-jogadores':           { title: '2 Jogadores',         desc: 'Jogue com um amigo' },
  'classicos-atemporais':  { title: 'Clássicos Atemporais', desc: 'Jogos que todo mundo conhece' }
};

// ===== VIEW MANAGEMENT =====
function showView(view) {
  landing.classList.add('hidden');
  modal.classList.add('hidden');
  gameView.classList.add('hidden');
  STATE.currentView = view;
  if (view === 'landing') {
    landing.classList.remove('hidden');
    landing.classList.add('active');
  } else if (view === 'modal') {
    modal.classList.remove('hidden');
  } else if (view === 'game') {
    gameView.classList.remove('hidden');
    gameView.classList.add('active');
  }
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
    ${game.difficulty ? `<dt>Difficulty</dt><dd>${game.difficulty.join(' / ')}</dd>` : ''}
  `;
  modalRules.innerHTML = `
    <h4>Rules Summary</h4>
    <ul>${game.rules.map(r => `<li>${r}</li>`).join('')}</ul>
  `;
  
  // Wordsearch specific config
  if (gameId === 'wordsearch') {
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
    // Render wordsearch preview
    import('/games/wordsearch/static/preview.js').then(m => m.renderPreview('modal-board-preview'));
  } else if (gameId === 'crossword') {
    modalRules.innerHTML += `
      <div class="config-group">
        <label>Dificuldade</label>
        <div>
          <label><input type="radio" name="cw-difficulty" value="easy" checked> Fácil (8×8)</label>
        </div>
        <div>
          <label><input type="radio" name="cw-difficulty" value="medium"> Médio (12×12)</label>
        </div>
        <div>
          <label><input type="radio" name="cw-difficulty" value="hard"> Difícil (15×15)</label>
        </div>
      </div>
    `;
    // Render crossword preview
    import('/games/crossword/static/preview.js').then(m => m.renderPreview('modal-board-preview'));
  } else {
    // Render checkers preview
    renderPreview('modal-board-preview');
  }
  
  showView('modal');
}

function closeModal() {
  modal.classList.add('hidden');
  showView('landing');
  STATE.selectedGame = null;
}

let wordSearchGame = null;
let crosswordGame = null;

async function startGame(gameId) {
  if (gameId === 'wordsearch') {
    const config = getWordSearchConfig();
    await startWordSearch(config);
    return;
  }
  if (gameId === 'crossword') {
    await startCrossword();
    return;
  }
  closeModal();
  showView('game');
  STATE.game.id = gameId;
  STATE.currentGameType = gameId;
  restoreBoard();
  // Create game on server
  const resp = await fetch('/games', { method: 'POST' });
  const data = await resp.json();
  STATE.game.id = data.id;
  connectWebSocket();
}

function getWordSearchConfig() {
  const difficulty = document.querySelector('input[name="ws-difficulty"]:checked')?.value || 'easy';
  const category = document.getElementById('ws-category')?.value || 'random';
  const diff = DIFFICULTIES[difficulty];
  return { ...diff, difficulty, category };
}

async function startWordSearch(config) {
  closeModal();
  showView('game');
  STATE.currentGameType = 'wordsearch';
  STATE.game.id = 'wordsearch-' + Date.now();
  
  const { startTimer, stopTimer, saveScore } = await import('/games/wordsearch/static/timer.js');
  const { WordSearchGame } = await import('/games/wordsearch/static/board.js');
  wordSearchGame = new WordSearchGame({ containerId: 'board-wrapper', ...config });
  wordSearchGame.onGameComplete = (time, difficulty) => {
    stopTimer();
    saveScore(config, time * 1000);
    alert(`Parabéns! Você completou em ${formatTime(time * 1000)}`);
  };
  wordSearchGame.init();
  
  updateGameViewForWordSearch();
  
  startTimer((seconds) => {
    const el = document.getElementById('timer');
    if (el) el.textContent = formatTime(seconds * 1000);
  });
}

async function startCrossword() {
  const difficulty = document.querySelector('input[name="cw-difficulty"]:checked')?.value || 'easy';
  closeModal();
  showView('game');
  STATE.currentGameType = 'crossword';
  restoreBoard();
  setupCrosswordView();

  const resp = await fetch('/games', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ game_type: 'crossword', difficulty })
  });
  const data = await resp.json();
  STATE.game.id = data.id;
  connectWebSocket();
}

function setupCrosswordView() {
  const timerEl = document.getElementById('timer');
  if (timerEl) timerEl.classList.remove('hidden');
  const turnIndicator = document.getElementById('turn-indicator');
  if (turnIndicator) turnIndicator.textContent = 'Resolva as palavras cruzadas!';

  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.innerHTML = `
      <section class="panel clues-panel">
        <h4>Horizontal</h4>
        <ol class="clue-list" id="cw-across-list"></ol>
      </section>
      <section class="panel clues-panel">
        <h4>Vertical</h4>
        <ol class="clue-list" id="cw-down-list"></ol>
      </section>
    `;
  }
}

function updateGameViewForWordSearch() {
  // Show timer
  const timerEl = document.getElementById('timer');
  if (timerEl) {
    timerEl.classList.remove('hidden');
    timerEl.textContent = '00:00';
  }
  // Show game menu
  document.querySelectorAll('.game-menu').forEach(m => m.style.display = 'flex');
  // Update status
  const turnIndicator = document.getElementById('turn-indicator');
  if (turnIndicator) turnIndicator.textContent = 'Encontre palavras!';
  
  // Replace sidebar with word list for wordsearch
  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.innerHTML = `
      <section class="panel word-list-panel">
        <h4>Palavras</h4>
        <ul class="word-list" id="word-list"></ul>
      </section>
    `;
  }
  
  // Add hint button
  const gameMenu = document.querySelector('.game-menu');
  if (gameMenu && !document.getElementById('btn-hint')) {
    const hintBtn = document.createElement('button');
    hintBtn.id = 'btn-hint';
    hintBtn.className = 'btn-secondary';
    hintBtn.textContent = 'Dica';
    hintBtn.addEventListener('click', () => wordSearchGame?.useHint());
    gameMenu.prepend(hintBtn);
  }
}

function formatTime(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function backToLanding() {
  if (STATE.game.ws) {
    STATE.game.ws.close();
  }
  if (wordSearchGame) {
    wordSearchGame.destroy();
    wordSearchGame = null;
  }
  if (crosswordGame) {
    crosswordGame.destroy();
    crosswordGame = null;
  }
  restoreBoard();
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
btnNewGame?.addEventListener('click', () => { startNewGame(); });
btnResign?.addEventListener('click', () => { /* TODO: resign logic */ });
sidebarToggle?.addEventListener('click', () => sidebar.classList.toggle('open'));

async function startNewGame() {
  if (STATE.game.ws) {
    STATE.game.ws.close();
  }
  if (checkersGame) {
    checkersGame = null;
  }
  if (wordSearchGame) {
    wordSearchGame.destroy();
    wordSearchGame = null;
  }
  if (crosswordGame) {
    crosswordGame.destroy();
    crosswordGame = null;
  }
  const hintBtn = document.getElementById('btn-hint');
  if (hintBtn) hintBtn.remove();
  restoreBoard();
  STATE.game = { id: null, ws: null, myColor: null, board: null, history: [], captured: { w: [], b: [] }, turn: 'w', status: 'waiting' };
  await startGame(STATE.currentGameType || STATE.selectedGame);
}

// ===== LANDING CATEGORY NAV =====
let activeCategory = 'all';
const categoryTabs = $$('.category-tab');
const categoryList = $('.category-list');
const categoryToggle = $('.category-toggle');

categoryTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    activeCategory = tab.dataset.category;
    activeCollectionFilteredGames = null;
    categoryTabs.forEach(t => t.classList.toggle('active', t === tab));
    renderGameGrid(activeCategory);
    if (window.innerWidth <= 768) {
      categoryList.classList.remove('open');
      categoryToggle.setAttribute('aria-expanded', 'false');
    }
  });
});

categoryToggle?.addEventListener('click', () => {
  const open = categoryList.classList.toggle('open');
  categoryToggle.setAttribute('aria-expanded', String(open));
});

// ===== INIT =====
function init() {
  renderGameGrid();
  renderFeaturedSpotlight();
  renderFeaturedSecondary();
  renderCollections();
}

function formatPlays(plays) {
  if (plays >= 1000000) return (plays / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (plays >= 1000) return (plays / 1000).toFixed(0) + 'K';
  return String(plays);
}

function getBadgeLabel(badge) {
  const labels = { 'novo': 'Novo', 'popular': 'Popular', 'destaque': 'Em Destaque' };
  return labels[badge] || '';
}

function getBadgeClass(badge) {
  const classes = { 'novo': 'badge-novo', 'popular': 'badge-popular', 'destaque': 'badge-destaque' };
  return classes[badge] || '';
}

function renderBadge(game) {
  if (!game.badge) return '';
  return `<div class="game-badges"><span class="badge ${getBadgeClass(game.badge)}">${getBadgeLabel(game.badge)}</span></div>`;
}

function renderThumbnail(game) {
  if (game.thumbnail) {
    return `<img src="${game.thumbnail}" alt="${game.title}" onerror="this.onerror=null; this.outerHTML='<svg class=\\'game-preview\\' viewBox=\\'0 0 80 80\\' width=\\'80\\' height=\\'80\\'>' + generateGamePreviewSVG('${game.id}') + '</svg>'">`;
  }
  return `<svg class="game-preview" viewBox="0 0 80 80" width="80" height="80">${generateGamePreviewSVG(game.id)}</svg>`;
}

function renderHoverOverlay(game) {
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

function renderFeaturedSpotlight() {
  const container = $('#featured-spotlight');
  if (!container) return;
  const game = Object.values(GAMES).find(g => g.featured);
  if (!game) {
    container.classList.add('hidden');
    return;
  }
  container.classList.remove('hidden');
  container.innerHTML = `
    <div class="featured-card featured-spotlight">
      <div class="featured-badges">
        ${renderBadge(game)}
        <span class="badge">${game.players} Players</span>
        ${game.duration ? `<span class="badge">${game.duration}</span>` : ''}
      </div>
      <div class="featured-info">
        <h3>${game.title}</h3>
        <p class="featured-desc">${game.shortDesc}</p>
        <div class="featured-meta">
          <span>★ <span class="val">${game.rating.toFixed(1)}</span></span>
          <span><span class="val">${formatPlays(game.plays)}</span> plays</span>
        </div>
        <button class="btn-play" data-game="${game.id}">Jogar Agora</button>
      </div>
    </div>
  `;
}

function renderFeaturedSecondary() {
  const container = $('#featured-secondary');
  if (!container) return;
  const games = Object.values(GAMES)
    .filter(g => !g.featured)
    .sort((a, b) => b.plays - a.plays)
    .slice(0, 2);
  if (games.length < 2) {
    container.innerHTML = '';
    return;
  }
  container.innerHTML = games.map(game => `
    <article class="game-card" data-game="${game.id}">
      <div class="game-thumb">
        ${renderThumbnail(game)}
      </div>
      ${renderBadge(game)}
      <div class="game-info">
        <h3>${game.title}</h3>
        <p class="game-desc">${game.shortDesc}</p>
        <div class="game-meta">
          <span class="badge">${game.players} Players</span>
          <span class="badge">${game.duration}</span>
        </div>
      </div>
      <button class="btn-play" data-game="${game.id}">Jogar Agora</button>
      ${renderHoverOverlay(game)}
    </article>
  `).join('');
}

// Featured play buttons live OUTSIDE #game-grid, so wire them explicitly.
const featuredSection = $('.featured');
featuredSection?.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-game]');
  if (btn) openModal(btn.dataset.game);
});
// ===== COLLECTIONS =====
const collectionsContainer = $('.collections');
let activeCollectionFilteredGames = null;

function gamesForCollection(category, collectFilter) {
  return Object.values(GAMES).filter(game => {
    if (collectFilter) {
      return game.collections && game.collections.includes(collectFilter);
    }
    return !category || category === 'all' || (game.category && game.category.includes(category));
  });
}

function renderCollections() {
  if (!collectionsContainer) return;
  collectionsContainer.innerHTML = Object.keys(COLLECTIONS).map(key => {
    const games = Object.values(GAMES).filter(g => g.collections && g.collections.includes(key));
    if (games.length === 0) return '';
    const col = COLLECTIONS[key];
    return `
      <section class="collection-section" data-collection-section="${key}">
        <div class="collection-title">
          <div>
            <h2>${col.title}</h2>
            <p>${col.desc}</p>
          </div>
          <button class="collection-see-all" data-collection="${key}">Ver todos</button>
        </div>
        <div class="collection-slider">
          ${games.map(game => `
            <article class="game-card collection-card" data-game="${game.id}">
              <div class="game-thumb">
                ${renderThumbnail(game)}
              </div>
              ${renderBadge(game)}
              <div class="game-info">
                <h3>${game.title}</h3>
                <p class="game-desc">${game.shortDesc}</p>
                <div class="game-meta">
                  <span class="badge">${game.players} Players</span>
                </div>
              </div>
              <button class="btn-play" data-game="${game.id}">Jogar Agora</button>
              ${renderHoverOverlay(game)}
            </article>
          `).join('')}
        </div>
      </section>
    `;
  }).filter(Boolean).join('');
}

collectionsContainer?.addEventListener('click', (e) => {
  const collectBtn = e.target.closest('[data-collection]');
  if (collectBtn) {
    activeCollectionFilteredGames = collectBtn.dataset.collection;
    activeCategory = 'all';
    categoryTabs.forEach(t => t.classList.toggle('active', t.dataset.category === 'all'));
    renderGameGrid();
    const grid = document.getElementById('game-grid');
    if (grid) grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  const card = e.target.closest('[data-game]');
  if (card) openModal(card.dataset.game);
});

function renderGameGrid(category) {
  const games = gamesForCollection(category, activeCollectionFilteredGames);
  gameGrid.innerHTML = games.map(game => `
    <article class="game-card" data-game="${game.id}">
      <div class="game-thumb">
        ${renderThumbnail(game)}
      </div>
      ${renderBadge(game)}
      <div class="game-info">
        <h3>${game.title}</h3>
        <p class="game-desc">${game.shortDesc}</p>
        <div class="game-meta">
          <span class="badge">${game.players} Players</span>
          <span class="badge">${game.duration}</span>
        </div>
      </div>
      <button class="btn-play" data-game="${game.id}">Jogar Agora</button>
      ${renderHoverOverlay(game)}
    </article>
  `).join('');
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
    // Show a letter grid pattern for word search
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
  // Checkers board preview
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

// ===== WEBSOCKET =====
let checkersGame = null;

async function connectWebSocket() {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${protocol}://${location.host}/ws/${STATE.game.id}`);
  STATE.game.ws = ws;

  ws.onopen = () => console.log('WebSocket opened');
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (STATE.currentGameType === 'crossword') {
      handleCrosswordMessage(msg, ws);
    } else {
      handleCheckersMessage(msg, ws);
    }
  };
  ws.onclose = () => {
    console.log('WebSocket closed');
  };
}

function handleCheckersMessage(msg, ws) {
  if (msg.type === 'color') {
    STATE.game.myColor = msg.color;
    if (!checkersGame) {
      checkersGame = new CheckersGame('board-canvas');
    }
    checkersGame.init(STATE.game.id, ws);
    checkersGame.setMyColor(msg.color);
  } else if (checkersGame) {
    checkersGame.handleMessage(msg);
  }
}

function handleCrosswordMessage(msg, ws) {
  if (msg.type === 'color') {
    STATE.game.myColor = msg.color;
  } else if (msg.type === 'crossword_init') {
    if (!crosswordGame) {
      crosswordGame = new CrosswordGame('board-wrapper');
    }
    crosswordGame.ws = ws;
    crosswordGame.onGameComplete = () => {
      const el = document.getElementById('timer');
      const turnIndicator = document.getElementById('turn-indicator');
      if (turnIndicator) turnIndicator.textContent = 'Parabéns, você completou!';
      if (el && crosswordGame.startTime) {
        el.textContent = formatTime(Date.now() - crosswordGame.startTime);
      }
    };
    crosswordGame.init(msg);
  } else if (crosswordGame) {
    crosswordGame.handleMessage(msg);
  }
}

init();