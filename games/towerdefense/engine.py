from typing import List, Tuple, Dict, Optional
from games.towerdefense.pathfinding import astar
from games.towerdefense.towers import get_tower_stats, get_combo_bonus
from games.towerdefense.waves import get_wave


class Enemy:
    def __init__(self, hp: int, speed: float, path: List[Tuple[int, int]], enemy_type: str, **kwargs):
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.path = path
        self.path_index = 0
        self.x = float(path[0][0])
        self.y = float(path[0][1])
        self.type = enemy_type
        self.alive = True
        self.reached_base = False
        for k, v in kwargs.items():
            setattr(self, k, v)


class Projectile:
    def __init__(self, x: float, y: float, target: Enemy, damage: int, tower_type: str, **kwargs):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.tower_type = tower_type
        self.speed = 8.0
        for k, v in kwargs.items():
            setattr(self, k, v)


class Tower:
    def __init__(self, tower_type: str, row: int, col: int, level: int = 1):
        self.type = tower_type
        self.row = row
        self.col = col
        self.level = level
        stats = get_tower_stats(tower_type, level)
        self.damage = stats["damage"]
        self.range = stats["range"]
        self.fire_rate = stats.get("fire_rate", 1.0)
        self.cooldown = 0.0
        for k, v in stats.items():
            if k not in ("damage", "range", "fire_rate"):
                setattr(self, k, v)


class GameEngine:
    def __init__(self, map_config: dict):
        self.grid = map_config["grid"]
        self.spawn = map_config["spawn"]
        self.base = map_config["base"]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.lives = 20
        self.gold = 200
        self.wave = 0
        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.tower_grid: Dict[Tuple[int, int], Tower] = {}

    def can_place(self, row: int, col: int) -> bool:
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return False
        if self.grid[row][col] != 0:
            return False
        if (row, col) in self.tower_grid:
            return False
        test_grid = [r[:] for r in self.grid]
        test_grid[row][col] = 1
        return astar(test_grid, self.spawn, self.base) is not None

    def place_tower(self, tower_type: str, row: int, col: int, cost: int) -> bool:
        if not self.can_place(row, col):
            return False
        if self.gold < cost:
            return False
        self.gold -= cost
        tower = Tower(tower_type, row, col)
        self.towers.append(tower)
        self.tower_grid[(row, col)] = tower
        return True

    def start_wave(self):
        self.wave += 1
        wave_config = get_wave(self.wave)
        ec = wave_config["enemies"]
        path = astar(self.grid, self.spawn, self.base)
        if not path:
            return
        for _ in range(ec["count"]):
            self.enemies.append(Enemy(ec["hp"], ec["speed"], list(path), ec["type"]))
        if wave_config["boss"]:
            bc = wave_config["boss"]
            self.enemies.append(Enemy(bc["hp"], bc["speed"], list(path), bc["type"]))

    def update(self, dt: float):
        for tower in self.towers:
            tower.cooldown -= dt
            if tower.cooldown <= 0:
                target = self._find_target(tower)
                if target:
                    self.projectiles.append(Projectile(
                        float(tower.row), float(tower.col), target, tower.damage, tower.type
                    ))
                    tower.cooldown = tower.fire_rate

        for proj in list(self.projectiles):
            dx = proj.target.x - proj.x
            dy = proj.target.y - proj.y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < 0.3:
                proj.target.hp -= proj.damage
                if proj.target.hp <= 0:
                    proj.target.alive = False
                    self.gold += 10
                self.projectiles.remove(proj)
            else:
                proj.x += (dx / dist) * proj.speed * dt
                proj.y += (dy / dist) * proj.speed * dt

        for enemy in list(self.enemies):
            if not enemy.alive:
                self.enemies.remove(enemy)
                continue
            if enemy.path_index < len(enemy.path) - 1:
                target = enemy.path[enemy.path_index + 1]
                dx = target[0] - enemy.x
                dy = target[1] - enemy.y
                dist = (dx * dx + dy * dy) ** 0.5
                move = enemy.speed * dt
                if move >= dist:
                    enemy.x = float(target[0])
                    enemy.y = float(target[1])
                    enemy.path_index += 1
                else:
                    enemy.x += (dx / dist) * move
                    enemy.y += (dy / dist) * move
            else:
                enemy.reached_base = True
                enemy.alive = False
                self.lives -= 1

        self.enemies = [e for e in self.enemies if e.alive]

    def _find_target(self, tower: Tower) -> Optional[Enemy]:
        best = None
        best_dist = float('inf')
        for enemy in self.enemies:
            dx = enemy.x - tower.row
            dy = enemy.y - tower.col
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= tower.range and dist < best_dist:
                best = enemy
                best_dist = dist
        return best
