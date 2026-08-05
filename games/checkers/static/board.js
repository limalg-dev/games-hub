const SQUARE_SIZE = 80;
const BOARD_SIZE = 8;
const PIECE_RADIUS = 30;
const PIECE_STROKE = 2;
const ANIMATION_DURATION = 150;

// Wood texture cache
let woodPattern = null;

function createWoodPattern(ctx) {
  if (woodPattern) return woodPattern;
  const canvas = document.createElement('canvas');
  canvas.width = 256; canvas.height = 256;
  const c = canvas.getContext('2d');
  // Base
  const gradient = c.createLinearGradient(0, 0, 256, 256);
  gradient.addColorStop(0, '#e8c58a');
  gradient.addColorStop(0.5, '#d4a574');
  gradient.addColorStop(1, '#c4945a');
  c.fillStyle = gradient;
  c.fillRect(0, 0, 256, 256);
  // Noise
  const imgData = c.getImageData(0, 0, 256, 256);
  const data = imgData.data;
  for (let i = 0; i < data.length; i += 4) {
    const noise = (Math.random() - 0.5) * 20;
    data[i] = Math.max(0, Math.min(255, data[i] + noise));
    data[i+1] = Math.max(0, Math.min(255, data[i+1] + noise));
    data[i+2] = Math.max(0, Math.min(255, data[i+2] + noise));
  }
  c.putImageData(imgData, 0, 0);
  woodPattern = ctx.createPattern(canvas, 'repeat');
  return woodPattern;
}

export function drawBoard(ctx, board, options = {}) {
  const { selectedSquare, validMoves = [], lastMove, animateFrom, animateTo, animateProgress, kingPromotion } = options;
  const width = ctx.canvas.width;
  const height = ctx.canvas.height;
  const squareSize = width / BOARD_SIZE;
  const radius = squareSize * 0.375;

  // Clear
  ctx.clearRect(0, 0, width, height);

  // Wood background
  ctx.fillStyle = createWoodPattern(ctx);
  ctx.fillRect(0, 0, width, height);

  // Squares
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      const x = c * squareSize;
      const y = r * squareSize;
      const isDark = (r + c) % 2 === 0;

      // Dark squares
      if (isDark) {
        ctx.fillStyle = '#b58863';
        ctx.fillRect(x, y, squareSize, squareSize);
      }

      // Highlights
      if (selectedSquare && selectedSquare[0] === r && selectedSquare[1] === c) {
        ctx.fillStyle = 'rgba(233, 69, 96, 0.3)';
        ctx.fillRect(x, y, squareSize, squareSize);
      }
      if (validMoves.some(([vr, vc]) => vr === r && vc === c)) {
        // Pulsing dot
        const pulse = 0.5 + 0.5 * Math.sin(Date.now() / 200);
        ctx.fillStyle = `rgba(255, 215, 0, ${0.4 + 0.3 * pulse})`;
        ctx.beginPath();
        ctx.arc(x + squareSize/2, y + squareSize/2, squareSize * 0.15, 0, Math.PI * 2);
        ctx.fill();
      }
      if (lastMove?.from && lastMove?.to && ((lastMove.from[0] === r && lastMove.from[1] === c) || (lastMove.to[0] === r && lastMove.to[1] === c))) {
        ctx.fillStyle = 'rgba(255, 215, 0, 0.25)';
        ctx.fillRect(x, y, squareSize, squareSize);
      }
    }
  }

  // Border
  ctx.strokeStyle = '#8b6b4a';
  ctx.lineWidth = 4;
  ctx.strokeRect(2, 2, width - 4, height - 4);

  // Pieces
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      const piece = board[r][c];
      if (!piece) continue;

      // Skip animating piece
      if (animateFrom && animateFrom[0] === r && animateFrom[1] === c) continue;

      const x = c * squareSize + squareSize / 2;
      const y = r * squareSize + squareSize / 2;
      drawPiece(ctx, x, y, radius, piece.color, piece.king);
    }
  }

  // Animating piece
  if (animateFrom && animateTo && animateProgress !== undefined) {
    const piece = board[animateFrom[0]][animateFrom[1]];
    if (piece) {
      const sx = animateFrom[1] * squareSize + squareSize / 2;
      const sy = animateFrom[0] * squareSize + squareSize / 2;
      const tx = animateTo[1] * squareSize + squareSize / 2;
      const ty = animateTo[0] * squareSize + squareSize / 2;
      const x = sx + (tx - sx) * animateProgress;
      const y = sy + (ty - sy) * animateProgress;
      // Lift effect
      const lift = Math.sin(animateProgress * Math.PI) * 20;
      drawPiece(ctx, x, y - lift, radius, piece.color, piece.king);
    }
  }

  // King promotion animation
  if (kingPromotion) {
    const { r, c, progress } = kingPromotion;
    const x = c * squareSize + squareSize / 2;
    const y = r * squareSize + squareSize / 2;
    const scale = 1 + 0.5 * Math.sin(progress * Math.PI);
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(scale, scale);
    drawPiece(ctx, 0, 0, radius, 'w', true); // crown preview
    ctx.restore();
  }
}

