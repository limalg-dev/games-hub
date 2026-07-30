import { DIRS_4, DIRS_8 } from './words.js';

export function createGrid(config) {
  const { gridSize, wordCount, directions, words } = config;
  const grid = Array.from({ length: gridSize }, () => Array(gridSize).fill(''));
  const directionsList = directions === 4 ? DIRS_4 : DIRS_8;
  const placedWords = [];

  for (const word of words) {
    let placed = false;
    let attempts = 0;
    const maxAttempts = 100;

    while (!placed && attempts < maxAttempts) {
      const dir = directionsList[Math.floor(Math.random() * directionsList.length)];
      const [dr, dc] = dir;
      const len = word.length;

      const maxRow = dr === 1 ? gridSize - len : dr === -1 ? len - 1 : gridSize - 1;
      const minRow = dr === 1 ? len - 1 : dr === -1 ? 0 : 0;
      const maxCol = dc === 1 ? gridSize - len : dc === -1 ? len - 1 : gridSize - 1;
      const minCol = dc === 1 ? len - 1 : dc === -1 ? 0 : 0;

      const r = Math.floor(Math.random() * (maxRow - minRow + 1)) + minRow;
      const c = Math.floor(Math.random() * (maxCol - minCol + 1)) + minCol;

      let canPlace = true;
      for (let i = 0; i < len; i++) {
        const nr = r + dr * i;
        const nc = c + dc * i;
        if (grid[nr][nc] !== '' && grid[nr][nc] !== word[i]) {
          canPlace = false;
          break;
        }
      }

      if (canPlace) {
        for (let i = 0; i < len; i++) {
          const nr = r + dr * i;
          const nc = c + dc * i;
          grid[nr][nc] = word[i];
        }
        placedWords.push({ word, row: r, col: c, dr, dc });
        placed = true;
      }
      attempts++;
    }

    if (!placed) {
      console.warn(`Could not place word: ${word}`);
    }
  }

  // Fill empty cells with random letters
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {
      if (grid[r][c] === '') {
        grid[r][c] = letters[Math.floor(Math.random() * letters.length)];
      }
    }
  }

  return { grid, placedWords };
}

export function getWordAt(grid, r, c, dr, dc, length) {
  let word = '';
  for (let i = 0; i < length; i++) {
    const nr = r + dr * i;
    const nc = c + dc * i;
    if (nr < 0 || nr >= grid.length || nc < 0 || nc >= grid[0].length) {
      return null;
    }
    word += grid[nr][nc];
  }
  return word;
}

export function checkWordFound(grid, word, placedWords) {
  for (const placed of placedWords) {
    if (placed.word === word && !placed.found) {
      const { row, col, dr, dc, word: w } = placed;
      const foundWord = getWordAt(grid, row, col, dr, dc, w.length);
      if (foundWord === word) {
        placed.found = true;
        return true;
      }
    }
  }
  return false;
}

export function getAllWords(grid, placedWords) {
  return placedWords.map(p => p.word);
}