import { MAPS, TILE_SIZE, TILE_TYPES } from "./maps.js";
import { ENEMY_COLORS, drawEnemy } from "./enemies.js";
import { TOWER_COLORS, TOWER_COSTS, drawTower, drawRange } from "./towers.js";
import { astar } from "./pathfinding.js";
import { createEnemy, updateEnemies, fireTowers, updateProjectiles } from "./logic.js";
import { createHUD, updateHUD } from "./ui.js";

const WAVES = [
    { type: "zombie", hp: 50, speed: 1.0, count: 15 },
    { type: "zombie_fast", hp: 30, speed: 2.0, count: 20 },
    { type: "tank", hp: 150, speed: 0.6, count: 8 },
    { type: "suicide", hp: 40, speed: 1.5, count: 12 },
    { type: "vampire", hp: 100, speed: 1.0, count: 10 },
    { type: "stealth", hp: 60, speed: 1.2, count: 15 },
    { type: "swarm", hp: 10, speed: 2.5, count: 100 },
    { type: "shield", hp: 80, speed: 0.8, count: 10 },
    { type: "necro", hp: 80, speed: 0.8, count: 8 },
    { type: "final", hp: 1000, speed: 0.5, count: 1 },
];

export class TowerDefenseGame {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.gold = 200;
        this.lives = 20;
        this.wave = 0;
        this.towers = [];
        this.enemies = [];
        this.projectiles = [];
        this.selectedTower = null;
        this.grid = MAPS.urban.grid.map((r) => [...r]);
        this.spawn = [...MAPS.urban.spawn];
        this.base = [...MAPS.urban.base];
        this.rows = this.grid.length;
        this.cols = this.grid[0].length;
        this.towerGrid = {};
        this.running = false;
        this.animFrame = null;
        this.lastTime = 0;
        this.hud = null;
        this.canvas = null;
        this.ctx = null;

