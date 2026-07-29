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