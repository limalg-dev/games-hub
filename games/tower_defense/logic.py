"""
Neon Tower Defense — Backend Logic
3 tower types with upgrades, 6 enemy types with armor/regen/boss,
progressive wave scaling, and rebalanced economy.
"""

import math
import uuid
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ═══════════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════════

class TowerType(Enum):
    ARCHER = "archer"   # Fast single-target
    BOMB = "bomb"       # Slow AoE
    ICE = "ice"         # Slow + debuff


class EnemyType(Enum):
    FLY = "fly"             # Fast, low HP, no armor
    BEETLE = "beetle"       # Slow, high HP, some armor
    SKY_BUG = "sky_bug"     # Balanced flyer
    SPRINTER = "sprinter"   # Very fast, very low HP
    TANK = "tank"           # Very slow, massive HP, high armor
    BOSS = "boss"           # Massive HP, slows towers, loses 3 lives


# ═══════════════════════════════════════════════════════════════
#  TOWER DEFINITIONS
# ═══════════════════════════════════════════════════════════════

TOWER_STATS = {
    TowerType.ARCHER: {
        "cost": 50,
        "damage": (18, 28),
        "attack_speed": 0.7,       # seconds between shots
        "range": 3.2,
        "description": "Fast single-target",
        # Per-level bonuses
        "damage_mult": [1.0, 1.25, 1.55],     # L1, L2, L3
        "speed_mult":  [1.0, 0.90, 0.80],     # faster = lower cooldown
        "range_mult":  [1.0, 1.15, 1.35],
        "special": None,
    },
    TowerType.BOMB: {
        "cost": 120,
        "damage": (45, 70),
        "attack_speed": 2.5,
        "range": 2.5,
        "aoe_radius": 1.5,         # cells
        "description": "Slow AoE damage",
        "damage_mult": [1.0, 1.3, 1.7],
        "speed_mult":  [1.0, 0.92, 0.85],
        "range_mult":  [1.0, 1.12, 1.28],
        "special": "aoe",
    },
    TowerType.ICE: {
        "cost": 80,
        "damage": (10, 16),
        "attack_speed": 1.2,
        "range": 2.8,
        "slow_factor": 0.55,       # 45% slow
        "slow_duration": 2.5,      # seconds
        "description": "Slow + debuff",
        "damage_mult": [1.0, 1.2, 1.45],
        "speed_mult":  [1.0, 0.90, 0.82],
        "range_mult":  [1.0, 1.12, 1.25],
        "special": "slow",
        # L3 bonus: stronger slow
        "slow_factor_l3": 0.40,    # 60% slow at L3
    },
}

UPGRADE_COST_FACTOR = 0.70   # 70% of base cost per upgrade
SELL_FACTOR = 0.50           # 50% of total invested
MAX_TOWER_LEVEL = 3


# ═══════════════════════════════════════════════════════════════
#  ENEMY DEFINITIONS
# ═══════════════════════════════════════════════════════════════

ENEMY_STATS = {
    EnemyType.FLY: {
        "hp": 35, "speed": 2.0, "reward": 8, "armor": 0,
        "regen": 0, "lives_cost": 1,
        "description": "Fast, fragile",
    },
    EnemyType.BEETLE: {
        "hp": 130, "speed": 0.8, "reward": 18, "armor": 3,
        "regen": 0, "lives_cost": 1,
        "description": "Slow, armored",
    },
    EnemyType.SKY_BUG: {
        "hp": 55, "speed": 1.5, "reward": 12, "armor": 1,
        "regen": 0, "lives_cost": 1,
        "description": "Balanced flyer",
    },
    EnemyType.SPRINTER: {
        "hp": 20, "speed": 3.0, "reward": 6, "armor": 0,
        "regen": 0, "lives_cost": 1,
        "description": "Very fast, very fragile",
    },
    EnemyType.TANK: {
        "hp": 280, "speed": 0.5, "reward": 30, "armor": 8,
        "regen": 2, "lives_cost": 2,
        "description": "Massive HP, heavy armor",
    },
    EnemyType.BOSS: {
        "hp": 600, "speed": 0.6, "reward": 75, "armor": 5,
        "regen": 4, "lives_cost": 3,
        "description": "Boss — loses 3 lives on reach",
    },
}

# ═══════════════════════════════════════════════════════════════
#  DIFFICULTY CONFIGS
# ═══════════════════════════════════════════════════════════════

class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    INSANE = "insane"


