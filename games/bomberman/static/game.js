// games/bomberman/static/game.js
// Super Bomberman Game Engine - GameHub
import { sound } from './audio.js';

const COLS = 15;
const ROWS = 13;
const TILE = 48; // Canvas size: 720 x 624

// Grid cell codes
const EMPTY = 0;
const WALL = 1;
const CRATE = 2;
const EXIT = 3;

// Powerup codes
const PWR_NONE = 0;
const PWR_BOMB = 1;
const PWR_FIRE = 2;
const PWR_SPEED = 3;
const PWR_KICK = 4;
const PWR_SHIELD = 5;
const PWR_REMOTE = 6;

const COLORS = {
  white:  { body: '#ffffff', suit: '#3498db', head: '#f1c40f', hat: '#ffffff', skin: '#f5cd79' },
  black:  { body: '#2c3e50', suit: '#e74c3c', head: '#e67e22', hat: '#1a1a1a', skin: '#f5cd79' },
  red:    { body: '#e74c3c', suit: '#ffffff', head: '#f39c12', hat: '#c0392b', skin: '#f5cd79' },
  blue:   { body: '#2980b9', suit: '#ffffff', head: '#27ae60', hat: '#1f618d', skin: '#f5cd79' },
  yellow: { body: '#f1c40f', suit: '#2c3e50', head: '#e67e22', hat: '#d4ac0d', skin: '#f5cd79' },
};

class Particle {
  constructor(x, y, color, vx, vy, size, life) {
    this.x = x;
    this.y = y;
    this.color = color;
    this.vx = vx;
    this.vy = vy;
    this.size = size;
    this.maxLife = life;
    this.life = life;
  }
  update(dt) {
    this.x += this.vx * dt * 60;
    this.y += this.vy * dt * 60;
    this.life -= dt;
    return this.life > 0;
  }
  draw(ctx) {
    const alpha = Math.max(0, this.life / this.maxLife);
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = this.color;
    ctx.fillRect(this.x - this.size / 2, this.y - this.size / 2, this.size, this.size);
    ctx.restore();
  }
}

class FloatingText {
  constructor(x, y, text, color = '#ffd700') {
    this.x = x;
    this.y = y;
    this.text = text;
    this.color = color;
    this.life = 1.2;
  }
  update(dt) {
    this.y -= 25 * dt;
    this.life -= dt;
    return this.life > 0;
  }
  draw(ctx) {
    ctx.save();
    ctx.globalAlpha = Math.max(0, this.life);
    ctx.fillStyle = this.color;
    ctx.font = 'bold 16px "SF Mono", monospace';
    ctx.textAlign = 'center';
    ctx.shadowColor = '#000';
    ctx.shadowBlur = 4;
    ctx.fillText(this.text, this.x, this.y);
    ctx.restore();
  }
}

