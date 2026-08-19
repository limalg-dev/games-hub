"""
🐜 Ant Defense - Lógica Principal do Jogo Tower Defense
Implementação das mecânicas core conforme DESIGN_DOC.md
"""

import math
import uuid
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TowerType(Enum):
    """Tipos de torres disponíveis"""
    ARCHER = "archer"  # Torre Formigueira - Ataque rápido
    BOMB = "bomb"      # Torre Explosiva - Dano em área
    ICE = "ice"        # Torre Congelante - Slow


class EnemyType(Enum):
    """Tipos de inimigos"""
    FLY = "fly"        # Mosca Veloz - Rápido e frágil
    BEETLE = "beetle"  # Besouro Tanque - Lento e resistente
    SKY_BUG = "sky_bug"  # Percevejo Voador - Balanceado


@dataclass
class Enemy:
    """Representa um inimigo no jogo"""
    id: str
    enemy_type: EnemyType
    x: float
    y: float
    hp: int
    max_hp: int
    speed: float
    base_speed: float
    reward: int
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
            "slowed": self.slowed
        }


@dataclass
class Tower:
    """Representa uma torre no jogo"""
    id: str
    tower_type: TowerType
    x: int
    y: int
    level: int = 1
    cooldown: float = 0.0
    
    @property
    def damage(self) -> Tuple[int, int]:
        """Retorna dano mínimo e máximo"""
        damages = {
            TowerType.ARCHER: (15, 25),
            TowerType.BOMB: (40, 60),
            TowerType.ICE: (8, 12)
        }
        base = damages[self.tower_type]
        # Aumenta 20% por nível
        multiplier = 1.0 + (self.level - 1) * 0.2
        return (int(base[0] * multiplier), int(base[1] * multiplier))
    
    @property
    def attack_speed(self) -> float:
        """Tempo entre ataques em segundos"""
        speeds = {
            TowerType.ARCHER: 0.8,
            TowerType.BOMB: 2.5,
            TowerType.ICE: 1.2
        }
        # Reduz cooldown com upgrade (máx 20%)
        multiplier = max(0.8, 1.0 - (self.level - 1) * 0.1)
        return speeds[self.tower_type] * multiplier
    
    @property
    def range(self) -> float:
        """Alcance da torre em células"""
        ranges = {
            TowerType.ARCHER: 3.0,
            TowerType.BOMB: 2.5,
            TowerType.ICE: 2.5
        }
        # Aumenta alcance com upgrade
        return ranges[self.tower_type] + (self.level - 1) * 0.3
    
    @property
    def cost(self) -> int:
        """Custo base da torre"""
        costs = {
            TowerType.ARCHER: 50,
            TowerType.BOMB: 120,
            TowerType.ICE: 80
        }
        return costs[self.tower_type]
    
    @property
    def sell_value(self) -> int:
        """Valor de venda (50% do custo total)"""
        total_invested = self.cost * (1 + 0.75 * (self.level - 1))
        return int(total_invested * 0.5)
    
    @property
    def upgrade_cost(self) -> int:
        """Custo para próximo nível (75% do custo base)"""
        return int(self.cost * 0.75)
    
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
            "attack_speed": round(self.attack_speed, 2)
        }


