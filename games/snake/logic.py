"""
Snake Game Logic
Modern implementation of the classic Snake game
"""

from typing import List, Tuple, Optional
from enum import Enum
import random


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class SnakeGame:
    def __init__(self, width: int = 20, height: int = 20):
        self.width = width
        self.height = height
        self.reset()
    
    def reset(self):
        """Reset game to initial state"""
        # Start snake in the middle
        start_x = self.width // 2
        start_y = self.height // 2
        
        self.snake: List[Tuple[int, int]] = [
            (start_x, start_y),
            (start_x, start_y + 1),
            (start_x, start_y + 2)
        ]
        self.direction = Direction.UP
        self.next_direction = Direction.UP
        self.food: Optional[Tuple[int, int]] = None
        self.score = 0
        self.game_over = False
        self.paused = False
        self.speed = 150  # milliseconds between moves
        self._spawn_food()
    
    def _spawn_food(self):
        """Spawn food at a random position not occupied by snake"""
        empty_positions = []
        for x in range(self.width):
            for y in range(self.height):
                if (x, y) not in self.snake:
                    empty_positions.append((x, y))
        
        if empty_positions:
            self.food = random.choice(empty_positions)
        else:
            self.food = None  # Snake fills entire grid - win condition
    
    def set_direction(self, direction: Direction):
        """Set next direction (validated to prevent 180° turns)"""
        if self.game_over or self.paused:
            return
        
        # Prevent 180° turns
        opposite_directions = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }
        
        if opposite_directions.get(direction) != self.direction:
            self.next_direction = direction
    
    def update(self) -> bool:
        """
        Update game state. Returns True if game continues, False if game over.
        """
        if self.game_over or self.paused:
            return not self.game_over
        
        self.direction = self.next_direction
        
        # Calculate new head position
        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)
        
        # Check wall collision
        if not (0 <= new_head[0] < self.width and 0 <= new_head[1] < self.height):
            self.game_over = True
            return False
        
        # Check self collision
        if new_head in self.snake[:-1]:  # Exclude tail as it will move
            self.game_over = True
            return False
        
        # Move snake
        self.snake.insert(0, new_head)
        
        # Check food collision
        if self.food and new_head == self.food:
            self.score += 10
            # Increase speed slightly
            self.speed = max(50, self.speed - 2)
            self._spawn_food()
        else:
            self.snake.pop()  # Remove tail if no food eaten
        
        # Check win condition (snake fills entire grid)
        if len(self.snake) == self.width * self.height:
            self.game_over = True
            return False
        
        return True
    
    def get_state(self) -> dict:
        """Get current game state as dictionary"""
        return {
            'snake': self.snake,
            'food': self.food,
            'direction': self.direction.name,
            'score': self.score,
            'game_over': self.game_over,
            'paused': self.paused,
            'speed': self.speed,
            'width': self.width,
            'height': self.height
        }
    
    def toggle_pause(self):
        """Toggle pause state"""
        if not self.game_over:
            self.paused = not self.paused
    
    def get_grid(self) -> List[List[int]]:
        """
        Get grid representation for rendering
        0 = empty, 1 = snake body, 2 = snake head, 3 = food
        """
        grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        # Place food
        if self.food:
            fx, fy = self.food
            grid[fy][fx] = 3
        
        # Place snake body
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                grid[y][x] = 2  # Head
            else:
                grid[y][x] = 1  # Body
        
        return grid
