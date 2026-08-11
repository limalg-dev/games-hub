# 🐜 Ant Defense - Documentação de Design do Jogo

## Visão Geral
**Tema:** Formigas defendendo o formigueiro contra invasores.
**Gênero:** Tower Defense (Defesa de Torres)
**Objetivo:** Posicionar torres estrategicamente ao longo de um caminho para impedir que ondas de inimigos cheguem à base (formigueiro).

---

## 🎮 Mecânicas Principais

### 1. Sistema de Grid (Posicionamento)
- **Grid:** 15x10 células (150 posições possíveis)
- **Caminho Pré-definido:** Os inimigos seguem um caminho fixo do ponto de entrada até o formigueiro
- **Posicionamento de Torres:** 
  - Jogador pode colocar torres apenas em células vazias (não no caminho)
  - Cada torre ocupa 1 célula do grid
  - Custo de posicionamento: Variável por tipo de torre
- **Visualização:** 
  - Células válidas destacadas em verde ao selecionar uma torre
  - Células inválidas (caminho ou ocupadas) em vermelho

### 2. Economia do Jogo
- **Recurso Principal:** "Folhas" (🍃)
- **Obtenção de Folhas:**
  - Inicial: 100 folhas
  - Por inimigo abatido: 5-20 folhas (depende do tipo)
  - Bônus por onda completada: 25 folhas
- **Gastos:**
  - Construção de torres: 50-150 folhas
  - Upgrade de torres: 75% do custo original
  - Venda de torres: 50% do valor pago

### 3. Sistema de Vidas da Base
- **Vidas Iniciais:** 20 vidas (corações ❤️)
- **Perda de Vidas:** 
  - Cada inimigo que chega ao formigueiro: -1 vida
  - Inimigos especiais (Boss): -3 a -5 vidas
- **Game Over:** Quando vidas chegam a 0
- **Vitória:** Sobreviver a todas as ondas (configurável, padrão: 10 ondas)

---

## 🏰 Tipos de Torres (3 Iniciais)

### 1. 🎯 Torre Formigueira (Ant Archer)
- **Função:** Ataque rápido de alvo único
- **Dano:** 15-25 por tiro
- **Velocidade de Ataque:** 0.8 segundos entre tiros
- **Alcance:** 3 células
- **Custo:** 50 folhas
- **Especial:** Nenhuma (torre básica balanceada)
- **Visual:** Formiga com arco e flecha

### 2. 💣 Torre Explosiva (Bomb Beetle)
- **Função:** Dano em área (AoE) lento
- **Dano:** 40-60 no centro, 20-30 na borda
- **Velocidade de Ataque:** 2.5 segundos entre tiros
- **Alcance:** 2.5 células
- **Raio de Explosão:** 1.5 células
- **Custo:** 120 folhas
- **Especial:** Dano em área afeta múltiplos inimigos
- **Visual:** Besouro com barriga brilhante/explosiva

### 3. ❄️ Torre Congelante (Ice Aphid)
- **Função:** Desaceleração (Slow/Debuff)
- **Dano:** 8-12 por tiro (baixo)
- **Velocidade de Ataque:** 1.2 segundos entre tiros
- **Alcance:** 2.5 células
- **Custo:** 80 folhas
- **Especial:** Reduz velocidade do inimigo em 40% por 2 segundos
- **Visual:** Pulgão azul cristalino que atira gelo

---

## 👾 Tipos de Inimigos (3 Iniciais)

### 1. 🪰 Mosca Veloz (Swift Fly)
- **Características:** Rápido mas frágil
- **Velocidade:** 2.0 células/segundo
- **Vida:** 30 HP
- **Recompensa:** 8 folhas
- **Ondas:** Aparece nas ondas 1-5 (comum), 6-10 (misturado)
- **Visual:** Mosca pequena e ágil com asas transparentes

### 2. 🐞 Besouro Tanque (Armored Beetle)
- **Características:** Lento mas resistente (tanque)
- **Velocidade:** 0.8 células/segundo
- **Vida:** 120 HP
- **Recompensa:** 18 folhas
- **Ondas:** Aparece a partir da onda 3
- **Visual:** Besouro grande com carapaça dura e escura

