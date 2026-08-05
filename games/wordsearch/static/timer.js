import { CATEGORIES } from './words.js';

let startTime = null;
let timerInterval = null;
let elapsedTime = 0;

export function startTimer(onTick) {
  // O módulo é global e sobrevive a um "New Game": sem limpar o intervalo
  // anterior, cada partida nova deixava mais um setInterval vivo.
  stopTimer();
  startTime = Date.now() - elapsedTime;
  timerInterval = setInterval(() => {
    elapsedTime = Date.now() - startTime;
    if (onTick) onTick(Math.floor(elapsedTime / 1000));
  }, 1000);
}

export function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

export function getTime() {
  if (startTime) {
    return Math.floor((Date.now() - startTime) / 1000);
  }
  return Math.floor(elapsedTime / 1000);
}

export function resetTimer() {
  stopTimer();
  startTime = null;
  elapsedTime = 0;
}

function getStorageKey(difficulty) {
  return `wordsearch_leaderboard_${difficulty}`;
}

export function saveScore(config, time) {
  const key = getStorageKey(config.difficulty);
  const leaderboard = JSON.parse(localStorage.getItem(key) || '[]');
  
  const entry = {
    time,
    category: config.category,
    date: new Date().toISOString()
  };
  
  leaderboard.push(entry);
  leaderboard.sort((a, b) => a.time - b.time);
  
  const top10 = leaderboard.slice(0, 10);
  localStorage.setItem(key, JSON.stringify(top10));
}

export function getLeaderboard(difficulty) {
  const key = getStorageKey(difficulty);
  return JSON.parse(localStorage.getItem(key) || '[]');
}

export function getStorageKeyForExport(difficulty) {
  return getStorageKey(difficulty);
}

export function renderLeaderboard(containerId, difficulty) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const leaderboard = getLeaderboard(difficulty);
  
  if (leaderboard.length === 0) {
    container.innerHTML = '<p class="no-scores">Nenhum recorde ainda. Jogue para aparecer aqui!</p>';
    return;
  }

  const rows = leaderboard.map((entry, index) => `
    <tr>
      <td>${index + 1}º</td>
      <td>${formatTime(entry.time)}</td>
      <td>${CATEGORIES[entry.category]?.name || entry.category}</td>
      <td>${new Date(entry.date).toLocaleDateString()}</td>
    </tr>
  `).join('');

  container.innerHTML = `
    <table class="leaderboard">
      <thead>
        <tr><th>Pos</th><th>Tempo</th><th>Categoria</th><th>Data</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}