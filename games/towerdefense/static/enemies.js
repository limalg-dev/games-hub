export const ENEMY_COLORS = {
    zombie: "#4a7a4a", zombie_fast: "#7a7a4a", tank: "#5a5a5a",
    suicide: "#ff4444", vampire: "#8a2a8a", stealth: "rgba(100,100,100,0.3)",
    swarm: "#6a8a6a", shield: "#4a6a8a", necro: "#3a3a6a",
    final: "#8a2a2a", dracula: "#6a1a6a", golem: "#4a4a4a", reaper: "#2a2a2a",
};

export function drawEnemy(ctx, enemy, tileSize) {
    const x = enemy.x * tileSize;
    const y = enemy.y * tileSize;

    ctx.fillStyle = ENEMY_COLORS[enemy.type] || "#ff0000";
    ctx.beginPath();
    ctx.arc(x + tileSize / 2, y + tileSize / 2, tileSize / 3, 0, Math.PI * 2);
    ctx.fill();

    const hpPct = enemy.hp / enemy.max_hp;
    ctx.fillStyle = "#333";
    ctx.fillRect(x + 4, y - 4, tileSize - 8, 3);
    ctx.fillStyle = hpPct > 0.5 ? "#4caf50" : hpPct > 0.25 ? "#ff9800" : "#f44336";
    ctx.fillRect(x + 4, y - 4, (tileSize - 8) * hpPct, 3);
}
