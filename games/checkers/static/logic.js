/**
 * Checkers (Damas) — Client-side rule engine.
 *
 * Rules enforced:
 * - Mandatory capture: if captures exist, only captures are legal.
 * - Multi-capture chain: after a capture, if the same piece can capture
 *   again, the turn continues.
 * - King movement: slides any number of empty squares along a diagonal.
 */
export const COLS = 8, ROWS = 8;
export const EMPTY = null;

export function createInitialBoard() {
  const board = Array(ROWS).fill(null).map(() => Array(COLS).fill(EMPTY));
  for (let r = 5; r < 8; r++)
    for (let c = 0; c < COLS; c++)
      if ((r + c) % 2 === 0) board[r][c] = { color: 'w', king: false };
  for (let r = 0; r < 3; r++)
    for (let c = 0; c < COLS; c++)
      if ((r + c) % 2 === 0) board[r][c] = { color: 'b', king: false };
  return board;
}

export function cloneBoard(board) {
  return board.map(row => row.map(p => p ? { ...p } : null));
}

export function getPieceAt(board, [r, c]) {
  if (r < 0 || r >= ROWS || c < 0 || c >= COLS) return null;
  return board[r][c];
}

// ═══════════════════════════════════════════════════════════════
//  LEGAL MOVES — with mandatory capture + king sliding
// ═══════════════════════════════════════════════════════════════

/**
 * Get all legal moves for `color`.
 * Returns array of move objects:
 *   { from: [r,c], to: [r,c], capture: bool, captured?: [[r,c],...], distance?: number }
 *
 * If any capture exists, ONLY captures are returned (mandatory capture).
 */
export function getLegalMoves(board, color) {
  const captures = [];
  const normals = [];

  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const piece = board[r][c];
      if (!piece || piece.color !== color) continue;

      // Find captures
      const caps = findCaptures(board, r, c, piece, color, new Set(), [], r, c);
      captures.push(...caps);

      // Find normal moves
      const norms = findNormalMoves(board, r, c, piece, color);
      normals.push(...norms);
    }
  }

  // Mandatory capture rule
  if (captures.length > 0) return captures;
  return normals;
}

/**
 * Get moves for a specific piece at (r, c).
 * During a multi-capture chain, only returns captures for that piece.
 */
export function getMovesForPiece(board, r, c, color, captureOnly = false) {
  const piece = board[r][c];
  if (!piece || piece.color !== color) return [];

  const caps = findCaptures(board, r, c, piece, color, new Set(), [], r, c);
  if (captureOnly || caps.length > 0) return caps;

  return findNormalMoves(board, r, c, piece, color);
}

// ── Normal moves ────────────────────────────────────────────────

function findNormalMoves(board, r, c, piece, color) {
  const moves = [];
  if (piece.king) {
    // King slides along diagonals
    for (const [dr, dc] of [[-1, -1], [-1, 1], [1, -1], [1, 1]]) {
      for (let dist = 1; dist < 8; dist++) {
        const nr = r + dr * dist, nc = c + dc * dist;
        if (nr < 0 || nr >= ROWS || nc < 0 || nc >= COLS) break;
        if (board[nr][nc]) break; // blocked
        moves.push({ from: [r, c], to: [nr, nc], capture: false, distance: dist });
      }
    }
  } else {
    // Regular piece: one step forward
    const dirs = color === 'w' ? [[-1, -1], [-1, 1]] : [[1, -1], [1, 1]];
    for (const [dr, dc] of dirs) {
      const nr = r + dr, nc = c + dc;
      if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS && !board[nr][nc]) {
        moves.push({ from: [r, c], to: [nr, nc], capture: false, distance: 1 });
      }
    }
  }
  return moves;
}

// ── Captures (single + multi-chain) ─────────────────────────────

function findCaptures(board, r, c, piece, color, visited, path, startR, startC) {
  const results = [];
  _dfsCaptures(board, r, c, piece, color, visited, path, results, startR, startC);
  return results;
}

