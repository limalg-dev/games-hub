// static/app.js
import { renderPreview } from '/games/checkers/static/preview.js';
import { CheckersGame } from '/games/checkers/static/board.js';
import { CrosswordGame } from '/games/crossword/static/board.js';
import { DIFFICULTIES } from '/games/wordsearch/static/words.js';
import { buildPlayUrl, parsePlayUrl } from '/static/play-url.js';
import { GAMES, categories, categoryLabel, gamesByCategory, gameCard } from '/static/games.js';

// ===== STATE =====
const STATE = {
  currentView: 'landing',
  selectedGame: null,
  currentGameType: null,
  playConfig: null,
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

// ===== VIEW MANAGEMENT =====
// A visibilidade de uma `.page` vem só da classe `active`
// (`.page { display: none }` / `.page.active { display: block }`). Portanto
// esconder uma página exige REMOVER `active`: marcar `hidden` sozinho não
// esconde nada, e era isso que fazia a landing continuar renderizada por cima
// do jogo em /play/*.
function setPageVisible(page, visible) {
  if (!page) return;
  page.classList.toggle('active', visible);
  page.classList.toggle('hidden', !visible);
}

function showView(view) {
  STATE.currentView = view;
  // O modal é uma sobreposição sobre a landing, não uma página própria: com ele
  // aberto a página que fica atrás continua sendo a landing.
  const gameActive = view === 'game';
  setPageVisible(gameView, gameActive);
  setPageVisible(landing, !gameActive);
  modal.classList.toggle('hidden', view !== 'modal');
}

function refreshPlayLink() {
  if (!modalPlayBtn || !STATE.selectedGame) return;
  const difficulty =
    document.querySelector('input[name="ws-difficulty"]:checked')?.value ||
    document.querySelector('input[name="cw-difficulty"]:checked')?.value;
  const category = document.getElementById('ws-category')?.value;
  const url = buildPlayUrl(STATE.selectedGame, { difficulty, category });
  // buildPlayUrl devolve null para um jogo fora de PLAYABLE_GAMES; sem href o
  // link deixa de ser acionável em vez de levar a um 404.
  if (!url) {
    modalPlayBtn.removeAttribute('href');
    return;
  }
  modalPlayBtn.href = url;
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

  refreshPlayLink();
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
  const play = STATE.playConfig;
  const difficulty = play?.difficulty
    || document.querySelector('input[name="ws-difficulty"]:checked')?.value
    || 'easy';
  const category = play?.category
    || document.getElementById('ws-category')?.value
    || 'random';
  const diff = DIFFICULTIES[difficulty];
  return { ...diff, difficulty, category };
}

let wordSearchTimer = null;

async function prepareWordSearch(config) {
  closeModal();
  showView('game');
  STATE.currentGameType = 'wordsearch';
  STATE.game.id = 'wordsearch-' + Date.now();

  wordSearchTimer = await import('/games/wordsearch/static/timer.js');
  const { WordSearchGame } = await import('/games/wordsearch/static/board.js');
  wordSearchGame = new WordSearchGame({ containerId: 'board-wrapper', ...config });
  wordSearchGame.onGameComplete = (time) => {
    // completeGame() already saved the score, in seconds — the unit timer.js
    // stores and formats. Saving again here wrote a second, 1000x entry.
    wordSearchTimer.stopTimer();
    alert(`Parabéns! Você completou em ${formatTime(time * 1000)}`);
  };
  wordSearchGame.init();
  updateGameViewForWordSearch();
}

function beginWordSearch() {
  // `elapsedTime` vive no módulo do timer, que é importado uma única vez por
  // aba. Sem o reset, um "New Game" retomaria o relógio da partida anterior.
  wordSearchTimer.resetTimer();
  wordSearchGame.start();
  wordSearchTimer.startTimer((seconds) => {
    const el = document.getElementById('timer');
    if (el) el.textContent = formatTime(seconds * 1000);
  });
}

async function startWordSearch(config) {
  await prepareWordSearch(config);
  beginWordSearch();
}

async function startCrossword(difficultyFromUrl) {
  const difficulty = difficultyFromUrl
    || STATE.playConfig?.difficulty
    || document.querySelector('input[name="cw-difficulty"]:checked')?.value
    || 'easy';
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
modalRules.addEventListener('change', refreshPlayLink);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !modal.classList.contains('hidden')) closeModal(); });

