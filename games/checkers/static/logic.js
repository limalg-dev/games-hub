export const COLS = 8, ROWS = 8;
export const EMPTY = null;
export const COLORS = { WHITE: 'w', BLACK: 'b' };

export function createInitialBoard() {
  const board = Array(ROWS).fill(null).map(() => Array(COLS).fill(EMPTY));
  // White pieces (bottom, rows 5-7)
  for (let r = 5; r < 8; r++) {
    for (let c = 0; c < COLS; c++) {
      if ((r + c) % 2 === 0) board[r][c] = { color: 'w', king: false };
    }
  }
  // Black pieces (top, rows 0-2)
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < COLS; c++) {
      if ((r + c) % 2 === 0) board[r][c] = { color: 'b', king: false };
    }
  }
  return board;
}

export function cloneBoard(board) {
  return board.map(row => row.map(p => p ? {...p} : null));
}

export function getPieceAt(board, [r, c]) {
  if (r < 0 || r >= ROWS || c < 0 || c >= COLS) return null;
  return board[r][c];
}

export function getLegalMoves(board, color) {
  const moves = [];
  const dirs = color === 'w' ? [[-1,-1],[-1,1]] : [[1,-1],[1,1]];
  const kingDirs = [[-1,-1],[-1,1],[1,-1],[1,1]];

  // First pass: captures (mandatory)
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const piece = board[r][c];
      if (!piece || piece.color !== color) continue;
      const pieceMoves = piece.king ? kingDirs : dirs;
      findCaptures(board, r, c, piece, pieceMoves, [], moves, r, c);
    }
  }
  if (moves.length) return moves;

  // Second pass: normal moves
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const piece = board[r][c];
      if (!piece || piece.color !== color) continue;
      const pieceMoves = piece.king ? kingDirs : dirs;
      for (const [dr, dc] of pieceMoves) {
        const nr = r + dr, nc = c + dc;
        if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS && !board[nr][nc]) {
          moves.push({ from: [r,c], to: [nr,nc], capture: false });
        }
      }
    }
  }
  return moves;
}

function findCaptures(board, r, c, piece, dirs, path, moves, startR, startC) {
  let found = false;
  for (const [dr, dc] of dirs) {
    const midR = r + dr, midC = c + dc;
    const landR = r + 2*dr, landC = c + 2*dc;
    if (landR < 0 || landR >= ROWS || landC < 0 || landC >= COLS) continue;
    const midPiece = board[midR][midC];
    const landPiece = board[landR][landC];
    if (midPiece && midPiece.color !== piece.color && !landPiece) {
      found = true;
      // Simulate capture
      board[midR][midC] = null;
      board[landR][landC] = piece;
      board[r][c] = null;
      const newPath = [...path, [midR, midC]];
      findCaptures(board, landR, landC, piece, dirs, newPath, moves, startR, startC);
      // Undo
      board[r][c] = piece;
      board[landR][landC] = null;
      board[midR][midC] = midPiece;
    }
  }
  if (!found && path.length > 0) {
    moves.push({ from: [startR, startC], to: [r,c], capture: true, captured: path });
  }
}

export function applyMove(board, from, to) {
  const [fr, fc] = from;
  const [tr, tc] = to;
  const piece = board[fr][fc];
  if (!piece) return false;

  board[tr][tc] = piece;
  board[fr][fc] = null;

  // King promotion
  if (!piece.king && ((piece.color === 'w' && tr === 0) || (piece.color === 'b' && tr === ROWS-1))) {
    piece.king = true;
  }
  return true;
}

export function isValidMove(board, from, to, color) {
  const moves = getLegalMoves(board, color);
  return moves.some(m => m.from[0]===from[0] && m.from[1]===from[1] && m.to[0]===to[0] && m.to[1]===to[1]);
}

export function algebraic([r, c]) {
  const files = 'abcdefgh';
  const ranks = '87654321'; // White at bottom (rank 1 = row 7)
  return `${files[c]}${ranks[r]}`;
}

export function parseAlgebraic(str) {
  const files = 'abcdefgh';
  const c = files.indexOf(str[0]);
  const r = 7 - parseInt(str[1], 10);
  return [r, c];
}