### 3. 🦟 Percevejo Voador (Sky Bug)
- **Características:** Voador que ignora obstáculos (mas segue o caminho)
- **Velocidade:** 1.5 células/segundo
- **Vida:** 50 HP
- **Recompensa:** 12 folhas
- **Ondas:** Aparece a partir da onda 5
- **Especial:** Não pode ser atingido por torres terrestres (futuro balanceamento)
- **Visual:** Percevejo alado com brilho prateado

---

## 💻 Estrutura de Código Básica

### Exemplo: Lógica de Torre (Detecção e Tiro)

```python
import math
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

class TowerType(Enum):
    ARCHER = "archer"
    BOMB = "bomb"
    ICE = "ice"

@dataclass
class Enemy:
    id: str
    x: float
    y: float
    hp: int
    max_hp: int
    speed: float
    reward: int
    slowed: bool = False
    slow_timer: float = 0.0

@dataclass
class Tower:
    id: str
    tower_type: TowerType
    x: int
    y: int
    level: int = 1
    cooldown: float = 0.0
    
    @property
    def damage(self) -> tuple:
        damages = {
            TowerType.ARCHER: (15, 25),
            TowerType.BOMB: (40, 60),
            TowerType.ICE: (8, 12)
        }
        return damages[self.tower_type]
    
    @property
    def attack_speed(self) -> float:
        speeds = {
            TowerType.ARCHER: 0.8,
            TowerType.BOMB: 2.5,
            TowerType.ICE: 1.2
        }
        return speeds[self.tower_type]
    
    @property
    def range(self) -> float:
        ranges = {
            TowerType.ARCHER: 3.0,
            TowerType.BOMB: 2.5,
            TowerType.ICE: 2.5
        }
        return ranges[self.tower_type]
    
    @property
    def cost(self) -> int:
        costs = {
            TowerType.ARCHER: 50,
            TowerType.BOMB: 120,
            TowerType.ICE: 80
        }
        return costs[self.tower_type]

def distance(tower: Tower, enemy: Enemy) -> float:
    """Calcula distância euclidiana entre torre e inimigo"""
    return math.sqrt((tower.x - enemy.x) ** 2 + (tower.y - enemy.y) ** 2)

def find_closest_enemy(tower: Tower, enemies: List[Enemy]) -> Optional[Enemy]:
    """Encontra o inimigo mais próximo dentro do alcance da torre"""
    closest = None
    min_dist = float('inf')
    
    for enemy in enemies:
        dist = distance(tower, enemy)
        if dist <= tower.range and dist < min_dist:
            min_dist = dist
            closest = enemy
    
    return closest

def apply_damage(enemy: Enemy, damage: int, tower_type: TowerType) -> Dict[str, Any]:
    """Aplica dano ao inimigo e retorna status"""
    enemy.hp -= damage
    effects = []
    
    # Aplica slow se for torre de gelo
    if tower_type == TowerType.ICE:
        enemy.slowed = True
        enemy.slow_timer = 2.0
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

def update_tower(tower: Tower, enemies: List[Enemy], dt: float) -> Dict[str, Any]:
    """Atualiza estado da torre e realiza ataque se possível"""
    result = {"attacks": [], "state_change": False}
    
    # Reduz cooldown
    if tower.cooldown > 0:
        tower.cooldown -= dt
        return result
    
    # Encontra alvo
    target = find_closest_enemy(tower, enemies)
    if target is None:
        return result
    
    # Calcula dano
    dmg_min, dmg_max = tower.damage
    damage = int((dmg_min + dmg_max) / 2)  # Simplificação para MVP
    
    # Aplica dano
    attack_result = apply_damage(target, damage, tower.tower_type)
    
    # Registra ataque
    result["attacks"].append({
        "tower_id": tower.id,
        "enemy_id": target.id,
        "damage": damage,
        "target_x": target.x,
        "target_y": target.y
    })
    
    # Reseta cooldown
    tower.cooldown = tower.attack_speed
    result["state_change"] = True
    
    return result

def update_enemy(enemy: Enemy, dt: float) -> None:
    """Atualiza estado do inimigo (movimento e debuffs)"""
    # Atualiza timer de slow
    if enemy.slowed:
        enemy.slow_timer -= dt
        if enemy.slow_timer <= 0:
            enemy.slowed = False
            enemy.slow_timer = 0.0

# Exemplo de uso no game loop
def game_loop_example():
    # Inicialização
    tower = Tower(id="t1", tower_type=TowerType.ARCHER, x=5, y=5)
    enemies = [
        Enemy(id="e1", x=10.0, y=5.0, hp=30, max_hp=30, speed=2.0, reward=8),
        Enemy(id="e2", x=12.0, y=5.0, hp=120, max_hp=120, speed=0.8, reward=18)
    ]
    
    dt = 0.016  # ~60 FPS
    
    # Loop principal
    while enemies:
        # Atualiza torres
        for tower in towers:
            result = update_tower(tower, enemies, dt)
            if result["attacks"]:
                print(f"Torre {tower.id} atacou!")
        
        # Atualiza inimigos
        for enemy in enemies[:]:  # Cópia para permitir remoção segura
            update_enemy(enemy, dt)
            if enemy.hp <= 0:
                enemies.remove(enemy)
                print(f"Inimigo {enemy.id} destruído! +{enemy.reward} folhas")
```

