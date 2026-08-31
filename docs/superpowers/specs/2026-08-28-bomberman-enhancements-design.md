# Super Bomberman — Gameplay, Combat & Game Feel Enhancements Spec

> **Status:** Approved
> **Target:** `games/bomberman/` (`logic.py`, `routes.py`, `static/game.js`, `static/audio.js`, `static/index.html`, `static/style.css`, tests)
> **Goal:** Upgrade Super Bomberman with SNES-grade game feel and competitive depth: corner-assist navigation, dynamic bomb heartbeat pulse, chiptune BGM music generator, 3 tactical power-ups (Pierce, Punch, Skull), Revenge Cart mechanic for eliminated players, and custom match settings (Best of 1, 3, 5 rounds).

---

## 1. Architecture & Component Decomposition

```
┌───────────────────────────────────────────────────────────────┐
│                    FRONTEND (Canvas & Audio)                  │
│  - audio.js: ChiptuneBGM (Procedural WebAudio melody/bass)    │
│  - game.js:                                                   │
│    * Corner-Assist (Corner-sliding on tile edges)             │
│    * Dynamic Bomb Pulse (Heartbeat expansion + fuse spark)    │
│    * 3 New Power-ups (Pierce, Punch [F], Skull / Curse)       │
│    * Revenge Cart (Eliminated players patrol perimeter)       │
│    * Match Settings HUD (Best of 1/3/5 rounds + scoreboard)   │
└───────────────────────────────┬───────────────────────────────┘
                                │ REST (/api/bomberman/*)
┌───────────────────────────────▼───────────────────────────────┐
│                    BACKEND (FastAPI + logic.py)               │
│  - logic.py:                                                  │
│    * Power-up definitions (PIERCE=7, PUNCH=8, SKULL=9)        │
│    * generate_map() power-up distribution                     │
│    * Stage configs with tactical item distribution            │
│  - routes.py:                                                 │
│    * Highscores & metadata endpoints                          │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Specifications

### 2.1 Corner-Assistance Navigation Engine (`game.js`)
- **Problem:** Rigid AABB collision causes the player to get stuck when turning into a 1-tile corridor if misaligned by just a few pixels.
- **Solution:** When player attempts to move perpendicular to an obstacle (e.g. moving Up into a tile where only the left/right half is open), calculate offset from tile center.
  - If offset $\le 14\text{px}$ (out of $48\text{px}$ tile), slide the player horizontally/vertically toward the corridor center at current speed.
- **Result:** Silky smooth navigation on keyboard and mobile touch D-pad.

---

### 2.2 Bomb Heartbeat Pulse & Scorch Visuals (`game.js`)
- **Visuals:**
  - Bombs expand and contract using a sine wave whose frequency increases exponentially as the 3.0s fuse expires:
    $\text{scale} = 1.0 + 0.18 \times \sin(2\pi \cdot f(t) \cdot t)$, where $f(t)$ goes from $2\text{Hz}$ to $10\text{Hz}$.
  - Top fuse emits dynamic spark particles.
  - Explosions leave semi-transparent scorch marks on the ground tile that fade over 8 seconds.

---

### 2.3 Chiptune BGM Generator (`audio.js`)
- **Implementation:** Web Audio API synth tracker running a looping 16-step arcade melody + bassline + noise hi-hat:
  - Lead channel: Square wave melody (retro upbeat tempo 135 BPM).
  - Bass channel: Triangle wave walking bassline.
  - Percussion: Short white noise decay for snare/hi-hat on beats.
- **Controls:** BGM button (`🎵 Música: ON/OFF`) in HUD with volume control and `localStorage` state.

---

### 2.4 Three New Tactical Power-ups (`logic.py` + `game.js`)

1. 💥 **Bomba Espinho (Pierce Bomb) — `PWR_PIERCE = 7` (Icon: ⚡):**
   - Explosions pierce through all destructible crates in the blast path without stopping at the first crate.
2. 🥊 **Soco de Bomba (Boxing Glove) — `PWR_PUNCH = 8` (Icon: 🥊):**
   - Player can press `[F]` (or click Punch button / tap punch on mobile) when facing a bomb to punch it 3 tiles forward over walls and crates.
3. 💀 **Caveira da Maldição (Skull / Curse) — `PWR_SKULL = 9` (Icon: 💀):**
   - Picking up a skull afflicts the player with a random 10-second curse:
     - 🌀 *Confusão:* Controles invertidos.
     - 💨 *Diarreia:* Coloca bombas automaticamente a cada passo.
     - 🐢 *Lentidão Extrema:* Velocidade reduzida a 30%.
     - 🕯️ *Foguinho:* Alcance da explosão reduzido a 1 célula.
   - Touching another player passes the curse to them!

---

### 2.5 Revenge Cart Mechanic (`game.js`)
- In **Battle Mode**, when Player 1 is eliminated:
  - Player transitions to a **Revenge Cart** circling the outer boundary of the arena.
  - Controls: Move along the perimeter track and press `[Espaço]` to launch a bomb into the arena (1 bomb at a time, cooldown 4s).
  - If a Revenge Cart bomb eliminates the surviving bot, the round ends with a revenge bonus!

---

### 2.6 Match Settings & Round Progression (`game.js` + `index.html`)
- Match Format options on start screen:
  - **Melhor de 1** (Partida Rápida)
  - **Melhor de 3** (Primeiro a 2 vitórias)
  - **Melhor de 5** (Primeiro a 3 vitórias)
- Trophy HUD counter displaying round wins per player with crowning celebration on match victory.

---

## 3. Verification & Testing Strategy
- Unit tests in `games/bomberman/tests/test_logic.py`:
  - Verify `generate_map` includes all power-up types (1 to 9).
  - Verify stage configurations and highscore operations.
- Integration tests in `tests/test_bomberman_api.py`:
  - Verify `/api/bomberman/map`, `/api/bomberman/highscores`, `/api/bomberman/stages`.
- Frontend verification:
  - Playable testing of corner-assist, bomb pulse, chiptune BGM, punch, pierce, skull, and revenge cart.
