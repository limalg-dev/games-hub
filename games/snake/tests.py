"""
Snake Game Tests
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from logic import SnakeGame, Direction


class TestSnakeGame:
    """Test snake game logic"""
    
    def test_initial_state(self):
        """Test initial game state"""
        game = SnakeGame()
        state = game.get_state()
        
        assert len(game.snake) == 3
        assert state['score'] == 0
        assert not state['game_over']
        assert not state['paused']
        assert state['width'] == 20
        assert state['height'] == 20
    
    def test_snake_position(self):
        """Test snake starts in the middle"""
        game = SnakeGame()
        start_x = game.width // 2
        start_y = game.height // 2
        
        # Snake should be vertical pointing up
        assert game.snake[0] == (start_x, start_y)
        assert game.snake[1] == (start_x, start_y + 1)
        assert game.snake[2] == (start_x, start_y + 2)
    
    def test_direction_change(self):
        """Test direction changes"""
        game = SnakeGame()
        
        # Should be able to change to right
        game.set_direction(Direction.RIGHT)
        assert game.next_direction == Direction.RIGHT
        
        # After queuing RIGHT, DOWN is a legal 90° turn (not a 180° reversal)
        game.set_direction(Direction.DOWN)
        assert game.next_direction == Direction.DOWN
        
        # Reset and test properly
        game2 = SnakeGame()
        game2.direction = Direction.UP
        game2.next_direction = Direction.UP
        
        # Try to reverse direction (should be blocked)
        game2.set_direction(Direction.DOWN)
        assert game2.next_direction == Direction.UP  # Still UP, reversal blocked
    
    def test_move_right(self):
        """Test moving right"""
        game = SnakeGame()
        game.set_direction(Direction.RIGHT)
        
        initial_head = game.snake[0]
        game.update()
        new_head = game.snake[0]
        
        assert new_head[0] == initial_head[0] + 1
        assert new_head[1] == initial_head[1]
    
    def test_eat_food(self):
        """Test eating food increases score and snake length"""
        game = SnakeGame()
        initial_length = len(game.snake)
        initial_score = game.score
        
        # Place food next to head
        head_x, head_y = game.snake[0]
        game.food = (head_x, head_y - 1)  # Above head
        game.set_direction(Direction.UP)
        
        game.update()
        
        assert len(game.snake) == initial_length + 1
        assert game.score == initial_score + 10
    
    def test_wall_collision(self):
        """Test wall collision ends game"""
        game = SnakeGame(width=5, height=5)
        game.snake = [(0, 0)]  # Top-left corner
        game.set_direction(Direction.UP)
        
        result = game.update()
        
        assert not result
        assert game.game_over
    
    def test_self_collision(self):
        """Test self collision ends game"""
        game = SnakeGame(width=5, height=5)
        game.snake = [(2, 2), (2, 1), (1, 1), (1, 2), (2, 2)]  # Loop back to head
        game.set_direction(Direction.DOWN)
        
        result = game.update()
        
        assert not result
        assert game.game_over
    
    def test_pause(self):
        """Test pause functionality"""
        game = SnakeGame()
        
        assert not game.paused
        game.toggle_pause()
        assert game.paused
        game.toggle_pause()
        assert not game.paused
    
    def test_grid_representation(self):
        """Test grid representation"""
        game = SnakeGame(width=5, height=5)
        grid = game.get_grid()
        
        assert len(grid) == 5
        assert len(grid[0]) == 5
        
        # Check snake positions
        for x, y in game.snake:
            if (x, y) == game.snake[0]:
                assert grid[y][x] == 2  # Head
            else:
                assert grid[y][x] == 1  # Body
        
        # Check food position
        if game.food:
            fx, fy = game.food
            assert grid[fy][fx] == 3
    
    def test_speed_increase(self):
        """Test speed increases when eating food"""
        game = SnakeGame()
        initial_speed = game.speed
        
        # Place food and eat it multiple times
        for _ in range(5):
            head_x, head_y = game.snake[0]
            game.food = (head_x, head_y - 1)
            game.set_direction(Direction.UP)
            game.update()
        
        assert game.speed < initial_speed
        assert game.speed >= 50  # Minimum speed
    
    def test_custom_size(self):
        """Test custom grid size"""
        game = SnakeGame(width=30, height=15)
        
        assert game.width == 30
        assert game.height == 15
        assert len(game.get_grid()) == 15
        assert len(game.get_grid()[0]) == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
