export function astar(grid, start, end) {
    const rows = grid.length, cols = grid[0].length;
    if (start[0] < 0 || start[0] >= rows || start[1] < 0 || start[1] >= cols) return null;
    if (end[0] < 0 || end[0] >= rows || end[1] < 0 || end[1] >= cols) return null;
    if (grid[start[0]][start[1]] === 1 || grid[end[0]][end[1]] === 1) return null;
    if (start[0] === end[0] && start[1] === end[1]) return [start];

    const openSet = [[0, start[0], start[1]]];
    const cameFrom = {};
    const gScore = {};
    gScore[`${start[0]},${start[1]}`] = 0;
    const dirs = [[-1,0],[1,0],[0,-1],[0,1]];

    while (openSet.length > 0) {
        openSet.sort((a, b) => a[0] - b[0]);
        const [, cr, cc] = openSet.shift();
        if (cr === end[0] && cc === end[1]) {
            const path = [];
            let key = `${cr},${cc}`;
            while (key) {
                const [r, c] = key.split(',').map(Number);
                path.unshift([r, c]);
                key = cameFrom[key];
            }
            return path;
        }
        for (const [dr, dc] of dirs) {
            const nr = cr + dr, nc = cc + dc;
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && grid[nr][nc] !== 1) {
                const tentG = gScore[`${cr},${cc}`] + 1;
                const nKey = `${nr},${nc}`;
                if (tentG < (gScore[nKey] ?? Infinity)) {
                    cameFrom[nKey] = `${cr},${cc}`;
                    gScore[nKey] = tentG;
                    openSet.push([tentG + Math.abs(nr - end[0]) + Math.abs(nc - end[1]), nr, nc]);
                }
            }
        }
    }
    return null;
}
