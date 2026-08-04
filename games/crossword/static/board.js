import { buildPlayableMap, wordStart, wordCells, nextCell, prevCell, nextWord, firstPlayable, inBounds } from './logic.js';

export class CrosswordGame {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.size = 0;
    this.playable = [];
    this.numGrid = [];
    this.values = [];
    this.direction = 'across';
    this.current = null;
    this.correct = 0;
    this.total = 0;
    this.isComplete = false;
    this.ws = null;
    this.myColor = null;
    this.onGameComplete = null;
    this.onLetterRejected = null;
    this._cells = [];
    this.startTime = null;
    this.timerInterval = null;
  }

  init(msg) {
    this.size = msg.size;
    this.numGrid = msg.num_grid;
    this.playable = buildPlayableMap(this.size, msg.filled);
    this.values = Array.from({ length: this.size }, () => Array(this.size).fill(''));
    this._cells = Array.from({ length: this.size }, () => Array(this.size).fill(null));
    this.correct = 0;
    this.total = 0;
    for (let r = 0; r < this.size; r++) {
      for (let c = 0; c < this.size; c++) {
        if (this.playable[r][c]) this.total++;
      }
    }
    this.render();
    this.renderClues(msg.across_clues, msg.down_clues);
    const first = firstPlayable(this.playable);
    this.focusCell(first.row, first.col);
    this.startTimer();
  }

  startTimer() {
    this.startTime = Date.now();
    const timerEl = document.getElementById('timer');
    if (timerEl) timerEl.classList.remove('hidden');
    if (this.timerInterval) clearInterval(this.timerInterval);
    this.timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
      const el = document.getElementById('timer');
      if (el) el.textContent = formatTime(elapsed);
    }, 1000);
  }

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  render() {
    if (!this.container) return;
    this.container.innerHTML = '';

    const table = document.createElement('table');
    table.className = 'crossword-grid';

    for (let r = 0; r < this.size; r++) {
      const tr = document.createElement('tr');
      for (let c = 0; c < this.size; c++) {
        if (!this.playable[r][c]) {
          const td = document.createElement('td');
          td.className = 'black';
          tr.appendChild(td);
          continue;
        }
        const td = document.createElement('td');
        td.className = 'white';
        const num = this.numGrid[r][c];
        if (num) {
          const numEl = document.createElement('span');
          numEl.className = 'cell-number';
          numEl.textContent = num;
          td.appendChild(numEl);
        }
        const input = document.createElement('input');
        input.type = 'text';
        input.maxLength = 1;
        input.autocomplete = 'off';
        input.dataset.row = r;
        input.dataset.col = c;
        input.addEventListener('focus', () => this.focusCell(r, c, false));
        input.addEventListener('input', () => {
          const val = input.value.toUpperCase().replace(/[^A-Z]/g, '');
          input.value = val;
          if (val) this.placeLetter(r, c, val);
        });
        input.addEventListener('keydown', (e) => this.handleKey(r, c, e));
        td.appendChild(input);
        tr.appendChild(td);
        this._cells[r][c] = input;
      }
      table.appendChild(tr);
    }
    this.container.appendChild(table);
  }

  renderClues(across, down) {
    const acrossList = document.getElementById('cw-across-list');
    const downList = document.getElementById('cw-down-list');
    if (acrossList) {
      acrossList.innerHTML = across.map(clue =>
        `<li class="clue" data-row="${clue.row}" data-col="${clue.col}" data-direction="across">
          <span class="clue-number">${clue.number}</span>
          <span class="clue-text">${clue.clue}</span>
        </li>`
      ).join('');
      acrossList.querySelectorAll('.clue').forEach(el => {
        el.addEventListener('click', () => {
          this.direction = 'across';
          this.focusCell(parseInt(el.dataset.row), parseInt(el.dataset.col));
        });
      });
    }
    if (downList) {
      downList.innerHTML = down.map(clue =>
        `<li class="clue" data-row="${clue.row}" data-col="${clue.col}" data-direction="down">
          <span class="clue-number">${clue.number}</span>
          <span class="clue-text">${clue.clue}</span>
        </li>`
      ).join('');
      downList.querySelectorAll('.clue').forEach(el => {
        el.addEventListener('click', () => {
          this.direction = 'down';
          this.focusCell(parseInt(el.dataset.row), parseInt(el.dataset.col));
        });
      });
    }
  }

  focusCell(row, col, followDirection = true) {
    if (!inBounds(row, col, this.size) || !this.playable[row][col]) return;
    this.current = { row, col };
    const input = this._cells[row]?.[col];
    if (!input) return;
    input.focus();
    if (input.value) input.select();
    this.highlightWord(row, col);
  }

  highlightWord(row, col) {
    if (!this.playable) return;
    const cells = wordCells(row, col, this.direction, this.playable);
    this.container.querySelectorAll('.active').forEach(c => c.classList.remove('active'));
    this.container.querySelectorAll('.highlighted').forEach(c => c.classList.remove('highlighted'));
    for (const cell of cells) {
      const input = this._cells[cell.row]?.[cell.col];
      if (input) input.closest('td').classList.add('highlighted');
    }
    this.highlightClue(row, col);
  }

  highlightClue(row, col) {
    const cells = wordCells(row, col, this.direction, this.playable);
    const start = wordStart(row, col, this.direction, this.playable);
    const num = this.numGrid[start.row][start.col];
    const listId = this.direction === 'across' ? 'cw-across-list' : 'cw-down-list';
    const list = document.getElementById(listId);
    if (!list) return;
    list.querySelectorAll('.clue.active').forEach(c => c.classList.remove('active'));
    if (!num) return;
    const el = list.querySelector(`.clue[data-row="${start.row}"][data-col="${start.col}"]`);
    if (el) el.classList.add('active');
    void cells;
  }

  handleKey(row, col, e) {
    if (e.key === 'Backspace') {
      e.preventDefault();
      const prev = prevCell(row, col, this.direction, this.playable);
      if (prev) this.focusCell(prev.row, prev.col);
      return;
    }
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      this.direction = 'across';
      const next = nextCell(row, col, 'across', this.playable);
      this.focusCell(next ? next.row : row, next ? next.col : col);
      return;
    }
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      this.direction = 'across';
      const prev = prevCell(row, col, 'across', this.playable);
      this.focusCell(prev ? prev.row : row, prev ? prev.col : col);
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.direction = 'down';
      const next = nextCell(row, col, 'down', this.playable);
      this.focusCell(next ? next.row : row, next ? next.col : col);
      return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.direction = 'down';
      const prev = prevCell(row, col, 'down', this.playable);
      this.focusCell(prev ? prev.row : row, prev ? prev.col : col);
      return;
    }
    if (/^[a-zA-Z]$/.test(e.key)) {
      e.preventDefault();
      this.placeLetter(row, col, e.key.toUpperCase());
    }
  }

  placeLetter(row, col, letter) {
    if (this.isComplete || !this.ws) return;
    this.ws.send(JSON.stringify({ type: 'move', row, col, letter }));
  }

  handleMessage(msg) {
    if (msg.type === 'crossword_update') {
      this.updateCell(msg.row, msg.col, msg.letter);
    } else if (msg.type === 'error') {
      this.rejectLetter(msg.row, msg.col, msg.message);
    } else if (msg.type === 'game_over') {
      this.completeGame();
    }
  }

  updateCell(row, col, letter) {
    if (!inBounds(row, col, this.size)) return;
    const input = this._cells[row]?.[col];
    if (!input) return;
    input.value = letter;
    this.values[row][col] = letter;
    this.correct++;
    input.closest('td').classList.add('filled');
    this.advance(row, col);
    if (this.correct >= this.total) {
      this.completeGame();
    }
  }

  advance(row, col) {
    const next = nextCell(row, col, this.direction, this.playable);
    if (next) {
      this.focusCell(next.row, next.col);
    } else {
      const start = nextWord(row, col, this.direction, this.playable, this.numGrid);
      this.focusCell(start.row, start.col);
    }
  }

  rejectLetter(row, col) {
    const input = this._cells[row]?.[col];
    if (!input) return;
    const td = input.closest('td');
    td.classList.add('wrong');
    setTimeout(() => td.classList.remove('wrong'), 400);
    input.value = '';
    if (this.onLetterRejected) this.onLetterRejected();
  }

  completeGame() {
    if (this.isComplete) return;
    this.isComplete = true;
    this.stopTimer();
    this.current = null;
    if (this.onGameComplete) this.onGameComplete();
  }

  destroy() {
    this.stopTimer();
    this.isComplete = true;
    if (this.container) this.container.innerHTML = '';
  }
}

function formatTime(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}