---

## ✅ Próximos Passos (To-Do List para MVP)

### Fase 1: Estrutura Básica (Dia 1-2)
- [ ] Criar estrutura de diretórios (`games/tower_defense/`)
- [ ] Implementar classe `TowerDefenseGame` com estado básico
- [ ] Criar sistema de grid (15x10) com caminho pré-definido
- [ ] Implementar classes `Tower` e `Enemy` conforme design doc
- [ ] Criar testes unitários básicos

### Fase 2: Mecânicas Core (Dia 3-4)
- [ ] Implementar sistema de colocação de torres
- [ ] Criar lógica de movimento dos inimigos ao longo do caminho
- [ ] Implementar detecção de colisão torre-inimigo
- [ ] Adicionar sistema de tiro das torres (projéteis)
- [ ] Implementar sistema de economia (folhas, custos, recompensas)

### Fase 3: Sistema de Ondas (Dia 5)
- [ ] Criar configurador de ondas (inimigos por onda)
- [ ] Implementar spawn de inimigos por onda
- [ ] Adicionar sistema de vidas da base
- [ ] Criar condições de vitória/derrota
- [ ] Implementar contagem de ondas

### Fase 4: Interface e Renderização (Dia 6-7)
- [ ] Criar HTML com canvas para renderização
- [ ] Implementar rendering do grid, caminho, torres e inimigos
- [ ] Adicionar UI para seleção de torres e informações
- [ ] Criar overlay de Game Over/Vitória
- [ ] Implementar controles (mouse/toque)

### Fase 5: Integração e Polimento (Dia 8)
- [ ] Integrar com rotas FastAPI da plataforma
- [ ] Adicionar WebSocket para multiplayer/espectadores
- [ ] Implementar efeitos visuais (tiros, explosões, slow)
- [ ] Adicionar sons (opcional para MVP)
- [ ] Testes de integração e balanceamento
- [ ] Documentação final e README

### Fase 6: Expansão (Pós-MVP)
- [ ] Adicionar mais tipos de torres (5+)
- [ ] Adicionar mais tipos de inimigos (5+)
- [ ] Implementar sistema de upgrade de torres
- [ ] Criar múltiplos mapas/caminhos
- [ ] Modo infinito (sobrevivência)
- [ ] Sistema de conquistas

---

## 📊 Métricas de Balanceamento Inicial

| Torre | DPS Médio | Custo | Eficiência (DPS/Custo) |
|-------|-----------|-------|------------------------|
| Archer | ~25 | 50 | 0.50 |
| Bomb | ~20 | 120 | 0.17 |
| Ice | ~8 + slow | 80 | 0.10 + utilidade |

| Inimigo | HP | Velocidade | Recompensa | Dificuldade Relativa |
|---------|----|------------|------------|---------------------|
| Fly | 30 | 2.0 | 8 | Baixa |
| Beetle | 120 | 0.8 | 18 | Média |
| Sky Bug | 50 | 1.5 | 12 | Média-Alta |

---

**Próxima Ação:** Iniciar implementação da Fase 1 criando a estrutura de código Python para a lógica do jogo.
