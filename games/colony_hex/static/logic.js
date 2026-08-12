import { HexBoard } from './board.js';

let board = new HexBoard("colony-canvas");
board.bindEvents();

let gameId = location.pathname.split("/").pop();
let wsProtocol = location.protocol === "https:" ? "wss" : "ws";
let ws = new WebSocket(`${wsProtocol}://${location.host}/games/colony_hex/ws/${gameId}`);

let myColor = null;
let gameState = null;

const turnIndicator = document.getElementById("turn-indicator");
const lobbyPanel = document.getElementById("lobby-panel");
const lobbySlots = document.getElementById("lobby-slots");
const btnStart = document.getElementById("btn-start-game");
const btnForfeit = document.getElementById("btn-forfeit");

const hudColor = document.getElementById("hud-my-color");
const hudActions = document.getElementById("hud-actions");
const hudLeaves = document.getElementById("hud-leaves");

const btnRecruitWorker = document.getElementById("btn-recruit-worker");
const btnRecruitSoldier = document.getElementById("btn-recruit-soldier");
const btnEndTurn = document.getElementById("btn-end-turn");

ws.onmessage = (event) => {
  let msg = JSON.parse(event.data);
  if (msg.type === "welcome") {
    myColor = msg.seat;
    hudColor.textContent = myColor.toUpperCase();
    hudColor.style.color = getPlayerColorHex(myColor);
    updateState(msg.state);
  } else if (msg.type === "state") {
    updateState(msg.state);
  } else if (msg.type === "error") {
    alert(msg.message);
  }
};

function getPlayerColorHex(color) {
  const map = { red: "#e94560", blue: "#4a90e2", green: "#4ade80", yellow: "#ffd700" };
  return map[color] || "#fff";
}

function updateState(state) {
  gameState = state;
  board.update(state.map, state.units);
  
  let activePlayer = state.players[state.turn_index];
  let myPlayerInfo = state.players.find(p => p.color === myColor);
  
  if (myPlayerInfo) {
    hudActions.textContent = state.turn_index === state.players.indexOf(myPlayerInfo) ? state.actions_left : "0";
    hudLeaves.textContent = myPlayerInfo.leaves;
  }
  
  if (state.status === "lobby") {
    lobbyPanel.style.display = "block";
    turnIndicator.textContent = "Aguardando início da partida no lobby...";
    lobbySlots.innerHTML = state.players.map(p => `
      <div style="color: ${getPlayerColorHex(p.color)}">
        Slot ${p.color.toUpperCase()} ${p.is_ai ? "(IA)" : "(Humano)"}
      </div>
    `).join("");
    if (myColor === "red") {
      btnStart.style.display = "block";
    }
  } else if (state.status === "active") {
    lobbyPanel.style.display = "none";
    let isMyTurn = activePlayer.color === myColor;
    turnIndicator.textContent = isMyTurn ? "Sua vez de jogar!" : `Vez do jogador ${activePlayer.color.toUpperCase()}...`;
    document.getElementById("timer").textContent = `Turno ${state.turn_number}/20`;
  } else if (state.status === "finished") {
    let overlay = document.getElementById("game-over-overlay");
    let msgEl = document.getElementById("game-over-message");
    document.getElementById("game-over-title").textContent = state.winner === myColor ? "Vitória!" : "Fim de Jogo";
    msgEl.textContent = state.winner === myColor ? "Parabéns, você dominou o formigueiro!" : `O jogador ${state.winner?.toUpperCase()} venceu.`;
    overlay.classList.remove("hidden");
  }
}

btnStart.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "start" }));
});

btnForfeit.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "forfeit" }));
});

btnEndTurn.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "action", action: { kind: "end_turn" } }));
});

btnRecruitWorker.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "action", action: { kind: "recruit", unit_type: "worker" } }));
});

btnRecruitSoldier.addEventListener("click", () => {
  ws.send(JSON.stringify({ type: "action", action: { kind: "recruit", unit_type: "soldier" } }));
});

function getDistance(q1, r1, q2, r2) {
  return Math.floor((Math.abs(q1 - q2) + Math.abs(q1 + r1 - q2 - r2) + Math.abs(r1 - r2)) / 2);
}

// Canvas cell click moves & attacks
board.onCellSelected = (cell) => {
  if (!gameState || gameState.status !== "active") return;
  let activePlayer = gameState.players[gameState.turn_index];
  if (activePlayer.color !== myColor) return;
  
  // 1. Check if there is an own unit on the clicked cell
  let ownUnit = gameState.units.find(u => u.q === cell.q && u.r === cell.r && u.owner === myColor);
  if (ownUnit) {
    board.selectedUnit = ownUnit;
  } 
  // 2. Else if we already have a unit selected
  else if (board.selectedUnit) {
    let ownUnitClick = gameState.units.find(u => u.q === cell.q && u.r === cell.r && u.owner === myColor);
    if (ownUnitClick) {
      // Switch selection to the clicked unit
      board.selectedUnit = ownUnitClick;
      board.render();
    } else {
      let dist = getDistance(board.selectedUnit.q, board.selectedUnit.r, cell.q, cell.r);
      if (dist === 1) {
        // Adjacent target cell -> Move or Attack
        let targetUnit = gameState.units.find(u => u.q === cell.q && u.r === cell.r);
        let isEnemyUnit = targetUnit && targetUnit.owner !== myColor;
        let isEnemyTerritory = cell.owner !== null && cell.owner !== myColor;
        
        if (isEnemyUnit || isEnemyTerritory) {
          // Attack
          ws.send(JSON.stringify({
            type: "action",
            action: {
              kind: "attack",
              unit_id: board.selectedUnit.id,
              to_q: cell.q,
              to_r: cell.r
            }
          }));
        } else {
          // Move
          ws.send(JSON.stringify({
            type: "action",
            action: {
              kind: "move",
              unit_id: board.selectedUnit.id,
              to_q: cell.q,
              to_r: cell.r
            }
          }));
        }
      }
      // Clear selection after move/attack attempt or if clicked too far
      board.selectedUnit = null;
      board.render();
    }
  } 
  // 3. Else (no own unit on cell, and no selected unit) -> Expand option
  else if (cell.owner === null && cell.terrain !== "rock") {
    ws.send(JSON.stringify({
      type: "action",
      action: { kind: "expand", q: cell.q, r: cell.r }
    }));
  }
};