function _dfsCaptures(board, r, c, piece, color, visited, path, results, startR, startC) {
  let foundAny = false;

  if (piece.king) {
    // King captures: slide along diagonal, find enemy, land beyond
    for (const [dr, dc] of [[-1, -1], [-1, 1], [1, -1], [1, 1]]) {
      for (let dist = 1; dist < 8; dist++) {
        const midR = r + dr * dist, midC = c + dc * dist;
        if (midR < 0 || midR >= ROWS || midC < 0 || midC >= COLS) break;

        if (board[midR][midC]) {
          // Found a piece — check if it's enemy and not already captured
          if (board[midR][midC].color !== color && !visited.has(`${midR},${midC}`)) {
            // Look for landing squares beyond
            for (let landDist = dist + 1; landDist < 8; landDist++) {
              const landR = r + dr * landDist, landC = c + dc * landDist;
              if (landR < 0 || landR >= ROWS || landC < 0 || landC >= COLS) break;
              if (board[landR][landC]) break; // blocked

              // Valid capture
              foundAny = true;
              const newVisited = new Set(visited);
              newVisited.add(`${midR},${midC}`);
              const newPath = [...path, [midR, midC]];

              _dfsCaptures(
                board, landR, landC, piece, color,
                newVisited, newPath, results, startR, startC
              );
            }
          }
          break; // can't jump further past a piece
        }
        // Empty square — king slides through (no capture here)
      }
    }
  } else {
    // Regular piece: jumps exactly 2 squares
    for (const [dr, dc] of [[-1, -1], [-1, 1], [1, -1], [1, 1]]) {
      const midR = r + dr, midC = c + dc;
      const landR = r + 2 * dr, landC = c + 2 * dc;
      if (midR < 0 || midR >= ROWS || midC < 0 || midC >= COLS) continue;
      if (landR < 0 || landR >= ROWS || landC < 0 || landC >= COLS) continue;
      if (visited.has(`${midR},${midC}`)) continue;

      const midPiece = board[midR][midC];
      if (midPiece && midPiece.color !== color && !board[landR][landC]) {
        foundAny = true;
        const newVisited = new Set(visited);
        newVisited.add(`${midR},${midC}`);
        const newPath = [...path, [midR, midC]];

        _dfsCaptures(
          board, landR, landC, piece, color,
          newVisited, newPath, results, startR, startC
        );
      }
    }
  }

  // If no further captures possible and we captured at least one piece → valid chain end
  if (!foundAny && path.length > 0) {
    results.push({
      from: [startR, startC],
      to: [r, c],
      capture: true,
      captured: [...path],
    });
  }
}

// ═══════════════════════════════════════════════════════════════
//  APPLY MOVE
// ═══════════════════════════════════════════════════════════════

export function applyMove(board, from, to) {
  const [fr, fc] = from;
  const [tr, tc] = to;
  const piece = board[fr][fc];
  if (!piece) return false;

  board[tr][tc] = piece;
  board[fr][fc] = null;

  // King promotion
  if (!piece.king && ((piece.color === 'w' && tr === 0) || (piece.color === 'b' && tr === ROWS - 1))) {
    piece.king = true;
  }
  return true;
}

export function isValidMove(board, from, to, color) {
  const moves = getLegalMoves(board, color);
  return moves.some(m =>
    m.from[0] === from[0] && m.from[1] === from[1] &&
    m.to[0] === to[0] && m.to[1] === to[1]
  );
}

export function algebraic([r, c]) {
  const files = 'abcdefgh';
  const ranks = '87654321';
  return `${files[c]}${ranks[r]}`;
}

export function parseAlgebraic(str) {
  const files = 'abcdefgh';
  const c = files.indexOf(str[0]);
  const r = 7 - parseInt(str[1], 10);
  return [r, c];
}