export function drawPiece(ctx, x, y, radius, color, isKing) {
  // Shadow
  ctx.shadowColor = 'rgba(0,0,0,0.4)';
  ctx.shadowBlur = 8;
  ctx.shadowOffsetY = 4;

  // Piece body
  const grad = ctx.createRadialGradient(x - radius*0.3, y - radius*0.3, radius*0.1, x, y, radius);
  if (color === 'w') {
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.5, '#f0f0f0');
    grad.addColorStop(1, '#d0d0d0');
  } else {
    grad.addColorStop(0, '#333333');
    grad.addColorStop(0.5, '#1a1a1a');
    grad.addColorStop(1, '#000000');
  }
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();

  // Stroke
  ctx.shadowColor = 'transparent';
  ctx.strokeStyle = color === 'w' ? '#aaa' : '#000';
  ctx.lineWidth = PIECE_STROKE;
  ctx.stroke();

  // King crown
  if (isKing) {
    ctx.fillStyle = '#ffd700';
    ctx.strokeStyle = '#b8860b';
    ctx.lineWidth = 1.5;
    const crownSize = radius * 0.55;
    ctx.beginPath();
    ctx.moveTo(x - crownSize, y + crownSize * 0.3);
    ctx.lineTo(x - crownSize * 0.5, y - crownSize * 0.3);
    ctx.lineTo(x, y + crownSize * 0.2);
    ctx.lineTo(x + crownSize * 0.5, y - crownSize * 0.3);
    ctx.lineTo(x + crownSize, y + crownSize * 0.3);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    // Cross on top
    ctx.beginPath();
    ctx.moveTo(x, y - crownSize * 0.3);
    ctx.lineTo(x, y - crownSize * 0.6);
    ctx.moveTo(x - crownSize * 0.2, y - crownSize * 0.45);
    ctx.lineTo(x + crownSize * 0.2, y - crownSize * 0.45);
    ctx.stroke();
  }
}

export function animateMove(board, from, to, onComplete) {
  const startTime = performance.now();
  function frame(now) {
    const progress = Math.min(1, (now - startTime) / ANIMATION_DURATION);
    const eased = 1 - Math.pow(1 - progress, 3); // cubic ease-out
    // Redraw with animation
    // This will be called from game controller with requestAnimationFrame
    onComplete(eased);
    if (progress < 1) requestAnimationFrame(frame);
    else onComplete(1);
  }
  requestAnimationFrame(frame);
}

export function highlightSquares(ctx, squares, color) {
  // Used by preview
}

export class CheckersGame {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.board = null;
    this.myColor = null;
    this.turn = 'w';
    this.history = [];
    this.captured = { w: [], b: [] };
    this.selectedSquare = null;
    this.validMoves = [];
    this.lastMove = null;
    this.animating = false;
    this.animationStart = 0;
    this.animationFrom = null;
    this.animationTo = null;
    this.ws = null;
    this.gameId = null;

