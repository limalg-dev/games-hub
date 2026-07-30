import { CATEGORIES, DIFFICULTIES, getRandomCategory } from './words.js';
import { createGrid, getAllWords } from './logic.js';

export function renderPreview(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const size = Math.min(canvas.width, canvas.height);
  const cellSize = size / 10;

  const category = getRandomCategory();
  const words = CATEGORIES[category].words.slice(0, 6);
  
  const { grid } = createGrid({
    gridSize: 10,
    wordCount: 6,
    directions: 4,
    words
  });

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = `${cellSize * 0.8}px Arial`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  for (let r = 0; r < 10; r++) {
    for (let c = 0; c < 10; c++) {
      const x = c * cellSize + cellSize / 2;
      const y = r * cellSize + cellSize / 2;
      ctx.fillStyle = '#f0f0f0';
      ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
      ctx.strokeStyle = '#ddd';
      ctx.strokeRect(c * cellSize, r * cellSize, cellSize, cellSize);
      ctx.fillStyle = '#333';
      ctx.fillText(grid[r][c], x, y);
    }
  }
}

export function renderPreviewGrid(config, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const words = Object.values(CATEGORIES[config.category]?.words || CATEGORIES.animals.words).slice(0, config.wordCount);
  
  const { grid } = createGrid({
    gridSize: config.gridSize,
    wordCount: config.wordCount,
    directions: config.directions,
    words
  });

  container.innerHTML = '';
  const table = document.createElement('table');
  table.className = 'wordsearch-preview';
  
  for (let r = 0; r < config.gridSize; r++) {
    const tr = document.createElement('tr');
    for (let c = 0; c < config.gridSize; c++) {
      const td = document.createElement('td');
      td.textContent = grid[r][c];
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
  
  container.appendChild(table);
}

export function getPreviewWords(config) {
  return Object.values(CATEGORIES[config.category]?.words || CATEGORIES.animals.words).slice(0, config.wordCount);
}