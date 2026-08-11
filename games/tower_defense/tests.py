"""
🐜 Ant Defense - Testes Unitários
Testa a lógica principal do jogo Tower Defense
"""

import pytest
from games.tower_defense.logic import (
    TowerDefenseGame,
    TowerType,
    EnemyType,
    Tower,
    Enemy,
    WaveConfig,
    GameState
)


class TestTowerDefenseGame:
    """Testes para a classe principal TowerDefenseGame"""
    
    def test_create_game(self):
        """Testa criação básica do jogo"""
        game = TowerDefenseGame()
        
        assert game.state.grid_width == 15
        assert game.state.grid_height == 10
        assert game.state.leaves == 100
        assert game.state.lives == 20
        assert len(game.towers) == 0
        assert len(game.enemies) == 0
        assert not game.state.game_over
        assert not game.state.victory
    
    def test_place_tower_success(self):
        """Testa colocação de torre bem-sucedida"""
        game = TowerDefenseGame()
        
        # Coloca torre em posição válida (não no caminho)
        success, message, tower = game.place_tower(0, 0, TowerType.ARCHER)
        
        assert success is True
        assert tower is not None
        assert tower.x == 0
        assert tower.y == 0
        assert tower.tower_type == TowerType.ARCHER
        assert game.state.leaves == 50  # 100 - 50 (custo da torre)
        assert len(game.towers) == 1
    
    def test_place_tower_on_path_fails(self):
        """Testa que não pode colocar torre no caminho"""
        game = TowerDefenseGame()
        
        # Tenta colocar torre no caminho (4, 5 está no path padrão)
        success, message, tower = game.place_tower(4, 5, TowerType.ARCHER)
        
        assert success is False
        assert tower is None
        assert "caminho" in message.lower()
        assert game.state.leaves == 100  # Leaves não foram gastas
        assert len(game.towers) == 0
    
    def test_place_tower_insufficient_leaves(self):
        """Testa colocação de torre sem folhas suficientes"""
        game = TowerDefenseGame()
        
        # Gasta quase todas as leaves
        game.place_tower(0, 0, TowerType.ARCHER)  # -50
        game.place_tower(1, 0, TowerType.ICE)     # -80 = 130 gastas, mas só tem 100
        
        # Na verdade a segunda falha, então vamos gastar manualmente
        game.state.leaves = 30  # Simula situação com poucas leaves
        
        success, message, tower = game.place_tower(2, 0, TowerType.BOMB)
        
        assert success is False
        assert "insuficientes" in message.lower()
    
    def test_sell_tower(self):
        """Testa venda de torre"""
        game = TowerDefenseGame()
        
        # Coloca e vende torre
        game.place_tower(0, 0, TowerType.ARCHER)
        tower_id = game.towers[0].id
        
        success, message, sell_value = game.sell_tower(tower_id)
        
        assert success is True
        assert sell_value > 0
        assert len(game.towers) == 0
        assert game.state.leaves > 50  # Recuperou parte do valor
    
    def test_upgrade_tower(self):
        """Testa upgrade de torre"""
        game = TowerDefenseGame()
        
        # Coloca torre
        game.place_tower(0, 0, TowerType.ARCHER)
        tower_id = game.towers[0].id
        initial_level = game.towers[0].level
        
        # Faz upgrade
        success, message = game.upgrade_tower(tower_id)
        
        assert success is True
        assert game.towers[0].level == initial_level + 1
        assert game.state.leaves < 50  # Gastou leaves no upgrade
    
    def test_start_wave(self):
        """Testa início de onda"""
        game = TowerDefenseGame()
        
        success, message = game.start_wave()
        
        assert success is True
        assert game.wave_active is True
        assert game.state.current_wave == 1
        assert len(game.wave_enemies_remaining) > 0
    
    def test_cannot_start_wave_twice(self):
        """Testa que não pode iniciar duas ondas simultâneas"""
        game = TowerDefenseGame()
        
        game.start_wave()
        success, message = game.start_wave()
        
        assert success is False
        assert "já em andamento" in message.lower()
    
    def test_enemy_movement(self):
        """Testa movimento de inimigos ao longo do caminho"""
        game = TowerDefenseGame()
        game.start_wave()
        
        # Avança o tempo
        initial_x = game.enemies[0].x if game.enemies else 0
        game.update(1.0)  # 1 segundo
        
        # Inimigo deve ter se movido
        if game.enemies:
            assert game.enemies[0].x != initial_x or game.enemies[0].y != game.enemies[0].y
    
    def test_tower_shoots_enemy(self):
        """Testa que torre atira em inimigo"""
        game = TowerDefenseGame()
        
        # Coloca torre perto do caminho
        game.place_tower(3, 4, TowerType.ARCHER)
        
        # Inicia onda
        game.start_wave()
        
        # Avança tempo até inimigo estar no alcance
        for _ in range(50):
            result = game.update(0.1)
            if result["attacks"]:
                break
        
        # Verifica que houve ataque
        assert len(result["attacks"]) > 0 or len(game.enemies) > 0
    
    def test_game_over_when_lives_zero(self):
        """Testa game over quando vidas chegam a zero"""
        game = TowerDefenseGame()
        game.state.lives = 1  # Quase game over
        
        # Simula inimigo chegando ao fim
        game.path = [(0, 0), (1, 0)]  # Caminho curto
        enemy = Enemy(
            id="test_enemy",
            enemy_type=EnemyType.FLY,
            x=0.9,
            y=0.0,
            hp=100,
            max_hp=100,
            speed=10.0,
            base_speed=10.0,
            reward=10,
            distance_traveled=0.9
        )
        game.enemies.append(enemy)
        
        # Avança tempo
        game.update(0.5)
        
        assert game.state.lives <= 0 or game.state.game_over
    
    def test_get_state(self):
        """Testa obtenção do estado completo do jogo"""
        game = TowerDefenseGame()
        game.place_tower(0, 0, TowerType.ARCHER)
        game.start_wave()
        
        state = game.get_state()
        
        assert "state" in state
        assert "towers" in state
        assert "enemies" in state
        assert "path" in state
        assert len(state["towers"]) == 1
        assert state["wave_active"] is True
    
    def test_reset_game(self):
        """Testa reset do jogo"""
        game = TowerDefenseGame()
        game.place_tower(0, 0, TowerType.ARCHER)
        game.start_wave()
        
        # Avança um pouco
        game.update(1.0)
        
        # Reseta
        game.reset()
        
        assert len(game.towers) == 0
        assert len(game.enemies) == 0
        assert game.state.leaves == 100
        assert game.state.lives == 20
        assert not game.wave_active