def _enemy_hp_mult_for_damage(base_hp: int, mult: float) -> float:
    """Helper: scale HP and return effective multiplier."""
    return base_hp * mult


DIFFICULTY_CONFIGS = {
    Difficulty.EASY: {
        "label": "Fácil",
        "start_crystals": 200,
        "start_lives": 25,
        "enemy_hp_mult": 0.7,     # -30% enemy HP
        "enemy_speed_mult": 0.85, # -15% enemy speed
        "tower_cost_mult": 0.80,  # -20% tower costs
        "enemy_armor_mult": 1.0,  # armor unchanged
        "enemy_regen_mult": 1.0,  # regen unchanged
        "permadeath": False,
        "description": "Inimigos mais fracos, mais recursos iniciais",
    },
    Difficulty.NORMAL: {
        "label": "Normal",
        "start_crystals": 150,
        "start_lives": 20,
        "enemy_hp_mult": 1.0,
        "enemy_speed_mult": 1.0,
        "tower_cost_mult": 1.0,
        "enemy_armor_mult": 1.0,
        "enemy_regen_mult": 1.0,
        "permadeath": False,
        "description": "Experiência padrão balanceada",
    },
    Difficulty.HARD: {
        "label": "Difícil",
        "start_crystals": 120,
        "start_lives": 15,
        "enemy_hp_mult": 1.4,     # +40% enemy HP
        "enemy_speed_mult": 1.15, # +15% enemy speed
        "tower_cost_mult": 1.15,  # +15% tower costs
        "enemy_armor_mult": 1.2,  # +20% armor
        "enemy_regen_mult": 1.3,  # +30% regen
        "permadeath": False,
        "description": "Inimigos mais fortes, menos recursos",
    },
    Difficulty.INSANE: {
        "label": "Insano",
        "start_crystals": 100,
        "start_lives": 10,
        "enemy_hp_mult": 2.0,     # +100% enemy HP
        "enemy_speed_mult": 1.35, # +35% enemy speed
        "tower_cost_mult": 1.30,  # +30% tower costs
        "enemy_armor_mult": 1.5,  # +50% armor
        "enemy_regen_mult": 2.0,  # +100% regen
        "permadeath": True,       # No restart — game over is final
        "description": "Sem segundas chances. Inimigos brutais.",
    },
}


# Wave scaling: HP multiplier and speed multiplier per wave number
def _wave_hp_mult(wave: int) -> float:
    """Enemy HP scales +12% per wave, starting at wave 1 = 1.0"""
    return 1.0 + (wave - 1) * 0.12

def _wave_speed_mult(wave: int) -> float:
    """Enemy speed scales +2% per wave (capped at +20%)"""
    return min(1.20, 1.0 + (wave - 1) * 0.02)


# ═══════════════════════════════════════════════════════════════
#  WAVE DEFINITIONS (15 waves)
# ═══════════════════════════════════════════════════════════════

