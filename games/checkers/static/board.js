const BOARD_SIZE = 8;
const ANIMATION_DURATION = 200;
const DRAG_LIFT = 12; // pixels piece lifts when dragged

// Wood texture cache
let woodPattern = null;

// ── Server board normalization ──────────────────────────────────
function normalizeServerBoard(rawBoard) {
  if (!rawBoard) return rawBoard;
  return rawBoard.map(row => row.map(cell => {
    if (!cell) return null;
    if (typeof cell === 'object') return cell;
    return { color: cell.toLowerCase(), king: cell === cell.toUpperCase() };
  }));
}

function createWoodPattern(ctx) {
  if (woodPattern) return woodPattern;
  const canvas = document.createElement('canvas');
  canvas.width = 256; canvas.height = 256;
  const c = canvas.getContext('2d');
  const gradient = c.createLinearGradient(0, 0, 256, 256);
  gradient.addColorStop(0, '#e8c58a');
  gradient.addColorStop(0.5, '#d4a574');
  gradient.addColorStop(1, '#c4945a');
  c.fillStyle = gradient;
  c.fillRect(0, 0, 256, 256);
  const imgData = c.getImageData(0, 0, 256, 256);
  const data = imgData.data;
  for (let i = 0; i < data.length; i += 4) {
    const noise = (Math.random() - 0.5) * 20;
    data[i]   = Math.max(0, Math.min(255, data[i] + noise));
    data[i+1] = Math.max(0, Math.min(255, data[i+1] + noise));
    data[i+2] = Math.max(0, Math.min(255, data[i+2] + noise));
  }
  c.putImageData(imgData, 0, 0);
  woodPattern = ctx.createPattern(canvas, 'repeat');
  return woodPattern;
}

