export function renderPreview(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    canvas.width = 100;
    canvas.height = 100;

    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, 100, 100);

    for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
            ctx.fillStyle = Math.random() < 0.3 ? "#8B7355" : "#2d5a1e";
            ctx.fillRect(c * 20, r * 20, 18, 18);
        }
    }

    ctx.fillStyle = "#ff4444";
    ctx.beginPath();
    ctx.arc(10, 10, 5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#4a8af4";
    ctx.fillRect(72, 72, 16, 16);
}