@dataclass
class WaveConfig:
    """Configuração de uma onda de inimigos"""
    wave_number: int
    enemies: List[Tuple[EnemyType, int]]  # (tipo, quantidade)
    spawn_interval: float = 1.5  # fallback interval
    # Per-group spawn intervals: maps enemy type to seconds between spawns.
    # If set, each enemy group spawns at its own rate instead of sharing
    # a single global interval.
    group_intervals: Optional[Dict[EnemyType, float]] = None

    @staticmethod
    def get_default_waves() -> List['WaveConfig']:
        """Retorna configuração padrão de 10 ondas"""
        return [
            WaveConfig(1, [(EnemyType.FLY, 5)], 2.0),
            WaveConfig(2, [(EnemyType.FLY, 8)], 1.8),
            WaveConfig(3, [(EnemyType.FLY, 6), (EnemyType.BEETLE, 2)], 1.5,
                         {EnemyType.FLY: 1.2, EnemyType.BEETLE: 3.0}),
            WaveConfig(4, [(EnemyType.FLY, 8), (EnemyType.BEETLE, 3)], 1.5,
                         {EnemyType.FLY: 1.0, EnemyType.BEETLE: 2.5}),
            WaveConfig(5, [(EnemyType.FLY, 5), (EnemyType.BEETLE, 4), (EnemyType.SKY_BUG, 2)], 1.3,
                         {EnemyType.FLY: 1.0, EnemyType.BEETLE: 2.0, EnemyType.SKY_BUG: 2.0}),
            WaveConfig(6, [(EnemyType.FLY, 10), (EnemyType.BEETLE, 5), (EnemyType.SKY_BUG, 3)], 1.2,
                         {EnemyType.FLY: 0.8, EnemyType.BEETLE: 1.8, EnemyType.SKY_BUG: 1.5}),
            WaveConfig(7, [(EnemyType.BEETLE, 8), (EnemyType.SKY_BUG, 5)], 1.0,
                         {EnemyType.BEETLE: 1.0, EnemyType.SKY_BUG: 1.2}),
            WaveConfig(8, [(EnemyType.FLY, 15), (EnemyType.BEETLE, 6), (EnemyType.SKY_BUG, 6)], 1.0,
                         {EnemyType.FLY: 0.6, EnemyType.BEETLE: 1.5, EnemyType.SKY_BUG: 1.2}),
            WaveConfig(9, [(EnemyType.BEETLE, 10), (EnemyType.SKY_BUG, 8)], 0.9,
                         {EnemyType.BEETLE: 0.9, EnemyType.SKY_BUG: 1.0}),
            WaveConfig(10, [(EnemyType.FLY, 20), (EnemyType.BEETLE, 15), (EnemyType.SKY_BUG, 10)], 0.8,
                          {EnemyType.FLY: 0.5, EnemyType.BEETLE: 0.8, EnemyType.SKY_BUG: 0.7}),
        ]


@dataclass
class GameState:
    """Estado completo do jogo"""
    id: str
    grid_width: int = 15
    grid_height: int = 10
    leaves: int = 100  # Moeda do jogo
    lives: int = 20
    current_wave: int = 0
    total_waves: int = 10
    game_over: bool = False
    victory: bool = False
    score: int = 0
    enemies_killed: int = 0
    towers_placed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "leaves": self.leaves,
            "lives": self.lives,
            "current_wave": self.current_wave,
            "total_waves": self.total_waves,
            "game_over": self.game_over,
            "victory": self.victory,
            "score": self.score,
            "enemies_killed": self.enemies_killed,
            "towers_placed": self.towers_placed
        }