    this.resize();
    window.addEventListener('resize', () => this.resize());
    this.canvas.addEventListener('click', (e) => this.handleClick(e));
    this.render();
  }

  resize() {
    const wrapper = this.canvas.parentElement;
    const size = Math.min(wrapper.clientWidth - 40, wrapper.clientHeight - 40, 640);
    this.canvas.width = size;
    this.canvas.height = size;
    this.render();
  }

  async init(gameId, ws) {
    this.gameId = gameId;
    this.ws = ws;
    const { createInitialBoard } = await import('./logic.js');
    this.board = createInitialBoard();
    this.render();
  }

  setMyColor(color) {
    this.myColor = color;
    this.updateTurnIndicator();
  }

  handleMessage(msg) {
    if (msg.type === 'color') {
      this.setMyColor(msg.color);
    } else if (msg.type === 'board') {
      this.animateToBoard(msg.board);
    } else if (msg.type === 'game_over') {
      this.handleGameOver(msg.winner);
    } else if (msg.type === 'error') {
      console.warn('Server error:', msg.message);
    }
  }

  animateToBoard(newBoard) {
    // Find moved piece
    let from = null, to = null;
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const oldP = this.board?.[r]?.[c];
        const newP = newBoard[r][c];
        if (oldP && !newP) from = [r,c];
        if (!oldP && newP) to = [r,c];
      }
    }
    // A board that arrives without a matching from/to pair is a sync, not a
    // move — highlighting it would mean indexing a null coordinate.
    this.lastMove = from && to ? { from, to } : null;
    if (from && to) {
      this.animateMove(from, to, () => {
        this.board = newBoard;
        this.turn = this.turn === 'w' ? 'b' : 'w';
        this.updateHistory(from, to);
        this.updateCaptured();
        this.render();
      });
    } else {
      this.board = newBoard;
      this.render();
    }
  }

  animateMove(from, to, onComplete) {
    this.animating = true;
    this.animationFrom = from;
    this.animationTo = to;
    this.animationStart = performance.now();
    const animate = (now) => {
      const progress = Math.min(1, (now - this.animationStart) / 150);
      const eased = 1 - Math.pow(1 - progress, 3);
      this.render({ animateFrom: from, animateTo: to, animateProgress: eased });
      if (progress < 1) requestAnimationFrame(animate);
      else {
        this.animating = false;
        this.animationFrom = this.animationTo = null;
        onComplete();
      }
    };
    requestAnimationFrame(animate);
  }

  render(options = {}) {
    if (!this.board) return;
    drawBoard(this.ctx, this.board, {
      selectedSquare: options.selectedSquare ?? this.selectedSquare,
      validMoves: options.validMoves ?? this.validMoves,
      lastMove: options.lastMove ?? this.lastMove,
      animateFrom: options.animateFrom,
      animateTo: options.animateTo,
      animateProgress: options.animateProgress
    });
  }

  async handleClick(e) {
    if (this.animating || this.turn !== this.myColor) return;
    const rect = this.canvas.getBoundingClientRect();
    const squareSize = this.canvas.width / 8;
    const c = Math.floor((e.clientX - rect.left) / squareSize);
    const r = Math.floor((e.clientY - rect.top) / squareSize);
    if (r < 0 || r >= 8 || c < 0 || c >= 8) return;

    const piece = this.board[r][c];
    const { getLegalMoves } = await import('./logic.js');
    
    if (!this.selectedSquare) {
      if (piece && piece.color === this.myColor) {
        this.selectedSquare = [r, c];
        const allMoves = getLegalMoves(this.board, this.myColor);
        this.validMoves = allMoves.filter(move => move.from[0] === r && move.from[1] === c);
        this.render();
      }
    } else {
      if (this.selectedSquare[0] === r && this.selectedSquare[1] === c) {
        this.selectedSquare = null;
        this.validMoves = [];
        this.render();
      } else if (this.validMoves.some(([vr, vc]) => vr === r && vc === c)) {
        this.sendMove(this.selectedSquare, [r, c]);
        this.selectedSquare = null;
        this.validMoves = [];
      } else if (piece && piece.color === this.myColor) {
        this.selectedSquare = [r, c];
        const allMoves = getLegalMoves(this.board, this.myColor);
        this.validMoves = allMoves.filter(move => move.from[0] === r && move.from[1] === c);
        this.render();
      }
    }
  }

  getValidMovesForPiece(r, c) {
    import('./logic.js').then(m => {
      const allMoves = m.getLegalMoves(this.board, this.myColor);
      return allMoves.filter(move => move.from[0] === r && move.from[1] === c);
    });
    // Return empty for now - the async import won't work synchronously
    // We'll handle this in handleClick by calling getLegalMoves directly
    return [];
  }

  sendMove(from, to) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'move', from, to }));
    }
  }

  updateTurnIndicator() {
    const el = document.getElementById('turn-indicator');
    if (el) {
      el.textContent = `${this.turn === 'w' ? 'White' : 'Black'} to move`;
      el.className = this.turn;
    }
  }

  updateHistory(from, to) {
    import('./logic.js').then(m => {
      const moveStr = `${m.algebraic(from)}-${m.algebraic(to)}`;
      const moveNum = Math.floor(this.history.length / 2) + 1;
      const entry = `${moveNum}. ${moveStr}`;
      this.history.push(entry);
      const list = document.getElementById('history-list');
      if (list) {
        const li = document.createElement('li');
        li.textContent = entry;
        list.appendChild(li);
        list.scrollTop = list.scrollHeight;
      }
    });
  }

  updateCaptured() {
    // Compare captured pieces count
    const initial = { w: 12, b: 12 };
    let wCount = 0, bCount = 0;
    for (const row of this.board) {
      for (const p of row) {
        if (p) { if (p.color === 'w') wCount++; else bCount++; }
      }
    }
    const capturedW = initial.b - bCount;
    const capturedB = initial.w - wCount;
    this.renderCaptured('captured-white-pieces', capturedW, 'w');
    this.renderCaptured('captured-black-pieces', capturedB, 'b');
  }

  renderCaptured(containerId, count, color) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    const maxShow = 12;
    for (let i = 0; i < Math.min(count, maxShow); i++) {
      const div = document.createElement('div');
      div.className = `captured-piece ${color === 'b' ? 'black' : ''}`;
      container.appendChild(div);
    }
    if (count > maxShow) {
      const div = document.createElement('div');
      div.className = 'captured-piece';
      div.textContent = `+${count - maxShow}`;
      div.style.fontSize = '10px';
      div.style.display = 'flex';
      div.style.alignItems = 'center';
      div.style.justifyContent = 'center';
      container.appendChild(div);
    }
  }

  handleGameOver(winner) {
    const won = winner === this.myColor;
    alert(won ? 'You win!' : 'You lose.');
    // Could show a nice modal instead
  }
}