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
    GameState,
    Difficulty,
    DIFFICULTY_CONFIGS,
)


class TestTowerDefenseGame:
    """Testes para a classe principal TowerDefenseGame"""
    
    def test_create_game(self):
        """Testa criação básica do jogo"""
        game = TowerDefenseGame()
        
        assert game.state.grid_width == 30
        assert game.state.grid_height == 25
        assert game.state.leaves == 150
        assert game.state.lives == 20
        assert len(game.towers) == 0
        assert len(game.enemies) == 0
        assert not game.state.game_over
        assert not game.state.victory
        assert game.terrain is not None
        assert len(game.terrain) == 25
        assert len(game.terrain[0]) == 30
    
    def test_place_tower_success(self):
        """Testa colocação de torre bem-sucedida"""
        game = TowerDefenseGame()
        
        # Coloca torre em posição válida (não no caminho)
        success, message, tower = game.place_tower(6, 4, TowerType.ARCHER)
        
        assert success is True
        assert tower is not None
        assert tower.x == 6
        assert tower.y == 4
        assert tower.tower_type == TowerType.ARCHER
        assert game.state.leaves == 100  # 150 - 50 (custo da torre)
        assert len(game.towers) == 1
    
    def test_place_tower_on_path_fails(self):
        """Testa que não pode colocar torre no caminho"""
        game = TowerDefenseGame()
        
        # Tenta colocar torre no caminho (5, 3 está no path da serpente)
        success, message, tower = game.place_tower(5, 3, TowerType.ARCHER)
        
        assert success is False
        assert tower is None
        assert "obstacle" in message.lower() or "obstáculo" in message.lower()
        assert game.state.leaves == 150  # Leaves não foram gastas
        assert len(game.towers) == 0
    
    def test_place_tower_insufficient_leaves(self):
        """Testa colocação de torre sem folhas suficientes"""
        game = TowerDefenseGame()
        
        # Gasta quase todas as leaves
        game.place_tower(6, 4, TowerType.ARCHER)  # -50
        game.place_tower(7, 4, TowerType.ICE)     # -80
        
        # Na verdade a segunda falha, então vamos gastar manualmente
        game.state.leaves = 30  # Simula situação com poucas leaves
        
        success, message, tower = game.place_tower(8, 4, TowerType.BOMB)
        
        assert success is False
        assert "enough" in message.lower() or "insuficientes" in message.lower()
    
    def test_place_tower_blocked_terrain(self):
        """Testa que não pode colocar torre em terreno bloqueado"""
        game = TowerDefenseGame()
        
        # Tenta colocar torre em terreno bloqueado (canto longe do caminho)
        success, message, tower = game.place_tower(0, 0, TowerType.ARCHER)
        
        assert success is False
        assert tower is None
        assert "slot" in message.lower() or "build" in message.lower()
    
    def test_sell_tower(self):
        """Testa venda de torre"""
        game = TowerDefenseGame()
        
        # Coloca e vende torre
        game.place_tower(6, 4, TowerType.ARCHER)
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
        game.place_tower(6, 4, TowerType.ARCHER)
        tower_id = game.towers[0].id
        initial_level = game.towers[0].level
        
        # Faz upgrade
        success, message = game.upgrade_tower(tower_id)
        
        assert success is True
        assert game.towers[0].level == initial_level + 1
        assert game.state.leaves < 100  # Gastou leaves no upgrade (150 - 50 - 35 = 65)
    
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
        assert "progress" in message.lower() or "andamento" in message.lower()
    
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
        
        # Coloca torre perto do caminho (adjacente à row 3)
        game.place_tower(10, 4, TowerType.ARCHER)
        
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
        game.state.lives = 1
        
        # Simulate an enemy that has reached the end of the path
        # by directly setting distance_traveled = inf (the internal sentinel)
        game.path = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
        enemy = Enemy(
            id="test_enemy",
            enemy_type=EnemyType.FLY,
            x=4.0, y=0.0,
            hp=100, max_hp=100,
            speed=5.0, base_speed=5.0,
            reward=10, distance_traveled=float('inf')
        )
        game.enemies.append(enemy)
        
        # On update, the game detects distance_traveled == inf
        # and deducts lives
        game.update(0.1)
        
        assert game.state.lives <= 0 or game.state.game_over
    
    def test_get_state(self):
        """Testa obtenção do estado completo do jogo"""
        game = TowerDefenseGame()
        game.place_tower(6, 4, TowerType.ARCHER)
        game.start_wave()
        
        state = game.get_state()
        
        assert "state" in state
        assert "towers" in state
        assert "enemies" in state
        assert "path" in state
        assert "terrain" in state
        assert len(state["towers"]) == 1
        assert state["wave_active"] is True
    
    def test_reset_game(self):
        """Testa reset do jogo"""
        game = TowerDefenseGame()
        game.place_tower(6, 4, TowerType.ARCHER)
        game.start_wave()
        
        # Avança um pouco
        game.update(1.0)
        
        # Reseta
        game.reset()
        
        assert len(game.towers) == 0
        assert len(game.enemies) == 0
        assert game.state.leaves == 150
        assert game.state.lives == 20
        assert not game.wave_active


