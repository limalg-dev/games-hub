export function renderPreview(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const size = canvas.width;
  const cell = size / 11;
  const words = [
    { r: 1, c: 1, d: 'across', w: 'PYTHON' },
    { r: 1, c: 1, d: 'down', w: 'PIZZA' },
    { r: 3, c: 3, d: 'across', w: 'MODEL' },
    { r: 4, c: 1, d: 'across', w: 'SERVER' },
    { r: 1, c: 7, d: 'down', w: 'CLOUD' },
    { r: 3, c: 7, d: 'across', w: 'TIGER' }
  ];
  const letters = {};
  for (const p of words) {
    const dr = p.d === 'down' ? 1 : 0;
    const dc = p.d === 'down' ? 0 : 1;
    for (let i = 0; i < p.w.length; i++) {
      letters[p.r + dr * i] = letters[p.r + dr * i] || {};
      letters[p.r + dr * i][p.c + dc * i] = p.w[i];
    }
  }
  const nums = { '1:1': 1, '3:3': 2, '4:1': 3, '3:7': 4, '1:7': 5 };
  ctx.clearRect(0, 0, size, size);
  ctx.fillStyle = '#0f3460';
  ctx.fillRect(0, 0, size, size);
  for (let r = 0; r < 11; r++) {
    for (let c = 0; c < 11; c++) {
      const x = c * cell, y = r * cell;
      if (letters[r] && letters[r][c]) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(x, y, cell, cell);
        ctx.strokeStyle = '#b58863';
        ctx.strokeRect(x, y, cell, cell);
        ctx.fillStyle = '#222';
        ctx.font = `${cell * 0.62}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(letters[r][c], x + cell / 2, y + cell / 2 + 1);
        const num = nums[`${r}:${c}`];
        if (num) {
          ctx.fillStyle = '#0f3460';
          ctx.font = `${cell * 0.28}px Arial`;
          ctx.fillText(num, x + cell * 0.18, y + cell * 0.24);
        }
      } else {
        ctx.fillStyle = '#0f3460';
        ctx.fillRect(x, y, cell, cell);
        ctx.strokeStyle = 'rgba(255,255,255,0.08)';
        ctx.strokeRect(x, y, cell, cell);
      }
    }
  }
}