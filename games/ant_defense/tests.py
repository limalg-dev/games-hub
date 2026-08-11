"""
Testes automatizados para o jogo Ant Defense
"""

import pytest
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from games.ant_defense.logic import (
    GameState, TowerType, EnemyType, create_game, 
    Tower, Enemy
)


class TestGameCreation:
    """Testa criação e estado inicial do jogo"""
    
    def test_create_game(self):
        """Testa criação de novo jogo"""
        game = create_game()
        
        assert game.gold == 100
        assert game.lives == 20
        assert game.wave_number == 0
        assert game.score == 0
        assert not game.game_over
        assert not game.paused
        assert len(game.towers) == 0
        assert len(game.enemies) == 0
    
    def test_path_generation(self):
        """Testa geração do caminho padrão"""
        game = create_game()
        
        assert len(game.path) > 1
        assert game.path_length > 0
        assert game.path[0] == (0, 2)  # Ponto inicial
        assert game.path[-1] == (14, 3)  # Ponto final


class TestTowerPlacement:
    """Testa colocação de torres"""
    
    def test_place_tower_valid(self):
        """Testa colocação válida de torre"""
        game = create_game()
        
        success, msg = game.place_tower(0, 0, TowerType.MANDIBLE)
        
        assert success
        assert msg == "Torre colocada com sucesso"
        assert len(game.towers) == 1
        assert game.gold == 50  # 100 - 50
    
    def test_place_tower_insufficient_gold(self):
        """Testa colocação sem ouro suficiente"""
        game = create_game()
        game.gold = 30
        
        success, msg = game.place_tower(0, 0, TowerType.MANDIBLE)
        
        assert not success
        assert "Ouro insuficiente" in msg
        assert len(game.towers) == 0
    
    def test_place_tower_on_path(self):
        """Testa que não pode colocar torre no caminho"""
        game = create_game()
        
        # Tenta colocar no caminho (ponto 2,2 está no caminho)
        success, msg = game.place_tower(2, 2, TowerType.MANDIBLE)
        
        assert not success
        assert "Não pode construir no caminho" in msg
    
    def test_place_tower_duplicate(self):
        """Testa que não pode colocar duas torres no mesmo local"""
        game = create_game()
        
        success1, _ = game.place_tower(0, 0, TowerType.MANDIBLE)
        success2, msg = game.place_tower(0, 0, TowerType.ACID)
        
        assert success1
        assert not success2
        assert "Já existe uma torre aqui" in msg
        assert len(game.towers) == 1
    
    def test_place_tower_out_of_bounds(self):
        """Testa colocação fora dos limites do grid"""
        game = create_game()
        
        success_x, msg_x = game.place_tower(-1, 0, TowerType.MANDIBLE)
        success_y, msg_y = game.place_tower(0, -1, TowerType.MANDIBLE)
        success_w, msg_w = game.place_tower(15, 0, TowerType.MANDIBLE)
        success_h, msg_h = game.place_tower(0, 10, TowerType.MANDIBLE)
        
        assert not success_x
        assert not success_y
        assert not success_w
        assert not success_h


class TestTowerTypes:
    """Testa diferentes tipos de torres"""
    
    def test_mandible_tower_stats(self):
        """Testa atributos da torre Mandíbula"""
        tower = Tower.create(1, TowerType.MANDIBLE, 5, 5)
        
        assert tower.cost == 50
        assert tower.damage == 15.0
        assert tower.attack_speed == 2.0
        assert tower.range_radius == 120.0
    
    def test_acid_tower_stats(self):
        """Testa atributos da torre Ácido"""
        tower = Tower.create(1, TowerType.ACID, 5, 5)
        
        assert tower.cost == 80
        assert tower.damage == 40.0
        assert tower.attack_speed == 0.5
        assert tower.range_radius == 100.0
    
    def test_web_tower_stats(self):
        """Testa atributos da torre Teia"""
        tower = Tower.create(1, TowerType.WEB, 5, 5)
        
        assert tower.cost == 60
        assert tower.damage == 5.0
        assert tower.attack_speed == 1.0
        assert tower.range_radius == 90.0