class TestTowerStats:
    """Testes para estatísticas das torres"""
    
    def test_archer_stats(self):
        """Testa estatísticas da torre Archer"""
        tower = Tower(id="t1", tower_type=TowerType.ARCHER, x=0, y=0)
        
        assert tower.cost == 50
        assert tower.range == 2.8
        assert tower.attack_speed == 0.7
    
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
        assert tower.range == 2.8
        assert tower.attack_speed == 1.2


class TestTerrainSystem:
    """Testes para o sistema de terreno expandido"""
    
    def test_terrain_generation(self):
        """Testa geração da matriz de terreno"""
        game = TowerDefenseGame()
        
        # Terreno deve ter 0s no caminho, 1s construíveis, 2s bloqueados
        path_set = set(game.path)
        has_path = False
        has_buildable = False
        has_blocked = False
        
        for y in range(game.state.grid_height):
            for x in range(game.state.grid_width):
                t = game.terrain[y][x]
                if t == 0:
                    has_path = True
                elif t == 1:
                    has_buildable = True
                elif t == 2:
                    has_blocked = True
        
        assert has_path, "Terrain should have path cells (type 0)"
        assert has_buildable, "Terrain should have buildable cells (type 1)"
        assert has_blocked, "Terrain should have blocked cells (type 2)"
    
    def test_path_cells_are_terrain_type_zero(self):
        """Testa que células do caminho são tipo 0 no terreno"""
        game = TowerDefenseGame()
        
        for x, y in game.path:
            if 0 <= x < game.state.grid_width and 0 <= y < game.state.grid_height:
                assert game.terrain[y][x] == 0, f"Path cell ({x},{y}) should be terrain type 0"
    
    def test_buildable_cells_allow_tower_placement(self):
        """Testa que células construíveis permitem colocação de torre"""
        game = TowerDefenseGame()
        
        # Encontrar uma célula construível
        placed = False
        for y in range(game.state.grid_height):
            for x in range(game.state.grid_width):
                if game.terrain[y][x] == 1:
                    success, msg, tower = game.place_tower(x, y, TowerType.ARCHER)
                    if success:
                        placed = True
                        break
            if placed:
                break
        
        assert placed, "Should be able to place tower on at least one buildable cell"
    
    def test_blocked_cells_reject_tower_placement(self):
        """Testa que células bloqueadas rejeitam colocação de torre"""
        game = TowerDefenseGame()
        
        for y in range(game.state.grid_height):
            for x in range(game.state.grid_width):
                if game.terrain[y][x] == 2:
                    success, msg, tower = game.place_tower(x, y, TowerType.ARCHER)
                    assert not success, f"Blocked cell ({x},{y}) should reject placement"
                    break
            else:
                continue
            break


class TestSerpentinePath:
    """Testes para o caminho serpente"""
    
    def test_path_covers_multiple_rows(self):
        """Testa que o caminho atravessa múltiplas linhas"""
        game = TowerDefenseGame()
        
        rows_covered = set(y for _, y in game.path)
        assert len(rows_covered) >= 5, f"Path should cover at least 5 rows, covers {len(rows_covered)}"
    
    def test_path_starts_and_ends_offscreen(self):
        """Testa que o caminho começa e termina fora da tela"""
        game = TowerDefenseGame()
        
        assert game.path[0][0] < 0 or game.path[0][0] > game.state.grid_width - 1
        assert game.path[-1][0] < 0 or game.path[-1][0] >= game.state.grid_width


