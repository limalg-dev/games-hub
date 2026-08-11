# 🐜 Ant Defense - Tower Defense

Jogo de Tower Defense onde formigas defendem o formigueiro contra invasores.

## 🎮 Visão Geral

**Tema:** Formigas defendendo o formigueiro  
**Objetivo:** Posicionar torres estrategicamente ao longo de um caminho para impedir que ondas de inimigos cheguem à base.

## 🏗️ Mecânicas Principais

### Sistema de Grid
- Grid 15x10 células (40px cada)
- Clique para posicionar torres
- Validação automática de posição válida

### Economia
- **Ouro inicial:** 100
- **Recompensas por inimigo abatido:**
  - Aphid: 5 ouro
  - Beetle: 15 ouro
  - Fly: 10 ouro
- Torres custam entre 50-80 ouro

### Sistema de Vidas
- **Vidas iniciais:** 20
- Perde 1 vida quando inimigo chega na base
- Game Over quando vidas = 0

## 🗼 Tipos de Torres

| Torre | Custo | Dano | Velocidade | Alcance | Função |
|-------|-------|------|------------|---------|--------|
| 🦷 **Mandíbula** | 50 | 15 | 2.0/s | 120px | Ataque rápido, alvo único |
| 🧪 **Ácido** | 80 | 40 | 0.5/s | 100px | Dano alto em área, lento |
| 🕸️ **Teia** | 60 | 5 | 1.0/s | 90px | Desacelera inimigos (50% por 2s) |

## 🐛 Tipos de Inimigos

| Inimigo | Vida | Velocidade | Recompensa | Características |
|---------|------|------------|------------|-----------------|
| 🐛 **Aphid** | 30 | 120 u/s | 5 | Rápido mas frágil |
| 🪲 **Beetle** | 100 | 40 u/s | 15 | Lento mas tanque |
| 🪰 **Fly** | 50 | 80 u/s | 10 | Voador equilibrado |

## 📊 Estrutura de Ondas

### Wave 1
- 5x Aphid (intervalo: 1.5s)

### Wave 2
- 8x Aphid (intervalo: 1.2s)
- 2x Beetle (intervalo: 3.0s)

### Wave 3+
- 10x Aphid (intervalo: 1.0s)
- 3x Beetle (intervalo: 2.5s)
- 4x Fly (intervalo: 2.0s)

## 💻 Estrutura de Código

### Arquivos Principais

```
games/ant_defense/
├── logic.py          # Lógica do jogo (GameState, Tower, Enemy)
├── routes.py         # API REST e WebSocket
├── index.html        # Interface do jogador
├── tests.py          # Testes automatizados
└── README.md         # Esta documentação
```

### Exemplo de Uso da API

```python
# Criar novo jogo
POST /games/ant_defense
Response: { "game_id": "...", "initial_state": {...} }

# Colocar torre
POST /games/ant_defense/{game_id}/tower?grid_x=5&grid_y=5&tower_type=mandible

# Iniciar wave
POST /games/ant_defense/{game_id}/wave?wave_number=1

# WebSocket para updates em tempo real
ws://localhost:8000/ws/ant_defense/{game_id}
```

### Script Base de Torre (Exemplo)

```python
class Tower:
    def find_closest_enemy(self, enemies):
        """Encontra inimigo mais próximo no alcance"""
        closest = None
        min_distance = self.range_radius
        
        for enemy in enemies:
            distance = sqrt((enemy.x - self.x)**2 + (enemy.y - self.y)**2)
            if distance <= self.range_radius and distance < min_distance:
                min_distance = distance
                closest = enemy
        
        return closest
    
    def update(self, dt, enemies):
        """Atualiza torre e atira se possível"""
        self.attack_timer += dt
        attack_interval = 1.0 / self.attack_speed
        
        if self.attack_timer >= attack_interval:
            target = self.find_closest_enemy(enemies)
            if target:
                self.attack_timer = 0
                return (target, self.damage)
        
        return None
```

## ✅ To-Do List (MVP)

### Fase 1 - Core (✅ Concluído)
- [x] Sistema de grid e posicionamento
- [x] 3 tipos de torres funcionais
- [x] 3 tipos de inimigos com pathfinding
- [x] Sistema de economia (ouro/recompensas)
- [x] Sistema de vidas e game over
- [x] 3 ondas de inimigos balanceadas
- [x] API REST completa
- [x] WebSocket para tempo real
- [x] Interface HTML5 Canvas
- [x] 15 testes automatizados

### Fase 2 - Melhorias (Sugestões)
- [ ] Sons e efeitos sonoros
- [ ] Partículas e efeitos visuais
- [ ] Mais tipos de torres (5+)
- [ ] Mais tipos de inimigos (5+)
- [ ] Sistema de upgrades de torres
- [ ] Power-ups temporários
- [ ] Leaderboard online
- [ ] Temas visuais alternativos
- [ ] Caminhos customizáveis
- [ ] Modo sandbox (infinito)

### Fase 3 - Avançado
- [ ] Multijogador cooperativo
- [ ] Editor de mapas
- [ ] Sistema de conquistas
- [ ] Tutorial interativo
- [ ] Suporte mobile touch
- [ ] Analytics de gameplay

## 🚀 Como Jogar

1. **Inicie o servidor:**
   ```bash
   cd /workspace/checkers-platform
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Acesse no navegador:**
   ```
   http://localhost:8000/play/ant_defense
   ```

3. **Jogue:**
   - Selecione uma torre no painel direito
   - Clique no grid para posicionar
   - Inicie a wave
   - Não deixe inimigos chegarem na base!

## 🧪 Rodar Testes

```bash
cd /workspace/checkers-platform
pytest games/ant_defense/tests.py -v
```

## 📈 Status

- ✅ Lógica do jogo implementada
- ✅ API REST funcional
- ✅ WebSocket para tempo real
- ✅ Interface gráfica moderna
- ✅ 15 testes passando
- ✅ Integrado com a plataforma

---

**Desenvolvido para Checkers-Platform** 🎮
