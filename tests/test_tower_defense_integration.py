"""
Tests for Tower Defense integration and logic edge cases
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, engine
from sqlmodel import SQLModel
from games.tower_defense.logic import (
    TowerDefenseGame,
    TowerType,
    EnemyType,
    Tower,
    Enemy,
    WaveConfig,
    GameState,
)


@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.fixture
def game():
    """Create a fresh TowerDefenseGame"""
    return TowerDefenseGame(game_id="test-game")


# --- Tower Upgrade Tests ---


class TestTowerUpgrade:
    """Tests for tower upgrade mechanics"""

    def test_upgrade_increases_damage(self, game):
        """Tower upgrade increases damage"""
        success, msg, tower = game.place_tower(1, 1, TowerType.ARCHER)
        assert success

        dmg_before = tower.damage
        game.state.leaves = 500  # Ensure enough for upgrade
        game.upgrade_tower(tower.id)

        assert tower.damage[0] > dmg_before[0]
        assert tower.damage[1] > dmg_before[1]

    def test_upgrade_increases_range(self, game):
        """Tower upgrade increases range"""
        success, msg, tower = game.place_tower(1, 1, TowerType.ARCHER)
        assert success

        range_before = tower.range
        game.state.leaves = 500
        game.upgrade_tower(tower.id)

        assert tower.range > range_before

    def test_upgrade_deducts_leaves(self, game):
        """Upgrade cost is deducted from leaves"""
        game.place_tower(1, 1, TowerType.ARCHER)
        tower = game.towers[0]

        leaves_before = game.state.leaves
        upgrade_cost = tower.upgrade_cost
        success, msg = game.upgrade_tower(tower.id)
        assert success

        assert game.state.leaves == leaves_before - upgrade_cost

    def test_upgrade_insufficient_leaves(self, game):
        """Cannot upgrade tower with insufficient leaves"""
        game.place_tower(1, 1, TowerType.ARCHER)
        tower = game.towers[0]

        game.state.leaves = 0  # No leaves
        success, msg = game.upgrade_tower(tower.id)
        assert not success
        assert "insuficientes" in msg.lower() or "Folhas" in msg

    def test_upgrade_nonexistent_tower(self, game):
        """Upgrading a nonexistent tower fails"""
        success, msg = game.upgrade_tower("fake-tower-id")
        assert not success


# --- Tower Sell Tests ---


class TestTowerSell:
    """Tests for tower sell mechanics"""

    def test_sell_returns_correct_value(self, game):
        """Sell tower returns 50% of total invested"""
        game.place_tower(1, 1, TowerType.ARCHER)
        tower = game.towers[0]

        expected_sell = tower.sell_value
        success, msg, value = game.sell_tower(tower.id)
        assert success
        assert value == expected_sell

    def test_sell_adds_leaves(self, game):
        """Selling a tower adds leaves back"""
        game.place_tower(1, 1, TowerType.ARCHER)
        tower = game.towers[0]

        leaves_before = game.state.leaves
        sell_value = tower.sell_value
        game.sell_tower(tower.id)

        assert game.state.leaves == leaves_before + sell_value

    def test_sell_removes_tower(self, game):
        """Selling removes the tower from the game"""
        game.place_tower(1, 1, TowerType.ARCHER)
        assert len(game.towers) == 1

        game.sell_tower(game.towers[0].id)
        assert len(game.towers) == 0

    def test_sell_nonexistent_tower(self, game):
        """Selling nonexistent tower fails"""
        success, msg, value = game.sell_tower("fake-id")
        assert not success
        assert value == 0


# --- Tower Stats Tests ---


class TestTowerStats:
    """Tests for tower type stats"""

    def test_archer_attack_speed(self):
        """Archer tower has correct attack speed"""
        tower = Tower(id="t1", tower_type=TowerType.ARCHER, x=0, y=0)
        assert tower.attack_speed == 0.8

    def test_bomb_attack_speed(self):
        """Bomb tower has correct attack speed"""
        tower = Tower(id="t1", tower_type=TowerType.BOMB, x=0, y=0)
        assert tower.attack_speed == 2.5

    def test_ice_attack_speed(self):
        """Ice tower has correct attack speed"""
        tower = Tower(id="t1", tower_type=TowerType.ICE, x=0, y=0)
        assert tower.attack_speed == 1.2

    def test_archer_cost(self):
        """Archer tower costs 50"""
        tower = Tower(id="t1", tower_type=TowerType.ARCHER, x=0, y=0)
        assert tower.cost == 50

    def test_bomb_cost(self):
        """Bomb tower costs 120"""
        tower = Tower(id="t1", tower_type=TowerType.BOMB, x=0, y=0)
        assert tower.cost == 120

    def test_ice_cost(self):
        """Ice tower costs 80"""
        tower = Tower(id="t1", tower_type=TowerType.ICE, x=0, y=0)
        assert tower.cost == 80


# --- Enemy Stats Tests ---


class TestEnemyStats:
    """Tests for enemy type stats"""

    def test_fly_stats(self, game):
        """Fly enemy has correct stats"""
        stats = game._get_enemy_stats(EnemyType.FLY)
        assert stats["hp"] == 30
        assert stats["speed"] == 2.0
        assert stats["reward"] == 8

    def test_beetle_stats(self, game):
        """Beetle enemy has correct stats"""
        stats = game._get_enemy_stats(EnemyType.BEETLE)
        assert stats["hp"] == 120
        assert stats["speed"] == 0.8
        assert stats["reward"] == 18

    def test_sky_bug_stats(self, game):
        """Sky bug enemy has correct stats"""
        stats = game._get_enemy_stats(EnemyType.SKY_BUG)
        assert stats["hp"] == 50
        assert stats["speed"] == 1.5
        assert stats["reward"] == 12


# --- Wave and Game State Tests ---


class TestWaveSystem:
    """Tests for wave system"""

    def test_start_wave_activates(self, game):
        """Starting a wave sets wave_active True"""
        success, msg = game.start_wave()
        assert success
        assert game.wave_active
        assert game.state.current_wave == 1

    def test_cannot_double_start_wave(self, game):
        """Cannot start wave while one is active"""
        game.start_wave()
        success, msg = game.start_wave()
        assert not success

    def test_cannot_start_wave_after_game_over(self, game):
        """Cannot start wave after game over"""
        game.state.game_over = True
        success, msg = game.start_wave()
        assert not success

    def test_cannot_start_wave_after_victory(self, game):
        """Cannot start wave after victory"""
        game.state.victory = True
        success, msg = game.start_wave()
        assert not success

    def test_sequential_waves(self, game):
        """Can start wave 2 after completing wave 1"""
        game.start_wave()
        # Complete wave by clearing enemies and remaining
        game.wave_enemies_remaining.clear()
        game.enemies.clear()
        game.update(0.016)  # Should detect wave complete

        assert not game.wave_active

        success, msg = game.start_wave()
        assert success
        assert game.state.current_wave == 2


class TestGameOver:
    """Tests for game over and victory conditions"""

    def test_game_over_when_lives_zero(self, game):
        """Game over when lives reach 0"""
        game.state.lives = 0
        game.state.game_over = True
        assert game.state.game_over

    def test_reset_restores_initial_state(self, game):
        """Reset restores the game to initial state"""
        # Modify state
        game.state.leaves = 999
        game.state.lives = 1
        game.state.score = 5000
        game.state.current_wave = 5
        game.state.game_over = True
        game.place_tower(1, 1, TowerType.ARCHER)

        game.reset()

        assert game.state.leaves == 100
        assert game.state.lives == 20
        assert game.state.score == 0
        assert game.state.current_wave == 0
        assert not game.state.game_over
        assert len(game.towers) == 0
        assert len(game.enemies) == 0


# --- Tower Placement Edge Cases ---


class TestTowerPlacement:
    """Tests for tower placement edge cases"""

    def test_place_on_occupied_cell(self, game):
        """Cannot place tower where another tower exists"""
        game.place_tower(1, 1, TowerType.ARCHER)
        success, msg, _ = game.place_tower(1, 1, TowerType.BOMB)
        assert not success

    def test_custom_path(self):
        """Custom path works correctly"""
        custom = [(0, 0), (1, 0), (2, 0), (3, 0)]
        game = TowerDefenseGame(custom_path=custom)
        assert game.path == custom
        # Path cells should be marked as occupied
        for x, y in custom:
            assert game.occupied_grid[x][y] is True

    def test_default_wave_configs(self):
        """Default wave configs have 10 waves"""
        configs = WaveConfig.get_default_waves()
        assert len(configs) == 10


# --- Integration with main app ---


class TestIntegration:
    """Integration tests with the main FastAPI app"""

    @pytest.mark.asyncio
    async def test_tower_defense_router_mounted(self, transport):
        """Tower defense router IS mounted in main app"""
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/tower-defense/")
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "Ant Defense"

    @pytest.mark.asyncio
    async def test_tower_defense_create_game(self, transport):
        """POST /tower-defense/games/create creates a game"""
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/tower-defense/games/create")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert "game_id" in data
            assert "initial_state" in data

    @pytest.mark.asyncio
    async def test_tower_defense_get_game(self, transport):
        """GET /tower-defense/games/{game_id} returns state"""
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            create = await ac.post("/tower-defense/games/create")
            game_id = create.json()["game_id"]

            resp = await ac.get(f"/tower-defense/games/{game_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["state"]["id"] == game_id

    @pytest.mark.asyncio
    async def test_tower_defense_get_nonexistent_game_404(self, transport):
        """GET /tower-defense/games/{game_id} for unknown id returns 404"""
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/tower-defense/games/fake-id")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_play_tower_defense_exists(self, transport):
        """/play/tower_defense route exists and returns 200"""
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/play/tower_defense")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_state_structure(self):
        """get_state returns expected structure"""
        game = TowerDefenseGame()
        state = game.get_state()

        assert "state" in state
        assert "towers" in state
        assert "enemies" in state
        assert "path" in state
        assert "wave_active" in state
        assert "occupied_cells" in state
        assert state["state"]["leaves"] == 100
        assert state["state"]["lives"] == 20