@dataclass
class WaveConfig:
    wave_number: int
    enemies: List[Tuple[EnemyType, int]]
    spawn_interval: float = 1.5
    group_intervals: Optional[Dict[EnemyType, float]] = None
    bonus: int = 25  # crystals earned on completion

    @staticmethod
    def get_default_waves() -> List['WaveConfig']:
        return [
            # ── Early game: learn mechanics ──
            WaveConfig(1,
                [(EnemyType.FLY, 6)],
                2.0,
                bonus=30),
            WaveConfig(2,
                [(EnemyType.FLY, 8), (EnemyType.SPRINTER, 2)],
                1.8,
                {EnemyType.FLY: 1.5, EnemyType.SPRINTER: 1.0},
                bonus=30),
            WaveConfig(3,
                [(EnemyType.FLY, 6), (EnemyType.BEETLE, 2)],
                1.5,
                {EnemyType.FLY: 1.2, EnemyType.BEETLE: 3.0},
                bonus=35),

            # ── Mid game: introduce new types ──
            WaveConfig(4,
                [(EnemyType.FLY, 8), (EnemyType.BEETLE, 3), (EnemyType.SKY_BUG, 2)],
                1.4,
                {EnemyType.FLY: 1.0, EnemyType.BEETLE: 2.5, EnemyType.SKY_BUG: 2.0},
                bonus=35),
            WaveConfig(5,
                [(EnemyType.SPRINTER, 8), (EnemyType.BEETLE, 4), (EnemyType.SKY_BUG, 3)],
                1.3,
                {EnemyType.SPRINTER: 0.7, EnemyType.BEETLE: 2.0, EnemyType.SKY_BUG: 1.8},
                bonus=40),
            WaveConfig(6,
                [(EnemyType.BEETLE, 5), (EnemyType.TANK, 1), (EnemyType.SKY_BUG, 4)],
                1.2,
                {EnemyType.BEETLE: 1.5, EnemyType.TANK: 4.0, EnemyType.SKY_BUG: 1.5},
                bonus=40),

            # ── Boss wave 1 ──
            WaveConfig(7,
                [(EnemyType.FLY, 10), (EnemyType.BEETLE, 4), (EnemyType.BOSS, 1)],
                1.2,
                {EnemyType.FLY: 0.8, EnemyType.BEETLE: 2.0, EnemyType.BOSS: 5.0},
                bonus=50),

            # ── Late game: mixed waves ──
            WaveConfig(8,
                [(EnemyType.SPRINTER, 12), (EnemyType.TANK, 2), (EnemyType.SKY_BUG, 5)],
                1.0,
                {EnemyType.SPRINTER: 0.5, EnemyType.TANK: 3.0, EnemyType.SKY_BUG: 1.2},
                bonus=45),
            WaveConfig(9,
                [(EnemyType.BEETLE, 8), (EnemyType.TANK, 3), (EnemyType.SKY_BUG, 6)],
                1.0,
                {EnemyType.BEETLE: 1.0, EnemyType.TANK: 2.5, EnemyType.SKY_BUG: 1.0},
                bonus=45),
            WaveConfig(10,
                [(EnemyType.FLY, 15), (EnemyType.BEETLE, 6), (EnemyType.SPRINTER, 10)],
                0.9,
                {EnemyType.FLY: 0.5, EnemyType.BEETLE: 1.5, EnemyType.SPRINTER: 0.4},
                bonus=50),

            # ── Boss wave 2 ──
            WaveConfig(11,
                [(EnemyType.TANK, 4), (EnemyType.BOSS, 2), (EnemyType.SKY_BUG, 8)],
                1.0,
                {EnemyType.TANK: 2.0, EnemyType.BOSS: 4.0, EnemyType.SKY_BUG: 1.0},
                bonus=60),

            # ── Endgame gauntlet ──
            WaveConfig(12,
                [(EnemyType.SPRINTER, 20), (EnemyType.BEETLE, 8), (EnemyType.TANK, 3)],
                0.8,
                {EnemyType.SPRINTER: 0.3, EnemyType.BEETLE: 1.0, EnemyType.TANK: 2.0},
                bonus=50),
            WaveConfig(13,
                [(EnemyType.BEETLE, 12), (EnemyType.TANK, 5), (EnemyType.SKY_BUG, 10)],
                0.8,
                {EnemyType.BEETLE: 0.8, EnemyType.TANK: 1.8, EnemyType.SKY_BUG: 0.8},
                bonus=55),
            WaveConfig(14,
                [(EnemyType.FLY, 20), (EnemyType.SPRINTER, 15), (EnemyType.TANK, 4)],
                0.7,
                {EnemyType.FLY: 0.3, EnemyType.SPRINTER: 0.3, EnemyType.TANK: 1.5},
                bonus=55),

            # ── Final boss wave ──
            WaveConfig(15,
                [(EnemyType.TANK, 6), (EnemyType.BOSS, 3), (EnemyType.BEETLE, 10), (EnemyType.SKY_BUG, 8)],
                0.7,
                {EnemyType.TANK: 1.5, EnemyType.BOSS: 3.0, EnemyType.BEETLE: 0.7, EnemyType.SKY_BUG: 0.7},
                bonus=100),
        ]


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Enemy:
    id: str
    enemy_type: EnemyType
    x: float
    y: float
    hp: int
    max_hp: int
    speed: float
    base_speed: float
    reward: int
    armor: int = 0
    regen: float = 0.0
    lives_cost: int = 1
    slowed: bool = False
    slow_timer: float = 0.0
    distance_traveled: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.enemy_type.value,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "hp": self.hp,
            "max_hp": self.max_hp,
            "speed": round(self.speed, 2),
            "reward": self.reward,
            "armor": self.armor,
            "regen": round(self.regen, 1),
            "lives_cost": self.lives_cost,
            "slowed": self.slowed,
        }


