// Axial hex grid canvas rendering
const COLOR_MAP = {
  red: "#e94560",
  blue: "#4a90e2",
  green: "#4ade80",
  yellow: "#ffd700",
  neutral: "#2a2a4a",
  rock: "#444"
};

export class HexBoard {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext("2d");
    this.hexRadius = 26;
    this.cells = [];
    this.units = [];
    this.selectedCell = null;
    this.onCellSelected = null;
  }

  update(cells, units) {
    this.cells = cells;
    this.units = units;
    this.render();
  }

  getHexCorner(center, size, i) {
    let angle_deg = 60 * i;
    let angle_rad = Math.PI / 180 * angle_deg;
    return {
      x: center.x + size * Math.cos(angle_rad),
      y: center.y + size * Math.sin(angle_rad)
    };
  }

  hexToPixel(q, r) {
    let x = this.hexRadius * (Math.sqrt(3) * q + Math.sqrt(3)/2 * r);
    let y = this.hexRadius * (3./2 * r);
    return { x: x + this.canvas.width / 2, y: y + this.canvas.height / 2 };
  }

  pixelToHex(x, y) {
    let px = x - this.canvas.width / 2;
    let py = y - this.canvas.height / 2;
    let q = (Math.sqrt(3)/3 * px - 1./3 * py) / this.hexRadius;
    let r = (2./3 * py) / this.hexRadius;
    return this.hexRound(q, r);
  }

  hexRound(fractional_q, fractional_r) {
    let s = -fractional_q - fractional_r;
    let q = Math.round(fractional_q);
    let r = Math.round(fractional_r);
    let s_round = Math.round(s);
    let q_diff = Math.abs(q - fractional_q);
    let r_diff = Math.abs(r - fractional_r);
    let s_diff = Math.abs(s_round - s);
    if (q_diff > r_diff && q_diff > s_diff) {
      q = -r - s_round;
    } else if (r_diff > s_diff) {
      r = -q - s_round;
    }
    return { q, r };
  }

  drawHex(center, color, fill = true, stroke = true, width = 1) {
    this.ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      let corner = this.getHexCorner(center, this.hexRadius - 1, i);
      if (i === 0) this.ctx.moveTo(corner.x, corner.y);
      else this.ctx.lineTo(corner.x, corner.y);
    }
    this.ctx.closePath();
    if (fill) {
      this.ctx.fillStyle = color;
      this.ctx.fill();
    }
    if (stroke) {
      this.ctx.strokeStyle = "#2a2a4a";
      this.ctx.lineWidth = width;
      this.ctx.stroke();
    }
  }

  render() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Draw cells
    for (let cell of this.cells) {
      let center = this.hexToPixel(cell.q, cell.r);
      let color = COLOR_MAP.neutral;
      if (cell.terrain === "rock") color = COLOR_MAP.rock;
      else if (cell.owner) color = COLOR_MAP[cell.owner];
      
      // Selected outline
      let isSelected = this.selectedCell && this.selectedCell.q === cell.q && this.selectedCell.r === cell.r;
      this.drawHex(center, color, true, true, isSelected ? 3 : 1);
      
      if (isSelected) {
        this.ctx.strokeStyle = "#e94560";
        this.ctx.stroke();
      }

      // Draw leaves icon
      if (cell.terrain === "leaf") {
        this.ctx.fillStyle = "#4ade80";
        this.ctx.font = "12px sans-serif";
        this.ctx.fillText("🍃", center.x - 7, center.y + 4);
      }
    }

    // Draw units
    for (let u of this.units) {
      let center = this.hexToPixel(u.q, u.r);
      // Unit color boundary circle
      this.ctx.beginPath();
      this.ctx.arc(center.x, center.y, 14, 0, 2 * Math.PI);
      this.ctx.fillStyle = COLOR_MAP[u.owner];
      this.ctx.fill();
      this.ctx.lineWidth = 2;
      this.ctx.strokeStyle = "#fff";
      this.ctx.stroke();
      
      // Unit type emoji
      this.ctx.fillStyle = "#fff";
      this.ctx.font = "14px sans-serif";
      this.ctx.fillText(u.type === "worker" ? "🐜" : "🪖", center.x - 7, center.y + 5);
    }
  }

  bindEvents() {
    this.canvas.addEventListener("click", (e) => {
      let rect = this.canvas.getBoundingClientRect();
      let clickX = (e.clientX - rect.left) * (this.canvas.width / rect.width);
      let clickY = (e.clientY - rect.top) * (this.canvas.height / rect.height);
      let target = this.pixelToHex(clickX, clickY);
      
      let matchedCell = this.cells.find(c => c.q === target.q && c.r === target.r);
      if (matchedCell) {
        this.selectedCell = matchedCell;
        this.render();
        if (this.onCellSelected) this.onCellSelected(matchedCell);
      }
    });
  }
}
