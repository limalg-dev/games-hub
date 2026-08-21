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

// ===== PLAYER ID (stable across sessions) =====
function getPlayerId() {
  let pid = localStorage.getItem('checkers_player_id');
  if (!pid) {
    pid = crypto.randomUUID ? crypto.randomUUID().replace(/-/g, '').slice(0, 16) : Math.random().toString(36).slice(2, 18);
    localStorage.setItem('checkers_player_id', pid);
  }
  return pid;
}
const PLAYER_ID = getPlayerId();

// ===== ELO HELPERS =====
let currentEloRatings = {};

async function fetchEloRatings() {
  try {
    const res = await fetch(`/api/ratings/${PLAYER_ID}?game_type=checkers`);
    if (!res.ok) return;
    const data = await res.json();
    currentEloRatings = data.ratings || {};
    updateEloPanel();
  } catch (e) { console.warn('Failed to fetch ELO:', e); }
}

function updateEloPanel() {
  const el = document.getElementById('elo-rating');
  const rec = document.getElementById('elo-record');
  const peak = document.getElementById('elo-peak');
  if (!el) return;
  const r = currentEloRatings[checkersDifficulty];
  if (r) {
    el.textContent = r.rating;
    rec.textContent = `V: ${r.wins} / D: ${r.losses} / E: ${r.draws}`;
    peak.textContent = `Recorde: ${r.peak_rating} (${r.games_played} jogos)`;
  } else {
    el.textContent = '1000';
    rec.textContent = 'V: 0 / D: 0 / E: 0';
    peak.textContent = 'Novo jogador';
  }
}

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

// ===== SCROLL REVEAL =====
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

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
  if (!visible && page.classList.contains('active')) {
    // Smooth fade-out before hiding
    page.classList.add('leaving');
    page.addEventListener('animationend', () => {
      page.classList.remove('active', 'leaving');
      page.classList.add('hidden');
    }, { once: true });
  } else {
    page.classList.remove('leaving', 'hidden');
    page.classList.toggle('active', visible);
  }
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

function showGameOver(title, message, eloData) {
  if (!gameOverOverlay) return;
  gameOverTitle.textContent = title;
  gameOverTitle.className = 'game-over-title ' + (eloData ? (eloData.result === 'win' ? 'win' : 'loss') : '');
  gameOverMessage.textContent = message;

  const eloChange = document.getElementById('elo-change');
  const eloNew = document.getElementById('elo-new-rating');
  const eloStats = document.getElementById('elo-stats-line');
  const eloSummary = document.getElementById('elo-summary');

  if (eloData && eloChange && eloNew && eloStats && eloSummary) {
    eloSummary.classList.remove('hidden');
    const sign = eloData.change > 0 ? '+' : '';
    eloChange.textContent = `${sign}${eloData.change}`;
    eloChange.className = 'elo-change ' + (eloData.change > 0 ? 'positive' : eloData.change < 0 ? 'negative' : 'neutral');
    eloNew.textContent = `${eloData.new_rating} ELO  (vs ${eloData.opponent_name} ${eloData.opponent_rating})`;
    eloStats.textContent = `${eloData.games_played} jogos  ·  V: ${eloData.wins}  D: ${eloData.losses}  E: ${eloData.draws}  ·  Recorde: ${eloData.peak_rating}`;
  } else if (eloSummary) {
    eloSummary.classList.add('hidden');
  }

  gameOverOverlay.classList.remove('hidden');
  // Refresh sidebar ELO
  fetchEloRatings();
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
  fetchEloRatings();
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

// ===== SCROLL-AWARE STICKY NAV =====
const categoryNav = document.querySelector('.category-nav');
if (categoryNav) {
  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;
    categoryNav.classList.toggle('scrolled', scrollY > 80);
    lastScroll = scrollY;
  }, { passive: true });
}

// ===== HERO CTA SMOOTH SCROLL =====
const heroCtaBtn = document.getElementById('hero-cta-btn');
if (heroCtaBtn) {
  heroCtaBtn.addEventListener('click', (e) => {
    e.preventDefault();
    const target = document.getElementById('game-grid');
    if (target) {
      const navHeight = categoryNav ? categoryNav.offsetHeight : 0;
      const targetTop = target.getBoundingClientRect().top + window.scrollY - navHeight - 16;
      window.scrollTo({ top: targetTop, behavior: 'smooth' });
    }
  });
}

// ===== BONUS / LEAD CAPTURE =====
const bonusForm = document.getElementById('bonus-form');
const bonusEmail = document.getElementById('bonus-email');
const bonusSubmitBtn = document.getElementById('bonus-submit-btn');
const bonusSubmitText = bonusSubmitBtn?.querySelector('.bonus-submit-text');
const bonusSubmitLoading = bonusSubmitBtn?.querySelector('.bonus-submit-loading');
const bonusFeedback = document.getElementById('bonus-feedback');
const bonusHoneypot = document.getElementById('bonus-website');