@dataclass
class Tower:
    id: str
    tower_type: TowerType
    x: int
    y: int
    level: int = 1
    cooldown: float = 0.0

    @property
    def stats(self) -> Dict[str, Any]:
        return TOWER_STATS[self.tower_type]

    @property
    def damage(self) -> Tuple[int, int]:
        base = self.stats["damage"]
        mult = self.stats["damage_mult"][self.level - 1]
        return (int(base[0] * mult), int(base[1] * mult))

    @property
    def attack_speed(self) -> float:
        return self.stats["attack_speed"] * self.stats["speed_mult"][self.level - 1]

    @property
    def range(self) -> float:
        return self.stats["range"] * self.stats["range_mult"][self.level - 1]

    @property
    def cost(self) -> int:
        return self.stats["cost"]

    @property
    def upgrade_cost(self) -> int:
        if self.level >= MAX_TOWER_LEVEL:
            return -1  # max level
        return int(self.cost * UPGRADE_COST_FACTOR * self.level)

    @property
    def sell_value(self) -> int:
        total = self.cost
        for lvl in range(1, self.level):
            total += int(self.cost * UPGRADE_COST_FACTOR * lvl)
        return int(total * SELL_FACTOR)

    @property
    def aoe_radius(self) -> Optional[float]:
        return self.stats.get("aoe_radius")

    @property
    def slow_factor(self) -> float:
        if self.level >= 3 and "slow_factor_l3" in self.stats:
            return self.stats["slow_factor_l3"]
        return self.stats.get("slow_factor", 0.55)

    @property
    def slow_duration(self) -> float:
        base = self.stats.get("slow_duration", 2.0)
        # L3 gets longer slow
        if self.level >= 3:
            base += 0.5
        return base

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.tower_type.value,
            "x": self.x,
            "y": self.y,
            "level": self.level,
            "cooldown": round(self.cooldown, 2),
            "damage": self.damage,
            "range": round(self.range, 2),
            "attack_speed": round(self.attack_speed, 2),
            "upgrade_cost": self.upgrade_cost,
            "sell_value": self.sell_value,
            "max_level": MAX_TOWER_LEVEL,
            "aoe_radius": self.aoe_radius,
            "special": self.stats.get("special"),
        }


@dataclass
class GameState:
    id: str
    grid_width: int = 30
    grid_height: int = 25
    world_width: int = 1500   # pixels
    world_height: int = 1250  # pixels
    cell_size: int = 50       # pixels per cell
    crystals: int = 150     # Starting currency
    lives: int = 20
    current_wave: int = 0
    total_waves: int = 15
    game_over: bool = False
    victory: bool = False
    score: int = 0
    enemies_killed: int = 0
    towers_placed: int = 0
    # Time control
    time_scale: int = 1       # 1, 2, or 4
    auto_wave: bool = False   # auto-start next wave after clear
    permadeath: bool = False  # no restart on game over

    @property
    def leaves(self) -> int:
        return self.crystals

    @leaves.setter
    def leaves(self, val: int):
        self.crystals = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "world_width": self.world_width,
            "world_height": self.world_height,
            "cell_size": self.cell_size,
            "crystals": self.crystals,
            "lives": self.lives,
            "current_wave": self.current_wave,
            "total_waves": self.total_waves,
            "game_over": self.game_over,
            "victory": self.victory,
            "score": self.score,
            "enemies_killed": self.enemies_killed,
            "towers_placed": self.towers_placed,
            "time_scale": self.time_scale,
            "auto_wave": self.auto_wave,
            "permadeath": self.permadeath,
            "leaves": self.crystals,
        }


