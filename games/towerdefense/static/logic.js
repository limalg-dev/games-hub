export function createEnemy(type, hp, speed, path) {
    return {
        type,
        hp,
        maxHp: hp,
        speed,
        path,
        pathIndex: 0,
        x: path[0][0],
        y: path[0][1],
        alive: true,
        reachedBase: false,
    };
}

export function updateEnemies(enemies, dt) {
    for (const e of enemies) {
        if (!e.alive) continue;
        if (e.pathIndex < e.path.length - 1) {
            const target = e.path[e.pathIndex + 1];
            const dx = target[0] - e.x;
            const dy = target[1] - e.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const move = e.speed * dt;
            if (move >= dist) {
                e.x = target[0];
                e.y = target[1];
                e.pathIndex++;
            } else {
                e.x += (dx / dist) * move;
                e.y += (dy / dist) * move;
            }
        } else {
            e.alive = false;
            e.reachedBase = true;
        }
    }
}

export function fireTowers(towers, enemies, dt) {
    const projectiles = [];
    for (const t of towers) {
        t.cooldown = (t.cooldown || 0) - dt;
        if (t.cooldown <= 0) {
            let best = null;
            let bestDist = Infinity;
            for (const e of enemies) {
                if (!e.alive) continue;
                const d = Math.sqrt((e.x - t.row) ** 2 + (e.y - t.col) ** 2);
                if (d <= t.range && d < bestDist) {
                    best = e;
                    bestDist = d;
                }
            }
            if (best) {
                projectiles.push({
                    x: t.row,
                    y: t.col,
                    target: best,
                    damage: t.damage,
                    speed: 8,
                });
                t.cooldown = t.fireRate || 1;
            }
        }
    }
    return projectiles;
}

export function updateProjectiles(projectiles, dt) {
    for (const p of projectiles) {
        const dx = p.target.x - p.x;
        const dy = p.target.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 0.3) {
            p.target.hp -= p.damage;
            if (p.target.hp <= 0) p.target.alive = false;
            p.done = true;
        } else {
            p.x += (dx / dist) * p.speed * dt;
            p.y += (dy / dist) * p.speed * dt;
        }
    }
    return projectiles.filter((p) => !p.done);
}
