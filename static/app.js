// deploy-test: force redeploy 735adb9
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
const gameOverOverlay = $('#game-over-overlay');
const gameOverTitle = $('#game-over-title');
const gameOverMessage = $('#game-over-message');
const btnGameOverAgain = $('#btn-game-over-again');
const btnGameOverBack = $('#btn-game-over-back');

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

  // Reset overlay when switching views
  if (!gameActive) hideGameOver();
}

function showGameOver(title, message) {
  if (!gameOverOverlay) return;
  gameOverTitle.textContent = title;
  gameOverMessage.textContent = message;
  gameOverOverlay.classList.remove('hidden');
}

function hideGameOver() {
  gameOverOverlay?.classList.add('hidden');
}

function refreshPlayLink() {
  if (!modalPlayBtn || !STATE.selectedGame) return;
  // Agora o botão do modal inicia o jogo in-place (SPA), 
  // então não precisamos mais do href do play-url.js aqui.
}

function openModal(gameId) {
  const game = GAMES[gameId];
  if (!game) return;
  STATE.selectedGame = gameId;
  modalTitle.textContent = game.title;
  modalDesc.textContent = game.desc;
  
  const previewCanvas = document.getElementById('modal-board-preview');
  if (previewCanvas) {
    previewCanvas.setAttribute('aria-label', `Prévia do jogo ${game.title}`);
  }

  modalSpecs.innerHTML = `
    <dt>Jogadores</dt><dd>${game.players}</dd>
    <dt>Modos</dt><dd>${game.modes.join(', ')}</dd>
    <dt>Duração</dt><dd>${game.duration}</dd>
    ${game.difficulty ? `<dt>Dificuldade</dt><dd>${game.difficulty.join(' / ')}</dd>` : ''}
  `;
  modalRules.innerHTML = `
    <h4>Resumo das Regras</h4>
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
  } else if (gameId === 'checkers') {
    // Render checkers preview
    renderPreview('modal-board-preview');
  } else {
    // For other games, show the game icon instead of the checkers board
    const previewEl = document.getElementById('modal-board-preview');
    if (previewEl) {
      const icon = game.icon || '';
      const iconOverlay = document.createElement('div');
      iconOverlay.className = 'modal-game-icon-overlay';
      iconOverlay.textContent = icon;
      iconOverlay.style.cssText = 'position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:4rem;background:var(--surface-2, #1a1a2e);border-radius:inherit;z-index:2;';
      previewEl.parentElement.style.position = 'relative';
      // Remove any previous icon overlay
      previewEl.parentElement.querySelectorAll('.modal-game-icon-overlay').forEach(el => el.remove());
      previewEl.parentElement.appendChild(iconOverlay);
      previewEl.style.display = 'none';
    }
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
  // Non-checkers games: redirect to their dedicated play page
  if (gameId !== 'checkers') {
    window.location.href = buildPlayUrl(gameId);
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
    wordSearchTimer.stopTimer();
    showGameOver('Parabéns!', `Você completou o desafio em ${formatTime(time * 1000)}`);
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
modalPlayBtn?.addEventListener('click', () => startGame(STATE.selectedGame));
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
btnResign?.addEventListener('click', () => { resignGame(); });
sidebarToggle?.addEventListener('click', () => {
  const open = sidebar.classList.toggle('open');
  sidebarToggle.setAttribute('aria-expanded', String(open));
  sidebarToggle.setAttribute('aria-label', open ? 'Fechar painel do jogo' : 'Abrir painel do jogo');
});

// Game Over Overlay
btnGameOverAgain?.addEventListener('click', () => {
  hideGameOver();
  startNewGame();
});
btnGameOverBack?.addEventListener('click', () => {
  hideGameOver();
  backToLanding();
});

function resignGame() {
  if (STATE.currentGameType === 'checkers') {
    if (STATE.game.ws && STATE.game.ws.readyState === WebSocket.OPEN) {
      STATE.game.ws.send(JSON.stringify({ type: 'resign' }));
    }
  } else {
    backToLanding();
  }
}

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
        categoryToggle?.setAttribute('aria-label', 'Abrir categorias');
      }
    });
  });
}

categoryToggle?.addEventListener('click', () => {
  const open = categoryList.classList.toggle('open');
  categoryToggle?.setAttribute('aria-expanded', String(open));
  categoryToggle?.setAttribute('aria-label', open ? 'Fechar categorias' : 'Abrir categorias');
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
let checkersDifficulty = 'medium';

window.setCheckersDifficulty = function(diff) {
  checkersDifficulty = diff;
  document.querySelectorAll('.diff-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.diff === diff);
  });
  const desc = document.getElementById('ai-diff-desc');
  const labels = { easy: 'Profundidade: 2', medium: 'Profundidade: 3', hard: 'Profundidade: 5' };
  if (desc) desc.textContent = labels[diff] || '';
  // Send to server if connected
  if (STATE.game.ws && STATE.game.ws.readyState === WebSocket.OPEN) {
    STATE.game.ws.send(JSON.stringify({ type: 'set_difficulty', difficulty: diff }));
  }
};

async function connectWebSocket() {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${protocol}://${location.host}/ws/${STATE.game.id}`);
  STATE.game.ws = ws;

  ws.onopen = () => {
    console.log('WebSocket opened');
    // Send difficulty to AI
    if (STATE.currentGameType === 'checkers') {
      ws.send(JSON.stringify({ type: 'set_difficulty', difficulty: checkersDifficulty }));
    }
  };
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
  if (msg.type === 'difficulty_set') {
    console.log(`AI difficulty set to: ${msg.difficulty} (${msg.label}, depth ${msg.depth})`);
    return;
  }
  if (msg.type === 'color') {
    STATE.game.myColor = msg.color;
    if (!checkersGame) {
      checkersGame = new CheckersGame('board-canvas');
    }
    checkersGame.init(STATE.game.id, ws);
    checkersGame.setMyColor(msg.color);
    checkersGame.onGameOver = (winner, reason) => {
      let title = 'Fim de Jogo';
      let message = '';
      if (reason === 'resign') {
        if (winner === STATE.game.myColor) {
          title = 'Vitória!';
          message = 'O oponente desistiu. Você venceu!';
        } else {
          title = 'Fim de Jogo';
          message = 'Você desistiu da partida.';
        }
      } else {
        if (winner === STATE.game.myColor) {
          title = 'Vitória!';
          message = 'Parabéns! Você venceu a partida.';
        } else {
          title = 'Derrota';
          message = 'Você perdeu esta partida.';
        }
      }
      showGameOver(title, message);
    };
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
        const elapsed = Date.now() - crosswordGame.startTime;
        const timeStr = formatTime(elapsed);
        el.textContent = timeStr;
        showGameOver('Parabéns!', `Você resolveu as palavras cruzadas em ${timeStr}`);
      }
    };
    crosswordGame.init(msg);
  } else if (crosswordGame) {
    crosswordGame.handleMessage(msg);
  }
}

init();