# Tower Defense Map & Zoom Level Design Spec

> **Status:** Approved
> **Target:** `games/tower_defense/` (`logic.py`, `test_tower_defense_logic.py`, `static/index.html`)
> **Goal:** Overhaul the Tower Defense map pathing and build slot layout to align with industry benchmarks (Kingdom Rush, Bloons TD), ensuring tactical chokepoints, double-coverage curve pockets, and base defense slots. Upgrade camera zoom to 3.0x max with smooth zooming and visual polish.

---

## 1. Map Layout & Pathing Design

### 1.1 Pathing Architecture (Organic Double-Loop Ant Trail)
The map uses a 30×25 grid (1500×1250 world pixels) with smooth Catmull-Rom spline interpolation. The new waypoint geometry creates **3 high-impact tactical zones**:

```
[Entry: Top-Left (-1, 4)]
       │
       ▼ (Curve 1: The High Ridge)
   (7, 3) ──► (15, 3) ──► (23, 4)
                            │
                            ▼ (Loop Alpha: Chokepoint 1)
   (10, 8) ◄── (18, 9) ◄── (27, 8)
      │
      ▼ (Loop Beta: Central Gauntlet - Double-lap overlap)
   (4, 13) ──► (14, 13) ──► (24, 14)
                              │
                              ▼ (The Hairpin Turn)
   (8, 19) ◄── (16, 18) ◄── (27, 18)
      │
      ▼ (Final Approach: Last Stand)
   (3, 21) ──► (12, 22) ──► (22, 22) ──► [Anthill Base: (31, 21)]
```

### 1.2 Strategic Build Slot Categorization (44 Tactical Slots)
Slots are placed in high-leverage geometric positions:

1. **Inner Curve Pockets (Apex Slots):** Inside hairpin bends, granting towers 270°–360° firing arcs.
2. **Gauntlet Chokepoints (Dual-Lap Overlap):** Placed between upper and lower trail segments, allowing a single AoE or Slow tower to attack enemies twice.
3. **Last Stand Base Perimeter:** 4 dedicated slots guarding the colony entrance for emergency clutches.

---

## 2. Camera Zoom Specification

- **Max Zoom:** `3.0x` (300% magnification for inspecting combat details and tower micro).
- **Min Zoom:** `0.35x` (Full map view fit).
- **Default Zoom:** `0.75x`.
- **Zoom Step:** Factor `1.10` per mouse wheel tick or touch pinch increment for smooth zooming.
- **Minimap Viewport Indicator:** Accurately scales with 3.0x zoom and displays real-time camera position.

---

## 3. Verification & Testing Strategy
- Unit tests in `games/tower_defense/test_tower_defense_logic.py`:
  - Verify path generation continuity and boundary safety.
  - Verify all 44 build slots are on buildable terrain (type 1) and never overlap path (type 0) or obstacles (type 2).
  - Verify tower placement succeeds on all slots.
- Frontend verification:
  - Verify 3.0x max zoom on canvas.
  - Verify smooth panning, pinch-zoom, and range rendering at 3.0x.