// Game view
btnBack?.addEventListener('click', () => {
  // Uma aba aberta em /play não tem landing atrás dela para revelar.
  if (parsePlayUrl(location.pathname, location.search)) {
    location.href = '/';
    return;
  }
  backToLanding();
});
btnNewGame?.addEventListener('click', () => { startNewGame(); });
btnResign?.addEventListener('click', () => { /* TODO: resign logic */ });
sidebarToggle?.addEventListener('click', () => {
  const open = sidebar.classList.toggle('open');
  sidebarToggle.setAttribute('aria-expanded', String(open));
  sidebarToggle.setAttribute('aria-label', open ? 'Fechar painel do jogo' : 'Abrir painel do jogo');
});

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
const categoryList = $('.category-list');
const categoryToggle = $('.category-toggle');

function renderCategoryTabs() {
  if (!categoryList) return;
  const tabs = [
    `<li><button class="category-tab active" data-category="all">Todos os Jogos</button></li>`,
    ...categories().map(cat =>
      `<li><button class="category-tab" data-category="${cat}">${categoryLabel(cat)}</button></li>`
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

// ===== INIT =====
function init() {
  renderCategoryTabs();
  renderGameGrid('all');

  const play = parsePlayUrl(location.pathname, location.search);
  if (play) void openPlayGate(play);
}

async function openPlayGate(play) {
  const gate = document.getElementById('play-gate');
  const title = document.getElementById('play-gate-title');
  const button = document.getElementById('play-gate-btn');
  if (!gate || !button) return;
  STATE.selectedGame = play.game;
  STATE.currentGameType = play.game;
  STATE.playConfig = play;
  showView('game');
  // parsePlayUrl já filtra por PLAYABLE_GAMES, mas as duas listas são
  // independentes: sem o `?.` uma divergência viraria um TypeError dentro de
  // init(), que derrubaria a renderização da landing inteira, inclusive em /.
  if (title) title.textContent = GAMES[play.game]?.title || play.game;
  gate.classList.remove('hidden');

  // O listener entra ANTES de qualquer await: um clique durante a preparação
  // não pode ser engolido, e uma falha na preparação não pode deixar o botão
  // sem handler nenhum.
  let ready = false;
  let started = false;
  button.disabled = true;
  button.addEventListener('click', () => {
    if (!ready || started) return;
    started = true;
    gate.classList.add('hidden');
    if (play.game === 'wordsearch') {
      beginWordSearch();
    } else if (play.game === 'crossword') {
      startCrossword(play.difficulty);
    } else {
      startGame(play.game);
    }
  });

  try {
    if (play.game === 'wordsearch') {
      // Só o wordsearch tem o que mostrar antes do Play: o grid montado aqui é
      // o mesmo que segue em jogo depois.
      await prepareWordSearch(getWordSearchConfig());
    } else if (play.game === 'crossword') {
      // Sem isto o gate translúcido deixa legível a UI de damas ("White to
      // move", "Captured (White)", "Move History") numa aba de cruzadas.
      setupCrosswordView();
      const indicator = document.getElementById('turn-indicator');
      if (indicator) indicator.textContent = '';
    }
  } catch (err) {
    console.error('[play] falha ao preparar o jogo', err);
    if (title) title.textContent = 'Não foi possível carregar o jogo';
    button.textContent = 'Recarregar';
    button.disabled = false;
    button.addEventListener('click', () => location.reload());
    return;
  }

  ready = true;
  button.disabled = false;
}

function renderGameGrid(category) {
  const games = gamesByCategory(category || activeCategory);
  gameGrid.innerHTML = games.map(gameCard).join('');
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