"""
Ant Defense - Tower Defense Game Logic
Formigas defendendo o formigueiro contra invasores
"""

import math
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class EnemyType(Enum):
    APHID = "aphid"  # Rápido e frágil
    BEETLE = "beetle"  # Lento e tanque
    FLY = "fly"  # Voador (ignora terreno)


class TowerType(Enum):
    MANDIBLE = "mandible"  # Ataque rápido, alvo único
    ACID = "acid"  # Dano em área, lento
    WEB = "web"  # Desaceleração


@dataclass
class Enemy:
    id: int
    enemy_type: EnemyType
    x: float
    y: float
    path_index: float  # Posição no caminho (0.0 a 1.0)
    health: float
    max_health: float
    speed: float
    reward: int
    slowed: bool = False
    slow_timer: float = 0.0
    
    @classmethod
    def create(cls, enemy_id: int, enemy_type: EnemyType, path_length: float) -> 'Enemy':
        """Cria um inimigo com atributos baseados no tipo"""
        if enemy_type == EnemyType.APHID:
            return cls(
                id=enemy_id,
                enemy_type=enemy_type,
                x=0, y=0,
                path_index=0.0,
                health=30.0,
                max_health=30.0,
                speed=120.0,  # Unidades por segundo
                reward=5,
                slowed=False
            )
        elif enemy_type == EnemyType.BEETLE:
            return cls(
                id=enemy_id,
                enemy_type=enemy_type,
                x=0, y=0,
                path_index=0.0,
                health=100.0,
                max_health=100.0,
                speed=40.0,
                reward=15,
                slowed=False
            )
        elif enemy_type == EnemyType.FLY:
            return cls(
                id=enemy_id,
                enemy_type=enemy_type,
                x=0, y=0,
                path_index=0.0,
                health=50.0,
                max_health=50.0,
                speed=80.0,
                reward=10,
                slowed=False
            )
        raise ValueError(f"Tipo de inimigo desconhecido: {enemy_type}")
    
    def take_damage(self, damage: float) -> bool:
        """Aplica dano e retorna True se morreu"""
        self.health -= damage
        return self.health <= 0
    
    def apply_slow(self, slow_factor: float, duration: float):
        """Aplica efeito de desaceleração"""
        self.slowed = True
        self.slow_timer = duration
        self.current_speed = self.speed * slow_factor
    
    def update_slow(self, dt: float):
        """Atualiza timer de desaceleração"""
        if self.slowed:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.slowed = False


@dataclass
class Tower:
    id: int
    tower_type: TowerType
    x: float
    y: float
    grid_x: int
    grid_y: int
    range_radius: float
    damage: float
    attack_speed: float  # Ataques por segundo
    attack_timer: float = 0.0
    cost: int = 0
    target_enemy_id: Optional[int] = None
    
    @classmethod
    def create(cls, tower_id: int, tower_type: TowerType, grid_x: int, grid_y: int, 
               cell_size: float = 40.0) -> 'Tower':
        """Cria uma torre com atributos baseados no tipo"""
        x = grid_x * cell_size + cell_size / 2
        y = grid_y * cell_size + cell_size / 2
        
        if tower_type == TowerType.MANDIBLE:
            return cls(
                id=tower_id,
                tower_type=tower_type,
                x=x, y=y,
                grid_x=grid_x,
                grid_y=grid_y,
                range_radius=120.0,
                damage=15.0,
                attack_speed=2.0,  # 2 ataques por segundo
                attack_timer=0.0,
                cost=50
            )
        elif tower_type == TowerType.ACID:
            return cls(
                id=tower_id,
                tower_type=tower_type,
                x=x, y=y,
                grid_x=grid_x,
                grid_y=grid_y,
                range_radius=100.0,
                damage=40.0,
                attack_speed=0.5,  # 1 ataque a cada 2 segundos
                attack_timer=0.0,
                cost=80
            )
        elif tower_type == TowerType.WEB:
            return cls(
                id=tower_id,
                tower_type=tower_type,
                x=x, y=y,
                grid_x=grid_x,
                grid_y=grid_y,
                range_radius=90.0,
                damage=5.0,
                attack_speed=1.0,
                attack_timer=0.0,
                cost=60
            )
        raise ValueError(f"Tipo de torre desconhecido: {tower_type}")
    
    def find_closest_enemy(self, enemies: List[Enemy]) -> Optional[Enemy]:
        """Encontra o inimigo mais próximo dentro do alcance"""
        closest = None
        min_distance = self.range_radius
        
        for enemy in enemies:
            distance = math.sqrt((enemy.x - self.x)**2 + (enemy.y - self.y)**2)
            if distance <= self.range_radius and distance < min_distance:
                min_distance = distance
                closest = enemy
        
        return closest
    
    def update(self, dt: float, enemies: List[Enemy]) -> Optional[Tuple[Enemy, float]]:
        """
        Atualiza a torre e retorna (inimigo_alvo, dano) se atacou
        """
        self.attack_timer += dt
        
        # Verifica cooldown de ataque
        attack_interval = 1.0 / self.attack_speed
        if self.attack_timer < attack_interval:
            return None
        
        # Encontra inimigo mais próximo
        target = self.find_closest_enemy(enemies)
        
        if target is not None:
            self.attack_timer = 0.0
            self.target_enemy_id = target.id
            
            # Aplica efeito especial para torre Web
            if self.tower_type == TowerType.WEB:
                target.apply_slow(slow_factor=0.5, duration=2.0)
            
            return (target, self.damage)
        
        return None