        this.camera = { x: 0, y: 0, zoom: 1, dragging: false, dragStart: { x: 0, y: 0 }, camStart: { x: 0, y: 0 } };
    }

    init() {
        if (!this.container) return;
        this.container.innerHTML = "";

        this.canvas = document.createElement("canvas");
        this.canvas.className = "td-canvas";
        this.canvas.width = this.cols * TILE_SIZE;
        this.canvas.height = this.rows * TILE_SIZE;
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext("2d");

        this.hud = createHUD(this.container);

        this.bindEvents();
        this.running = true;
        this.lastTime = performance.now();
        this.gameLoop(this.lastTime);
    }

    destroy() {
        this.running = false;
        if (this.animFrame) cancelAnimationFrame(this.animFrame);
        if (this.container) this.container.innerHTML = "";
    }

    bindEvents() {
        this.canvas.addEventListener("click", (e) => this.handleClick(e));
        this.canvas.addEventListener("wheel", (e) => this.handleWheel(e));
        this.canvas.addEventListener("mousedown", (e) => this.handleMouseDown(e));
        this.canvas.addEventListener("mousemove", (e) => this.handleMouseMove(e));
        this.canvas.addEventListener("mouseup", () => (this.camera.dragging = false));
        this.canvas.addEventListener("mouseleave", () => (this.camera.dragging = false));

        this.hud.querySelectorAll(".td-tower-btn").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                const type = e.target.dataset.tower;
                if (this.gold >= TOWER_COSTS[type]) {
                    this.selectedTower = type;
                    this.hud.querySelectorAll(".td-tower-btn").forEach((b) => b.classList.remove("selected"));
                    e.target.classList.add("selected");
                }
            });
        });

        this.hud.querySelector(".td-start-wave").addEventListener("click", () => this.startWave());
    }

    handleClick(e) {
        if (this.camera.dragging) return;
        const rect = this.canvas.getBoundingClientRect();
        const mx = (e.clientX - rect.left) / this.camera.zoom;
        const my = (e.clientY - rect.top) / this.camera.zoom;
        const col = Math.floor(mx / TILE_SIZE);
        const row = Math.floor(my / TILE_SIZE);

        if (!this.selectedTower || col < 0 || col >= this.cols || row < 0 || row >= this.rows) return;

        const cost = TOWER_COSTS[this.selectedTower];
        if (this.gold < cost) return;
        if (this.grid[row][col] !== 0) return;
        if (this.towerGrid[`${row},${col}`]) return;

        const testGrid = this.grid.map((r) => [...r]);
        testGrid[row][col] = 1;
        if (!astar(testGrid, this.spawn, this.base)) return;

        this.gold -= cost;
        const tower = {
            type: this.selectedTower,
            row,
            col,
            level: 1,
            damage: 10,
            range: 3,
            fireRate: 1.0,
            cooldown: 0,
        };
        this.towers.push(tower);
        this.towerGrid[`${row},${col}`] = tower;
        updateHUD(this.hud, this.gold, this.lives, this.wave);
    }

    handleWheel(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        this.camera.zoom = Math.max(0.5, Math.min(3, this.camera.zoom * delta));
    }

    handleMouseDown(e) {
        this.camera.dragging = true;
        this.camera.dragStart = { x: e.clientX, y: e.clientY };
        this.camera.camStart = { x: this.camera.x, y: this.camera.y };
    }

    handleMouseMove(e) {
        if (!this.camera.dragging) return;
        this.camera.x = this.camera.camStart.x + (e.clientX - this.camera.dragStart.x);
        this.camera.y = this.camera.camStart.y + (e.clientY - this.camera.dragStart.y);
    }

    startWave() {
        this.wave++;
        const waveIdx = Math.min(this.wave - 1, WAVES.length - 1);
        const waveData = WAVES[waveIdx];
        const path = astar(this.grid, this.spawn, this.base);
        if (!path) return;

        const scale = this.wave > WAVES.length ? 1 + (this.wave - WAVES.length) * 0.5 : 1;

        for (let i = 0; i < waveData.count; i++) {
            const enemy = createEnemy(
                waveData.type,
                Math.floor(waveData.hp * scale),
                waveData.speed,
                path.map((p) => [...p])
            );
            enemy.pathIndex = 0;
            this.enemies.push(enemy);
        }

        updateHUD(this.hud, this.gold, this.lives, this.wave);
    }

    gameLoop(now) {
        if (!this.running) return;
        const dt = Math.min((now - this.lastTime) / 1000, 0.1);
        this.lastTime = now;

        this.update(dt);
        this.render();

        this.animFrame = requestAnimationFrame((t) => this.gameLoop(t));
    }

    update(dt) {
        updateEnemies(this.enemies, dt);

        for (const e of this.enemies) {
            if (e.reachedBase) {
                this.lives--;
            }
        }
        this.enemies = this.enemies.filter((e) => e.alive);

        const newProjectiles = fireTowers(this.towers, this.enemies, dt);
        this.projectiles.push(...newProjectiles);
        this.projectiles = updateProjectiles(this.projectiles, dt);

        for (const e of this.enemies) {
            if (!e.alive && !e.reachedBase) {
                this.gold += 10;
            }
        }

        updateHUD(this.hud, this.gold, this.lives, this.wave);

        if (this.lives <= 0) {
            this.running = false;
            alert("Game Over! You reached wave " + this.wave);
        }
    }

    render() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        ctx.save();
        ctx.clearRect(0, 0, w, h);
        ctx.translate(this.camera.x, this.camera.y);
        ctx.scale(this.camera.zoom, this.camera.zoom);

        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const tile = this.grid[r][c];
                ctx.fillStyle = TILE_TYPES[tile]?.color || "#000";
                ctx.fillRect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                ctx.strokeStyle = "rgba(255,255,255,0.05)";
                ctx.strokeRect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            }
        }

        ctx.fillStyle = "#ff4444";
        ctx.fillRect(this.spawn[1] * TILE_SIZE, this.spawn[0] * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        ctx.fillStyle = "#4a8af4";
        ctx.fillRect(this.base[1] * TILE_SIZE, this.base[0] * TILE_SIZE, TILE_SIZE, TILE_SIZE);

        for (const tower of this.towers) {
            drawTower(ctx, tower, TILE_SIZE);
        }

        for (const enemy of this.enemies) {
            drawEnemy(ctx, enemy, TILE_SIZE);
        }

        ctx.fillStyle = "#ffd700";
        for (const p of this.projectiles) {
            ctx.beginPath();
            ctx.arc(p.y * TILE_SIZE + TILE_SIZE / 2, p.x * TILE_SIZE + TILE_SIZE / 2, 3, 0, Math.PI * 2);
            ctx.fill();
        }

        ctx.restore();
    }
}
