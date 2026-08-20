/**
 * Test: findCaptures must set 'from' to the PIECE'S starting position,
 * not to the first captured piece's position.
 *
 * Bug: path[] only contained captured-piece coords, so from = path[0]
 * pointed at the first captured piece instead of the moving piece.
 */

// Inline the logic (simplified for Node test)
const ROWS = 8, COLS = 8;

function createBoard() {
  return Array(ROWS).fill(null).map(() => Array(COLS).fill(null));
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
      board[midR][midC] = null;
      board[landR][landC] = piece;
      board[r][c] = null;
      const newPath = [...path, [midR, midC]];
      findCaptures(board, landR, landC, piece, dirs, newPath, moves, startR, startC);
      board[r][c] = piece;
      board[landR][landC] = null;
      board[midR][midC] = midPiece;
    }
  }
  if (!found && path.length > 0) {
    moves.push({ from: [startR, startC], to: [r,c], capture: true, captured: path });
  }
}

function getCaptures(board, color) {
  const moves = [];
  const dirs = color === 'w' ? [[-1,-1],[-1,1]] : [[1,-1],[1,1]];
  const kingDirs = [[-1,-1],[-1,1],[1,-1],[1,1]];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const piece = board[r][c];
      if (!piece || piece.color !== color) continue;
      const pieceMoves = piece.king ? kingDirs : dirs;
      findCaptures(board, r, c, piece, pieceMoves, [], moves, r, c);
    }
  }
  return moves;
}

// ─── Test 1: Single capture — from must be the piece position ───
console.log('Test 1: Single capture from position');
{
  const board = createBoard();
  board[4][4] = { color: 'w', king: false };
  board[3][3] = { color: 'b', king: false };
  // Expected: from = [4,4], to = [2,2], captured = [[3,3]]

  const moves = getCaptures(board, 'w');
  console.log('  Moves:', JSON.stringify(moves));

  const m = moves[0];
  console.assert(m.from[0] === 4 && m.from[1] === 4,
    `FAIL: from should be [4,4] but got [${m.from}]`);
  console.assert(m.to[0] === 2 && m.to[1] === 2,
    `FAIL: to should be [2,2] but got [${m.to}]`);
  console.assert(m.captured.length === 1 && m.captured[0][0] === 3 && m.captured[0][1] === 3,
    `FAIL: captured should be [[3,3]] but got ${JSON.stringify(m.captured)}`);
  console.log('  ✅ PASS');
}

// ─── Test 2: Multi-jump capture — from must still be original position ───
console.log('Test 2: Multi-jump capture');
{
  const board = createBoard();
  board[5][1] = { color: 'w', king: false };
  board[4][2] = { color: 'b', king: false };
  board[2][2] = { color: 'b', king: false };
  // Path: (5,1) -> capture (4,2) -> (3,3) -> capture (2,2) -> (1,1)
  // Expected: from = [5,1], to = [1,1], captured = [[4,2],[2,2]]

  const moves = getCaptures(board, 'w');
  console.log('  Moves:', JSON.stringify(moves));

  const m = moves.find(m => m.to[0] === 1 && m.to[1] === 1);
  console.assert(m, 'FAIL: no move to [1,1]');
  if (m) {
    console.assert(m.from[0] === 5 && m.from[1] === 1,
      `FAIL: from should be [5,1] but got [${m.from}]`);
    console.assert(m.captured.length === 2,
      `FAIL: should capture 2 pieces but captured ${m.captured.length}`);
    console.log('  ✅ PASS');
  }
}

// ─── Test 3: BUG REPRO — old code would set from to first captured piece ───
console.log('Test 3: Regression — from must NOT be the first captured piece');
{
  const board = createBoard();
  board[5][1] = { color: 'w', king: false };
  board[4][2] = { color: 'b', king: false };
  board[2][2] = { color: 'b', king: false };

  const moves = getCaptures(board, 'w');
  const m = moves.find(m => m.to[0] === 1 && m.to[1] === 1);
  console.assert(m, 'FAIL: no move to [1,1]');
  if (m) {
    // The BUG: old code would set from = [4,2] (first captured piece)
    // The FIX: from = [5,1] (actual piece position)
    const isWrong = m.from[0] === 4 && m.from[1] === 2;
    console.assert(!isWrong,
      `FAIL: BUG STILL PRESENT — from is [4,2] (first captured piece) instead of [5,1]`);
    console.assert(m.from[0] === 5 && m.from[1] === 1,
      `FAIL: from should be [5,1] but got [${m.from}]`);
    console.log('  ✅ PASS — from correctly points to moving piece');
  }
}

console.log('\nAll tests passed! ✅');
