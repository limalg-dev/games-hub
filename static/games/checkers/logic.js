export const COLS = 8, ROWS = 8;
export const EMPTY = null;
export const COLORS = { WHITE: 'w', BLACK: 'b' };

export function createInitialBoard() { ... }
export function getLegalMoves(board, color) { ... }
export function applyMove(board, from, to) { ... }
export function isValidMove(board, from, to, color) { ... }
export function getPieceAt(board, pos) { ... }
export function algebraic(pos) { ... }