class Sparkle {
  constructor(x, y, color, angle, speed, size, life) {
    this.x = x;
    this.y = y;
    this.color = color;
    this.vx = Math.cos(angle) * speed;
    this.vy = Math.sin(angle) * speed;
    this.size = size;
    this.maxLife = life;
    this.life = life;
    this.rotation = Math.random() * Math.PI * 2;
    this.rotSpeed = (Math.random() - 0.5) * 8;
  }
  update(dt) {
    this.x += this.vx * dt * 60;
    this.y += this.vy * dt * 60;
    this.vx *= 0.96;
    this.vy *= 0.96;
    this.rotation += this.rotSpeed * dt;
    this.life -= dt;
    return this.life > 0;
  }
  draw(ctx) {
    const t = 1 - (this.life / this.maxLife);
    const alpha = Math.max(0, 1 - t * t);
    const s = this.size * (1 - t * 0.5);
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate(this.rotation);
    ctx.globalAlpha = alpha;
    ctx.fillStyle = this.color;
    // Draw a 4-pointed star
    ctx.beginPath();
    for (let i = 0; i < 8; i++) {
      const a = (i * Math.PI) / 4;
      const r = i % 2 === 0 ? s : s * 0.4;
      ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r);
    }
    ctx.closePath();
    ctx.fill();
    // Bright center glow
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.beginPath();
    ctx.arc(0, 0, s * 0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

export class BombermanGame {
  constructor() {
    this.canvas = document.getElementById('gameCanvas');
    this.ctx = this.canvas.getContext('2d');
    this.canvas.width = COLS * TILE;
    this.canvas.height = ROWS * TILE;

    this.mode = 'battle'; // 'battle' or 'arcade'
    this.difficulty = 'medium'; // 'easy', 'medium', 'hard'
    this.stage = 1;
    this.maxStages = 5;

    this.grid = [];
    this.powerupMap = [];
    this.exitPos = null;
    this.exitRevealed = false;

    this.players = [];
    this.monsters = [];
    this.bombs = [];
    this.flames = [];
    this.particles = [];
    this.floatingTexts = [];
    this.sparkles = [];

    this.timer = 120;
    this.state = 'start'; // 'start', 'playing', 'paused', 'game_over', 'stage_clear', 'match_win', 'round_over'
    this.lastTime = 0;
    this.suddenDeathStarted = false;
    this.suddenDeathIndex = 0;
    this.suddenDeathTimer = 0;

    // Screen shake
    this.shake = { x: 0, y: 0, intensity: 0, duration: 0 };

    this.keys = {};
    this.touchInput = { up: false, down: false, left: false, right: false, bomb: false, remote: false };

    this.score = 0;
    this.roundWins = [0, 0, 0, 0]; // Wins per player slot

    // Pre-generate background arena
    this.generateArena();
    this.spawnEntities();

    this.setupListeners();
    this.initUI();
    this.loadHighscores();
    this.startLoop();
  }

  setupListeners() {
    window.addEventListener('keydown', (e) => {
      sound.init();
      this.keys[e.code] = true;

      if (e.code === 'KeyP' || e.code === 'Escape') {
        this.togglePause();
      }
      if (e.code === 'Space' || e.code === 'KeyJ') {
        if (this.state === 'playing' && this.players[0] && this.players[0].alive) {
          this.dropBomb(this.players[0]);
        }
      }
      if (e.code === 'KeyE' || e.code === 'KeyK') {
        if (this.state === 'playing' && this.players[0] && this.players[0].hasRemote) {
          this.detonateRemote(this.players[0]);
        }
      }
      if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) {
        e.preventDefault();
      }
    });

    window.addEventListener('keyup', (e) => {
      this.keys[e.code] = false;
    });

    // Touch controls
    const bindTouch = (id, key) => {
      const el = document.getElementById(id);
      if (!el) return;
      const start = (ev) => { ev.preventDefault(); sound.init(); this.touchInput[key] = true; };
      const end = (ev) => { ev.preventDefault(); this.touchInput[key] = false; };
      el.addEventListener('touchstart', start, { passive: false });
      el.addEventListener('touchend', end, { passive: false });
      el.addEventListener('mousedown', start);
      el.addEventListener('mouseup', end);
      el.addEventListener('mouseleave', end);
    };

    bindTouch('btnUp', 'up');
    bindTouch('btnDown', 'down');
    bindTouch('btnLeft', 'left');
    bindTouch('btnRight', 'right');

    const btnBomb = document.getElementById('btnBomb');
    if (btnBomb) {
      btnBomb.addEventListener('touchstart', (e) => {
        e.preventDefault();
        sound.init();
        if (this.state === 'playing' && this.players[0] && this.players[0].alive) {
          this.dropBomb(this.players[0]);
        }
      }, { passive: false });
      btnBomb.addEventListener('click', () => {
        if (this.state === 'playing' && this.players[0] && this.players[0].alive) {
          this.dropBomb(this.players[0]);
        }
      });
    }

    const btnRemote = document.getElementById('btnRemote');
    if (btnRemote) {
      btnRemote.addEventListener('touchstart', (e) => {
        e.preventDefault();
        sound.init();
        if (this.state === 'playing' && this.players[0] && this.players[0].hasRemote) {
          this.detonateRemote(this.players[0]);
        }
      }, { passive: false });
      btnRemote.addEventListener('click', () => {
        if (this.state === 'playing' && this.players[0] && this.players[0].hasRemote) {
          this.detonateRemote(this.players[0]);
        }
      });
    }
  }

  initUI() {
    // Mode tabs
    document.querySelectorAll('.mode-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.mode = tab.dataset.mode;
        this.updateHUDMode();
      });
    });

    // Difficulty buttons
    document.querySelectorAll('.diff-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.diff-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.difficulty = btn.dataset.diff;
      });
    });

    // Sound toggle
    const btnMute = document.getElementById('btnMute');
    if (btnMute) {
      btnMute.addEventListener('click', () => {
        const isMuted = sound.toggleMute();
        btnMute.innerHTML = isMuted ? '🔇' : '🔊';
      });
    }

    // Modal buttons
    document.getElementById('btnStartGame')?.addEventListener('click', () => {
      sound.init();
      this.hideModal('startModal');
      this.resetMatch();
    });

    document.getElementById('btnResume')?.addEventListener('click', () => {
      this.togglePause();
    });

    document.getElementById('btnRestartPause')?.addEventListener('click', () => {
      this.hideModal('pauseModal');
      this.startRound();
    });

    document.getElementById('btnNextStage')?.addEventListener('click', () => {
      this.hideModal('stageClearModal');
      this.stage++;
      if (this.stage > this.maxStages) {
        this.showMatchWin('Você completou todas as 5 fases do Modo Arcade!');
      } else {
        this.startRound();
      }
    });

    document.getElementById('btnRestartGameOver')?.addEventListener('click', () => {
      this.hideModal('gameOverModal');
      this.resetMatch();
    });

    document.getElementById('btnPlayAgainWin')?.addEventListener('click', () => {
      this.hideModal('matchWinModal');
      this.resetMatch();
    });

    document.getElementById('btnSaveScore')?.addEventListener('click', () => {
      const nameInput = document.getElementById('playerNameInput');
      const name = nameInput ? nameInput.value.trim() : 'JOGADOR';
      this.submitHighscore(name);
    });
  }

  updateHUDMode() {
    const badge = document.getElementById('modeBadge');
    if (badge) {
      badge.textContent = this.mode === 'battle' ? 'Modo Batalha' : `Arcade - Fase ${this.stage}`;
    }
  }

  showModal(id) {
    document.getElementById(id)?.classList.remove('hidden');
  }

  hideModal(id) {
    document.getElementById(id)?.classList.add('hidden');
  }

  togglePause() {
    if (this.state === 'playing') {
      this.state = 'paused';
      this.showModal('pauseModal');
    } else if (this.state === 'paused') {
      this.state = 'playing';
      this.hideModal('pauseModal');
    }
  }

  resetMatch() {
    this.roundWins = [0, 0, 0, 0];
    this.stage = 1;
    this.score = 0;
    this.updateHUDMode();
    this.startRound();
  }

  startRound() {
    this.bombs = [];
    this.flames = [];
    this.particles = [];
    this.floatingTexts = [];
    this.sparkles = [];
    this.suddenDeathStarted = false;
    this.suddenDeathIndex = 0;
    this.suddenDeathTimer = 0;
    this.exitRevealed = false;
    this.shake = { x: 0, y: 0, intensity: 0, duration: 0 };

    this.timer = this.mode === 'battle' ? 120 : (200 - this.stage * 10);
    this.generateArena();
    this.spawnEntities();
    this.state = 'playing';
    this.updateHUD();
  }

  generateArena() {
    this.grid = [];
    this.powerupMap = [];

    for (let r = 0; r < ROWS; r++) {
      this.grid[r] = [];
      this.powerupMap[r] = [];
      for (let c = 0; c < COLS; c++) {
        if (r === 0 || r === ROWS - 1 || c === 0 || c === COLS - 1) {
          this.grid[r][c] = WALL;
        } else if (r % 2 === 0 && c % 2 === 0) {
          this.grid[r][c] = WALL;
        } else {
          this.grid[r][c] = EMPTY;
        }
        this.powerupMap[r][c] = PWR_NONE;
      }
    }

    const safeTiles = new Set();
    const addSafe = (r, c) => {
      safeTiles.add(`${r},${c}`);
      safeTiles.add(`${r+1},${c}`);
      safeTiles.add(`${r-1},${c}`);
      safeTiles.add(`${r},${c+1}`);
      safeTiles.add(`${r},${c-1}`);
    };

    if (this.mode === 'battle') {
      addSafe(1, 1);
      addSafe(1, COLS - 2);
      addSafe(ROWS - 2, 1);
      addSafe(ROWS - 2, COLS - 2);
    } else {
      addSafe(1, 1);
    }

    const density = this.difficulty === 'easy' ? 0.50 : (this.difficulty === 'medium' ? 0.65 : 0.75);
    const crateList = [];

    for (let r = 1; r < ROWS - 1; r++) {
      for (let c = 1; c < COLS - 1; c++) {
        if (this.grid[r][c] === EMPTY && !safeTiles.has(`${r},${c}`)) {
          if (Math.random() < density) {
            this.grid[r][c] = CRATE;
            crateList.push({ r, c });
          }
        }
      }
    }

    const pwrPool = [PWR_BOMB, PWR_BOMB, PWR_FIRE, PWR_FIRE, PWR_SPEED, PWR_SPEED, PWR_KICK, PWR_SHIELD, PWR_REMOTE];
    crateList.sort(() => Math.random() - 0.5);

    if (this.mode === 'arcade' && crateList.length > 0) {
      this.exitPos = { ...crateList[0] };
    } else {
      this.exitPos = null;
    }

    crateList.forEach((tile, i) => {
      if (this.mode === 'arcade' && i === 0) return; // Hidden exit door
      if (Math.random() < 0.42) {
        this.powerupMap[tile.r][tile.c] = pwrPool[Math.floor(Math.random() * pwrPool.length)];
      }
    });
  }

  spawnEntities() {
    this.players = [];
    this.monsters = [];

    const p1 = {
      id: 0,
      name: 'P1',
      isBot: false,
      color: COLORS.white,
      x: 1 * TILE + TILE / 2,
      y: 1 * TILE + TILE / 2,
      speed: 3.2,
      maxBombs: 1,
      activeBombs: 0,
      fireRange: 2,
      hasKick: false,
      hasShield: false,
      hasRemote: false,
      alive: true,
      facing: 'down',
      animStep: 0,
      invulnTimer: 0,
      bombFlash: 0,
    };
    this.players.push(p1);

    if (this.mode === 'battle') {
      const spawns = [
        { r: ROWS - 2, c: COLS - 2, color: COLORS.red, name: 'Bot Vermelho' },
        { r: 1, c: COLS - 2, color: COLORS.blue, name: 'Bot Azul' },
        { r: ROWS - 2, c: 1, color: COLORS.yellow, name: 'Bot Amarelo' },
      ];

      spawns.forEach((s, idx) => {
        this.players.push({
          id: idx + 1,
          name: s.name,
          isBot: true,
          color: s.color,
          x: s.c * TILE + TILE / 2,
          y: s.r * TILE + TILE / 2,
          speed: this.difficulty === 'easy' ? 2.2 : (this.difficulty === 'medium' ? 2.8 : 3.2),
          maxBombs: 1,
          activeBombs: 0,
          fireRange: 2,
          hasKick: this.difficulty === 'hard',
          hasShield: false,
          hasRemote: false,
          alive: true,
          facing: 'down',
          animStep: 0,
          invulnTimer: 0,
          bombFlash: 0,
          botThinkTimer: Math.random() * 0.5,
          botMoveDir: null,
        });
      });
    } else {
      const count = 3 + this.stage * 2;
      let availableTiles = [];

      for (let r = 3; r < ROWS - 1; r++) {
        for (let c = 3; c < COLS - 1; c++) {
          if (this.grid[r][c] === EMPTY) {
            availableTiles.push({ r, c });
          }
        }
      }
      availableTiles.sort(() => Math.random() - 0.5);

      for (let i = 0; i < count && i < availableTiles.length; i++) {
        let type = 'ballom';
        if (this.stage >= 2 && Math.random() < 0.4) type = 'pass';
        if (this.stage >= 3 && Math.random() < 0.3) type = 'phantom';
        if (this.stage >= 4 && Math.random() < 0.4) type = 'pontan';

        const t = availableTiles[i];
        this.monsters.push({
          type,
          x: t.c * TILE + TILE / 2,
          y: t.r * TILE + TILE / 2,
          speed: type === 'pontan' ? 2.8 : (type === 'pass' ? 2.0 : 1.4),
          alive: true,
          dir: ['up', 'down', 'left', 'right'][Math.floor(Math.random() * 4)],
          changeDirTimer: Math.random() * 2,
        });
      }
    }
  }

  startLoop() {
    const loop = (timestamp) => {
      try {
        if (!this.lastTime) this.lastTime = timestamp;
        const dt = Math.min((timestamp - this.lastTime) / 1000, 0.1);
        this.lastTime = timestamp;

        this.update(dt);
        this.render();
      } catch (err) {
        console.error('Game loop error:', err);
      }
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  update(dt) {
    if (this.state !== 'playing') return;

    this.timer -= dt;
    if (this.timer <= 0) {
      if (this.mode === 'battle' && !this.suddenDeathStarted) {
        this.suddenDeathStarted = true;
        sound.playWarning();
        this.floatingTexts.push(new FloatingText(this.canvas.width / 2, 100, 'MORTE SÚBITA!', '#ff4444'));
      } else if (this.mode === 'arcade') {
        this.playerDied(this.players[0]);
      }
    }

    if (this.suddenDeathStarted) {
      this.updateSuddenDeath(dt);
    }

    // Update screen shake
    if (this.shake.duration > 0) {
      this.shake.duration -= dt;
      const t = Math.max(0, this.shake.duration / 0.35);
      this.shake.intensity *= (0.85 + t * 0.1); // decays faster as it fades
      this.shake.x = (Math.random() * 2 - 1) * this.shake.intensity;
      this.shake.y = (Math.random() * 2 - 1) * this.shake.intensity;
    } else {
      this.shake.x = 0;
      this.shake.y = 0;
      this.shake.intensity = 0;
    }

    this.updatePlayers(dt);
    this.updateMonsters(dt);
    this.updateBombs(dt);
    this.updateFlames(dt);

    this.particles = this.particles.filter(p => p.update(dt));
    this.floatingTexts = this.floatingTexts.filter(t => t.update(dt));
    this.sparkles = this.sparkles.filter(s => s.update(dt));

    this.checkWinConditions();
    this.updateHUD();
  }

  updatePlayers(dt) {
    this.players.forEach(p => {
      if (!p.alive) return;
      if (p.invulnTimer > 0) p.invulnTimer -= dt;
      if (p.bombFlash > 0) p.bombFlash -= dt;

      if (p.isBot) {
        this.updateBot(p, dt);
      } else {
        this.updateHumanPlayer(p, dt);
      }
    });
  }

  updateHumanPlayer(p, dt) {
    let dx = 0;
    let dy = 0;

    if (this.keys['ArrowUp'] || this.keys['KeyW'] || this.touchInput.up) dy -= 1;
    if (this.keys['ArrowDown'] || this.keys['KeyS'] || this.touchInput.down) dy += 1;
    if (this.keys['ArrowLeft'] || this.keys['KeyA'] || this.touchInput.left) dx -= 1;
    if (this.keys['ArrowRight'] || this.keys['KeyD'] || this.touchInput.right) dx += 1;

    if (dx !== 0 && dy !== 0) {
      dx *= 0.7071;
      dy *= 0.7071;
    }

    if (dx !== 0 || dy !== 0) {
      p.animStep += dt * 10;
      if (Math.abs(dx) > Math.abs(dy)) {
        p.facing = dx > 0 ? 'right' : 'left';
      } else {
        p.facing = dy > 0 ? 'down' : 'up';
      }
    }

    this.moveEntity(p, dx * p.speed * 60 * dt, dy * p.speed * 60 * dt);
    this.checkPowerupPickup(p);

    if (this.mode === 'arcade' && this.exitRevealed && this.monsters.length === 0) {
      const tileR = Math.floor(p.y / TILE);
      const tileC = Math.floor(p.x / TILE);
      if (this.exitPos && tileR === this.exitPos.r && tileC === this.exitPos.c) {
        this.stageClear();
      }
    }
  }

  moveEntity(entity, vx, vy) {
    const radius = 16;
    const nextX = entity.x + vx;
    const nextY = entity.y + vy;

    // Corner slide assist
    if (vx !== 0 && vy === 0) {
      const currentTileY = Math.floor(entity.y / TILE);
      const targetCenterY = currentTileY * TILE + TILE / 2;
      const diffY = targetCenterY - entity.y;
      if (Math.abs(diffY) > 1 && Math.abs(diffY) < 14) {
        entity.y += Math.sign(diffY) * Math.min(Math.abs(diffY), 2.0);
      }
    } else if (vy !== 0 && vx === 0) {
      const currentTileX = Math.floor(entity.x / TILE);
      const targetCenterX = currentTileX * TILE + TILE / 2;
      const diffX = targetCenterX - entity.x;
      if (Math.abs(diffX) > 1 && Math.abs(diffX) < 14) {
        entity.x += Math.sign(diffX) * Math.min(Math.abs(diffX), 2.0);
      }
    }

    if (!this.checkSolidCollision(nextX, entity.y, radius, entity)) {
      entity.x = nextX;
    } else if (entity.hasKick && vx !== 0) {
      this.tryKickBomb(entity, Math.sign(vx), 0);
    }

    if (!this.checkSolidCollision(entity.x, nextY, radius, entity)) {
      entity.y = nextY;
    } else if (entity.hasKick && vy !== 0) {
      this.tryKickBomb(entity, 0, Math.sign(vy));
    }
  }

  checkSolidCollision(x, y, radius, entity) {
    const minC = Math.floor((x - radius) / TILE);
    const maxC = Math.floor((x + radius) / TILE);
    const minR = Math.floor((y - radius) / TILE);
    const maxR = Math.floor((y + radius) / TILE);

    for (let r = minR; r <= maxR; r++) {
      for (let c = minC; c <= maxC; c++) {
        if (r < 0 || r >= ROWS || c < 0 || c >= COLS) return true;
        const cell = this.grid[r][c];
        if (cell === WALL || cell === CRATE) return true;
      }
    }

    // Bomb collision: block entities from entering a tile that has a bomb,
    // but allow them to leave their own bomb tile.
    const targetR = Math.floor(y / TILE);
    const targetC = Math.floor(x / TILE);
    const currentR = Math.floor(entity.y / TILE);
    const currentC = Math.floor(entity.x / TILE);
    // Only block if moving INTO a bomb tile (not already on it)
    if (targetR !== currentR || targetC !== currentC) {
      const bomb = this.bombs.find(b => b.r === targetR && b.c === targetC);
      if (bomb) return true;
    }

    return false;
  }

  tryKickBomb(entity, dx, dy) {
    const targetC = Math.floor(entity.x / TILE) + dx;
    const targetR = Math.floor(entity.y / TILE) + dy;
    const bomb = this.bombs.find(b => b.r === targetR && b.c === targetC && !b.moving);
    if (bomb) {
      bomb.moving = true;
      bomb.dx = dx;
      bomb.dy = dy;
      sound.playKick();
    }
  }

  dropBomb(player) {
    if (!player.alive || player.activeBombs >= player.maxBombs) return;

    const r = Math.floor(player.y / TILE);
    const c = Math.floor(player.x / TILE);

    if (this.bombs.some(b => b.r === r && b.c === c)) return;

    const bomb = {
      r, c,
      x: c * TILE + TILE / 2,
      y: r * TILE + TILE / 2,
      owner: player,
      range: player.fireRange,
      timer: player.hasRemote ? 9999 : 2.5,
      moving: false,
      dx: 0, dy: 0,
      scale: 1.0,
    };

    this.bombs.push(bomb);
    player.activeBombs++;
    player.bombFlash = 0.35;
    sound.playBombDrop();
  }

  detonateRemote(player) {
    const remoteBombs = this.bombs.filter(b => b.owner === player);
    if (remoteBombs.length > 0) {
      remoteBombs.forEach(b => { b.timer = 0; });
    }
  }

  updateBombs(dt) {
    for (let i = this.bombs.length - 1; i >= 0; i--) {
      const b = this.bombs[i];
      b.timer -= dt;
      b.scale = 1.0 + 0.12 * Math.sin((2.5 - b.timer) * 10);

      if (b.moving) {
        b.x += b.dx * 8;
        b.y += b.dy * 8;
        const newR = Math.floor(b.y / TILE);
        const newC = Math.floor(b.x / TILE);

        if (this.grid[newR][newC] !== EMPTY || this.bombs.some(other => other !== b && other.r === newR && other.c === newC)) {
          b.moving = false;
          b.x = b.c * TILE + TILE / 2;
          b.y = b.r * TILE + TILE / 2;
        } else {
          b.r = newR;
          b.c = newC;
        }
      }

      if (b.timer <= 0) {
        this.explodeBomb(b);
        this.bombs.splice(i, 1);
        if (b.owner) b.owner.activeBombs = Math.max(0, b.owner.activeBombs - 1);
      }
    }
  }

  explodeBomb(bomb) {
    sound.playExplosion();
    const rays = [{ r: bomb.r, c: bomb.c, type: 'center' }];
    const dirs = [
      { dr: -1, dc: 0, type: 'up' },
      { dr: 1, dc: 0, type: 'down' },
      { dr: 0, dc: -1, type: 'left' },
      { dr: 0, dc: 1, type: 'right' },
    ];

    dirs.forEach(d => {
      for (let step = 1; step <= bomb.range; step++) {
        const nr = bomb.r + d.dr * step;
        const nc = bomb.c + d.dc * step;

        if (nr < 0 || nr >= ROWS || nc < 0 || nc >= COLS) break;
        if (this.grid[nr][nc] === WALL) break;

        rays.push({ r: nr, c: nc, type: d.type });

        if (this.grid[nr][nc] === CRATE) {
          this.destroyCrate(nr, nc);
          break;
        }
      }
    });

    this.flames.push({
      rays,
      duration: 0.45,
      maxDuration: 0.45,
    });

    for (let i = 0; i < 16; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = Math.random() * 4 + 2;
      this.particles.push(new Particle(
        bomb.c * TILE + TILE / 2,
        bomb.r * TILE + TILE / 2,
        ['#ff3838', '#ff9f1a', '#fff200'][Math.floor(Math.random() * 3)],
        Math.cos(angle) * speed,
        Math.sin(angle) * speed,
        Math.random() * 6 + 3,
        0.4
      ));
    }

    // Screen shake — intensity scales with proximity to nearest player
    const bx = bomb.c * TILE + TILE / 2;
    const by = bomb.r * TILE + TILE / 2;
    let minDist = Infinity;
    for (const p of this.players) {
      if (!p.alive) continue;
      const dx = p.x - bx;
      const dy = p.y - by;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < minDist) minDist = dist;
    }
    // Max shake at 0 tiles, fades to 0 at ~6 tiles away
    const maxShakeDist = 6 * TILE;
    if (minDist < maxShakeDist) {
      const proximity = 1 - (minDist / maxShakeDist);
      const intensity = 2 + proximity * 8; // 2px (far) → 10px (on top)
      const duration = 0.15 + proximity * 0.2; // 150ms → 350ms
      if (intensity > this.shake.intensity) {
        this.shake.intensity = intensity;
        this.shake.duration = duration;
      }
    }
  }

  destroyCrate(r, c) {
    this.grid[r][c] = EMPTY;
    this.score += 50;

    if (this.exitPos && this.exitPos.r === r && this.exitPos.c === c) {
      this.exitRevealed = true;
      sound.playDoorOpen();
      this.floatingTexts.push(new FloatingText(c * TILE + TILE / 2, r * TILE + TILE / 2, 'PORTAL ABERTO! 🚪', '#4ade80'));
    }

    for (let i = 0; i < 8; i++) {
      this.particles.push(new Particle(
        c * TILE + TILE / 2,
        r * TILE + TILE / 2,
        '#b58863',
        (Math.random() - 0.5) * 4,
        (Math.random() - 0.5) * 4,
        Math.random() * 5 + 3,
        0.5
      ));
    }
  }

  updateFlames(dt) {
    for (let i = this.flames.length - 1; i >= 0; i--) {
      const f = this.flames[i];
      f.duration -= dt;

      f.rays.forEach(ray => {
        this.players.forEach(p => {
          if (p.alive && p.invulnTimer <= 0) {
            const pr = Math.floor(p.y / TILE);
            const pc = Math.floor(p.x / TILE);
            if (pr === ray.r && pc === ray.c) {
              if (p.hasShield) {
                p.hasShield = false;
                p.invulnTimer = 1.5;
                this.floatingTexts.push(new FloatingText(p.x, p.y - 20, 'ESCUDO DESTRUIDO!', '#00f0ff'));
              } else {
                this.playerDied(p);
              }
            }
          }
        });

        for (let mIdx = this.monsters.length - 1; mIdx >= 0; mIdx--) {
          const m = this.monsters[mIdx];
          const mr = Math.floor(m.y / TILE);
          const mc = Math.floor(m.x / TILE);
          if (mr === ray.r && mc === ray.c) {
            this.killMonster(m, mIdx);
          }
        }

        this.bombs.forEach(b => {
          if (b.r === ray.r && b.c === ray.c && b.timer > 0.05) {
            b.timer = 0.05;
          }
        });

        if (this.powerupMap[ray.r][ray.c] !== PWR_NONE) {
          this.powerupMap[ray.r][ray.c] = PWR_NONE;
          this.floatingTexts.push(new FloatingText(ray.c * TILE + TILE / 2, ray.r * TILE + TILE / 2, 'ITEM QUEIMOU!', '#ff4444'));
        }
      });

      if (f.duration <= 0) {
        this.flames.splice(i, 1);
      }
    }
  }

  killMonster(m, index) {
    this.monsters.splice(index, 1);
    this.score += 200;
    sound.playExplosion();
    this.floatingTexts.push(new FloatingText(m.x, m.y, '+200', '#ffd700'));

    for (let i = 0; i < 12; i++) {
      this.particles.push(new Particle(
        m.x, m.y, '#e74c3c',
        (Math.random() - 0.5) * 5, (Math.random() - 0.5) * 5,
        5, 0.5
      ));
    }
  }

  playerDied(p) {
    p.alive = false;
    sound.playDeath();

    for (let i = 0; i < 20; i++) {
      this.particles.push(new Particle(
        p.x, p.y, p.color.body,
        (Math.random() - 0.5) * 6, (Math.random() - 0.5) * 6,
        6, 0.8
      ));
    }
  }

  checkPowerupPickup(p) {
    const r = Math.floor(p.y / TILE);
    const c = Math.floor(p.x / TILE);
    const pwr = this.powerupMap[r][c];

    if (pwr !== PWR_NONE && this.grid[r][c] === EMPTY) {
      this.powerupMap[r][c] = PWR_NONE;
      sound.playPowerup();

      let label = '';
      if (pwr === PWR_BOMB) { p.maxBombs = Math.min(6, p.maxBombs + 1); label = '+1 BOMBA! 💣'; }
      if (pwr === PWR_FIRE) { p.fireRange = Math.min(7, p.fireRange + 1); label = '+1 FOGO! 🔥'; }
      if (pwr === PWR_SPEED) { p.speed = Math.min(5.2, p.speed + 0.5); label = '+VELOCIDADE! 👟'; }
      if (pwr === PWR_KICK) { p.hasKick = true; label = 'CHUTE DE BOMBA! 🥊'; }
      if (pwr === PWR_SHIELD) { p.hasShield = true; label = 'ESCUDO ATIVADO! 🛡️'; }
      if (pwr === PWR_REMOTE) { p.hasRemote = true; label = 'DETONADOR REMOTO! ⏱️'; }

      this.score += 100;
      this.floatingTexts.push(new FloatingText(p.x, p.y - 20, label, '#4ade80'));

      // Sparkle burst at pickup location
      const sparkleColors = ['#ffd700', '#fff200', '#ffec80', '#ffffff', '#7df9ff'];
      const count = 12 + Math.floor(Math.random() * 6);
      for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2 + (Math.random() - 0.5) * 0.4;
        const speed = 1.5 + Math.random() * 3;
        const size = 3 + Math.random() * 4;
        const life = 0.3 + Math.random() * 0.4;
        const color = sparkleColors[Math.floor(Math.random() * sparkleColors.length)];
        this.sparkles.push(new Sparkle(p.x, p.y, color, angle, speed, size, life));
      }
    }
  }

  updateMonsters(dt) {
    this.monsters.forEach(m => {
      m.changeDirTimer -= dt;
      if (m.changeDirTimer <= 0) {
        m.changeDirTimer = Math.random() * 1.5 + 0.5;
        const dirs = ['up', 'down', 'left', 'right'];
        if (m.type === 'pass' && this.players[0] && this.players[0].alive) {
          const dx = this.players[0].x - m.x;
          const dy = this.players[0].y - m.y;
          m.dir = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up');
        } else {
          m.dir = dirs[Math.floor(Math.random() * dirs.length)];
        }
      }

      let vx = 0, vy = 0;
      if (m.dir === 'up') vy = -m.speed;
      if (m.dir === 'down') vy = m.speed;
      if (m.dir === 'left') vx = -m.speed;
      if (m.dir === 'right') vx = m.speed;

      const nextX = m.x + vx;
      const nextY = m.y + vy;
      const radius = 14;

      const canPass = m.type === 'phantom';
      if (!this.checkMonsterCollision(nextX, nextY, radius, canPass)) {
        m.x = nextX;
        m.y = nextY;
      } else {
        m.changeDirTimer = 0;
      }

      this.players.forEach(p => {
        if (p.alive && p.invulnTimer <= 0) {
          const dist = Math.hypot(p.x - m.x, p.y - m.y);
          if (dist < 24) {
            this.playerDied(p);
          }
        }
      });
    });
  }

  checkMonsterCollision(x, y, radius, canPassBricks) {
    const minC = Math.floor((x - radius) / TILE);
    const maxC = Math.floor((x + radius) / TILE);
    const minR = Math.floor((y - radius) / TILE);
    const maxR = Math.floor((y + radius) / TILE);

    for (let r = minR; r <= maxR; r++) {
      for (let c = minC; c <= maxC; c++) {
        if (r < 0 || r >= ROWS || c < 0 || c >= COLS) return true;
        const cell = this.grid[r][c];
        if (cell === WALL) return true;
        if (cell === CRATE && !canPassBricks) return true;
        if (this.bombs.some(b => b.r === r && b.c === c)) return true;
      }
    }
    return false;
  }

  // AI Bots in Battle Arena
  updateBot(bot, dt) {
    bot.botThinkTimer -= dt;
    const botR = Math.floor(bot.y / TILE);
    const botC = Math.floor(bot.x / TILE);

    const dangerGrid = this.computeDangerGrid();
    const isUnderDanger = dangerGrid[botR] && dangerGrid[botR][botC] > 0;

    if (isUnderDanger || bot.botThinkTimer <= 0) {
      bot.botThinkTimer = this.difficulty === 'easy' ? 0.35 : (this.difficulty === 'medium' ? 0.2 : 0.1);

      if (isUnderDanger) {
        const safePath = this.findPathToSafeTile(botR, botC, dangerGrid);
        if (safePath && safePath.length > 0) {
          bot.botMoveDir = safePath[0];
        }
      } else {
        const target = this.findBotObjective(bot, botR, botC, dangerGrid);
        if (target) {
          const path = this.findPathTo(botR, botC, target.r, target.c);
          if (path && path.length > 0) {
            bot.botMoveDir = path[0];
          }
        }

        if (Math.random() < 0.25 && this.shouldBotDropBomb(bot, botR, botC, dangerGrid)) {
          this.dropBomb(bot);
        }
      }
    }

    if (bot.botMoveDir) {
      let vx = 0, vy = 0;
      if (bot.botMoveDir === 'up') vy = -bot.speed;
      if (bot.botMoveDir === 'down') vy = bot.speed;
      if (bot.botMoveDir === 'left') vx = -bot.speed;
      if (bot.botMoveDir === 'right') vx = bot.speed;

      this.moveEntity(bot, vx * 60 * dt, vy * 60 * dt);
      this.checkPowerupPickup(bot);
    }
  }

  computeDangerGrid() {
    const danger = Array(ROWS).fill(0).map(() => Array(COLS).fill(0));
    this.bombs.forEach(b => {
      danger[b.r][b.c] = 1;
      const dirs = [{ dr: -1, dc: 0 }, { dr: 1, dc: 0 }, { dr: 0, dc: -1 }, { dr: 0, dc: 1 }];
      dirs.forEach(d => {
        for (let s = 1; s <= b.range; s++) {
          const nr = b.r + d.dr * s;
          const nc = b.c + d.dc * s;
          if (nr < 0 || nr >= ROWS || nc < 0 || nc >= COLS) break;
          if (this.grid[nr][nc] === WALL) break;
          danger[nr][nc] = 1;
          if (this.grid[nr][nc] === CRATE) break;
        }
      });
    });
    this.flames.forEach(f => {
      f.rays.forEach(r => { if (danger[r.r]) danger[r.r][r.c] = 2; });
    });
    return danger;
  }

  findPathToSafeTile(startR, startC, dangerGrid) {
    const queue = [[startR, startC, []]];
    const visited = new Set([`${startR},${startC}`]);

    while (queue.length > 0) {
      const [r, c, path] = queue.shift();
      if (dangerGrid[r] && dangerGrid[r][c] === 0) return path;

      const dirs = [
        { dr: -1, dc: 0, name: 'up' },
        { dr: 1, dc: 0, name: 'down' },
        { dr: 0, dc: -1, name: 'left' },
        { dr: 0, dc: 1, name: 'right' },
      ];

      dirs.forEach(d => {
        const nr = r + d.dr;
        const nc = c + d.dc;
        const key = `${nr},${nc}`;
        if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS && !visited.has(key)) {
          if (this.grid[nr][nc] === EMPTY && !this.bombs.some(b => b.r === nr && b.c === nc)) {
            visited.add(key);
            queue.push([nr, nc, [...path, d.name]]);
          }
        }
      });
    }
    return null;
  }

  findBotObjective(bot, botR, botC, dangerGrid) {
    let best = null;
    let minDist = 999;

    for (let r = 1; r < ROWS - 1; r++) {
      for (let c = 1; c < COLS - 1; c++) {
        if (this.powerupMap[r][c] !== PWR_NONE && this.grid[r][c] === EMPTY && dangerGrid[r][c] === 0) {
          const dist = Math.abs(botR - r) + Math.abs(botC - c);
          if (dist < minDist) {
            minDist = dist;
            best = { r, c };
          }
        }
      }
    }
    if (best) return best;

    const enemies = this.players.filter(p => p !== bot && p.alive);
    if (enemies.length > 0) {
      const targetEnemy = enemies[0];
      return { r: Math.floor(targetEnemy.y / TILE), c: Math.floor(targetEnemy.x / TILE) };
    }
    return null;
  }

  findPathTo(startR, startC, targetR, targetC) {
    const queue = [[startR, startC, []]];
    const visited = new Set([`${startR},${startC}`]);

    while (queue.length > 0) {
      const [r, c, path] = queue.shift();
      if (r === targetR && c === targetC) return path;

      const dirs = [
        { dr: -1, dc: 0, name: 'up' },
        { dr: 1, dc: 0, name: 'down' },
        { dr: 0, dc: -1, name: 'left' },
        { dr: 0, dc: 1, name: 'right' },
      ];

      dirs.forEach(d => {
        const nr = r + d.dr;
        const nc = c + d.dc;
        const key = `${nr},${nc}`;
        if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS && !visited.has(key)) {
          if (this.grid[nr][nc] === EMPTY && !this.bombs.some(b => b.r === nr && b.c === nc)) {
            visited.add(key);
            queue.push([nr, nc, [...path, d.name]]);
          }
        }
      });
    }
    return null;
  }

  shouldBotDropBomb(bot, botR, botC, dangerGrid) {
    const dirs = [{ dr: -1, dc: 0 }, { dr: 1, dc: 0 }, { dr: 0, dc: -1 }, { dr: 0, dc: 1 }];
    let hasNearbyTarget = false;

    dirs.forEach(d => {
      const nr = botR + d.dr;
      const nc = botC + d.dc;
      if (nr >= 0 && nr < ROWS && nc >= 0 && nc < COLS) {
        if (this.grid[nr][nc] === CRATE) hasNearbyTarget = true;
      }
    });

    if (!hasNearbyTarget) return false;
    const safeTiles = this.findPathToSafeTile(botR, botC, dangerGrid);
    return safeTiles !== null;
  }

  updateSuddenDeath(dt) {
    this.suddenDeathTimer -= dt;
    if (this.suddenDeathTimer <= 0) {
      this.suddenDeathTimer = 0.6;
      const spiral = [];
      for (let layer = 1; layer < 4; layer++) {
        for (let c = layer; c < COLS - layer; c++) spiral.push({ r: layer, c });
        for (let r = layer; r < ROWS - layer; r++) spiral.push({ r, c: COLS - 1 - layer });
        for (let c = COLS - 1 - layer; c >= layer; c--) spiral.push({ r: ROWS - 1 - layer, c });
        for (let r = ROWS - 1 - layer; r >= layer; r--) spiral.push({ r, c: layer });
      }

      if (this.suddenDeathIndex < spiral.length) {
        const t = spiral[this.suddenDeathIndex];
        this.grid[t.r][t.c] = WALL;
        sound.playBombDrop();

        this.players.forEach(p => {
          if (p.alive && Math.floor(p.y / TILE) === t.r && Math.floor(p.x / TILE) === t.c) {
            this.playerDied(p);
          }
        });
        this.suddenDeathIndex++;
      }
    }
  }

  checkWinConditions() {
    if (this.mode === 'battle') {
      const alivePlayers = this.players.filter(p => p.alive);
      if (alivePlayers.length <= 1) {
        this.state = 'round_over';
        if (alivePlayers.length === 1) {
          const winner = alivePlayers[0];
          this.roundWins[winner.id]++;
          if (winner.id === 0) sound.playWin();
          this.floatingTexts.push(new FloatingText(this.canvas.width / 2, this.canvas.height / 2, `${winner.name} VENCEU A RODADA! 🏆`, '#ffd700'));

          if (this.roundWins[winner.id] >= 3) {
            setTimeout(() => {
              if (winner.id === 0) {
                this.showMatchWin('Parabéns! Você venceu o Torneio Super Bomberman!');
              } else {
                this.showGameOver(`${winner.name} venceu o Torneio.`);
              }
            }, 1800);
            return;
          }
        } else {
          this.floatingTexts.push(new FloatingText(this.canvas.width / 2, this.canvas.height / 2, 'EMPATE!', '#eaeaea'));
        }

        setTimeout(() => {
          this.startRound();
        }, 2200);
      }
    } else {
      if (!this.players[0].alive) {
        this.state = 'game_over';
        this.showGameOver('Você foi derrotado nas fases Arcade.');
      }
    }
  }

  stageClear() {
    this.state = 'stage_clear';
    sound.playWin();
    this.score += 1000 + Math.floor(this.timer * 10);
    this.showModal('stageClearModal');
  }

  showGameOver(msg) {
    this.state = 'game_over';
    const title = document.getElementById('gameOverTitle');
    const desc = document.getElementById('gameOverDesc');
    if (title) title.textContent = 'FIM DE JOGO';
    if (desc) desc.textContent = msg;
    const finalScore = document.getElementById('finalScoreVal');
    if (finalScore) finalScore.textContent = this.score;
    this.showModal('gameOverModal');
  }

  showMatchWin(msg) {
    this.state = 'match_win';
    sound.playWin();
    const desc = document.getElementById('matchWinDesc');
    if (desc) desc.textContent = msg;
    const winScore = document.getElementById('winScoreVal');
    if (winScore) winScore.textContent = this.score;
    this.showModal('matchWinModal');
  }

  updateHUD() {
    const p1 = this.players[0];
    if (!p1) return;

    const scoreEl = document.getElementById('hudScore');
    const timerEl = document.getElementById('hudTimer');
    const bombsEl = document.getElementById('hudBombs');
    const fireEl = document.getElementById('hudFire');
    const speedEl = document.getElementById('hudSpeed');

    if (scoreEl) scoreEl.textContent = this.score;
    if (timerEl) timerEl.textContent = Math.max(0, Math.ceil(this.timer));
    if (bombsEl) bombsEl.textContent = `${p1.maxBombs - p1.activeBombs}/${p1.maxBombs}`;
    if (fireEl) fireEl.textContent = p1.fireRange;
    if (speedEl) speedEl.textContent = p1.speed.toFixed(1);

    const kickEl = document.getElementById('badgeKick');
    const shieldEl = document.getElementById('badgeShield');
    const remoteEl = document.getElementById('badgeRemote');

    if (kickEl) kickEl.style.display = p1.hasKick ? 'flex' : 'none';
    if (shieldEl) shieldEl.style.display = p1.hasShield ? 'flex' : 'none';
    if (remoteEl) remoteEl.style.display = p1.hasRemote ? 'flex' : 'none';
  }

  render() {
    this.ctx.fillStyle = '#0f1423';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Apply screen shake offset
    this.ctx.save();
    if (this.shake.intensity > 0.5) {
      this.ctx.translate(this.shake.x, this.shake.y);
    }

    this.drawGrid();
    this.drawExitDoor();
    this.drawPowerups();
    this.drawBombs();
    this.drawFlames();
    this.drawMonsters();
    this.drawPlayers();
    this.drawParticles();
    this.drawSparkles();
    this.drawFloatingTexts();

    this.ctx.restore();
  }

  drawGrid() {
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const x = c * TILE;
        const y = r * TILE;
        const cell = this.grid[r][c];

        if (cell === WALL) {
          this.ctx.fillStyle = '#16213e';
          this.ctx.fillRect(x, y, TILE, TILE);
          this.ctx.strokeStyle = '#2a2a4a';
          this.ctx.strokeRect(x + 2, y + 2, TILE - 4, TILE - 4);

          this.ctx.fillStyle = '#1f2e54';
          this.ctx.fillRect(x + 4, y + 4, TILE - 8, 6);
        } else if (cell === CRATE) {
          this.ctx.fillStyle = '#8b5a2b';
          this.ctx.fillRect(x + 2, y + 2, TILE - 4, TILE - 4);
          this.ctx.fillStyle = '#a06835';
          this.ctx.fillRect(x + 4, y + 4, TILE - 8, TILE - 8);

          this.ctx.strokeStyle = '#5c3a1e';
          this.ctx.lineWidth = 2;
          this.ctx.strokeRect(x + 4, y + 4, TILE - 8, TILE - 8);
          this.ctx.beginPath();
          this.ctx.moveTo(x + 4, y + 4);
          this.ctx.lineTo(x + TILE - 4, y + TILE - 4);
          this.ctx.moveTo(x + TILE - 4, y + 4);
          this.ctx.lineTo(x + 4, y + TILE - 4);
          this.ctx.stroke();
        } else {
          this.ctx.fillStyle = (r + c) % 2 === 0 ? '#12182b' : '#141b30';
          this.ctx.fillRect(x, y, TILE, TILE);
        }
      }
    }
  }

  drawExitDoor() {
    if (this.mode === 'arcade' && this.exitRevealed && this.exitPos) {
      const x = this.exitPos.c * TILE;
      const y = this.exitPos.r * TILE;
      this.ctx.fillStyle = '#27ae60';
      this.ctx.fillRect(x + 6, y + 6, TILE - 12, TILE - 12);
      this.ctx.strokeStyle = '#2ecc71';
      this.ctx.lineWidth = 3;
      this.ctx.strokeRect(x + 6, y + 6, TILE - 12, TILE - 12);

      this.ctx.font = '22px sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.fillText('🚪', x + TILE / 2, y + TILE / 2 + 8);
    }
  }

  drawPowerups() {
    const time = Date.now() / 300;
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const pwr = this.powerupMap[r][c];
        if (pwr !== PWR_NONE && this.grid[r][c] === EMPTY) {
          const x = c * TILE + TILE / 2;
          const y = r * TILE + TILE / 2 + Math.sin(time) * 3;

          this.ctx.save();
          this.ctx.fillStyle = 'rgba(255, 215, 0, 0.2)';
          this.ctx.beginPath();
          this.ctx.arc(x, y, 16, 0, Math.PI * 2);
          this.ctx.fill();

          let icon = '💣';
          if (pwr === PWR_FIRE) icon = '🔥';
          if (pwr === PWR_SPEED) icon = '👟';
          if (pwr === PWR_KICK) icon = '🥊';
          if (pwr === PWR_SHIELD) icon = '🛡️';
          if (pwr === PWR_REMOTE) icon = '⏱️';

          this.ctx.font = '20px sans-serif';
          this.ctx.textAlign = 'center';
          this.ctx.textBaseline = 'middle';
          this.ctx.fillText(icon, x, y);
          this.ctx.restore();
        }
      }
    }
  }

  drawBombs() {
    this.bombs.forEach(b => {
      const cx = b.x;
      const cy = b.y;
      const r = 16 * b.scale;

      this.ctx.save();
      this.ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
      this.ctx.beginPath();
      this.ctx.ellipse(cx, cy + 12, r, r * 0.5, 0, 0, Math.PI * 2);
      this.ctx.fill();

      const grad = this.ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.3, 2, cx, cy, r);
      grad.addColorStop(0, '#555');
      grad.addColorStop(0.5, '#222');
      grad.addColorStop(1, '#0a0a0a');
      this.ctx.fillStyle = grad;
      this.ctx.beginPath();
      this.ctx.arc(cx, cy, r, 0, Math.PI * 2);
      this.ctx.fill();

      this.ctx.fillStyle = '#d35400';
      this.ctx.fillRect(cx - 3, cy - r - 4, 6, 6);

      this.ctx.fillStyle = ['#f39c12', '#e74c3c', '#ffffff'][Math.floor(Math.random() * 3)];
      this.ctx.beginPath();
      this.ctx.arc(cx, cy - r - 6, 4 + Math.random() * 2, 0, Math.PI * 2);
      this.ctx.fill();

      this.ctx.restore();
    });
  }

  drawFlames() {
    this.flames.forEach(f => {
      const alpha = Math.max(0, f.duration / f.maxDuration);
      this.ctx.save();
      this.ctx.globalAlpha = alpha;

      f.rays.forEach(ray => {
        const x = ray.c * TILE;
        const y = ray.r * TILE;

        this.ctx.fillStyle = '#ff3838';
        this.ctx.fillRect(x + 2, y + 2, TILE - 4, TILE - 4);

        this.ctx.fillStyle = '#ff9f1a';
        this.ctx.fillRect(x + 6, y + 6, TILE - 12, TILE - 12);

        this.ctx.fillStyle = '#ffffff';
        this.ctx.fillRect(x + 12, y + 12, TILE - 24, TILE - 24);
      });
      this.ctx.restore();
    });
  }

  drawMonsters() {
    this.monsters.forEach(m => {
      const cx = m.x;
      const cy = m.y;

      this.ctx.save();
      if (m.type === 'ballom') {
        this.ctx.fillStyle = '#e67e22';
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, 15, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.fillStyle = '#fff';
        this.ctx.fillRect(cx - 6, cy - 4, 4, 4);
        this.ctx.fillRect(cx + 2, cy - 4, 4, 4);
      } else if (m.type === 'pass') {
        this.ctx.fillStyle = '#2980b9';
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, 15, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.fillStyle = '#e74c3c';
        this.ctx.fillRect(cx - 6, cy - 4, 4, 4);
        this.ctx.fillRect(cx + 2, cy - 4, 4, 4);
      } else if (m.type === 'pontan') {
        this.ctx.fillStyle = '#e74c3c';
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, 16, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.fillStyle = '#f1c40f';
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, 8, 0, Math.PI * 2);
        this.ctx.fill();
      } else if (m.type === 'phantom') {
        this.ctx.fillStyle = 'rgba(155, 89, 182, 0.85)';
        this.ctx.beginPath();
        this.ctx.arc(cx, cy - 2, 15, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.fillStyle = '#fff';
        this.ctx.fillRect(cx - 5, cy - 5, 3, 3);
        this.ctx.fillRect(cx + 2, cy - 5, 3, 3);
      }
      this.ctx.restore();
    });
  }

  drawPlayers() {
    this.players.forEach(p => {
      if (!p.alive) return;

      const cx = p.x;
      const cy = p.y;
      const c = p.color;

      this.ctx.save();

      // Bomb placement flash — expanding shockwave ring + player blink
      if (p.bombFlash > 0) {
        const t = 1 - (p.bombFlash / 0.35); // 0→1 over duration
        const radius = 12 + t * 22;
        const alpha = (1 - t) * 0.7;
        this.ctx.save();
        this.ctx.strokeStyle = `rgba(255, 200, 60, ${alpha})`;
        this.ctx.lineWidth = 3 * (1 - t);
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        this.ctx.stroke();
        // Inner glow
        this.ctx.fillStyle = `rgba(255, 255, 200, ${alpha * 0.25})`;
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, radius * 0.6, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();
        // Brief white blink on the player sprite
        if (t < 0.3) {
          this.ctx.globalAlpha = 0.6;
          this.ctx.fillStyle = 'rgba(255, 255, 220, 0.5)';
          this.ctx.beginPath();
          this.ctx.arc(cx, cy, 18, 0, Math.PI * 2);
          this.ctx.fill();
        }
      }

      if (p.invulnTimer > 0 && Math.floor(p.invulnTimer * 10) % 2 === 0) {
        this.ctx.globalAlpha = 0.4;
      }

      if (p.hasShield) {
        this.ctx.strokeStyle = '#00f0ff';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.arc(cx, cy, 22, 0, Math.PI * 2);
        this.ctx.stroke();
      }

      this.ctx.fillStyle = 'rgba(0, 0, 0, 0.35)';
      this.ctx.beginPath();
      this.ctx.ellipse(cx, cy + 14, 14, 6, 0, 0, Math.PI * 2);
      this.ctx.fill();

      this.ctx.fillStyle = c.suit;
      this.ctx.beginPath();
      this.ctx.arc(cx, cy + 4, 11, 0, Math.PI * 2);
      this.ctx.fill();

      this.ctx.fillStyle = c.hat;
      this.ctx.beginPath();
      this.ctx.arc(cx, cy - 4, 13, 0, Math.PI * 2);
      this.ctx.fill();

      this.ctx.fillStyle = c.skin;
      this.ctx.fillRect(cx - 7, cy - 7, 14, 9);

      this.ctx.fillStyle = '#000';
      if (p.facing === 'down') {
        this.ctx.fillRect(cx - 4, cy - 6, 2, 5);
        this.ctx.fillRect(cx + 2, cy - 6, 2, 5);
      } else if (p.facing === 'up') {
        // Helmet rear
      } else if (p.facing === 'left') {
        this.ctx.fillRect(cx - 6, cy - 6, 2, 5);
      } else if (p.facing === 'right') {
        this.ctx.fillRect(cx + 4, cy - 6, 2, 5);
      }

      this.ctx.fillStyle = c.head;
      this.ctx.beginPath();
      this.ctx.arc(cx, cy - 17, 4, 0, Math.PI * 2);
      this.ctx.fill();

      this.ctx.restore();
    });
  }

  drawParticles() {
    this.particles.forEach(p => p.draw(this.ctx));
  }

  drawFloatingTexts() {
    this.floatingTexts.forEach(t => t.draw(this.ctx));
  }

  async loadHighscores() {
    try {
      const res = await fetch('/api/bomberman/highscores');
      if (res.ok) {
        const scores = await res.json();
        this.renderHighscoresList(scores);
      }
    } catch (e) {
      console.warn('Could not load highscores:', e);
    }
  }

  async submitHighscore(name) {
    try {
      const res = await fetch('/api/bomberman/highscores', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name || 'JOGADOR',
          score: this.score,
          mode: this.mode,
          difficulty: this.difficulty,
        }),
      });
      if (res.ok) {
        this.hideModal('gameOverModal');
        this.hideModal('matchWinModal');
        this.loadHighscores();
      }
    } catch (e) {
      console.warn('Could not submit highscore:', e);
    }
  }

  renderHighscoresList(scores) {
    const listEl = document.getElementById('highscoresList');
    if (!listEl) return;
    listEl.innerHTML = scores.map((s, idx) => `
      <div class="score-row">
        <span class="rank">#${idx + 1} ${s.name}</span>
        <span class="score-pts">${s.score} PTS</span>
      </div>
    `).join('');
  }
}

// Bootstrap game instance
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', () => {
      window.game = new BombermanGame();
    });
  } else {
    window.game = new BombermanGame();
  }
}