// ── Draw board ──────────────────────────────────────────────────
export function drawBoard(ctx, board, options = {}) {
  const {
    selectedSquare, validMoves = [], lastMove,
    animateFrom, animateTo, animateProgress,
    kingPromotion, dragPiece, dragX, dragY
  } = options;

  const width = ctx.canvas.width;
  const height = ctx.canvas.height;
  const sq = width / BOARD_SIZE;
  const radius = sq * 0.375;

  ctx.clearRect(0, 0, width, height);

  // Wood background
  ctx.fillStyle = createWoodPattern(ctx);
  ctx.fillRect(0, 0, width, height);

  // ── Squares ──
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      const x = c * sq, y = r * sq;
      const isDark = (r + c) % 2 === 0;

      if (isDark) {
        ctx.fillStyle = '#b58863';
        ctx.fillRect(x, y, sq, sq);
      }

      // Selected square highlight
      if (selectedSquare && selectedSquare[0] === r && selectedSquare[1] === c) {
        ctx.fillStyle = 'rgba(233, 69, 96, 0.35)';
        ctx.fillRect(x, y, sq, sq);
      }

      // Valid move highlights — filled circle with glow
      if (validMoves.some(m => m.to[0] === r && m.to[1] === c)) {
        const pulse = 0.5 + 0.5 * Math.sin(Date.now() / 180);
        // Outer glow
        ctx.save();
        ctx.shadowColor = 'rgba(255, 215, 0, 0.6)';
        ctx.shadowBlur = 10 + pulse * 6;
        ctx.fillStyle = `rgba(255, 215, 0, ${0.25 + 0.15 * pulse})`;
        ctx.beginPath();
        ctx.arc(x + sq/2, y + sq/2, sq * 0.22, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
        // Inner dot
        ctx.fillStyle = `rgba(255, 215, 0, ${0.6 + 0.3 * pulse})`;
        ctx.beginPath();
        ctx.arc(x + sq/2, y + sq/2, sq * 0.09, 0, Math.PI * 2);
        ctx.fill();

        // Capture indicator (ring)
        const isCapture = validMoves.some(m =>
          m.to[0] === r && m.to[1] === c && m.capture
        );
        if (isCapture) {
          ctx.strokeStyle = `rgba(255, 60, 60, ${0.4 + 0.3 * pulse})`;
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.arc(x + sq/2, y + sq/2, sq * 0.28, 0, Math.PI * 2);
          ctx.stroke();
        }
      }

      // Last move highlight
      if (lastMove?.from && lastMove?.to &&
          ((lastMove.from[0]===r && lastMove.from[1]===c) ||
           (lastMove.to[0]===r && lastMove.to[1]===c))) {
        ctx.fillStyle = 'rgba(255, 215, 0, 0.2)';
        ctx.fillRect(x, y, sq, sq);
      }
    }
  }

  // Border
  ctx.strokeStyle = '#8b6b4a';
  ctx.lineWidth = 4;
  ctx.strokeRect(2, 2, width - 4, height - 4);

  // ── Pieces ──
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      const piece = board[r][c];
      if (!piece) continue;

      // Skip the piece being dragged
      if (dragPiece && dragPiece.fromR === r && dragPiece.fromC === c) continue;
      // Skip animating piece (only if not the drag piece)
      if (animateFrom && animateFrom[0] === r && animateFrom[1] === c && !dragPiece) continue;

      const px = c * sq + sq / 2;
      const py = r * sq + sq / 2;
      drawPiece(ctx, px, py, radius, piece.color, piece.king);
    }
  }

  // ── Animating piece (move transition) ──
  if (animateFrom && animateTo && animateProgress !== undefined) {
    const piece = board[animateFrom[0]][animateFrom[1]];
    if (piece) {
      const sx = animateFrom[1] * sq + sq / 2;
      const sy = animateFrom[0] * sq + sq / 2;
      const tx = animateTo[1] * sq + sq / 2;
      const ty = animateTo[0] * sq + sq / 2;
      const x = sx + (tx - sx) * animateProgress;
      const y = sy + (ty - sy) * animateProgress;
      // Lift arc
      const lift = Math.sin(animateProgress * Math.PI) * 22;
      drawPiece(ctx, x, y - lift, radius, piece.color, piece.king);
    }
  }

  // ── Dragged piece (follows cursor) ──
  if (dragPiece && dragX !== undefined && dragY !== undefined) {
    const piece = dragPiece.piece;
    drawPiece(ctx, dragX, dragY - DRAG_LIFT, radius * 1.08, piece.color, piece.king);
  }

  // ── King promotion animation ──
  if (kingPromotion) {
    const { r, c, progress, color } = kingPromotion;
    const cx = c * sq + sq / 2;
    const cy = r * sq + sq / 2;

    // Particle burst
    const particleCount = 12;
    for (let i = 0; i < particleCount; i++) {
      const angle = (i / particleCount) * Math.PI * 2;
      const dist = progress * sq * 0.6;
      const px = cx + Math.cos(angle) * dist;
      const py = cy + Math.sin(angle) * dist;
      const alpha = Math.max(0, 1 - progress);
      const size = (1 - progress) * 5;
      ctx.fillStyle = `rgba(255, 215, 0, ${alpha})`;
      ctx.beginPath();
      ctx.arc(px, py, size, 0, Math.PI * 2);
      ctx.fill();
    }

    // Crown glow
    const glowAlpha = Math.sin(progress * Math.PI) * 0.5;
    ctx.save();
    ctx.shadowColor = '#ffd700';
    ctx.shadowBlur = 30 * glowAlpha;
    ctx.fillStyle = `rgba(255, 215, 0, ${glowAlpha * 0.3})`;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 1.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Scale pulse
    const scale = 1 + 0.3 * Math.sin(progress * Math.PI * 2);
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(scale, scale);
    drawPiece(ctx, 0, 0, radius, color || 'w', true);
    ctx.restore();
  }
}