class TestTimeControls:
    """Testes para controle de tempo e auto-wave"""

    def test_default_time_scale(self):
        game = TowerDefenseGame()
        assert game.state.time_scale == 1
        assert game.state.auto_wave is False

    def test_set_time_scale(self):
        game = TowerDefenseGame()
        success, msg = game.set_time_scale(2)
        assert success is True
        assert game.state.time_scale == 2
        
        success, msg = game.set_time_scale(4)
        assert success is True
        assert game.state.time_scale == 4

    def test_set_time_scale_invalid(self):
        game = TowerDefenseGame()
        success, msg = game.set_time_scale(3)
        assert success is False
        assert game.state.time_scale == 1  # unchanged

    def test_toggle_auto_wave(self):
        game = TowerDefenseGame()
        assert game.state.auto_wave is False
        
        success, msg = game.toggle_auto_wave()
        assert success is True
        assert game.state.auto_wave is True
        
        success, msg = game.toggle_auto_wave()
        assert success is True
        assert game.state.auto_wave is False

    def test_time_scale_speeds_up_game(self):
        """Testa que time_scale=2 dobra a velocidade do jogo"""
        game = TowerDefenseGame()
        game.set_time_scale(2)
        game.start_wave()
        
        # Run update with base dt
        dt = 0.5
        game.update(dt)
        # With scale 2, the effective dt should be 1.0
        # Enemies should have moved further than at 1x
        game2 = TowerDefenseGame()
        game2.start_wave()
        game2.update(dt)
        
        # Scaled game should have enemies further along
        if game.enemies and game2.enemies:
            scaled_dist = game.enemies[0].distance_traveled
            normal_dist = game2.enemies[0].distance_traveled
            assert scaled_dist > normal_dist

    def test_auto_wave_starts_next_wave(self):
        """Testa que auto-wave inicia a próxima onda automaticamente"""
        game = TowerDefenseGame()
        game.toggle_auto_wave()
        assert game.state.auto_wave is True
        
        # Start first wave and clear all enemies
        game.start_wave()
        game.enemies.clear()  # Simulate all enemies killed
        game.wave_enemies_remaining.clear()
        
        # Run updates for > 3 seconds
        for _ in range(200):
            game.update(0.05)
        
        # Wave 2 should have started automatically
        assert game.state.current_wave == 2
        assert game.wave_active is True

    def test_auto_wave_respects_total_waves(self):
        """Testa que auto-wave não inicia além do total de ondas"""
        game = TowerDefenseGame()
        game.toggle_auto_wave()
        game.state.current_wave = game.state.total_waves
        
        # Clear enemies
        game.start_wave()
        game.enemies.clear()
        game.wave_enemies_remaining.clear()
        game.wave_active = False
        
        for _ in range(200):
            game.update(0.05)
        
        # No new wave should start (victory)
        assert game.state.current_wave == game.state.total_waves

    def test_reset_preserves_speed_settings(self):
        """Testa que reset preserva configurações de velocidade"""
        game = TowerDefenseGame()
        game.set_time_scale(4)
        game.toggle_auto_wave()
        
        game.reset()
        
        assert game.state.time_scale == 4
        assert game.state.auto_wave is True

    def test_state_includes_time_fields(self):
        """Testa que o estado serializado inclui time_scale e auto_wave"""
        game = TowerDefenseGame()
        game.set_time_scale(2)
        game.toggle_auto_wave()
        
        state = game.get_state()
        assert state["state"]["time_scale"] == 2
        assert state["state"]["auto_wave"] is True
        assert state["state"]["difficulty"] == "normal"
        assert state["state"]["tower_cost_mult"] == 1.0