// Anti-spam: track when the form became visible
const bonusFormLoadTime = Date.now();
const BONUS_MIN_SECONDS = 3;   // human takes at least 3s to fill
const BONUS_COOLDOWN_MS = 30000; // 30s between submissions
let bonusLastSubmit = 0;

if (bonusForm) {
  bonusForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!bonusEmail || !bonusSubmitBtn) return;

    // ── Anti-spam layer 1: Honeypot ──
    if (bonusHoneypot && bonusHoneypot.value) {
      // Bot filled the hidden field — silently pretend success
      showBonusFeedback('✅ Bônus desbloqueado! Verifique seu email.', 'success');
      bonusEmail.value = '';
      return;
    }

    // ── Anti-spam layer 2: Time gate ──
    const elapsed = (Date.now() - bonusFormLoadTime) / 1000;
    if (elapsed < BONUS_MIN_SECONDS) {
      showBonusFeedback('Por favor, preencha o formulário com calma.', 'error');
      return;
    }

    // ── Anti-spam layer 3: Rate limit ──
    const now = Date.now();
    if (now - bonusLastSubmit < BONUS_COOLDOWN_MS) {
      const waitSec = Math.ceil((BONUS_COOLDOWN_MS - (now - bonusLastSubmit)) / 1000);
      showBonusFeedback(`Aguarde ${waitSec}s antes de enviar novamente.`, 'error');
      return;
    }

    const email = bonusEmail.value.trim();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      showBonusFeedback('Por favor, insira um email válido.', 'error');
      return;
    }

    // ── Anti-spam layer 4: Duplicate email ──
    const submittedKey = 'gamehub_submitted_emails';
    try {
      const stored = JSON.parse(localStorage.getItem(submittedKey) || '[]');
      if (stored.includes(email.toLowerCase())) {
        showBonusFeedback('✅ Este email já foi registrado! Verifique sua caixa de entrada.', 'success');
        bonusEmail.value = '';
        return;
      }
    } catch (_) { /* localStorage unavailable */ }

    const webhookUrl = bonusForm.dataset.webhookUrl;
    if (!webhookUrl) {
      showBonusFeedback('Formulário não configurado. Tente novamente mais tarde.', 'error');
      return;
    }

    // Show loading
    bonusSubmitBtn.disabled = true;
    bonusSubmitText.classList.add('hidden');
    bonusSubmitLoading.classList.remove('hidden');
    bonusSubmitLoading.setAttribute('aria-hidden', 'false');
    bonusFeedback.classList.add('hidden');

    try {
      const resp = await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          source: 'gamehub_bonus_form',
          timestamp: new Date().toISOString(),
          page_url: window.location.href,
        }),
      });

      if (resp.ok) {
        bonusLastSubmit = Date.now();
        // Store email to prevent duplicates
        try {
          const stored = JSON.parse(localStorage.getItem(submittedKey) || '[]');
          stored.push(email.toLowerCase());
          localStorage.setItem(submittedKey, JSON.stringify(stored));
        } catch (_) { /* localStorage unavailable */ }
        showBonusFeedback('✅ Bônus desbloqueado! Verifique seu email.', 'success');
        bonusEmail.value = '';
      } else {
        throw new Error(`HTTP ${resp.status}`);
      }
    } catch (err) {
      console.error('Bonus form error:', err);
      showBonusFeedback('Erro ao enviar. Tente novamente em alguns segundos.', 'error');
    } finally {
      bonusSubmitBtn.disabled = false;
      bonusSubmitText.classList.remove('hidden');
      bonusSubmitLoading.classList.add('hidden');
      bonusSubmitLoading.setAttribute('aria-hidden', 'true');
    }
  });
}

function showBonusFeedback(message, type) {
  if (!bonusFeedback) return;
  bonusFeedback.textContent = message;
  bonusFeedback.className = `bonus-feedback ${type}`;
  bonusFeedback.classList.remove('hidden');
}

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
  // Hide loading skeletons
  const skeletons = document.querySelectorAll('.game-skeleton');
  skeletons.forEach(s => s.classList.add('hidden-skeleton'));
  gameGrid.innerHTML = games.map(gameCard).join('');
  // Trigger scroll-reveal for newly rendered cards
  requestAnimationFrame(() => {
    gameGrid.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));
  });
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
  updateEloPanel();
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
    checkersGame.onGameOver = (winner, reason, elo) => {
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
      showGameOver(title, message, elo);
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