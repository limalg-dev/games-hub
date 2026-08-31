# Ant Defense (Colônia Neon) — Gameplay & Feature Enhancements Spec

> **Status:** Approved
> **Target:** `games/tower_defense/` (logic, routes, static/index.html, tests)
> **Goal:** Transform Ant Defense into a highly engaging, strategic, and polished tower defense game by adding WebAudio sound synthesis, targeting priorities, wave preview, pause control, 2 active player spells, and Level 4 branching tower specializations.

---

## 1. Overview & Architecture

Ant Defense receives a major upgrade divided into clean, decoupled layers:

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Canvas + UI)                 │
│  - WebAudio Sound Synthesizer (Procedural SFX, 0 audio files)│
│  - Active Spell Buttons [Q, E] + AoE targeting cursor       │
│  - Tower Panel: Targeting Mode Selector + L4 Branch Options │
│  - Wave Preview Card + Pause Button (⏸ / Spacebar)         │
│  - Highscore Modal                                          │
└──────────────────────────────┬──────────────────────────────┘
                               │ WebSocket (/tower-defense/ws/{id})
                               │ REST (/tower-defense/highscores)
┌──────────────────────────────▼──────────────────────────────┐
│                  BACKEND (FastAPI + logic.py)               │
│  - Targeting Priority Engine (first, last, strong, weak)    │
│  - Active Spell Engine (Acid Strike, Frost Nova cooldowns)   │
│  - L4 Tower Specialization Stats & Logic                    │
│  - In-Memory HighScoreManager (top 20 per difficulty)       │
│  - Time-scale pause control (scale=0)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Specifications

### 2.1 WebAudio Sound Synthesizer (`SoundSystem`)
**Location:** Frontend JS (`games/tower_defense/static/index.html`)
**Mechanism:** Real-time synthesis using `window.AudioContext` with zero external audio assets.
- **Mute / Volume Control:** Toggle button on top-right (`🔊 / 🔇`), volume slider or mute state stored in `localStorage.getItem('ant_td_muted')`.
- **Synthesized Sound Effects:**
  1. `shoot_archer`: Frequency glide 400Hz → 900Hz, Triangle wave, 0.08s decay.
  2. `shoot_bomb`: White noise buffer + Low-pass filter sweep 600Hz → 80Hz, 0.4s.
  3. `shoot_ice`: Sine wave harmonics 1200Hz + 1600Hz with fast arpeggio, 0.15s.
  4. `spell_acid`: Low rumble whoosh (sawtooth 120Hz → 40Hz) + sizzle noise, 0.5s.
  5. `spell_frost`: Resonant crystal chime chord (C5 + E5 + G5), 0.6s.
  6. `wave_start`: 3-note rising chime (330Hz → 440Hz → 660Hz).
  7. `wave_clear`: Triumphant arpeggio (C-E-G-C), 0.5s.
  8. `game_over`: Minor descending chord (440Hz → 349Hz → 261Hz).
  9. `tower_place`: Crisp wood-block click (800Hz → 200Hz, 0.05s).
  10. `enemy_hit`: Tiny click/pop on impact.

---

### 2.2 Targeting Priorities Engine
**Location:** `games/tower_defense/logic.py` + `static/index.html`
- **Options:**
  - `FIRST` (`"first"`): Targets the enemy with highest `distance_traveled` (closest to anthill exit). **[Default]**
  - `LAST` (`"last"`): Targets the enemy with lowest `distance_traveled` (closest to spawn).
  - `STRONGEST` (`"strongest"`): Targets the enemy with highest current `hp`.
  - `WEAKEST` (`"weakest"`): Targets the enemy with lowest current `hp`.
  - `CLOSEST` (`"closest"`): Targets the enemy closest to the tower coordinates.
- **WebSocket Protocol:**
  - Client → Server: `{"command": "set_target_mode", "tower_id": str, "target_mode": "first"|"last"|"strongest"|"weakest"|"closest"}`
  - Server → Client: Included in `tower.to_dict()` as `"target_mode": tower.target_mode`.
- **UI:** Dropdown / Pill selector in the Tower Info Panel when a tower is selected.

---

### 2.3 Wave Preview & Pause Control
**Location:** `games/tower_defense/logic.py` + `static/index.html`
- **Pause Mechanic:**
  - `time_scale` supports `0` (Paused). In `update(dt)`: `if time_scale == 0: scaled_dt = 0.0`.
  - Frontend has `⏸️ Pausa` button + Spacebar shortcut.
- **Wave Preview:**
  - `get_state()` includes `next_wave`: `{ wave_number, bonus, enemies: [{ type, count, label, icon }] }`.
  - Frontend renders a banner above the Start Wave button showing e.g.: `Próxima Onda 4: 🪰 ×8  🪲 ×3  🦟 ×2 (+35🍃)`.

