const boardEl = document.getElementById('board');
const statusEl = document.getElementById('status');
const newGameBtn = document.getElementById('new-game');
const gameId = location.pathname.match(/\/game\/([^/]+)/)?.[1];
let ws;
let boardData = [];
let selected = null;
let highlights = [];
let myColor = null;

if (gameId) {
  connect(gameId);
} else {
  statusEl.textContent = 'Click "New Game" to start.';
  newGameBtn.style.display = 'inline-block';
}

newGameBtn.addEventListener('click', async () => {
  const resp = await fetch('/games', { method: 'POST' });
  const { id } = await resp.json();
  history.pushState(null, '', `/game/${id}`);
  connect(id);
  newGameBtn.style.display = 'none';
});

function connect(gid) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/${gid}`);
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === 'board') {
      boardData = msg.board;
      render();
    } else if (msg.type === 'game_over') {
      statusEl.textContent = msg.winner === 'w' ? 'White wins!' : 'Black wins!';
      ws.close();
      newGameBtn.style.display = 'inline-block';
    } else if (msg.type === 'error') {
      statusEl.textContent = msg.message;
    }
  };
  ws.onopen = () => statusEl.textContent = 'Connected. Make a move.';
  ws.onclose = () => {
    if (statusEl.textContent === 'Connected. Make a move.') {
      statusEl.textContent = 'Disconnected.';
    }
  };
}

function render() {
  boardEl.innerHTML = '';
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const cell = document.createElement('div');
      cell.className = `cell ${(r + c) % 2 === 0 ? 'light' : 'dark'}`;
      cell.dataset.row = r;
      cell.dataset.col = c;
      const piece = boardData[r]?.[c];
      if (piece) {
        const div = document.createElement('div');
        div.className = `piece ${piece.toLowerCase() === 'w' ? 'white' : 'black'}`;
        if (piece === piece.toUpperCase()) div.classList.add('king');
        cell.appendChild(div);
      }
      if (selected && selected[0] === r && selected[1] === c) cell.classList.add('selected');
      if (highlights.some(h => h[0] === r && h[1] === c)) cell.classList.add('highlight');
      cell.addEventListener('click', () => cellClick(r, c));
      boardEl.appendChild(cell);
    }
  }
}

function cellClick(r, c) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  if (!selected && boardData[r]?.[c] && boardData[r][c].toLowerCase() === myColor) {
    selected = [r, c];
    // compute legal moves for this piece
    const moves = legalMovesFor(r, c);
    highlights = moves.map(m => m.to);
    render();
    return;
  }
  if (selected) {
    const fr = selected;
    const to = [r, c];
    ws.send(JSON.stringify({ type: 'move', from: fr, to: to }));
    selected = null;
    highlights = [];
    render();
  }
}

function legalMovesFor(r, c) {
  // simplified: just return immediate captures and moves based on delta
  const piece = boardData[r][c];
  if (!piece) return [];
  const color = piece.toLowerCase();
  const dirs = color === 'w' ? [[-1,-1],[-1,1]] : [[1,-1],[1,1]];
  if (piece === piece.toUpperCase()) dirs.push(...(color === 'w' ? [[1,-1],[1,1]] : [[-1,-1],[-1,1]]));
  const moves = [];
  for (const [dr, dc] of dirs) {
    const nr = r+dr, nc = c+dc;
    if (nr < 0 || nr > 7 || nc < 0 || nc > 7) continue;
    if (!boardData[nr][nc]) moves.push({ from: [r,c], to: [nr,nc] });
    const cr = r+2*dr, cc = c+2*dc;
    if (cr < 0 || cr > 7 || cc < 0 || cc > 7) continue;
    const mid = boardData[nr][nc];
    if (mid && mid.toLowerCase() !== color && !boardData[cr][cc]) {
      moves.push({ from: [r,c], to: [cr,cc] });
    }
  }
  return moves;
}
