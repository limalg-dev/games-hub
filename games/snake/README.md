# Snake Game

Modern implementation of the classic Snake game for the Checkers Platform.

## Features

- 🐍 Classic snake gameplay with modern graphics
- 🎮 Keyboard controls (Arrow keys or WASD)
- 📱 Mobile-friendly with touch controls
- ⚡ Progressive speed increase as you score
- 🏆 High score persistence using localStorage
- ⏸️ Pause/Resume functionality
- 🎨 Beautiful gradient visuals and animations

## How to Play

1. Click "Start Game" to begin
2. Use Arrow Keys or WASD to control the snake
3. Eat the red food to grow and increase your score
4. Avoid hitting walls or yourself
5. Try to achieve the highest score possible!

## API Endpoints

- `GET /api/snake` - Get game information
- `POST /api/snake/new` - Create a new game
- `GET /api/snake/{game_id}` - Get game state
- `POST /api/snake/{game_id}/direction` - Set snake direction
- `POST /api/snake/{game_id}/update` - Update game state
- `POST /api/snake/{game_id}/pause` - Toggle pause
- `DELETE /api/snake/{game_id}` - Delete game
- `WS /api/ws/snake/{game_id}` - WebSocket for real-time updates

## Controls

- **Arrow Up / W**: Move Up
- **Arrow Down / S**: Move Down
- **Arrow Left / A**: Move Left
- **Arrow Right / D**: Move Right
- **Space**: Pause/Resume

## Technical Details

- Grid size: 20x20 (customizable)
- Initial speed: 150ms per move
- Minimum speed: 50ms per move
- Speed increase: 2ms per food eaten
- Score: 10 points per food

## Running Tests

```bash
python -m pytest games/snake/tests.py -v
```

## Access the Game

Once the server is running, access the game at:
- http://localhost:8000/play/snake
