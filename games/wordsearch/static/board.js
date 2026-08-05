import { createGrid, checkWordFound, getAllWords } from './logic.js';
import { getWordsForCategory } from './words.js';
import { startTimer, stopTimer, getTime, saveScore, getLeaderboard, renderLeaderboard } from './timer.js';

export class WordSearchGame {
  constructor(config) {
    this.config = config;
    this.grid = null;
    this.placedWords = [];
    this.foundWords = new Set();
    this.selectedCells = [];
    this.startTime = null;
    this.timerInterval = null;
    this.isPlaying = false;
    this.container = document.getElementById(config.containerId);
    this.onWordFound = config.onWordFound || (() => {});
    this.onGameComplete = config.onGameComplete || (() => {});
    this.onTimerUpdate = config.onTimerUpdate || (() => {});
  }

  init() {
    const words = getWordsForCategory(this.config.category, this.config.wordCount);
    const { grid, placedWords } = createGrid({
      gridSize: this.config.gridSize,
      wordCount: this.config.wordCount,
      directions: this.config.directions,
      words
    });
    this.grid = grid;
    this.placedWords = placedWords;
    this.foundWords.clear();
    this.selectedCells = [];
    // Laid out but not live: start() opens play and the clock, so a Play gate
    // can sit in between.
    this.isPlaying = false;
    this.render();
  }

  start() {
    this.isPlaying = true;
    this.startTime = Date.now();
    this.timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
      this.onTimerUpdate(elapsed);
    }, 1000);
  }

  selectCell(row, col) {
    if (!this.isPlaying) return;

    const cell = { row, col };
    
    if (this.selectedCells.length === 0) {
      this.selectedCells = [cell];
      this.highlightCell(row, col);
      return;
    }

    const first = this.selectedCells[0];
    const last = this.selectedCells[this.selectedCells.length - 1];

    if (this.selectedCells.length === 1) {
      const dr = row - first.row;
      const dc = col - first.col;
      const dist = Math.max(Math.abs(dr), Math.abs(dc));
      
      if (dist === 0) return;
      
      const stepR = dr === 0 ? 0 : dr > 0 ? 1 : -1;
      const stepC = dc === 0 ? 0 : dc > 0 ? 1 : -1;
      
      if (Math.abs(dr) !== dist && Math.abs(dc) !== dist && Math.abs(dr) !== Math.abs(dc)) {
        return;
      }

      this.selectedCells = [];
      for (let i = 0; i <= dist; i++) {
        this.selectedCells.push({ row: first.row + stepR * i, col: first.col + stepC * i });
        this.highlightCell(first.row + stepR * i, first.col + stepC * i);
      }
    } else {
      const dr = last.row - first.row;
      const dc = last.col - first.col;
      const stepR = dr === 0 ? 0 : dr > 0 ? 1 : -1;
      const stepC = dc === 0 ? 0 : dc > 0 ? 1 : -1;
      const expectedR = last.row + stepR;
      const expectedC = last.col + stepC;

      if (row === expectedR && col === expectedC) {
        this.selectedCells.push(cell);
        this.highlightCell(row, col);
      }
    }
  }

  highlightCell(row, col) {
    const cell = this.container.querySelector(`[data-row="${row}"][data-col="${col}"]`);
    if (cell) cell.classList.add('selected');
  }

  clearSelection() {
    this.container.querySelectorAll('.selected').forEach(c => c.classList.remove('selected'));
    this.selectedCells = [];
  }

  checkWord() {
    if (this.selectedCells.length < 2) {
      this.clearSelection();
      return false;
    }

    const first = this.selectedCells[0];
    const last = this.selectedCells[this.selectedCells.length - 1];
    const dr = last.row - first.row;
    const dc = last.col - first.col;
    const stepR = dr === 0 ? 0 : dr > 0 ? 1 : -1;
    const stepC = dc === 0 ? 0 : dc > 0 ? 1 : -1;
    const length = Math.max(Math.abs(dr), Math.abs(dc)) + 1;

    let word = '';
    for (let i = 0; i < length; i++) {
      const r = first.row + stepR * i;
      const c = first.col + stepC * i;
      word += this.grid[r][c];
    }

    const reversed = word.split('').reverse().join('');
    const found = checkWordFound(this.grid, word, this.placedWords) || 
                  checkWordFound(this.grid, reversed, this.placedWords);

    if (found) {
      const foundWord = this.placedWords.find(p => p.word === word || p.word === reversed);
      if (foundWord) {
        foundWord.found = true;
        this.foundWords.add(foundWord.word);
        this.onWordFound(foundWord.word);
        this.highlightFoundWord(foundWord);
        
        if (this.foundWords.size === this.placedWords.length) {
          this.completeGame();
        }
      }
    } else {
      this.clearSelection();
    }

    return found;
  }

  highlightFoundWord(wordObj) {
    const { row, col, dr, dc, word } = wordObj;
    for (let i = 0; i < word.length; i++) {
      const r = row + dr * i;
      const c = col + dc * i;
      const cell = this.container.querySelector(`[data-row="${r}"][data-col="${c}"]`);
      if (cell) {
        cell.classList.remove('selected');
        cell.classList.add('found');
      }
    }
    this.clearSelection();
  }

  completeGame() {
    this.isPlaying = false;
    clearInterval(this.timerInterval);
    const time = Math.floor((Date.now() - this.startTime) / 1000);
    const config = this.config;
    saveScore({ difficulty: config.difficulty, category: config.category }, time);
    this.onGameComplete(time, config.difficulty);
  }

  getState() {
    return {
      grid: this.grid,
      placedWords: this.placedWords,
      foundWords: Array.from(this.foundWords),
      time: this.startTime ? Math.floor((Date.now() - this.startTime) / 1000) : 0,
      isPlaying: this.isPlaying
    };
  }

  render() {
    if (!this.container) return;
    
    this.container.innerHTML = '';
    const table = document.createElement('table');
    table.className = 'wordsearch-grid';
    
    for (let r = 0; r < this.config.gridSize; r++) {
      const tr = document.createElement('tr');
      for (let c = 0; c < this.config.gridSize; c++) {
        const td = document.createElement('td');
        td.textContent = this.grid[r][c];
        td.dataset.row = r;
        td.dataset.col = c;
        td.addEventListener('click', () => this.selectCell(r, c));
        tr.appendChild(td);
      }
      table.appendChild(tr);
    }
    
    this.container.appendChild(table);
    
    const wordList = document.createElement('div');
    wordList.className = 'word-list';
    wordList.innerHTML = '<h3>Palavras:</h3><ul>' + 
      this.placedWords.map(p => `<li data-word="${p.word}"${p.found ? ' class="found"' : ''}>${p.word}</li>`).join('') +
      '</ul>';
    this.container.appendChild(wordList);
  }

  destroy() {
    this.isPlaying = false;
    clearInterval(this.timerInterval);
    this.container.innerHTML = '';
  }

  useHint() {
    if (!this.isPlaying) return;
    const unfound = this.placedWords.filter(p => !p.found);
    if (unfound.length === 0) return;
    const hint = unfound[Math.floor(Math.random() * unfound.length)];
    this.highlightFoundWord(hint);
    hint.found = true;
    this.foundWords.add(hint.word);
    this.onWordFound(hint.word);
    if (this.foundWords.size === this.placedWords.length) {
      this.completeGame();
    }
  }
}