export const TOWER_COLORS = {
    rifle: "#4a8af4",
    sniper: "#f4a84a",
    missile: "#f44a4a",
    tesla: "#a44af4",
    slow: "#4af4f4",
};

export const TOWER_COSTS = {
    rifle: 50,
    sniper: 120,
    missile: 150,
    tesla: 100,
    slow: 80,
};

export function drawTower(ctx, tower, tileSize) {
    const x = tower.col * tileSize;
    const y = tower.row * tileSize;

    ctx.fillStyle = TOWER_COLORS[tower.type] || "#fff";
    ctx.fillRect(x + 4, y + 4, tileSize - 8, tileSize - 8);

    ctx.fillStyle = "#fff";
    ctx.font = "10px monospace";
    ctx.textAlign = "center";
    ctx.fillText(tower.level, x + tileSize / 2, y + tileSize / 2 + 4);
}

export function drawRange(ctx, row, col, range, tileSize) {
    ctx.strokeStyle = "rgba(255, 255, 255, 0.3)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(col * tileSize + tileSize / 2, row * tileSize + tileSize / 2, range * tileSize, 0, Math.PI * 2);
    ctx.stroke();
}
