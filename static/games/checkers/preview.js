// static/games/checkers/preview.js
import { createInitialBoard } from './logic.js';
import { drawBoard } from './board.js';

export function renderPreview(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const board = createInitialBoard();
  // Show a mid-game position for visual interest
  board[3][3] = { color: 'w', king: false };
  board[4][4] = { color: 'b', king: true };
  drawBoard(ctx, board);
}