// ── Draw single piece ───────────────────────────────────────────
export function drawPiece(ctx, x, y, radius, color, isKing) {
  ctx.save();
  // Shadow
  ctx.shadowColor = 'rgba(0,0,0,0.45)';
  ctx.shadowBlur = 8;
  ctx.shadowOffsetY = 3;

  // Body gradient
  const grad = ctx.createRadialGradient(x - radius*0.3, y - radius*0.3, radius*0.1, x, y, radius);
  if (color === 'w') {
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.4, '#f0f0f0');
    grad.addColorStop(0.8, '#d8d8d8');
    grad.addColorStop(1, '#b0b0b0');
  } else {
    grad.addColorStop(0, '#444');
    grad.addColorStop(0.4, '#222');
    grad.addColorStop(0.8, '#111');
    grad.addColorStop(1, '#000');
  }
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();

  // Inner ring
  ctx.shadowColor = 'transparent';
  ctx.strokeStyle = color === 'w' ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.08)';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(x, y, radius * 0.65, 0, Math.PI * 2);
  ctx.stroke();

  // Outer stroke
  ctx.strokeStyle = color === 'w' ? '#999' : '#000';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.stroke();

  // King crown
  if (isKing) {
    const cs = radius * 0.5;
    // Crown body
    ctx.fillStyle = '#ffd700';
    ctx.strokeStyle = '#b8860b';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(x - cs, y + cs * 0.3);
    ctx.lineTo(x - cs * 0.5, y - cs * 0.4);
    ctx.lineTo(x, y + cs * 0.15);
    ctx.lineTo(x + cs * 0.5, y - cs * 0.4);
    ctx.lineTo(x + cs, y + cs * 0.3);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    // Cross
    ctx.strokeStyle = '#b8860b';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(x, y - cs * 0.25);
    ctx.lineTo(x, y - cs * 0.6);
    ctx.moveTo(x - cs * 0.2, y - cs * 0.42);
    ctx.lineTo(x + cs * 0.2, y - cs * 0.42);
    ctx.stroke();
  }

  ctx.restore();
}

