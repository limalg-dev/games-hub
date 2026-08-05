export function inBounds(r, c, size) {
  return r >= 0 && r < size && c >= 0 && c < size;
}

export function buildPlayableMap(size, filled) {
  return filled.map(row => row.map(v => !v));
}

export function wordStart(row, col, direction, playable) {
  const size = playable.length;
  const dr = direction === 'down' ? -1 : 0;
  const dc = direction === 'down' ? 0 : -1;
  let r = row, c = col;
  while (inBounds(r + dr, c + dc, size) && playable[r + dr][c + dc]) {
    r += dr;
    c += dc;
  }
  return { row: r, col: c };
}

export function wordCells(row, col, direction, playable) {
  const size = playable.length;
  const start = wordStart(row, col, direction, playable);
  const cells = [];
  let r = start.row, c = start.col;
  while (inBounds(r, c, size) && playable[r][c]) {
    cells.push({ row: r, col: c });
    r += direction === 'down' ? 1 : 0;
    c += direction === 'down' ? 0 : 1;
  }
  return cells;
}

export function nextCell(row, col, direction, playable) {
  const cells = wordCells(row, col, direction, playable);
  for (let i = 0; i < cells.length - 1; i++) {
    if (cells[i].row === row && cells[i].col === col) return cells[i + 1];
  }
  return null;
}

export function nextWord(row, col, direction, playable, numGrid) {
  const size = playable.length;
  const last = prevCell(row, col, direction, playable);
  const after = last ? nextCell(last.row, last.col, direction, playable) : null;
  const cell = (after && inBounds(after.row, after.col, size)) ? after : { row, col };
  return wordStart(cell.row, cell.col, direction, playable);
}

export function prevCell(row, col, direction, playable) {
  const cells = wordCells(row, col, direction, playable);
  for (let i = 1; i < cells.length; i++) {
    if (cells[i].row === row && cells[i].col === col) return cells[i - 1];
  }
  return null;
}

export function firstPlayable(playable) {
  for (let r = 0; r < playable.length; r++) {
    for (let c = 0; c < playable.length; c++) {
      if (playable[r][c]) return { row: r, col: c };
    }
  }
  return null;
}