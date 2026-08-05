# Tower Defense ("Urban Assault") — Design Spec

## Overview

A tower defense game with free-form placement, A* pathfinding, 5 tower types with upgrade trees, 10 fixed waves with random elements, cooperative and competitive multiplayer, persistent economy (gold + gems), shop with skins, and global leaderboard.

## Architecture

```
┌──────────────────────────────────────────────────┐
│                Backend (FastAPI)                  │
│  POST /games              → Criar jogo TD        │
│  GET  /games/{id}         → Estado do jogo       │
│  POST /api/shop           → Comprar skins/torres │
│  GET  /api/leaderboard    → Ranking global       │
│  WS   /ws/{game_id}       → Competitive mode     │
│                                                  │
│  towerdefense/engine.py   → Game loop server-side │
│  towerdefense/pathfinding → A* pathfinding       │
│  towerdefense/models.py   → Player, Tower, Wave  │
│  towerdefense/economy.py  → Gold, Gems, Shop     │
└──────────────┬───────────────────────────────────┘
               │ JSON / WebSocket
┌──────────────▼───────────────────────────────────┐
│              Frontend (Canvas + DOM)              │
│  td/board.js       → Canvas rendering (map,      │
│                       enemies, towers, projectiles)│
│  td/logic.js       → Game loop, collision, waves  │
│  td/pathfinding.js → A* client-side (preview)    │
│  td/towers.js      → Tower types, upgrades, range│
│  td/ui.js          → DOM: HUD, shop, leaderboard │
│  td/preview.js     → Modal preview               │
└──────────────────────────────────────────────────┘
```

## Rendering & Game Loop

- Canvas 2D renders: tile map, enemies (animated sprites), towers (static with rotation), projectiles (particles), range indicators
- Game loop at 60fps via requestAnimationFrame
- Camera: pan/zoom with mouse (drag + scroll wheel)
- Map: 20x15 grid of 32x32px tiles
  - Tile types: grass (buildable), road (path), water (blocks), building (pre-existing)

## Pathfinding (A*)

- Enemies use A* to find path to base
- When player places tower, pathfinding recalculates for all enemies
- If no valid path exists → tower placement rejected (red highlight)
- Competitive: enemies that pass are sent to opponent's map with modified stats

## Towers (5 types + upgrades)

| Type | Role | Damage | Range | Cost | Upgrade 1 | Upgrade 2 | Upgrade 3 |
|------|------|--------|-------|------|-----------|-----------|-----------|
| **Rifle** | Fast single-target | 10 | 3 | 50g | +5 dmg | +range | Double shot |
| **Sniper** | High dmg, long range, slow | 50 | 6 | 120g | +25 dmg | +pierce | Headshot 2x |
| **Missile** | AOE explosion | 30 | 4 | 150g | +AOE radius | +dmg | Cluster missile |
| **Tesla** | Chain lightning (3 targets) | 15 | 3 | 100g | +4 targets | +stun 0.5s | Overcharge |
| **Slow** | Reduces speed 50% | 0 | 3 | 80g | -70% speed | +range | Freeze 2s |

- Upgrades: 3 levels each, cost scales (1x, 1.5x, 2x base cost)
- Combos: adjacent towers with synergy get bonus (+20% dmg)

## Enemies & Waves

**10 fixed waves with random elements:**

| Wave | Type | HP | Speed | Count | Boss? |
|------|------|----|-------|-------|-------|
| 1 | Basic Zombie | 50 | 1.0 | 15 | No |
| 2 | Fast Zombie | 30 | 2.0 | 20 | No |
| 3 | Tank | 150 | 0.6 | 8 | No |
| 4 | Suicide (explodes on death) | 40 | 1.5 | 12 | No |
| 5 | Vampire (heals on kill) | 100 | 1.0 | 10 | **Yes (Dracula)** |
| 6 | Stealth (invisible until hit) | 60 | 1.2 | 15 | No |
| 7 | Swarm (100 mini-zombies) | 10 | 2.5 | 100 | No |
| 8 | Boss Golem | 500 | 0.4 | 1 + 20 shields | **Yes** |
| 9 | Necromancer (resurrects dead) | 80 | 0.8 | 8 | **Yes** |
| 10 | **Boss Final: Reaper** | 1000 | 0.5 | 1 | **Yes** |

- Extra infinite waves after wave 10 (difficulty scales)

## Economy

- **Gold**: earned per kill (10-50g), wave completion bonus (100g)
- **Gem**: earned every 3 waves (1 gem), competitive win (3 gems)
- **Shop**:
  - Visual skins for towers (no gameplay effect)
  - Unlockable towers (start with Rifle, unlock others with gems)
  - Emotes for competitive

## Competitive Mode

- 2 players, each with own map
- Same wave sequence
- Enemies that pass defenses are sent to opponent
- When a player loses all lives (20 HP), the other wins
- **WebSocket sync**: validates tower placements, syncs waves

## Files to Create

```
games/towerdefense/
├── __init__.py
├── models.py          # SQLModel: PlayerProfile, TowerInstance, WaveConfig
├── engine.py          # Server-side game loop, wave spawning, damage calc
├── pathfinding.py     # A* algorithm
├── towers.py          # Tower definitions, upgrade tree, combos
├── economy.py         # Gold, gems, shop logic
├── waves.py           # Wave configs (10 waves + infinite scaling)
├── static/
│   ├── board.js       # Canvas rendering, camera, input
│   ├── logic.js       # Game loop, collision, projectiles
│   ├── pathfinding.js # Client-side A* (for placement preview)
│   ├── towers.js      # Tower rendering, range display
│   ├── ui.js          # DOM HUD, shop, leaderboard
│   ├── preview.js     # Modal preview
│   ├── enemies.js     # Enemy sprites, animations
│   └── maps.js        # Map definitions (tile grids)
└── tests/
    ├── __init__.py
    ├── test_pathfinding.py
    ├── test_engine.py
    ├── test_towers.py
    ├── test_economy.py
    └── test_waves.py
```

## Files to Modify

- `app/main.py` — add tower defense endpoints, lifespan shop seeding
- `app/models.py` — add `game_type: "towerdefense"` support, PlayerProfile model
- `app/schemas.py` — add TD schemas
- `app/websocket.py` — add competitive TD WebSocket handler
- `static/app.js` — register tower defense in GAMES
- `static/styles.css` — TD-specific styles
- `tests/test_api.py` — extend with TD tests
- `tests/test_websocket.py` — extend with TD tests