# ═══════════════════════════════════════════════════════════════
#  GAME CLASS
# ═══════════════════════════════════════════════════════════════
class TowerDefenseGame:

    def _get_enemy_stats(self, etype: EnemyType) -> Dict[str, Any]:
        return ENEMY_STATS.get(etype, {})

    @staticmethod
    def _generate_serpentine_path(gw: int = 30, gh: int = 25) -> List[Tuple[int, int]]:
        """Generate an S-curve serpentine path through the center rows."""
        path = []
        # Start off-screen left, row 3
        path.append((-1, 3))
        path.append((0, 3))

        # Horizontal run to col 28
        for x in range(1, 29):
            path.append((x, 3))
        # Down to row 7
        for y in range(4, 8):
            path.append((28, y))
        # Left to col 1
        for x in range(27, 0, -1):
            path.append((x, 7))
        # Down to row 12
        for y in range(8, 13):
            path.append((1, y))
        # Right to col 28
        for x in range(2, 29):
            path.append((x, 12))
        # Down to row 16
        for y in range(13, 17):
            path.append((28, y))
        # Left to col 1
        for x in range(27, 0, -1):
            path.append((x, 16))
        # Down to row 21
        for y in range(17, 22):
            path.append((1, y))
        # Right to exit off-screen
        for x in range(2, gw):
            path.append((x, 21))
        path.append((gw, 21))

        return path

    @staticmethod
    def _generate_terrain(path: List[Tuple[int, int]],
                          gw: int, gh: int) -> List[List[int]]:
        """Generate terrain matrix: 0=path, 1=buildable, 2=blocked."""
        # Initialize all as blocked
        terrain = [[2 for _ in range(gw)] for _ in range(gh)]

        # Mark path cells
        for x, y in path:
            if 0 <= x < gw and 0 <= y < gh:
                terrain[y][x] = 0

        # Mark buildable cells: empty cells adjacent to path
        # Also mark some decorative blocked cells (scenery)
        path_set = set(path)
        for y in range(gh):
            for x in range(gw):
                if (x, y) in path_set or terrain[y][x] == 0:
                    continue
                # Check if adjacent to any path cell
                is_adjacent = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in path_set:
                        is_adjacent = True
                        break
                if is_adjacent:
                    terrain[y][x] = 1  # buildable
                else:
                    # Two cells away from path = buildable
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            if (x + dx, y + dy) in path_set:
                                terrain[y][x] = 1
                                break
                        if terrain[y][x] == 1:
                            break

        return terrain

    def __init__(self, game_id: Optional[str] = None,
                 custom_path: Optional[List[Tuple[int, int]]] = None,
                 grid_width: int = 30, grid_height: int = 25,
                 difficulty: Difficulty = Difficulty.NORMAL):
        diff_cfg = DIFFICULTY_CONFIGS[difficulty]
        self.difficulty = difficulty
        self.diff_config = diff_cfg

        self.state = GameState(id=game_id or str(uuid.uuid4()),
                               grid_width=grid_width,
                               grid_height=grid_height,
                               world_width=grid_width * 50,
                               world_height=grid_height * 50,
                               crystals=diff_cfg["start_crystals"],
                               lives=diff_cfg["start_lives"],
                               permadeath=diff_cfg["permadeath"])
        self.path = custom_path or self._generate_serpentine_path(
            grid_width, grid_height)
        self.terrain = self._generate_terrain(
            self.path, grid_width, grid_height)
        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.projectiles: List[Dict[str, Any]] = []
        self.wave_config = WaveConfig.get_default_waves()

        self.wave_active = False
        self.wave_enemies_remaining: List[EnemyType] = []
        self.spawn_timer = 0.0
        self._group_spawn_timers: Dict[EnemyType, float] = {}
        self._group_spawn_counts: Dict[EnemyType, int] = {}
        self.auto_wave_timer: float = 0.0  # countdown for auto-wave

        self.occupied_grid = [
            [False for _ in range(grid_height)]
            for _ in range(grid_width)
        ]
        self._mark_path_as_occupied()

    # ── Grid helpers ────────────────────────────────────────────

    def _mark_path_as_occupied(self):
        for x, y in self.path:
            if 0 <= x < self.state.grid_width and 0 <= y < self.state.grid_height:
                self.occupied_grid[x][y] = True

    # ── Tower management ────────────────────────────────────────

    def can_place_tower(self, x: int, y: int, tower_type: TowerType) -> Tuple[bool, str]:
        if not (0 <= x < self.state.grid_width and 0 <= y < self.state.grid_height):
            return False, "Position out of grid"
        if self.occupied_grid[x][y]:
            return False, "Cannot place on path"
        # Check terrain: only type 1 (buildable) allows placement
        if self.terrain[y][x] != 1:
            return False, "Cannot build here (blocked terrain)"
        for t in self.towers:
            if t.x == x and t.y == y:
                return False, "Tower already here"
        cost = int(TOWER_STATS[tower_type]["cost"] * self.diff_config["tower_cost_mult"])
        if self.state.crystals < cost:
            return False, f"Not enough crystals (need {cost})"
        return True, "OK"

    def place_tower(self, x: int, y: int, tower_type: TowerType
                    ) -> Tuple[bool, str, Optional[Tower]]:
        ok, msg = self.can_place_tower(x, y, tower_type)
        if not ok:
            return False, msg, None
        tower = Tower(id=str(uuid.uuid4()), tower_type=tower_type, x=x, y=y)
        self.towers.append(tower)
        cost = int(TOWER_STATS[tower_type]["cost"] * self.diff_config["tower_cost_mult"])
        self.state.crystals -= cost
        self.state.towers_placed += 1
        return True, "Tower placed!", tower

    def sell_tower(self, tower_id: str) -> Tuple[bool, str, int]:
        for i, t in enumerate(self.towers):
            if t.id == tower_id:
                val = t.sell_value
                self.state.crystals += val
                self.towers.pop(i)
                return True, f"Sold for {val} crystals", val
        return False, "Tower not found", 0

    def upgrade_tower(self, tower_id: str) -> Tuple[bool, str]:
        for t in self.towers:
            if t.id == tower_id:
                if t.level >= MAX_TOWER_LEVEL:
                    return False, "Tower already at max level"
                cost = t.upgrade_cost
                if self.state.crystals < cost:
                    return False, f"Not enough crystals (need {cost})"
                self.state.crystals -= cost
                t.level += 1
                return True, f"Tower upgraded to level {t.level}!"
        return False, "Tower not found"

    # ── Time control ────────────────────────────────────────────

    def set_time_scale(self, scale: int) -> Tuple[bool, str]:
        if scale not in (1, 2, 4):
            return False, "Speed must be 1, 2, or 4"
        self.state.time_scale = scale
        return True, f"Speed set to {scale}x"

    def toggle_auto_wave(self) -> Tuple[bool, str]:
        self.state.auto_wave = not self.state.auto_wave
        self.auto_wave_timer = 0.0
        status = "ON" if self.state.auto_wave else "OFF"
        return True, f"Auto-wave {status}"

    # ── Wave management ─────────────────────────────────────────

    def start_wave(self) -> Tuple[bool, str]:
        if self.state.game_over or self.state.victory:
            return False, "Game already ended"
        if self.wave_active:
            return False, "Wave already in progress"
        if self.state.current_wave >= self.state.total_waves:
            return False, "All waves completed"

        cfg = self.wave_config[self.state.current_wave]
        self.wave_enemies_remaining = []
        for etype, count in cfg.enemies:
            for _ in range(count):
                self.wave_enemies_remaining.append(etype)

        self.wave_active = True
        self.spawn_timer = 0.0
        self.state.current_wave += 1

        self._group_spawn_timers = {}
        self._group_spawn_counts = {}
        if cfg.group_intervals:
            for etype, count in cfg.enemies:
                self._group_spawn_timers[etype] = 0.0
                self._group_spawn_counts[etype] = 0

        return True, f"Wave {self.state.current_wave} started!"

    def _spawn_enemy(self, enemy_type: EnemyType):
        base = ENEMY_STATS[enemy_type]
        wave = self.state.current_wave
        hp_mult = _wave_hp_mult(wave)
        spd_mult = _wave_speed_mult(wave)
        diff_hp = self.diff_config["enemy_hp_mult"]
        diff_spd = self.diff_config["enemy_speed_mult"]

        hp = int(base["hp"] * hp_mult * diff_hp)
        speed = base["speed"] * spd_mult * diff_spd
        armor = int(base["armor"] * self.diff_config.get("enemy_armor_mult", 1.0))
        regen = base["regen"] * self.diff_config.get("enemy_regen_mult", 1.0)

        sx, sy = self.path[0]
        enemy = Enemy(
            id=str(uuid.uuid4()),
            enemy_type=enemy_type,
            x=float(sx), y=float(sy),
            hp=hp, max_hp=hp,
            speed=speed, base_speed=speed,
            reward=base["reward"],
            armor=armor,
            regen=regen,
            lives_cost=base["lives_cost"],
        )
        self.enemies.append(enemy)

    # ── Combat ──────────────────────────────────────────────────

    def _find_targets(self, tower: Tower) -> List[Enemy]:
        """Find enemies in range, sorted by distance (closest first)."""
        targets = []
        tx, ty = tower.x, tower.y
        rng = tower.range
        for e in self.enemies:
            d = math.sqrt((tx - e.x) ** 2 + (ty - e.y) ** 2)
            if d <= rng:
                targets.append((d, e))
        targets.sort(key=lambda t: t[0])
        return [e for _, e in targets]

    def _apply_damage(self, enemy: Enemy, raw_damage: int,
                      tower: Tower) -> Dict[str, Any]:
        """Apply damage after armor, return result dict."""
        effective = max(1, raw_damage - enemy.armor)
        enemy.hp -= effective
        effects = []

        # Slow effect (ice tower)
        if tower.tower_type == TowerType.ICE:
            enemy.slowed = True
            enemy.slow_timer = tower.slow_duration
            enemy.speed = enemy.base_speed * tower.slow_factor
            effects.append("slowed")

        destroyed = enemy.hp <= 0
        return {
            "enemy_id": enemy.id,
            "damage": effective,
            "raw_damage": raw_damage,
            "armor_blocked": raw_damage - effective,
            "remaining_hp": max(0, enemy.hp),
            "destroyed": destroyed,
            "reward": enemy.reward if destroyed else 0,
            "effects": effects,
        }

    # ── Movement ────────────────────────────────────────────────

    def _move_enemy(self, enemy: Enemy, dt: float):
        if not self.path:
            return

        # Find current waypoint
        wp_idx = 0
        for i, (wx, wy) in enumerate(self.path):
            if self._distance(enemy.x, enemy.y, wx, wy) > 0.5:
                wp_idx = max(0, i - 1)
                break
            wp_idx = i

        if wp_idx >= len(self.path) - 1:
            enemy.distance_traveled = float('inf')
            return

        nx, ny = self.path[wp_idx + 1]
        dx, dy = nx - enemy.x, ny - enemy.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            move = enemy.speed * dt
            enemy.x += (dx / dist) * move
            enemy.y += (dy / dist) * move
            enemy.distance_traveled += move

    @staticmethod
    def _distance(x1, y1, x2, y2):
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    # ── Main update loop ────────────────────────────────────────

    def update(self, dt: float) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "attacks": [],
            "enemies_destroyed": [],
            "state_changes": [],
        }

        if self.state.game_over or self.state.victory:
            return result

        # ── Apply time scale ──
        scaled_dt = dt * self.state.time_scale

        # ── Spawn enemies ──
        if self.wave_active and self.wave_enemies_remaining:
            cfg = self.wave_config[self.state.current_wave - 1]
            if cfg.group_intervals:
                spawned = 0
                for etype, count in cfg.enemies:
                    if self._group_spawn_counts.get(etype, 0) >= count:
                        continue
                    self._group_spawn_timers[etype] = (
                        self._group_spawn_timers.get(etype, 0.0) + scaled_dt
                    )
                    interval = cfg.group_intervals[etype]
                    if self._group_spawn_timers[etype] >= interval:
                        self._group_spawn_timers[etype] = 0.0
                        self._spawn_enemy(etype)
                        self._group_spawn_counts[etype] = (
                            self._group_spawn_counts.get(etype, 0) + 1
                        )
                        self.wave_enemies_remaining.remove(etype)
                        spawned += 1
                        if spawned >= 1:
                            break
            else:
                self.spawn_timer += scaled_dt
                if self.spawn_timer >= cfg.spawn_interval:
                    etype = self.wave_enemies_remaining.pop(0)
                    self._spawn_enemy(etype)
                    self.spawn_timer = 0.0

        # ── Wave complete check ──
        if (self.wave_active
                and not self.wave_enemies_remaining
                and not self.enemies):
            self.wave_active = False
            cfg = self.wave_config[self.state.current_wave - 1]
            bonus = cfg.bonus
            # Interest: 5% of savings, max 30 bonus
            interest = min(30, int(self.state.crystals * 0.05))
            total_gain = bonus + interest
            self.state.crystals += total_gain
            result["state_changes"].append(
                f"Wave {self.state.current_wave} complete! +{bonus}💎 +{interest}💎 interest"
            )
            if self.state.current_wave >= self.state.total_waves:
                self.state.victory = True
                result["state_changes"].append("VICTORY! All waves cleared!")

        # ── Tower attacks ──
        for tower in self.towers:
            if tower.cooldown > 0:
                tower.cooldown -= scaled_dt
            if tower.cooldown <= 0:
                targets = self._find_targets(tower)
                if not targets:
                    continue

                if tower.aoe_radius:
                    # Bomb: hit ALL enemies in range
                    dmg_min, dmg_max = tower.damage
                    damage = (dmg_min + dmg_max) // 2
                    for target in targets:
                        res = self._apply_damage(target, damage, tower)
                        self.projectiles.append({
                            "from_x": tower.x, "from_y": tower.y,
                            "to_x": target.x, "to_y": target.y,
                            "type": tower.tower_type.value,
                            "lifetime": 0.3,
                        })
                        result["attacks"].append({
                            "tower_id": tower.id,
                            "enemy_id": target.id,
                            "damage": res["damage"],
                            "target_x": target.x,
                            "target_y": target.y,
                        })
                else:
                    # Single target: hit closest
                    target = targets[0]
                    dmg_min, dmg_max = tower.damage
                    damage = (dmg_min + dmg_max) // 2
                    res = self._apply_damage(target, damage, tower)
                    self.projectiles.append({
                        "from_x": tower.x, "from_y": tower.y,
                        "to_x": target.x, "to_y": target.y,
                        "type": tower.tower_type.value,
                        "lifetime": 0.3,
                    })
                    result["attacks"].append({
                        "tower_id": tower.id,
                        "enemy_id": target.id,
                        "damage": res["damage"],
                        "target_x": target.x,
                        "target_y": target.y,
                    })

                tower.cooldown = tower.attack_speed

        # ── Enemy update ──
        for enemy in self.enemies[:]:
            # Regeneration
            if enemy.regen > 0 and enemy.hp < enemy.max_hp:
                enemy.hp = min(enemy.max_hp, enemy.hp + enemy.regen * scaled_dt)

            # Slow decay
            if enemy.slowed:
                enemy.slow_timer -= scaled_dt
                if enemy.slow_timer <= 0:
                    enemy.slowed = False
                    enemy.speed = enemy.base_speed

            # Movement
            self._move_enemy(enemy, scaled_dt)

            # Reached end
            if enemy.distance_traveled == float('inf'):
                self.enemies.remove(enemy)
                self.state.lives -= enemy.lives_cost
                result["state_changes"].append(
                    f"Enemy escaped! -{enemy.lives_cost} lives"
                )
                if self.state.lives <= 0:
                    self.state.game_over = True
                    result["state_changes"].append("GAME OVER!")

            # Killed
            elif enemy.hp <= 0:
                self.enemies.remove(enemy)
                self.state.crystals += enemy.reward
                self.state.score += enemy.reward * 10
                self.state.enemies_killed += 1
                result["enemies_destroyed"].append({
                    "enemy_id": enemy.id,
                    "reward": enemy.reward,
                })

        # ── Auto-wave countdown ──
        if (not self.wave_active
                and self.state.auto_wave
                and not self.state.game_over
                and not self.state.victory
                and self.state.current_wave < self.state.total_waves):
            self.auto_wave_timer += scaled_dt
            if self.auto_wave_timer >= 3.0:  # 3 second delay
                self.auto_wave_timer = 0.0
                success, msg = self.start_wave()
                if success:
                    result["state_changes"].append(msg)
        else:
            self.auto_wave_timer = 0.0

        # ── Projectile cleanup ──
        for p in self.projectiles[:]:
            p["lifetime"] -= scaled_dt
            if p["lifetime"] <= 0:
                self.projectiles.remove(p)

        return result

    # ── State serialization ─────────────────────────────────────

    def get_state(self) -> Dict[str, Any]:
        state_dict = self.state.to_dict()
        # Inject difficulty info into state dict for frontend consumption
        state_dict["difficulty"] = self.difficulty.value
        state_dict["difficulty_label"] = self.diff_config["label"]
        state_dict["tower_cost_mult"] = self.diff_config["tower_cost_mult"]
        state_dict["permadeath"] = self.state.permadeath
        return {
            "state": state_dict,
            "towers": [t.to_dict() for t in self.towers],
            "enemies": [e.to_dict() for e in self.enemies],
            "projectiles": self.projectiles,
            "path": self.path,
            "terrain": self.terrain,
            "occupied_cells": [
                (x, y)
                for x in range(self.state.grid_width)
                for y in range(self.state.grid_height)
                if self.occupied_grid[x][y]
            ],
            "wave_active": self.wave_active,
            "wave_enemies_remaining": len(self.wave_enemies_remaining),
        }

    def reset(self):
        saved_scale = self.state.time_scale
        saved_auto = self.state.auto_wave
        saved_diff = self.difficulty
        self.__init__(
            game_id=self.state.id,
            custom_path=self.path,
            grid_width=self.state.grid_width,
            grid_height=self.state.grid_height,
            difficulty=saved_diff,
        )
        self.state.time_scale = saved_scale
        self.state.auto_wave = saved_auto
