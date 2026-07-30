// static/app.js
import { renderPreview } from '/games/checkers/static/preview.js';
import { CheckersGame } from '/games/checkers/static/board.js';
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
    duration: '5–15 min',
    difficulty: ['Easy', 'Medium', 'Hard'],
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
    duration: '5–20 min',
    difficulty: ['Fácil', 'Médio', 'Difícil'],
    rules: [
      'Palavras podem estar horizontais, verticais ou diagonais',
      'Podem ser lidas da esquerda para direita ou vice-versa',
      'Arraste para selecionar letras da palavra',
      'Palavras encontradas ficam marcadas na lista',
      'Complete todas as palavras para vencer'
    ]
  }
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

async function startGame(gameId) {
  if (gameId === 'wordsearch') {
    const config = getWordSearchConfig();
    await startWordSearch(config);
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
btnNewGame?.addEventListener('click', () => {
  if (checkersGame) {
    checkersGame = null;
  }
  if (wordSearchGame) {
    wordSearchGame.destroy();
    wordSearchGame = null;
  }
  const hintBtn = document.getElementById('btn-hint');
  if (hintBtn) hintBtn.remove();
  restoreBoard();
  startGame(STATE.currentGameType || STATE.selectedGame);
});
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
  const hintBtn = document.getElementById('btn-hint');
  if (hintBtn) hintBtn.remove();
  restoreBoard();
  STATE.game = { id: null, ws: null, myColor: null, board: null, history: [], captured: { w: [], b: [] }, turn: 'w', status: 'waiting' };
  await startGame(STATE.currentGameType || STATE.selectedGame);
}

// ===== INIT =====
function init() {
  renderGameGrid();
}
function renderGameGrid() {
  gameGrid.innerHTML = Object.values(GAMES).map(game => `
    <article class="game-card" data-game="${game.id}">
      <div class="game-thumb">
        <svg class="game-preview" viewBox="0 0 80 80" width="80" height="80">
          ${generateGamePreviewSVG(game.id)}
        </svg>
      </div>
      <div class="game-info">
        <h3>${game.title}</h3>
        <p class="game-desc">${game.shortDesc}</p>
        <div class="game-meta">
          <span class="badge">${game.players} Players</span>
          ${game.id === 'checkers' ? '<span class="badge ai">AI Opponent</span>' : ''}
          <span class="badge">${game.duration}</span>
        </div>
      </div>
      <button class="btn-play" data-game="${game.id}">Play</button>
    </article>
  `).join('');
}

function generateGamePreviewSVG(gameId) {
  const square = 10;
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
    if (msg.type === 'color') {
      STATE.game.myColor = msg.color;
      // Initialize game UI
      if (!checkersGame) {
        checkersGame = new CheckersGame('board-canvas');
      }
      checkersGame.init(STATE.game.id, ws);
      checkersGame.setMyColor(msg.color);
    } else if (checkersGame) {
      checkersGame.handleMessage(msg);
    }
  };
  ws.onclose = () => {
    console.log('WebSocket closed');
  };
}

init();