---

### 2.4 Active Player Spells (Abilities with Cooldown)
**Location:** `games/tower_defense/logic.py` + `static/index.html`
- **Spells:**
  1. 💥 **Chuva de Ácido (Acid Strike) [Key: Q]**
     - Target: Grid coordinate `(x, y)`.
     - Radius: 2.5 grid cells.
     - Damage: 120 instant damage to all enemies in radius.
     - Cooldown: 40.0 seconds.
  2. ❄️ **Névoa Congelante (Frost Nova) [Key: E]**
     - Target: Global (all active enemies).
     - Effect: Slows all enemies by 70% (`speed * 0.3`) for 5.0 seconds.
     - Cooldown: 60.0 seconds.
- **State & Cooldown Management:**
  - `GameState` tracks `spells: {"acid_strike": {"cooldown": 0.0, "max_cooldown": 40.0}, "frost_nova": {"cooldown": 0.0, "max_cooldown": 60.0}}`.
  - In `update(dt)`: decrement cooldowns by `scaled_dt`.
- **WebSocket Protocol:**
  - Client → Server: `{"command": "cast_spell", "spell": "acid_strike"|"frost_nova", "x": float, "y": float}`
  - Server validation: Checks `cooldown <= 0` and valid coordinates.
  - Server broadcast: Returns event in `state_changes` and visual event trigger.
- **Visuals:** Acid green splash particle circle for Acid Strike; full-screen ice crystal flash for Frost Nova.

---

### 2.5 Level 4 Tower Specializations (Branching Upgrades)
**Location:** `games/tower_defense/logic.py` + `static/index.html`
When an existing L3 tower is upgraded, the player chooses between 2 branches (cost: 140-180 crystals):

1. **🏹 Arqueira (Archer L4):**
   - **Branch A — Sniper (Atiradora de Elite):**
     - Range: `4.5` cells (huge!).
     - Damage: `(75, 110)` (high single-target punch).
     - Attack Speed: `1.8s` (slow firing).
     - Trait: Prioritizes armored and high HP targets.
   - **Branch B — Gatling Ant (Metralhadora):**
     - Range: `2.8` cells.
     - Damage: `(8, 12)`.
     - Attack Speed: `0.18s` (extreme rapid fire ~5 shots/sec).
     - Trait: Shreds swarms of fast enemies.

2. **💣 Bomba (Bomb L4):**
   - **Branch A — Toxic Mortar (Morteiro Ácido):**
     - Range: `3.0` cells.
     - AoE Radius: `2.0` cells.
     - Damage: `(50, 75)` + Poison DoT (15 dmg/sec for 3.0s).
   - **Branch B — Plasma Cannon (Canhão de Plasma):**
     - Range: `2.6` cells.
     - AoE Radius: `2.6` cells (massive explosion).
     - Damage: `(90, 140)` + 0.5s stun.

3. **❄️ Gelo (Ice L4):**
   - **Branch A — Blizzard Shrine (Nevasca Contínua):**
     - Range: `3.0` cells.
     - Trait: Continuous pulsing 50% slow aura in full radius (no projectiles, hits all inside every 0.5s, 10 damage).
   - **Branch B — Permafrost (Prisão de Cristal):**
     - Range: `3.0` cells.
     - Trait: Freezes primary target for 2.0s (100% stop) and applies 30% bonus damage vulnerability.

---

### 2.6 Highscore & Leaderboard Engine
**Location:** `games/tower_defense/routes.py`
- Endpoints:
  - `GET /tower-defense/highscores?difficulty=normal&limit=10`
  - `POST /tower-defense/highscores` with payload `{"name": "ANON", "score": 15000, "difficulty": "normal", "waves_cleared": 15, "victory": true}`
- Storage: In-memory `TowerDefenseHighScoreManager` with default classic entries, sorted by score descending, capped at 50 entries per difficulty.

---

## 3. Verification & Testing Strategy
- Unit tests in `games/tower_defense/test_tower_defense_logic.py`:
  - `test_target_modes`: Verify all 5 modes target the expected enemy under various path and HP scenarios.
  - `test_active_spells`: Verify cooldown decrements, valid/invalid casts, AoE damage application, and global frost slow.
  - `test_tower_l4_branches`: Verify branching upgrades, correct stat calculation, costs, and selling values.
  - `test_pause_time_scale`: Verify `time_scale=0` stops enemy movement and cooldowns without breaking tick loop.
- API tests in `tests/test_tower_defense_integration.py`:
  - Verify WS commands `set_target_mode`, `cast_spell`, `upgrade_tower_branch`.
  - Verify REST `/tower-defense/highscores` GET and POST.
- Frontend verification:
  - Playable run on `/play/tower_defense` or `/tower-defense/play`.