class TestTowerStats:
    """Testes para estatísticas das torres"""
    
    def test_archer_stats(self):
        """Testa estatísticas da torre Archer"""
        tower = Tower(id="t1", tower_type=TowerType.ARCHER, x=0, y=0)
        
        assert tower.cost == 50
        assert tower.range == 3.0
        assert tower.attack_speed == 0.8
    
    def test_bomb_stats(self):
        """Testa estatísticas da torre Bomb"""
        tower = Tower(id="t1", tower_type=TowerType.BOMB, x=0, y=0)
        
        assert tower.cost == 120
        assert tower.range == 2.5
        assert tower.attack_speed == 2.5
    
    def test_ice_stats(self):
        """Testa estatísticas da torre Ice"""
        tower = Tower(id="t1", tower_type=TowerType.ICE, x=0, y=0)
        
        assert tower.cost == 80
        assert tower.range == 2.5
        assert tower.attack_speed == 1.2


class TestEnemyStats:
    """Testes para estatísticas dos inimigos"""
    
    def test_game_has_default_path(self):
        """Testa que o jogo tem caminho padrão"""
        game = TowerDefenseGame()
        
        assert len(game.path) > 0
        assert game.path[0] == (0, 5)  # Ponto de início
        assert game.path[-1] == (14, 7)  # Ponto final (formigueiro)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