class TowerDefenseGame:
    """Classe principal do jogo Tower Defense"""
    
    # Caminho padrão (coordenadas do grid)
    DEFAULT_PATH = [
        (0, 5), (1, 5), (2, 5), (3, 5), (4, 5),
        (4, 4), (4, 3), (4, 2),
        (5, 2), (6, 2), (7, 2), (8, 2),
        (8, 3), (8, 4), (8, 5), (8, 6), (8, 7),
        (9, 7), (10, 7), (11, 7), (12, 7), (13, 7), (14, 7)
    ]
    
    def __init__(self, game_id: Optional[str] = None, custom_path: Optional[List[Tuple[int, int]]] = None):
        self.state = GameState(id=game_id or str(uuid.uuid4()))
        self.path = custom_path or self.DEFAULT_PATH
        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.projectiles: List[Dict[str, Any]] = []
        self.wave_config = WaveConfig.get_default_waves()
        
        # Estado da onda atual
        self.wave_active = False
        self.wave_enemies_remaining = []
        self.spawn_timer = 0.0
        self.between_waves_timer = 0.0
        self._group_spawn_timers: Dict[EnemyType, float] = {}
        self._group_spawn_counts: Dict[EnemyType, int] = {}
        
        # Grid de ocupação (True = ocupado/caminho, False = livre)
        self.occupied_grid = [[False for _ in range(self.state.grid_height)] 
                              for _ in range(self.state.grid_width)]
        self._mark_path_as_occupied()
    
    def _mark_path_as_occupied(self):
        """Marca as células do caminho como ocupadas"""
        for x, y in self.path:
            if 0 <= x < self.state.grid_width and 0 <= y < self.state.grid_height:
                self.occupied_grid[x][y] = True
    
    def _get_enemy_stats(self, enemy_type: EnemyType) -> Dict[str, Any]:
        """Retorna estatísticas base do inimigo"""
        stats = {
            EnemyType.FLY: {"hp": 30, "speed": 2.0, "reward": 8},
            EnemyType.BEETLE: {"hp": 120, "speed": 0.8, "reward": 18},
            EnemyType.SKY_BUG: {"hp": 50, "speed": 1.5, "reward": 12}
        }
        return stats[enemy_type]
    
    def can_place_tower(self, x: int, y: int, tower_type: TowerType) -> Tuple[bool, str]:
        """Verifica se é possível colocar uma torre na posição"""
        # Verifica limites do grid
        if not (0 <= x < self.state.grid_width and 0 <= y < self.state.grid_height):
            return False, "Posição fora do grid"
        
        # Verifica se está no caminho
        if self.occupied_grid[x][y]:
            return False, "Não pode colocar torre no caminho"
        
        # Verifica se já tem torre
        for tower in self.towers:
            if tower.x == x and tower.y == y:
                return False, "Já existe uma torre nesta posição"
        
        # Verifica recursos
        tower_cost = {
            TowerType.ARCHER: 50,
            TowerType.BOMB: 120,
            TowerType.ICE: 80
        }
        if self.state.leaves < tower_cost[tower_type]:
            return False, f"Folhas insuficientes (precisa de {tower_cost[tower_type]})"
        
        return True, "OK"
    
    def place_tower(self, x: int, y: int, tower_type: TowerType) -> Tuple[bool, str, Optional[Tower]]:
        """Coloca uma torre no grid"""
        can_place, message = self.can_place_tower(x, y, tower_type)
        if not can_place:
            return False, message, None
        
        tower = Tower(
            id=str(uuid.uuid4()),
            tower_type=tower_type,
            x=x,
            y=y
        )
        self.towers.append(tower)
        self.state.leaves -= tower.cost
        self.state.towers_placed += 1
        
        return True, "Torre colocada com sucesso!", tower
    
    def sell_tower(self, tower_id: str) -> Tuple[bool, str, int]:
        """Vende uma torre e retorna valor"""
        for i, tower in enumerate(self.towers):
            if tower.id == tower_id:
                sell_value = tower.sell_value
                self.state.leaves += sell_value
                self.towers.pop(i)
                return True, f"Torre vendida por {sell_value} folhas", sell_value
        
        return False, "Torre não encontrada", 0
    
    def upgrade_tower(self, tower_id: str) -> Tuple[bool, str]:
        """Faz upgrade de uma torre"""
        for tower in self.towers:
            if tower.id == tower_id:
                if self.state.leaves >= tower.upgrade_cost:
                    self.state.leaves -= tower.upgrade_cost
                    tower.level += 1
                    return True, f"Torre upada para nível {tower.level}!"
                else:
                    return False, f"Folhas insuficientes (precisa de {tower.upgrade_cost})"
        
        return False, "Torre não encontrada"
    
    def start_wave(self) -> Tuple[bool, str]:
        """Inicia uma nova onda de inimigos"""
        if self.state.game_over or self.state.victory:
            return False, "Jogo já terminou"
        
        if self.wave_active:
            return False, "Onda já em andamento"
        
        if self.state.current_wave >= self.state.total_waves:
            return False, "Todas as ondas já foram completadas"
        
        wave_idx = self.state.current_wave
        wave_config = self.wave_config[wave_idx]
        
        # Prepara lista de inimigos para spawn
        self.wave_enemies_remaining = []
        for enemy_type, count in wave_config.enemies:
            for _ in range(count):
                self.wave_enemies_remaining.append(enemy_type)
        
        self.wave_active = True
        self.spawn_timer = 0.0
        self.state.current_wave += 1

        # Initialize per-group spawn timers if intervals are defined
        self._group_spawn_timers = {}
        self._group_spawn_counts = {}
        if wave_config.group_intervals:
            for enemy_type, count in wave_config.enemies:
                self._group_spawn_timers[enemy_type] = 0.0
                self._group_spawn_counts[enemy_type] = 0
        
        return True, f"Onda {self.state.current_wave} iniciada!"
    
    def _spawn_enemy(self, enemy_type: EnemyType):
        """Cria e adiciona um inimigo ao jogo"""
        stats = self._get_enemy_stats(enemy_type)
        start_x, start_y = self.path[0]
        
        enemy = Enemy(
            id=str(uuid.uuid4()),
            enemy_type=enemy_type,
            x=float(start_x),
            y=float(start_y),
            hp=stats["hp"],
            max_hp=stats["hp"],
            speed=stats["speed"],
            base_speed=stats["speed"],
            reward=stats["reward"]
        )
        self.enemies.append(enemy)
    
    def _distance_to_point(self, x: float, y: float, target_x: int, target_y: int) -> float:
        """Calcula distância até um ponto"""
        return math.sqrt((x - target_x) ** 2 + (y - target_y) ** 2)
    
    def _move_enemy(self, enemy: Enemy, dt: float):
        """Move o inimigo ao longo do caminho"""
        if not self.path:
            return
        
        # Encontra o próximo waypoint
        current_waypoint_idx = 0
        for i, (wx, wy) in enumerate(self.path):
            if self._distance_to_point(enemy.x, enemy.y, wx, wy) > 0.5:
                current_waypoint_idx = max(0, i - 1)
                break
            current_waypoint_idx = i
        
        if current_waypoint_idx >= len(self.path) - 1:
            # Inimigo chegou ao fim
            enemy.distance_traveled = float('inf')
            return
        
        # Move em direção ao próximo waypoint
        next_x, next_y = self.path[current_waypoint_idx + 1]
        dx = next_x - enemy.x
        dy = next_y - enemy.y
        dist = math.sqrt(dx ** 2 + dy ** 2)
        
        if dist > 0:
            move_dist = enemy.speed * dt
            enemy.x += (dx / dist) * move_dist
            enemy.y += (dy / dist) * move_dist
            enemy.distance_traveled += move_dist
    
    def _find_closest_enemy(self, tower: Tower) -> Optional[Enemy]:
        """Encontra o inimigo mais próximo dentro do alcance"""
        closest = None
        min_dist = float('inf')
        
        for enemy in self.enemies:
            dist = math.sqrt((tower.x - enemy.x) ** 2 + (tower.y - enemy.y) ** 2)
            if dist <= tower.range and dist < min_dist:
                min_dist = dist
                closest = enemy
        
        return closest
    
    def _apply_damage(self, enemy: Enemy, damage: int, tower_type: TowerType) -> Dict[str, Any]:
        """Aplica dano a um inimigo"""
        enemy.hp -= damage
        effects = []
        
        # Aplica slow se for torre de gelo
        if tower_type == TowerType.ICE:
            enemy.slowed = True
            enemy.slow_timer = 2.0
            enemy.speed = enemy.base_speed * 0.6  # 40% reduction
            effects.append("slowed")
        
        destroyed = enemy.hp <= 0
        reward = enemy.reward if destroyed else 0
        
        return {
            "enemy_id": enemy.id,
            "remaining_hp": max(0, enemy.hp),
            "destroyed": destroyed,
            "reward": reward,
            "effects": effects
        }
    
    def update(self, dt: float) -> Dict[str, Any]:
        """
        Atualiza o estado do jogo
        dt: delta time em segundos
        """
        result = {
            "attacks": [],
            "enemies_destroyed": [],
            "state_changes": []
        }
        
        if self.state.game_over or self.state.victory:
            return result
        
        # Atualiza timer de spawn
        if self.wave_active and self.wave_enemies_remaining:
            wave_config = self.wave_config[self.state.current_wave - 1]

            if wave_config.group_intervals:
                # Per-group spawn: each enemy type has its own timer
                spawned_this_tick = 0
                for enemy_type, count in wave_config.enemies:
                    if self._group_spawn_counts.get(enemy_type, 0) >= count:
                        continue
                    self._group_spawn_timers[enemy_type] = (
                        self._group_spawn_timers.get(enemy_type, 0.0) + dt
                    )
                    interval = wave_config.group_intervals[enemy_type]
                    if self._group_spawn_timers[enemy_type] >= interval:
                        self._group_spawn_timers[enemy_type] = 0.0
                        self._spawn_enemy(enemy_type)
                        self._group_spawn_counts[enemy_type] = (
                            self._group_spawn_counts.get(enemy_type, 0) + 1
                        )
                        self.wave_enemies_remaining.remove(enemy_type)
                        spawned_this_tick += 1
                        if spawned_this_tick >= 1:  # max 1 per frame per group
                            break
            else:
                # Legacy flat-interval spawn
                self.spawn_timer += dt
                if self.spawn_timer >= wave_config.spawn_interval:
                    enemy_type = self.wave_enemies_remaining.pop(0)
                    self._spawn_enemy(enemy_type)
                    self.spawn_timer = 0.0
        
        # Verifica se onda terminou
        if self.wave_active and not self.wave_enemies_remaining and not self.enemies:
            self.wave_active = False
            self.state.leaves += 25  # Bônus por completar onda
            result["state_changes"].append(f"Onda {self.state.current_wave} completada! +25 folhas")
            
            # Verifica vitória
            if self.state.current_wave >= self.state.total_waves:
                self.state.victory = True
                result["state_changes"].append("VITÓRIA! Todas as ondas completadas!")
        
        # Atualiza torres
        for tower in self.towers:
            if tower.cooldown > 0:
                tower.cooldown -= dt
            
            if tower.cooldown <= 0:
                target = self._find_closest_enemy(tower)
                if target:
                    dmg_min, dmg_max = tower.damage
                    damage = (dmg_min + dmg_max) // 2
                    
                    attack_result = self._apply_damage(target, damage, tower.tower_type)
                    
                    # Adiciona projétil visual
                    self.projectiles.append({
                        "from_x": tower.x,
                        "from_y": tower.y,
                        "to_x": target.x,
                        "to_y": target.y,
                        "type": tower.tower_type.value,
                        "lifetime": 0.3
                    })
                    
                    result["attacks"].append({
                        "tower_id": tower.id,
                        "enemy_id": target.id,
                        "damage": damage,
                        "target_x": target.x,
                        "target_y": target.y
                    })
                    
                    tower.cooldown = tower.attack_speed
        
        # Atualiza inimigos
        for enemy in self.enemies[:]:
            # Atualiza slow
            if enemy.slowed:
                enemy.slow_timer -= dt
                if enemy.slow_timer <= 0:
                    enemy.slowed = False
                    enemy.speed = enemy.base_speed
            
            # Move inimigo
            self._move_enemy(enemy, dt)
            
            # Verifica se chegou ao fim
            if enemy.distance_traveled == float('inf'):
                self.enemies.remove(enemy)
                self.state.lives -= 1
                result["state_changes"].append(f"Inimigo escapou! -1 vida")
                
                if self.state.lives <= 0:
                    self.state.game_over = True
                    result["state_changes"].append("GAME OVER! O formigueiro foi invadido!")
            
            # Verifica se morreu
            elif enemy.hp <= 0:
                self.enemies.remove(enemy)
                self.state.leaves += enemy.reward
                self.state.score += enemy.reward * 10
                self.state.enemies_killed += 1
                result["enemies_destroyed"].append({
                    "enemy_id": enemy.id,
                    "reward": enemy.reward
                })
        
        # Atualiza projéteis
        for projectile in self.projectiles[:]:
            projectile["lifetime"] -= dt
            if projectile["lifetime"] <= 0:
                self.projectiles.remove(projectile)
        
        return result
    
    def get_state(self) -> Dict[str, Any]:
        """Retorna estado completo do jogo para o cliente"""
        return {
            "state": self.state.to_dict(),
            "towers": [t.to_dict() for t in self.towers],
            "enemies": [e.to_dict() for e in self.enemies],
            "projectiles": self.projectiles,
            "path": self.path,
            "occupied_cells": [(x, y) for x in range(self.state.grid_width) 
                                      for y in range(self.state.grid_height) 
                                      if self.occupied_grid[x][y]],
            "wave_active": self.wave_active,
            "wave_enemies_remaining": len(self.wave_enemies_remaining)
        }
    
    def reset(self):
        """Reseta o jogo para o estado inicial"""
        self.__init__(game_id=self.state.id, custom_path=self.path)