@dataclass
class Wave:
    wave_number: int
    enemies: List[Dict]  # Lista de {type, count, spawn_interval}
    spawn_timer: float = 0.0
    enemies_spawned: int = 0
    completed: bool = False


@dataclass
class GameState:
    gold: int = 100
    lives: int = 20
    wave_number: int = 0
    score: int = 0
    game_over: bool = False
    paused: bool = False
    
    # Grid do jogo
    grid_width: int = 15
    grid_height: int = 10
    cell_size: float = 40.0
    
    # Entidades
    towers: List[Tower] = field(default_factory=list)
    enemies: List[Enemy] = field(default_factory=list)
    projectiles: List[Dict] = field(default_factory=list)  # {x, y, target_id, damage, speed}
    
    # Caminho dos inimigos (lista de pontos)
    path: List[Tuple[float, float]] = field(default_factory=list)
    path_length: float = 0.0
    
    # Wave atual
    current_wave: Optional[Wave] = None
    wave_active: bool = False
    enemy_id_counter: int = 0
    tower_id_counter: int = 0
    
    def __post_init__(self):
        if not self.path:
            self.generate_default_path()
    
    def generate_default_path(self):
        """Gera um caminho padrão em forma de S"""
        self.path = [
            (0, 2),
            (4, 2),
            (4, 7),
            (10, 7),
            (10, 3),
            (14, 3)
        ]
        
        # Calcula comprimento total do caminho
        self.path_length = 0.0
        for i in range(len(self.path) - 1):
            p1 = self.path[i]
            p2 = self.path[i + 1]
            dx = (p2[0] - p1[0]) * self.cell_size
            dy = (p2[1] - p1[1]) * self.cell_size
            self.path_length += math.sqrt(dx**2 + dy**2)
    
    def get_position_on_path(self, progress: float) -> Tuple[float, float]:
        """Retorna posição (x, y) no caminho baseado no progresso (0.0 a 1.0)"""
        if not self.path or progress <= 0:
            p = self.path[0]
            return (p[0] * self.cell_size, p[1] * self.cell_size)
        
        if progress >= 1.0:
            p = self.path[-1]
            return (p[0] * self.cell_size, p[1] * self.cell_size)
        
        target_distance = progress * self.path_length
        current_distance = 0.0
        
        for i in range(len(self.path) - 1):
            p1 = self.path[i]
            p2 = self.path[i + 1]
            
            dx = (p2[0] - p1[0]) * self.cell_size
            dy = (p2[1] - p1[1]) * self.cell_size
            segment_length = math.sqrt(dx**2 + dy**2)
            
            if current_distance + segment_length >= target_distance:
                # Interpola neste segmento
                remaining = target_distance - current_distance
                t = remaining / segment_length if segment_length > 0 else 0
                
                x = (p1[0] + t * (p2[0] - p1[0])) * self.cell_size
                y = (p1[1] + t * (p2[1] - p1[1])) * self.cell_size
                return (x, y)
            
            current_distance += segment_length
        
        p = self.path[-1]
        return (p[0] * self.cell_size, p[1] * self.cell_size)
    
    def can_place_tower(self, grid_x: int, grid_y: int) -> Tuple[bool, str]:
        """Verifica se pode colocar torre na posição"""
        # Verifica limites do grid
        if grid_x < 0 or grid_x >= self.grid_width:
            return False, "Fora do grid (x)"
        if grid_y < 0 or grid_y >= self.grid_height:
            return False, "Fora do grid (y)"
        
        # Verifica se já tem torre
        for tower in self.towers:
            if tower.grid_x == grid_x and tower.grid_y == grid_y:
                return False, "Já existe uma torre aqui"
        
        # Verifica se está no caminho
        cell_center_x = grid_x * self.cell_size + self.cell_size / 2
        cell_center_y = grid_y * self.cell_size + self.cell_size / 2
        
        # Verifica proximidade com o caminho
        for i in range(len(self.path) - 1):
            p1 = self.path[i]
            p2 = self.path[i + 1]
            
            # Converte para coordenadas absolutas
            x1, y1 = p1[0] * self.cell_size, p1[1] * self.cell_size
            x2, y2 = p2[0] * self.cell_size, p2[1] * self.cell_size
            
            # Distância do ponto ao segmento de linha
            distance = self._point_to_segment_distance(
                cell_center_x, cell_center_y, x1, y1, x2, y2
            )
            
            if distance < self.cell_size * 0.8:  # Margem de segurança
                return False, "Não pode construir no caminho"
        
        return True, "OK"
    
    def _point_to_segment_distance(self, px: float, py: float, 
                                    x1: float, y1: float, x2: float, y2: float) -> float:
        """Calcula distância de ponto a segmento de linha"""
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return math.sqrt((px - x1)**2 + (py - y1)**2)
        
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx**2 + dy**2)))
        
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)
    
    def place_tower(self, grid_x: int, grid_y: int, tower_type: TowerType) -> Tuple[bool, str]:
        """Tenta colocar uma torre"""
        can_place, reason = self.can_place_tower(grid_x, grid_y)
        if not can_place:
            return False, reason
        
        tower_cost = 0
        if tower_type == TowerType.MANDIBLE:
            tower_cost = 50
        elif tower_type == TowerType.ACID:
            tower_cost = 80
        elif tower_type == TowerType.WEB:
            tower_cost = 60
        
        if self.gold < tower_cost:
            return False, "Ouro insuficiente"
        
        self.tower_id_counter += 1
        tower = Tower.create(self.tower_id_counter, tower_type, grid_x, grid_y, self.cell_size)
        self.towers.append(tower)
        self.gold -= tower_cost
        
        return True, "Torre colocada com sucesso"
    
    def start_wave(self, wave_number: int):
        """Inicia uma nova onda de inimigos"""
        self.wave_number = wave_number
        self.wave_active = True
        
        # Configuração das ondas
        wave_configs = [
            # Wave 1: Apenas Aphids
            [{"type": EnemyType.APHID, "count": 5, "spawn_interval": 1.5}],
            # Wave 2: Aphids + Beetles
            [{"type": EnemyType.APHID, "count": 8, "spawn_interval": 1.2},
             {"type": EnemyType.BEETLE, "count": 2, "spawn_interval": 3.0}],
            # Wave 3: Misturado com Flies
            [{"type": EnemyType.APHID, "count": 10, "spawn_interval": 1.0},
             {"type": EnemyType.BEETLE, "count": 3, "spawn_interval": 2.5},
             {"type": EnemyType.FLY, "count": 4, "spawn_interval": 2.0}],
        ]
        
        config_index = min(wave_number - 1, len(wave_configs) - 1)
        enemies_config = wave_configs[config_index]
        
        self.current_wave = Wave(
            wave_number=wave_number,
            enemies=enemies_config,
            spawn_timer=0.0,
            enemies_spawned=0,
            completed=False
        )
    
    def update(self, dt: float) -> Dict:
        """
        Atualiza o estado do jogo
        Retorna dict com eventos: {enemies_killed: [], base_hit: bool, wave_complete: bool}
        """
        events = {
            "enemies_killed": [],
            "base_hit": False,
            "wave_complete": False,
            "gold_earned": 0
        }
        
        if self.game_over or self.paused:
            return events
        
        # Atualiza spawning de inimigos
        if self.wave_active and self.current_wave:
            self._update_spawning(dt, events)
        
        # Atualiza torres
        for tower in self.towers:
            result = tower.update(dt, self.enemies)
            if result:
                target, damage = result
                # Adiciona projétil
                self.projectiles.append({
                    "start_x": tower.x,
                    "start_y": tower.y,
                    "target_id": target.id,
                    "damage": damage,
                    "speed": 300.0,
                    "tower_type": tower.tower_type
                })
        
        # Atualiza projéteis
        self._update_projectiles(dt, events)
        
        # Atualiza inimigos
        self._update_enemies(dt, events)
        
        # Verifica game over
        if self.lives <= 0:
            self.game_over = True
        
        return events
    
    def _update_spawning(self, dt: float, events: Dict):
        """Gerencia spawning de inimigos na wave atual"""
        if not self.current_wave:
            return
        
        wave = self.current_wave
        total_enemies = sum(e["count"] for e in wave.enemies)
        
        if wave.enemies_spawned >= total_enemies:
            # Todos spawnados, verifica se wave completou
            if len(self.enemies) == 0:
                wave.completed = True
                self.wave_active = False
                events["wave_complete"] = True
            return
        
        wave.spawn_timer += dt
        
        # Encontra próximo inimigo para spawnar
        spawned_in_this_call = 0
        for enemy_group in wave.enemies:
            enemies_of_this_type = sum(
                1 for e in self.enemies if e.enemy_type == enemy_group["type"]
            )
            already_spawned_of_type = sum(
                1 for i in range(wave.enemies_spawned) 
                if i < enemy_group["count"] and enemy_group["type"] == enemy_group["type"]
            )
            
            # Lógica simplificada de spawn
            if wave.spawn_timer >= enemy_group["spawn_interval"]:
                wave.spawn_timer = 0
                self.enemy_id_counter += 1
                enemy = Enemy.create(self.enemy_id_counter, enemy_group["type"], self.path_length)
                
                # Posição inicial
                pos = self.get_position_on_path(0.0)
                enemy.x, enemy.y = pos
                
                self.enemies.append(enemy)
                wave.enemies_spawned += 1
                spawned_in_this_call += 1
                
                if spawned_in_this_call >= 1:  # Limita spawns por frame
                    break
    
    def _update_projectiles(self, dt: float, events: Dict):
        """Atualiza projéteis e aplica dano"""
        projectiles_to_remove = []
        
        for i, proj in enumerate(self.projectiles):
            # Encontra alvo
            target = None
            for enemy in self.enemies:
                if enemy.id == proj["target_id"]:
                    target = enemy
                    break
            
            if not target:
                projectiles_to_remove.append(i)
                continue
            
            # Move projétil em direção ao alvo
            dx = target.x - proj["start_x"]
            dy = target.y - proj["start_y"]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 10:  # Acertou
                if target.take_damage(proj["damage"]):
                    # Inimigo morreu
                    events["enemies_killed"].append(target.id)
                    events["gold_earned"] += target.reward
                    self.score += target.reward * 2
                    self.gold += target.reward
                projectiles_to_remove.append(i)
            else:
                # Move projétil
                move_dist = proj["speed"] * dt
                ratio = move_dist / distance
                proj["start_x"] += dx * ratio
                proj["start_y"] += dy * ratio
        
        # Remove projéteis acertados em ordem reversa
        for i in sorted(projectiles_to_remove, reverse=True):
            if i < len(self.projectiles):
                self.projectiles.pop(i)
    
    def _update_enemies(self, dt: float, events: Dict):
        """Atualiza posição e estado dos inimigos"""
        enemies_to_remove = []
        
        for i, enemy in enumerate(self.enemies):
            # Atualiza slow
            enemy.update_slow(dt)
            
            # Calcula velocidade atual
            current_speed = enemy.speed
            if enemy.slowed:
                current_speed *= 0.5
            
            # Move inimigo ao longo do caminho
            segment_length = self.path_length / (len(self.path) - 1) if len(self.path) > 1 else self.path_length
            segments_total = len(self.path) - 1 if len(self.path) > 1 else 1
            
            # Avança no caminho
            progress_increment = (current_speed * dt) / self.path_length
            enemy.path_index += progress_increment
            
            if enemy.path_index >= 1.0:
                # Chegou na base
                events["base_hit"] = True
                self.lives -= 1
                enemies_to_remove.append(i)
            else:
                # Atualiza posição
                pos = self.get_position_on_path(enemy.path_index)
                enemy.x, enemy.y = pos
        
        # Remove inimigos que chegaram na base ou morreram
        for i in sorted(enemies_to_remove, reverse=True):
            if i < len(self.enemies):
                self.enemies.pop(i)
    
    def to_dict(self) -> Dict:
        """Serializa estado do jogo para JSON"""
        return {
            "gold": self.gold,
            "lives": self.lives,
            "wave_number": self.wave_number,
            "score": self.score,
            "game_over": self.game_over,
            "paused": self.paused,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "cell_size": self.cell_size,
            "towers": [
                {
                    "id": t.id,
                    "type": t.tower_type.value,
                    "x": t.x,
                    "y": t.y,
                    "grid_x": t.grid_x,
                    "grid_y": t.grid_y,
                    "range": t.range_radius,
                    "damage": t.damage,
                    "attack_speed": t.attack_speed
                }
                for t in self.towers
            ],
            "enemies": [
                {
                    "id": e.id,
                    "type": e.enemy_type.value,
                    "x": e.x,
                    "y": e.y,
                    "health": e.health,
                    "max_health": e.max_health,
                    "slowed": e.slowed
                }
                for e in self.enemies
            ],
            "projectiles": self.projectiles,
            "path": self.path,
            "wave_active": self.wave_active
        }


# Função utilitária para criar novo jogo
def create_game() -> GameState:
    """Cria um novo estado de jogo"""
    return GameState()