// ── Main game class ─────────────────────────────────────────────
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

    // Animation state
    this.animating = false;
    this.animationFrom = null;
    this.animationTo = null;
    this.animationStart = 0;

    // Drag state
    this.dragging = false;
    this.dragPiece = null;   // { piece, fromR, fromC }
    this.dragX = 0;
    this.dragY = 0;
    this.dragStartSquare = null;

    // Multi-capture chain state
    this.captureChain = null;  // { pieceR, pieceC, capturedSoFar: [[r,c],...] }

    // King promotion animation
    this.kingPromotion = null;

    // WebSocket
    this.ws = null;
    this.gameId = null;
    this.gameOver = false;
    this.onGameOver = null;

    this.resize();
    window.addEventListener('resize', () => this.resize());

    // Input events
    this.canvas.addEventListener('mousedown', (e) => this._onMouseDown(e));
    this.canvas.addEventListener('mousemove', (e) => this._onMouseMove(e));
    this.canvas.addEventListener('mouseup', (e) => this._onMouseUp(e));
    this.canvas.addEventListener('mouseleave', () => this._onMouseLeave());

    // Touch events for mobile
    this.canvas.addEventListener('touchstart', (e) => this._onTouchStart(e), { passive: false });
    this.canvas.addEventListener('touchmove', (e) => this._onTouchMove(e), { passive: false });
    this.canvas.addEventListener('touchend', (e) => this._onTouchEnd(e), { passive: false });

    this.render();
  }

  // ── Resize ──
  resize() {
    const wrapper = this.canvas.parentElement;
    const size = Math.min(wrapper.clientWidth - 40, wrapper.clientHeight - 40, 640);
    this.canvas.width = size;
    this.canvas.height = size;
    this.render();
  }

  _squareFromEvent(e) {
    const rect = this.canvas.getBoundingClientRect();
    const sq = this.canvas.width / BOARD_SIZE;
    const c = Math.floor((e.clientX - rect.left) / sq);
    const r = Math.floor((e.clientY - rect.top) / sq);
    if (r < 0 || r >= BOARD_SIZE || c < 0 || c >= BOARD_SIZE) return null;
    return [r, c];
  }

  _posFromEvent(e) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) * (this.canvas.width / rect.width),
      y: (e.clientY - rect.top) * (this.canvas.height / rect.height)
    };
  }

  // ── Init / WebSocket ──
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
      this.handleGameOver(msg.winner, msg.reason);
    } else if (msg.type === 'error') {
      console.warn('Server error:', msg.message);
    }
  }

  animateToBoard(rawBoard) {
    const newBoard = normalizeServerBoard(rawBoard);
    let from = null, to = null, captured = null;
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const oldP = this.board?.[r]?.[c];
        const newP = newBoard[r][c];
        if (oldP && !newP) from = [r, c];
        if (!oldP && newP) to = [r, c];
        // Detect captured piece (was opponent, now gone)
        if (oldP && !newP && oldP.color !== this.myColor) {
          captured = [r, c];
        }
      }
    }
    this.lastMove = from && to ? { from, to } : null;

    if (from && to) {
      // Detect king promotion
      const oldPiece = this.board[from[0]][from[1]];
      const newPiece = newBoard[to[0]][to[1]];
      const wasPromoted = oldPiece && newPiece && !oldPiece.king && newPiece.king;

      this.animateMove(from, to, () => {
        this.board = newBoard;
        this.turn = this.turn === 'w' ? 'b' : 'w';
        this.updateHistory(from, to);
        this.updateCaptured();
        this._endCaptureChain();
        this.render();

        // Trigger coronation animation
        if (wasPromoted) {
          this.playCoronation(to[0], to[1], newPiece.color);
        }
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
      const elapsed = now - this.animationStart;
      const t = Math.min(1, elapsed / ANIMATION_DURATION);
      // Cubic ease-out
      const eased = 1 - Math.pow(1 - t, 3);
      this.render({ animateFrom: from, animateTo: to, animateProgress: eased });
      if (t < 1) {
        requestAnimationFrame(animate);
      } else {
        this.animating = false;
        this.animationFrom = this.animationTo = null;
        onComplete();
      }
    };
    requestAnimationFrame(animate);
  }

  playCoronation(r, c, color) {
    this.kingPromotion = { r, c, progress: 0, color };
    const start = performance.now();
    const animate = (now) => {
      const t = Math.min(1, (now - start) / 600);
      this.kingPromotion.progress = t;
      this.render();
      if (t < 1) requestAnimationFrame(animate);
      else this.kingPromotion = null;
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
      animateProgress: options.animateProgress,
      kingPromotion: options.kingPromotion ?? this.kingPromotion,
      dragPiece: options.dragPiece ?? (this.dragging ? this.dragPiece : null),
      dragX: options.dragX ?? this.dragX,
      dragY: options.dragY ?? this.dragY,
    });
  }

  // ════════════════════════════════════════════════════════════════
  //  INPUT HANDLERS — Click + Drag & Drop
  // ════════════════════════════════════════════════════════════════

  async _selectPiece(r, c) {
    // If in a capture chain, only the chaining piece can be selected
    if (this.captureChain) {
      if (r !== this.captureChain.pieceR || c !== this.captureChain.pieceC) return;
    }
    this.selectedSquare = [r, c];
    const { getMovesForPiece } = await import('./logic.js');
    const captureOnly = !!this.captureChain;
    this.validMoves = getMovesForPiece(this.board, r, c, this.myColor, captureOnly);
    this.render();
  }

  _deselect() {
    // Don't allow deselection during a capture chain
    if (this.captureChain) return;
    this.selectedSquare = null;
    this.validMoves = [];
    this.render();
  }

  _endCaptureChain() {
    this.captureChain = null;
    this.selectedSquare = null;
    this.validMoves = [];
  }

  // ── Mouse ──
  _onMouseDown(e) {
    if (this.animating || this.gameOver || this.turn !== this.myColor) return;
    const sq = this._squareFromEvent(e);
    if (!sq) return;
    const [r, c] = sq;
    const piece = this.board[r][c];

    // Start drag if clicking on own piece
    if (piece && piece.color === this.myColor) {
      // During capture chain, only the chaining piece can be dragged
      if (this.captureChain) {
        if (r !== this.captureChain.pieceR || c !== this.captureChain.pieceC) return;
      }
      const pos = this._posFromEvent(e);
      this.dragging = true;
      this.dragPiece = { piece: {...piece}, fromR: r, fromC: c };
      this.dragX = pos.x;
      this.dragY = pos.y;
      this.dragStartSquare = [r, c];

      // Also select the piece for valid move highlights
      this._selectPiece(r, c);
    } else if (this.selectedSquare) {
      // Clicking on empty square while piece is selected → try to move
      this._tryMove(r, c);
    }
  }

  _onMouseMove(e) {
    if (!this.dragging) return;
    const pos = this._posFromEvent(e);
    this.dragX = pos.x;
    this.dragY = pos.y;
    this.render();
  }

  async _onMouseUp(e) {
    if (!this.dragging) return;
    this.dragging = false;

    const sq = this._squareFromEvent(e);
    if (sq) {
      const [r, c] = sq;
      // If dropped on a different square
      if (r !== this.dragStartSquare[0] || c !== this.dragStartSquare[1]) {
        if (this.validMoves.some(m => m.to[0] === r && m.to[1] === c)) {
          this.dragPiece = null;
          this._executeMove(this.dragStartSquare, [r, c]);
          return;
        }
      }
    }
    // Snap back — piece stays selected
    this.dragPiece = null;
    this.render();
  }

  _onMouseLeave() {
    if (this.dragging) {
      this.dragging = false;
      this.dragPiece = null;
      this.render();
    }
  }

  // ── Touch ──
  _onTouchStart(e) {
    e.preventDefault();
    if (this.animating || this.gameOver || this.turn !== this.myColor) return;
    const touch = e.touches[0];
    const sq = this._squareFromEvent(touch);
    if (!sq) return;
    const [r, c] = sq;
    const piece = this.board[r][c];

    // During capture chain, clicking anywhere not valid does nothing
    if (this.captureChain && !(piece && piece.color === this.myColor && r === this.captureChain.pieceR && c === this.captureChain.pieceC)) {
      if (!this.validMoves.some(m => m.to[0] === r && m.to[1] === c)) return;
    }

    if (piece && piece.color === this.myColor) {
      // During capture chain, only the chaining piece can be dragged
      if (this.captureChain) {
        if (r !== this.captureChain.pieceR || c !== this.captureChain.pieceC) return;
      }
      const pos = this._posFromEvent(touch);
      this.dragging = true;
      this.dragPiece = { piece: {...piece}, fromR: r, fromC: c };
      this.dragX = pos.x;
      this.dragY = pos.y;
      this.dragStartSquare = [r, c];
      this._selectPiece(r, c);
    } else if (this.selectedSquare) {
      this._tryMove(r, c);
    }
  }

  _onTouchMove(e) {
    e.preventDefault();
    if (!this.dragging) return;
    const touch = e.touches[0];
    const pos = this._posFromEvent(touch);
    this.dragX = pos.x;
    this.dragY = pos.y;
    this.render();
  }

  _onTouchEnd(e) {
    e.preventDefault();
    if (!this.dragging) return;
    this.dragging = false;

    const touch = e.changedTouches[0];
    const sq = this._squareFromEvent(touch);
    if (sq) {
      const [r, c] = sq;
      if (r !== this.dragStartSquare[0] || c !== this.dragStartSquare[1]) {
        if (this.validMoves.some(m => m.to[0] === r && m.to[1] === c)) {
          this.dragPiece = null;
          this._executeMove(this.dragStartSquare, [r, c]);
          return;
        }
      }
    }
    this.dragPiece = null;
    this.render();
  }

  // ── Move logic ──
  async _tryMove(r, c) {
    const move = this.validMoves.find(m => m.to[0] === r && m.to[1] === c);
    if (move) {
      this._executeMove(this.selectedSquare, [r, c]);
    } else if (this.board[r][c] && this.board[r][c].color === this.myColor) {
      // During capture chain, only the chaining piece can be reselected
      if (this.captureChain && (r !== this.captureChain.pieceR || c !== this.captureChain.pieceC)) return;
      this._selectPiece(r, c);
    } else {
      this._deselect();
    }
  }

  async _executeMove(from, to) {
    const { getMovesForPiece } = await import('./logic.js');
    const move = this.validMoves.find(m => m.to[0] === to[0] && m.to[1] === to[1]);
    if (!move) return;

    // Apply the move locally
    const { applyMove } = await import('./logic.js');
    if (move.capture && move.captured) {
      for (const [mr, mc] of move.captured) {
        this.board[mr][mc] = null;
      }
    }
    applyMove(this.board, from, to);

    // Check for multi-capture chain
    if (move.capture) {
      const [tr, tc] = to;
      const piece = this.board[tr][tc];
      if (piece && piece.color === this.myColor) {
        // Check if more captures available from this position
        const moreCaptures = getMovesForPiece(this.board, tr, tc, this.myColor, true);
        if (moreCaptures.length > 0) {
          // Continue the capture chain!
          this.captureChain = {
            pieceR: tr,
            pieceC: tc,
            capturedSoFar: move.captured ? [...move.captured] : [],
          };
          this.selectedSquare = [tr, tc];
          this.validMoves = moreCaptures;
          this.dragPiece = null;
          this.render();
          return; // Don't send yet — chain continues
        }
      }
    }

    // No more captures — send the complete move to server
    this.sendMove(from, to);
    this._endCaptureChain();
  }

  sendMove(from, to) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'move', from, to }));
    }
  }

  // ── UI updates ──
  updateTurnIndicator() {
    const el = document.getElementById('turn-indicator');
    if (el) {
      el.textContent = `${this.turn === 'w' ? 'Brancas' : 'Pretas'} jogam`;
      el.className = this.turn;
    }
  }

  updateHistory(from, to) {
    import('./logic.js').then(m => {
      const moveStr = `${m.algebraic(from)}-${m.algebraic(to)}`;
      const moveNum = Math.floor(this.history.length / 2) + 1;
      this.history.push(`${moveNum}. ${moveStr}`);
      const list = document.getElementById('history-list');
      if (list) {
        const li = document.createElement('li');
        li.textContent = `${moveNum}. ${moveStr}`;
        list.appendChild(li);
        list.scrollTop = list.scrollHeight;
      }
    });
  }

  updateCaptured() {
    let wCount = 0, bCount = 0;
    for (const row of this.board) {
      for (const p of row) {
        if (p) { if (p.color === 'w') wCount++; else bCount++; }
      }
    }
    this.renderCaptured('captured-white-pieces', 12 - bCount, 'w');
    this.renderCaptured('captured-black-pieces', 12 - wCount, 'b');
  }

  renderCaptured(containerId, count, color) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < Math.min(count, 12); i++) {
      const div = document.createElement('div');
      div.className = `captured-piece ${color === 'b' ? 'black' : ''}`;
      container.appendChild(div);
    }
    if (count > 12) {
      const div = document.createElement('div');
      div.className = 'captured-piece';
      div.textContent = `+${count - 12}`;
      div.style.fontSize = '10px';
      div.style.display = 'flex';
      div.style.alignItems = 'center';
      div.style.justifyContent = 'center';
      container.appendChild(div);
    }
  }

  handleGameOver(winner, reason = null) {
    this.gameOver = true;
    if (typeof this.onGameOver === 'function') {
      this.onGameOver(winner, reason);
    }
  }
}