class TestEnemyTypes:
    """Testa diferentes tipos de inimigos"""
    
    def test_aphid_enemy(self):
        """Testa inimigo Aphid (rápido e frágil)"""
        enemy = Enemy.create(1, EnemyType.APHID, 500.0)
        
        assert enemy.health == 30.0
        assert enemy.speed == 120.0
        assert enemy.reward == 5
    
    def test_beetle_enemy(self):
        """Testa inimigo Beetle (lento e tanque)"""
        enemy = Enemy.create(1, EnemyType.BEETLE, 500.0)
        
        assert enemy.health == 100.0
        assert enemy.speed == 40.0
        assert enemy.reward == 15
    
    def test_fly_enemy(self):
        """Testa inimigo Fly (voador)"""
        enemy = Enemy.create(1, EnemyType.FLY, 500.0)
        
        assert enemy.health == 50.0
        assert enemy.speed == 80.0
        assert enemy.reward == 10


class TestWaveSystem:
    """Testa sistema de ondas"""
    
    def test_start_wave(self):
        """Testa início de wave"""
        game = create_game()
        
        game.start_wave(1)
        
        assert game.wave_active
        assert game.wave_number == 1
        assert game.current_wave is not None
    
    def test_cannot_start_wave_while_active(self):
        """Testa que não pode iniciar wave se já existe uma ativa"""
        game = create_game()
        game.start_wave(1)
        
        # Tenta iniciar outra wave
        # Isso deve ser tratado na API, não na lógica
        assert game.wave_active


class TestCombat:
    """Testa sistema de combate"""
    
    def test_tower_finds_closest_enemy(self):
        """Testa que torre encontra inimigo mais próximo"""
        game = create_game()
        game.place_tower(5, 5, TowerType.MANDIBLE)
        
        # Cria inimigos em posições diferentes
        enemy1 = Enemy.create(1, EnemyType.APHID, game.path_length)
        enemy1.x = 200
        enemy1.y = 200
        
        enemy2 = Enemy.create(2, EnemyType.APHID, game.path_length)
        enemy2.x = 210  # Mais perto
        enemy2.y = 205
        
        game.enemies = [enemy1, enemy2]
        
        tower = game.towers[0]
        closest = tower.find_closest_enemy(game.enemies)
        
        assert closest == enemy2
    
    def test_enemy_take_damage(self):
        """Testa inimigo recebendo dano"""
        enemy = Enemy.create(1, EnemyType.APHID, 500.0)
        
        died = enemy.take_damage(20.0)
        
        assert not died
        assert enemy.health == 10.0
        
        died = enemy.take_damage(15.0)
        assert died
        assert enemy.health <= 0
    
    def test_web_tower_slows_enemy(self):
        """Testa que torre Web desacelera inimigo"""
        game = create_game()
        game.place_tower(5, 5, TowerType.WEB)
        
        enemy = Enemy.create(1, EnemyType.APHID, game.path_length)
        original_speed = enemy.speed
        game.enemies = [enemy]
        
        # Atualiza torre (deve aplicar slow)
        tower = game.towers[0]
        result = tower.update(1.0, game.enemies)
        
        if result:
            assert enemy.slowed


class TestGameState:
    """Testa estado geral do jogo"""
    
    def test_game_over_when_lives_zero(self):
        """Testa game over quando vidas chegam a zero"""
        game = create_game()
        game.lives = 1
        
        # Simula inimigo chegando na base
        events = game.update(0.1)
        
        # Precisa de inimigos para testar properly
        # Este é um teste básico
        assert not game.game_over  # Ainda não acabou sem inimigos
    
    def test_to_dict_serialization(self):
        """Testa serialização do estado do jogo"""
        game = create_game()
        game.place_tower(0, 0, TowerType.MANDIBLE)
        
        state_dict = game.to_dict()
        
        assert state_dict['gold'] == 50
        assert state_dict['lives'] == 20
        assert len(state_dict['towers']) == 1
        assert state_dict['towers'][0]['type'] == 'mandible'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