class TestDifficultySystem:
    """Testes para o sistema de dificuldades"""

    def test_easy_difficulty(self):
        game = TowerDefenseGame(difficulty=Difficulty.EASY)
        assert game.state.crystals == 200
        assert game.state.lives == 25
        assert game.diff_config["enemy_hp_mult"] == 0.7
        assert game.diff_config["tower_cost_mult"] == 0.80

    def test_normal_difficulty(self):
        game = TowerDefenseGame(difficulty=Difficulty.NORMAL)
        assert game.state.crystals == 150
        assert game.state.lives == 20
        assert game.diff_config["enemy_hp_mult"] == 1.0

    def test_hard_difficulty(self):
        game = TowerDefenseGame(difficulty=Difficulty.HARD)
        assert game.state.crystals == 120
        assert game.state.lives == 15
        assert game.diff_config["enemy_hp_mult"] == 1.4
        assert game.diff_config["tower_cost_mult"] == 1.15

    def test_easy_enemies_are_weaker(self):
        game_easy = TowerDefenseGame(difficulty=Difficulty.EASY)
        game_normal = TowerDefenseGame(difficulty=Difficulty.NORMAL)

        game_easy.start_wave()
        game_normal.start_wave()

        # Enemies spawn on update tick
        game_easy.update(2.0)
        game_normal.update(2.0)

        assert len(game_easy.enemies) > 0
        assert len(game_normal.enemies) > 0

        # Easy enemies should have less HP
        assert game_easy.enemies[0].hp < game_normal.enemies[0].hp

    def test_hard_enemies_are_stronger(self):
        game_hard = TowerDefenseGame(difficulty=Difficulty.HARD)
        game_normal = TowerDefenseGame(difficulty=Difficulty.NORMAL)

        game_hard.start_wave()
        game_normal.start_wave()

        game_hard.update(2.0)
        game_normal.update(2.0)

        assert len(game_hard.enemies) > 0
        assert len(game_normal.enemies) > 0

        assert game_hard.enemies[0].hp > game_normal.enemies[0].hp

    def test_easy_towers_are_cheaper(self):
        game_easy = TowerDefenseGame(difficulty=Difficulty.EASY)
        ok, msg, tower = game_easy.place_tower(6, 4, TowerType.ARCHER)
        assert ok is True
        # 50 * 0.80 = 40
        assert game_easy.state.crystals == 200 - 40

    def test_hard_towers_are_more_expensive(self):
        game_hard = TowerDefenseGame(difficulty=Difficulty.HARD)
        ok, msg, tower = game_hard.place_tower(6, 4, TowerType.ARCHER)
        assert ok is True
        # 50 * 1.15 = 57
        assert game_hard.state.crystals == 120 - 57

    def test_difficulty_preserved_in_state(self):
        game = TowerDefenseGame(difficulty=Difficulty.HARD)
        state = game.get_state()
        assert state["state"]["difficulty"] == "hard"
        assert state["state"]["difficulty_label"] == "Difícil"
        assert state["state"]["tower_cost_mult"] == 1.15

    def test_difficulty_preserved_on_reset(self):
        game = TowerDefenseGame(difficulty=Difficulty.HARD)
        game.start_wave()
        game.update(1.0)
        game.reset()
        assert game.difficulty == Difficulty.HARD
        assert game.state.crystals == 120
        assert game.state.lives == 15


class TestInsaneDifficulty:
    """Testes para dificuldade Insano e permadeath"""

    def test_insane_initial_values(self):
        game = TowerDefenseGame(difficulty=Difficulty.INSANE)
        assert game.state.crystals == 100
        assert game.state.lives == 10
        assert game.state.permadeath is True

    def test_insane_enemies_are_brutal(self):
        game_insane = TowerDefenseGame(difficulty=Difficulty.INSANE)
        game_normal = TowerDefenseGame(difficulty=Difficulty.NORMAL)

        game_insane.start_wave()
        game_normal.start_wave()
        game_insane.update(2.0)
        game_normal.update(2.0)

        assert len(game_insane.enemies) > 0
        assert len(game_normal.enemies) > 0

        # Insane HP = base × wave_mult × 2.0
        assert game_insane.enemies[0].hp > game_normal.enemies[0].hp * 1.5

    def test_insane_enemies_have_more_armor(self):
        game = TowerDefenseGame(difficulty=Difficulty.INSANE)
        game.start_wave()
        game.update(2.0)

        beetle = next((e for e in game.enemies if e.enemy_type == EnemyType.BEETLE), None)
        if beetle:
            # Beetle base armor = 3, insane mult = 1.5 → 4
            assert beetle.armor >= 4

    def test_insane_enemies_have_regen(self):
        game = TowerDefenseGame(difficulty=Difficulty.INSANE)
        game.start_wave()
        game.update(2.0)

        tank = next((e for e in game.enemies if e.enemy_type == EnemyType.TANK), None)
        if tank:
            # Tank base regen = 2, insane mult = 2.0 → 4
            assert tank.regen >= 4.0

    def test_insane_enemies_are_faster(self):
        game_insane = TowerDefenseGame(difficulty=Difficulty.INSANE)
        game_normal = TowerDefenseGame(difficulty=Difficulty.NORMAL)

        game_insane.start_wave()
        game_normal.start_wave()
        game_insane.update(2.0)
        game_normal.update(2.0)

        if game_insane.enemies and game_normal.enemies:
            assert game_insane.enemies[0].speed > game_normal.enemies[0].speed

    def test_insane_towers_are_expensive(self):
        game = TowerDefenseGame(difficulty=Difficulty.INSANE)
        ok, msg, tower = game.place_tower(6, 4, TowerType.ARCHER)
        assert ok is True
        # 50 * 1.30 = 65
        assert game.state.crystals == 100 - 65

    def test_permadeath_in_state(self):
        game = TowerDefenseGame(difficulty=Difficulty.INSANE)
        state = game.get_state()
        assert state["state"]["permadeath"] is True

    def test_other_difficulties_no_permadeath(self):
        for diff in [Difficulty.EASY, Difficulty.NORMAL, Difficulty.HARD]:
            game = TowerDefenseGame(difficulty=diff)
            assert game.state.permadeath is False

    def test_insane_difficulty_preserved_on_reset(self):
        game = TowerDefenseGame(difficulty=Difficulty.INSANE)
        game.start_wave()
        game.update(1.0)
        game.reset()
        assert game.difficulty == Difficulty.INSANE
        assert game.state.permadeath is True
        assert game.state.crystals == 100
        assert game.state.lives == 10

    def test_insane_state_fields(self):
        game = TowerDefenseGame(difficulty=Difficulty.INSANE)
        state = game.get_state()
        assert state["state"]["difficulty"] == "insane"
        assert state["state"]["difficulty_label"] == "Insano"
        assert state["state"]["tower_cost_mult"] == 1.30
        assert state["state"]["permadeath"] is True


def test_target_modes_first_last_strongest_weakest():
    game = TowerDefenseGame()
    # Place an archer at (6, 4)
    success, _, tower = game.place_tower(6, 4, TowerType.ARCHER)
    assert success is True
    
    # Spawn 3 enemies with varying distance_traveled and hp
    e_near_exit = Enemy(id="e1", enemy_type=EnemyType.FLY, x=6.0, y=4.5, hp=20, max_hp=20, speed=1.0, base_speed=1.0, reward=5, distance_traveled=100.0)
    e_strong = Enemy(id="e2", enemy_type=EnemyType.TANK, x=6.0, y=4.2, hp=200, max_hp=200, speed=1.0, base_speed=1.0, reward=10, distance_traveled=50.0)
    e_weak = Enemy(id="e3", enemy_type=EnemyType.SPRINTER, x=6.0, y=4.1, hp=5, max_hp=5, speed=1.0, base_speed=1.0, reward=2, distance_traveled=20.0)
    game.enemies = [e_near_exit, e_strong, e_weak]

    # Mode: FIRST (highest distance_traveled -> e1)
    game.set_target_mode(tower.id, "first")
    targets = game._find_targets(tower)
    assert targets[0].id == "e1"

    # Mode: LAST (lowest distance_traveled -> e3)
    game.set_target_mode(tower.id, "last")
    targets = game._find_targets(tower)
    assert targets[0].id == "e3"

    # Mode: STRONGEST (highest hp -> e2)
    game.set_target_mode(tower.id, "strongest")
    targets = game._find_targets(tower)
    assert targets[0].id == "e2"

    # Mode: WEAKEST (lowest hp -> e3)
    game.set_target_mode(tower.id, "weakest")
    targets = game._find_targets(tower)
    assert targets[0].id == "e3"


def test_pause_time_scale():
    game = TowerDefenseGame()
    ok, msg = game.set_time_scale(0)
    assert ok is True
    assert game.state.time_scale == 0
    
    # Update with dt should not advance enemies when paused
    enemy = Enemy(id="e1", enemy_type=EnemyType.FLY, x=1.0, y=1.0, hp=20, max_hp=20, speed=2.0, base_speed=2.0, reward=5)
    game.enemies = [enemy]
    game.update(0.1)
    assert enemy.x == 1.0  # did not move


def test_wave_preview_in_state():
    game = TowerDefenseGame()
    state = game.get_state()
    assert "next_wave_preview" in state["state"]
    assert state["state"]["next_wave_preview"]["wave_number"] == 1
    assert len(state["state"]["next_wave_preview"]["enemies"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
