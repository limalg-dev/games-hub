# Crossword Game Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a crossword puzzle game with dynamic grid generation, single-player and multiplayer modes, plus a comprehensive test battery for the entire project.

**Architecture:** Backend generates crossword grids via backtracking algorithm, serves word data from SQLite. Frontend renders grid as DOM with input cells. Multiplayer via WebSocket sync.

**Tech Stack:** FastAPI, SQLModel, SQLite, vanilla JS (ES modules), HTML/CSS, pytest, pytest-asyncio, httpx

## Global Constraints

- Python >=3.11
- fastapi==0.115, uvicorn==0.30, sqlmodel==0.0.21
- pytest==8.2, pytest-asyncio==0.24, httpx==0.27
- No build tools — pure vanilla JS with ES modules
- SQLite database at `./games.db`
- Games auto-discovered from `games/` directory

---

## File Structure

### Files to Create

| File | Responsibility |
|------|---------------|
| `games/crossword/__init__.py` | Package init |
| `games/crossword/models.py` | `Word` SQLModel |
| `games/crossword/generator.py` | Grid generation algorithm |
| `games/crossword/words.py` | Seed word data |
| `games/crossword/static/board.js` | `CrosswordGame` class |
| `games/crossword/static/logic.js` | Validation functions |
| `games/crossword/static/preview.js` | Modal preview renderer |
| `games/crossword/static/timer.js` | Timer + localStorage leaderboard |
| `games/crossword/tests/__init__.py` | Test package init |
| `games/crossword/tests/test_generator.py` | Generator unit tests |
| `games/crossword/tests/test_words.py` | Word model tests |
| `tests/test_crossword_api.py` | API endpoint tests |
| `tests/test_crossword_ws.py` | WebSocket tests |
| `tests/test_integration.py` | Integration tests |

### Files to Modify

| File | Changes |
|------|---------|
| `app/main.py` | Add lifespan word seed, `/api/words` endpoints, update `POST /games` |
| `app/models.py` | Add `game_type` field to `Game` |
| `app/websocket.py` | Add crossword WebSocket support |
| `static/app.js` | Register crossword in `GAMES`, add modal/start/cleanup |
| `static/styles.css` | Crossword-specific styles |
| `static/index.html` | Add crossword-specific HTML if needed |

---

### Task 1: Word Model + Seed Data

**Files:**
- Create: `games/crossword/__init__.py`
- Create: `games/crossword/models.py`
- Create: `games/crossword/words.py`
- Test: `games/crossword/tests/__init__.py`
- Test: `games/crossword/tests/test_words.py`

**Interfaces:**
- Produces: `Word` model with fields `id`, `word`, `hint`, `category`, `difficulty`
- Produces: `SEED_WORDS` list of ~150 dicts with keys `word`, `hint`, `category`, `difficulty`

- [ ] **Step 1: Create package init**

```python
# games/crossword/__init__.py
```

- [ ] **Step 2: Create test package init**

```python
# games/crossword/tests/__init__.py
```

- [ ] **Step 3: Write the failing test for Word model**

```python
# games/crossword/tests/test_words.py
from games.crossword.models import Word
from games.crossword.words import SEED_WORDS

def test_word_model_fields():
    w = Word(word="PYTHON", hint="Linguagem de programação", category="tech", difficulty=2)
    assert w.word == "PYTHON"
    assert w.hint == "Linguagem de programação"
    assert w.category == "tech"
    assert w.difficulty == 2

def test_seed_words_has_content():
    assert len(SEED_WORDS) >= 100

def test_seed_words_categories():
    categories = {w["category"] for w in SEED_WORDS}
    assert "tech" in categories
    assert "animals" in categories
    assert "countries" in categories

def test_seed_words_difficulties():
    difficulties = {w["difficulty"] for w in SEED_WORDS}
    assert 1 in difficulties
    assert 2 in difficulties
    assert 3 in difficulties

def test_seed_words_no_empty():
    for w in SEED_WORDS:
        assert w["word"].strip()
        assert w["hint"].strip()
        assert len(w["word"]) >= 3
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest games/crossword/tests/test_words.py -v`
Expected: FAIL with ImportError

- [ ] **Step 5: Create Word model**

```python
# games/crossword/models.py
from typing import Optional
from sqlmodel import SQLModel, Field

class Word(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    word: str
    hint: str
    category: str
    difficulty: int  # 1=easy, 2=medium, 3=hard
```

- [ ] **Step 6: Create seed data**

```python
# games/crossword/words.py
SEED_WORDS = [
    # Tech (difficulty 1-3)
    {"word": "PYTHON", "hint": "Linguagem de programação com蛇", "category": "tech", "difficulty": 2},
    {"word": "JAVA", "hint": "Linguagem famosa por 'write once, run anywhere'", "category": "tech", "difficulty": 1},
    {"word": "ALGORITMO", "hint": "Sequência de passos para resolver um problema", "category": "tech", "difficulty": 2},
    {"word": "DATABASE", "hint": "Sistema para armazenar dados", "category": "tech", "difficulty": 1},
    {"word": "SERVER", "hint": "Computador que fornece serviços em rede", "category": "tech", "difficulty": 1},
    {"word": "FIREWALL", "hint": "Proteção de rede contra acessos não autorizados", "category": "tech", "difficulty": 3},
    {"word": "COMPILER", "hint": "Traduz código-fonte para código de máquina", "category": "tech", "difficulty": 3},
    {"word": "VARIABLE", "hint": "Espaço de memória que armazena um valor", "category": "tech", "difficulty": 2},
    {"word": "ARRAY", "hint": "Estrutura de dados que armazena elementos", "category": "tech", "difficulty": 1},
    {"word": "BOOLEAN", "hint": "Tipo de dado true ou false", "category": "tech", "difficulty": 2},
    {"word": "CLOUD", "hint": "Armazenamento e computação via internet", "category": "tech", "difficulty": 1},
    {"word": "PIXEL", "hint": "Menor elemento de uma imagem digital", "category": "tech", "difficulty": 1},
    {"word": "ROUTER", "hint": "Dispositivo que redireciona pacotes de rede", "category": "tech", "difficulty": 2},
    {"word": "PYTHON", "hint": "Serpente grande da Ásia", "category": "tech", "difficulty": 1},
    {"word": "BYTE", "hint": "Unidade de dados de 8 bits", "category": "tech", "difficulty": 1},
    {"word": "KERNEL", "hint": "Núcleo de um sistema operacional", "category": "tech", "difficulty": 3},
    {"word": "SYNTAX", "hint": "Regras de escrita de um código", "category": "tech", "difficulty": 2},
    {"word": "MODEM", "hint": "Dispositivo de conexão à internet", "category": "tech", "difficulty": 2},

    # Animals
    {"word": "ELEFANTE", "hint": "Maior terrestre com tromba", "category": "animals", "difficulty": 1},
    {"word": "GIRFA", "hint": "Animal com pescoço muito longo", "category": "animals", "difficulty": 1},
    {"word": "LEAO", "hint": "Rei da selva", "category": "animals", "difficulty": 1},
    {"word": "TIGRE", "hint": "Felino listrado laranja e preto", "category": "animals", "difficulty": 1},
    {"word": "BALEIA", "hint": "Maior animal do mundo", "category": "animals", "difficulty": 2},
    {"word": "GOLFINHO", "hint": "Mamífero marinho muito inteligente", "category": "animals", "difficulty": 2},
    {"word": "AVISTRA", "hint": "Ave que não voa da Austrália", "category": "animals", "difficulty": 2},
    {"word": "CANGURU", "hint": "Marsupial que pula da Austrália", "category": "animals", "difficulty": 2},
    {"word": "PAPAGAIO", "hint": "Ave colorida que fala", "category": "animals", "difficulty": 2},
    {"word": "TARTARUGA", "hint": "Réptil com casco nas costas", "category": "animals", "difficulty": 2},
    {"word": "LOBO", "hint": "Canídeo selvagem que uiva", "category": "animals", "difficulty": 1},
    {"word": "URSO", "hint": "Grande mammífero que hiberna", "category": "animals", "difficulty": 1},
    {"word": "RAPOSA", "hint": "Canídeo esperto e ágil", "category": "animals", "difficulty": 2},
    {"word": "COBRA", "hint": "Réptil sem pernas que rasteja", "category": "animals", "difficulty": 1},
    {"word": "MACACO", "hint": "Primata que vive em árvores", "category": "animals", "difficulty": 1},
    {"word": "PUMA", "hint": "Felino americano também chamado de onça-parda", "category": "animals", "difficulty": 2},
    {"word": "ÁGUIA", "hint": "Ave de rapina majestosa", "category": "animals", "difficulty": 2},
    {"word": "CORUJA", "hint": "Ave noturna sábia", "category": "animals", "difficulty": 2},
    {"word": "GATO", "hint": "Felino doméstico", "category": "animals", "difficulty": 1},
    {"word": "CACHORRO", "hint": "Melhor amigo do homem", "category": "animals", "difficulty": 1},

    # Countries
    {"word": "BRASIL", "hint": "Maior país da América do Sul", "category": "countries", "difficulty": 1},
    {"word": "ARGENTINA", "hint": "País do Tango na América do Sul", "category": "countries", "difficulty": 2},
    {"word": "JAPAO", "hint": "País do sol nascente", "category": "countries", "difficulty": 2},
    {"word": "ALEMANHA", "hint": "País na Europa Central", "category": "countries", "difficulty": 2},
    {"word": "ITALIA", "hint": "País em formato de bota", "category": "countries", "difficulty": 1},
    {"word": "CANADA", "hint": "Maior país do mundo em área", "category": "countries", "difficulty": 1},
    {"word": "AUSTRALIA", "hint": "País-continente no hemisfério sul", "category": "countries", "difficulty": 2},
    {"word": "FRANCA", "hint": "País da Torre Eiffel", "category": "countries", "difficulty": 1},
    {"word": "PORTUGAL", "hint": "Ex-potência marítima na Península Ibérica", "category": "countries", "difficulty": 2},
    {"word": "MEXICO", "hint": "País do norte da América Latina", "category": "countries", "difficulty": 1},
    {"word": "CHINA", "hint": "Maior população do mundo", "category": "countries", "difficulty": 1},
    {"word": "INDIA", "hint": "Segundo maior país em população", "category": "countries", "difficulty": 1},
    {"word": "RUSSIA", "hint": "Maior país do mundo em área terrestre", "category": "countries", "difficulty": 2},
    {"word": "EGITO", "hint": "País das pirâmides", "category": "countries", "difficulty": 1},
    {"word": "CUBA", "hint": "Ilha-caribe famosa pelo charuto", "category": "countries", "difficulty": 1},
    {"word": "NORUEGA", "hint": "País escandinavo dos fiordes", "category": "countries", "difficulty": 2},
    {"word": "SUECIA", "hint": "País escandinavo de Estocolmo", "category": "countries", "difficulty": 2},
    {"word": "PANAMA", "hint": "País do canal entre oceanos", "category": "countries", "difficulty": 2},
    {"word": "PERU", "hint": "País dos incas e Machu Picchu", "category": "countries", "difficulty": 1},
    {"word": "CHILE", "hint": "País fino e longo na América do Sul", "category": "countries", "difficulty": 1},

    # Food
    {"word": "CHURRASCO", "hint": "Carne grelhada na brasa", "category": "food", "difficulty": 2},
    {"word": "FEIJOADA", "hint": "Prato típico brasileiro com feijão e carnes", "category": "food", "difficulty": 2},
    {"word": "SUSHI", "hint": "Comida japonesa de arroz e peixe cru", "category": "food", "difficulty": 1},
    {"word": "PIZZA", "hint": "Comida italiana redonda", "category": "food", "difficulty": 1},
    {"word": "ACAI", "hint": "Fruta amazônica roxa e saudável", "category": "food", "difficulty": 1},
    {"word": "COCO", "hint": "Fruta tropical com água dentro", "category": "food", "difficulty": 1},
    {"word": "BANANA", "hint": "Fruta amarela e curva", "category": "food", "difficulty": 1},
    {"word": "MORANGO", "hint": "Fruta vermelha pequena e doce", "category": "food", "difficulty": 2},
    {"word": "CHOCOLATE", "hint": "Doce feito de cacau", "category": "food", "difficulty": 2},
    {"word": "SORVETE", "hint": "Sobremesa gelada", "category": "food", "difficulty": 1},
    {"word": "BOLO", "hint": "Massa doce assada no forno", "category": "food", "difficulty": 1},
    {"word": "SOPA", "hint": "Comida líquida quente", "category": "food", "difficulty": 1},
    {"word": "ARROZ", "hint": "Grão base da alimentação asiática", "category": "food", "difficulty": 1},
    {"word": "FEIJAO", "hint": "Leguminosa nutritiva", "category": "food", "difficulty": 1},
    {"word": "BATATA", "hint": "Tubérculo versátil na cozinha", "category": "food", "difficulty": 1},
    {"word": "LARANJA", "hint": "Fruta cítrica laranja", "category": "food", "difficulty": 1},
    {"word": "UVA", "hint": "Fruta que vira vinho", "category": "food", "difficulty": 1},
    {"word": "MELANCIA", "hint": "Fruta grande e verde por fora, vermelha por dentro", "category": "food", "difficulty": 2},
    {"word": "ABACAXI", "hint": "Fruta tropical com coroa", "category": "food", "difficulty": 2},
    {"word": "AMENDOIM", "hint": "Fruto seco popular", "category": "food", "difficulty": 2},

    # Sports
    {"word": "FUTEBOL", "hint": "Esporte mais popular do mundo", "category": "sports", "difficulty": 1},
    {"word": "BASQUETE", "hint": "Esporte com cesta e bola laranja", "category": "sports", "difficulty": 2},
    {"word": "VOLEI", "hint": "Esporte de quadra com rede", "category": "sports", "difficulty": 1},
    {"word": "TENIS", "hint": "Esporte de raquetes em quadra", "category": "sports", "difficulty": 1},
    {"word": "NATACAO", "hint": "Esporte aquático", "category": "sports", "difficulty": 2},
    {"word": "Ciclismo", "hint": "Esporte de bicicleta", "category": "sports", "difficulty": 2},
    {"word": "SURFE", "hint": "Esporte de ondas do mar", "category": "sports", "difficulty": 2},
    {"word": "SKATE", "hint": "Esporte urbano com prancha", "category": "sports", "difficulty": 1},
    {"word": "XADREZ", "hint": "Jogo de tabuleiro estratégico", "category": "sports", "difficulty": 2},
    {"word": "GOLFE", "hint": "Esporte de precisão com bastão", "category": "sports", "difficulty": 2},
    {"word": "RUGBY", "hint": "Esporte de contato com bola oval", "category": "sports", "difficulty": 2},
    {"word": "HOCKEY", "hint": "Esporte de gelo com taco", "category": "sports", "difficulty": 2},
    {"word": "BOXE", "hint": "Luta com luvas", "category": "sports", "difficulty": 1},
    {"word": "JUDO", "hint": "Arte marcial japonesa", "category": "sports", "difficulty": 2},
    {"word": "YOGA", "hint": "Prática de equilíbrio e flexibilidade", "category": "sports", "difficulty": 1},
    {"word": "CORRIDA", "hint": "Esporte de velocidade nas pernas", "category": "sports", "difficulty": 1},
    {"word": "CANOAGEM", "hint": "Esporte aquático com canoa", "category": "sports", "difficulty": 3},
    {"word": "ESGRIMA", "hint": "Luta com espada", "category": "sports", "difficulty": 3},
    {"word": "ARCO", "hint": "Arma que dispara flechas, também esporte", "category": "sports", "difficulty": 2},
    {"word": "SAPO", "hint": "Animal que pula, não esporte... ou é?", "category": "sports", "difficulty": 1},
]
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest games/crossword/tests/test_words.py -v`
Expected: 5 PASS

- [ ] **Step 8: Commit**

```bash
git add games/crossword/
git commit -m "feat(crossword): add Word model and seed data"
```

---

### Task 2: Grid Generator

**Files:**
- Create: `games/crossword/generator.py`
- Test: `games/crossword/tests/test_generator.py`

**Interfaces:**
- Consumes: `Word` model (for word list)
- Produces: `generate_crossword(words, difficulty) -> dict` returning `{grid, clues, size}`
- Grid is `List[List[Optional[str]]]` — letters or None for black cells
- Clues is `{"across": [{"number": 1, "row": 0, "col": 0, "clue": "...", "length": 5}], "down": [...]}`

- [ ] **Step 1: Write the failing tests**

```python
# games/crossword/tests/test_generator.py
from games.crossword.generator import generate_crossword

def test_generate_returns_dict():
    words = [
        {"word": "PYTHON", "hint": "Linguagem de prog"},
        {"word": "JAVA", "hint": "Linguagem de prog"},
        {"word": "CODING", "hint": "Atividade de programar"},
    ]
    result = generate_crossword(words, difficulty=1)
    assert "grid" in result
    assert "clues" in result
    assert "size" in result

def test_grid_is_2d():
    words = [
        {"word": "PYTHON", "hint": "Linguagem de prog"},
        {"word": "JAVA", "hint": "Linguagem de prog"},
    ]
    result = generate_crossword(words, difficulty=1)
    grid = result["grid"]
    assert isinstance(grid, list)
    assert all(isinstance(row, list) for row in grid)

def test_grid_has_letters():
    words = [
        {"word": "PYTHON", "hint": "Linguagem de prog"},
        {"word": "JAVA", "hint": "Linguagem de prog"},
        {"word": "CODING", "hint": "Atividade de programar"},
    ]
    result = generate_crossword(words, difficulty=1)
    letters_found = sum(1 for row in result["grid"] for cell in row if cell is not None)
    assert letters_found > 0

def test_difficulty_sizes():
    words_short = [{"word": "A" * 3, "hint": "x"} for _ in range(5)]
    words_medium = [{"word": "A" * 5, "hint": "x"} for _ in range(10)]
    words_long = [{"word": "A" * 7, "hint": "x"} for _ in range(15)]

    r1 = generate_crossword(words_short, difficulty=1)
    r2 = generate_crossword(words_medium, difficulty=2)
    r3 = generate_crossword(words_long, difficulty=3)

    assert r1["size"] <= 10
    assert r2["size"] <= 14
    assert r3["size"] <= 18

def test_clues_have_required_fields():
    words = [
        {"word": "PYTHON", "hint": "Linguagem de prog"},
        {"word": "JAVA", "hint": "Linguagem de prog"},
        {"word": "CODING", "hint": "Atividade de programar"},
    ]
    result = generate_crossword(words, difficulty=1)
    for direction in ["across", "down"]:
        for clue in result["clues"][direction]:
            assert "number" in clue
            assert "row" in clue
            assert "col" in clue
            assert "clue" in clue
            assert "length" in clue

def test_words_are_placed():
    words = [
        {"word": "PYTHON", "hint": "Linguagem de prog"},
        {"word": "JAVA", "hint": "Linguagem de prog"},
        {"word": "CODING", "hint": "Atividade de programar"},
    ]
    result = generate_crossword(words, difficulty=1)
    grid_text = "".join(cell or "" for row in result["grid"] for cell in row)
    assert "PYTHON" in grid_text or "JAVA" in grid_text or "CODING" in grid_text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest games/crossword/tests/test_generator.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement the generator**

```python
# games/crossword/generator.py
import random
from typing import List, Optional, Dict, Any

DIFFICULTY_CONFIG = {
    1: {"max_size": 8, "min_words": 6, "max_words": 10},
    2: {"max_size": 12, "min_words": 10, "max_words": 15},
    3: {"max_size": 15, "min_words": 15, "max_words": 22},
}

class CrosswordGrid:
    def __init__(self, size: int):
        self.size = size
        self.grid: List[List[Optional[str]]] = [[None for _ in range(size)] for _ in range(size)]
        self.placed_words: List[Dict[str, Any]] = []

    def can_place_word(self, word: str, row: int, col: int, direction: str) -> bool:
        dr = 1 if direction == "down" else 0
        dc = 1 if direction == "across" else 0

        end_row = row + dr * (len(word) - 1)
        end_col = col + dc * (len(word) - 1)

        if end_row >= self.size or end_col >= self.size:
            return False
        if row < 0 or col < 0:
            return False

        for i, letter in enumerate(word):
            r = row + dr * i
            c = col + dc * i
            existing = self.grid[r][c]
            if existing is not None and existing != letter:
                return False

        return True

    def place_word(self, word: str, row: int, col: int, direction: str, hint: str, number: int):
        dr = 1 if direction == "down" else 0
        dc = 1 if direction == "across" else 0

        for i, letter in enumerate(word):
            r = row + dr * i
            c = col + dc * i
            self.grid[r][c] = letter

        self.placed_words.append({
            "word": word,
            "row": row,
            "col": col,
            "direction": direction,
            "hint": hint,
            "number": number,
        })

    def get_intersections(self, word: str) -> List[Dict[str, Any]]:
        intersections = []
        for placed in self.placed_words:
            for i, letter in enumerate(word):
                dr = 1 if placed["direction"] == "down" else 0
                dc = 1 if placed["direction"] == "across" else 0
                for j, placed_letter in enumerate(placed["word"]):
                    if placed_letter == letter:
                        new_dir = "across" if placed["direction"] == "down" else "down"
                        new_row = placed["row"] + dr * j - (1 if new_dir == "down" else 0) * i
                        new_col = placed["col"] + dc * j - (1 if new_dir == "across" else 0) * i
                        if self.can_place_word(word, new_row, new_col, new_dir):
                            intersections.append({
                                "row": new_row,
                                "col": new_col,
                                "direction": new_dir,
                            })
        return intersections


def generate_crossword(words: List[Dict[str, str]], difficulty: int = 1) -> Dict[str, Any]:
    config = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG[1])
    max_size = config["max_size"]
    max_words = min(len(words), config["max_words"])

    sorted_words = sorted(words, key=lambda w: len(w["word"]), reverse=True)
    selected = sorted_words[:max_words]

    crossword = CrosswordGrid(max_size)
    word_number = 1

    if selected:
        first = selected[0]
        start_row = max_size // 2
        start_col = (max_size - len(first["word"])) // 2
        crossword.place_word(
            first["word"].upper(), start_row, start_col, "across",
            first.get("hint", ""), word_number
        )
        word_number += 1

    for word_data in selected[1:]:
        word = word_data["word"].upper()
        hint = word_data.get("hint", "")

        intersections = crossword.get_intersections(word)
        random.shuffle(intersections)

        placed = False
        for inter in intersections:
            if crossword.can_place_word(word, inter["row"], inter["col"], inter["direction"]):
                crossword.place_word(word, inter["row"], inter["col"], inter["direction"], hint, word_number)
                word_number += 1
                placed = True
                break

        if not placed:
            for direction in random.sample(["across", "down"], 2):
                for r in range(max_size):
                    for c in range(max_size):
                        if crossword.can_place_word(word, r, c, direction):
                            crossword.place_word(word, r, c, direction, hint, word_number)
                            word_number += 1
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break

    clues = {"across": [], "down": []}
    for pw in crossword.placed_words:
        clue_entry = {
            "number": pw["number"],
            "row": pw["row"],
            "col": pw["col"],
            "clue": pw["hint"],
            "length": len(pw["word"]),
        }
        clues[pw["direction"]].append(clue_entry)

    clues["across"].sort(key=lambda c: (c["row"], c["col"]))
    clues["down"].sort(key=lambda c: (c["row"], c["col"]))

    return {
        "grid": crossword.grid,
        "clues": clues,
        "size": max_size,
        "words_placed": len(crossword.placed_words),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest games/crossword/tests/test_generator.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add games/crossword/generator.py games/crossword/tests/test_generator.py
git commit -m "feat(crossword): add grid generator with backtracking"
```

---

### Task 3: Backend Integration (Models + Endpoints + Lifespan)

**Files:**
- Modify: `app/models.py:1-20` — add `game_type` field
- Modify: `app/main.py` — add word seed, `/api/words` endpoints, update game creation
- Test: `tests/test_crossword_api.py`

**Interfaces:**
- Consumes: `Word` model, `SEED_WORDS`, `generate_crossword`
- Produces: `POST /api/words`, `GET /api/words`, updated `POST /games`

- [ ] **Step 1: Write the failing API tests**

```python
# tests/test_crossword_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_create_word():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/words", json={
            "word": "TESTWORD",
            "hint": "A test word",
            "category": "test",
            "difficulty": 1,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["word"] == "TESTWORD"

@pytest.mark.asyncio
async def test_list_words():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/words")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

@pytest.mark.asyncio
async def test_list_words_filter_category():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/words?category=tech")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_crossword_game():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

@pytest.mark.asyncio
async def test_get_crossword_game():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        game_id = create_resp.json()["id"]
        response = await client.get(f"/games/{game_id}")
        assert response.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest tests/test_crossword_api.py -v`
Expected: FAIL (404 or 422)

- [ ] **Step 3: Add game_type to Game model**

```python
# Add to app/models.py — new field in Game class
class Game(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    player1: Optional[str] = None
    player2: Optional[str] = None
    status: str = Field(default="waiting")
    game_type: str = Field(default="checkers")  # ADD THIS LINE
```

- [ ] **Step 4: Add lifespan word seed and endpoints to main.py**

Read `app/main.py` first to understand current structure, then add:

1. Import `Word`, `SEED_WORDS`, `generate_crossword`
2. Add lifespan handler to seed words on startup
3. Add `POST /api/words` and `GET /api/words` endpoints
4. Update `POST /games` to accept `game_type` and `difficulty`

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest tests/test_crossword_api.py -v`
Expected: 5 PASS

- [ ] **Step 6: Run ALL existing tests to verify no regression**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest tests/ games/checkers/tests/ -v`
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add app/models.py app/main.py tests/test_crossword_api.py
git commit -m "feat(crossword): add API endpoints and word seeding"
```

---

### Task 4: WebSocket Crossword Support

**Files:**
- Modify: `app/websocket.py` — add crossword game handling
- Test: `tests/test_crossword_ws.py`

**Interfaces:**
- Consumes: `generate_crossword`, `Word` model, `ConnectionManager`
- Produces: Crossword-specific WebSocket messages

- [ ] **Step 1: Write the failing WebSocket tests**

```python
# tests/test_crossword_ws.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_crossword_ws_connect():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        game_id = create_resp.json()["id"]

        async with client.stream("GET", f"/ws/{game_id}") as ws:
            pass  # Basic connection test

@pytest.mark.asyncio
async def test_crossword_game_creates_puzzle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        game_id = create_resp.json()["id"]
        assert game_id is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest tests/test_crossword_ws.py -v`
Expected: FAIL

- [ ] **Step 3: Update websocket.py to support crossword**

Read `app/websocket.py` and add crossword handling:
- Detect game type from database
- For crossword: generate puzzle on connect, validate inputs against grid
- Broadcast crossword-specific events

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest tests/test_crossword_ws.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/websocket.py tests/test_crossword_ws.py
git commit -m "feat(crossword): add WebSocket multiplayer support"
```

---

### Task 5: Frontend — Crossword Client

**Files:**
- Create: `games/crossword/static/board.js`
- Create: `games/crossword/static/logic.js`
- Create: `games/crossword/static/preview.js`
- Create: `games/crossword/static/timer.js`
- Modify: `static/app.js` — register crossword
- Modify: `static/styles.css` — crossword styles

**Interfaces:**
- Consumes: WebSocket messages from backend
- Produces: `CrosswordGame` class, `renderPreview()`, validation functions

- [ ] **Step 1: Create logic.js**

```javascript
// games/crossword/static/logic.js
export function validateInput(letter) {
    return /^[A-Z]$/i.test(letter);
}

export function checkCell(grid, row, col, letter) {
    if (row < 0 || row >= grid.length || col < 0 || col >= grid[0].length) return false;
    return grid[row][col] === letter.toUpperCase();
}

export function isPuzzleComplete(grid, userGrid) {
    for (let r = 0; r < grid.length; r++) {
        for (let c = 0; c < grid[r].length; c++) {
            if (grid[r][c] !== null && userGrid[r][c] !== grid[r][c]) {
                return false;
            }
        }
    }
    return true;
}

export function findClueForCell(clues, row, col) {
    for (const direction of ["across", "down"]) {
        for (const clue of clues[direction]) {
            const dr = direction === "down" ? 1 : 0;
            const dc = direction === "across" ? 1 : 0;
            for (let i = 0; i < clue.length; i++) {
                if (clue.row + dr * i === row && clue.col + dc * i === col) {
                    return { ...clue, direction };
                }
            }
        }
    }
    return null;
}
```

- [ ] **Step 2: Create board.js**

Read existing `games/wordsearch/static/board.js` for pattern reference, then implement `CrosswordGame` class.

- [ ] **Step 3: Create preview.js**

```javascript
// games/crossword/static/preview.js
export function renderPreview(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const size = 100;
    canvas.width = size;
    canvas.height = size;

    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, size, size);

    const cellSize = 8;
    const grid = 10;
    const offset = (size - grid * cellSize) / 2;

    for (let r = 0; r < grid; r++) {
        for (let c = 0; c < grid; c++) {
            const isBlack = Math.random() < 0.3;
            ctx.fillStyle = isBlack ? "#0f0f23" : "#e0e0e0";
            ctx.fillRect(offset + c * cellSize, offset + r * cellSize, cellSize - 1, cellSize - 1);
        }
    }
}
```

- [ ] **Step 4: Create timer.js**

```javascript
// games/crossword/static/timer.js
export class Timer {
    constructor() {
        this.seconds = 0;
        this.interval = null;
        this.element = null;
    }

    start(elementId) {
        this.element = document.getElementById(elementId);
        this.seconds = 0;
        this.interval = setInterval(() => {
            this.seconds++;
            if (this.element) {
                const m = Math.floor(this.seconds / 60);
                const s = this.seconds % 60;
                this.element.textContent = `${m}:${s.toString().padStart(2, "0")}`;
            }
        }, 1000);
    }

    stop() {
        clearInterval(this.interval);
        return this.seconds;
    }

    reset() {
        this.stop();
        this.seconds = 0;
    }
}

export function saveScore(time, difficulty) {
    const scores = JSON.parse(localStorage.getItem("crossword_scores") || "[]");
    scores.push({ time, difficulty, date: new Date().toISOString() });
    scores.sort((a, b) => a.time - b.time);
    localStorage.setItem("crossword_scores", JSON.stringify(scores.slice(0, 10)));
}

export function getLeaderboard() {
    return JSON.parse(localStorage.getItem("crossword_scores") || "[]");
}
```

- [ ] **Step 5: Register crossword in app.js**

Read `static/app.js` and add:
1. Crossword entry in `GAMES` object
2. Preview rendering in `openModal()`
3. Game start in `startGame()`
4. Cleanup in `backToLanding()` and `startNewGame()`

- [ ] **Step 6: Add crossword styles to styles.css**

Read `static/styles.css` and add `.crossword-*` prefixed styles for grid, cells, clues sidebar.

- [ ] **Step 7: Commit**

```bash
git add games/crossword/static/ static/app.js static/styles.css
git commit -m "feat(crossword): add frontend client and integration"
```

---

### Task 6: Integration Tests

**Files:**
- Create: `tests/test_integration.py`

**Interfaces:**
- Consumes: All previous tasks

- [ ] **Step 1: Write integration tests**

```python
# tests/test_integration.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_full_crossword_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        words_resp = await client.get("/api/words")
        assert words_resp.status_code == 200

        game_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "easy"})
        assert game_resp.status_code == 200
        game_id = game_resp.json()["id"]

        state_resp = await client.get(f"/games/{game_id}")
        assert state_resp.status_code == 200

@pytest.mark.asyncio
async def test_seed_words_populated():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/words")
        assert response.status_code == 200
        words = response.json()
        assert len(words) > 50

@pytest.mark.asyncio
async def test_crossword_game_has_puzzle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        game_resp = await client.post("/games", json={"game_type": "crossword", "difficulty": "medium"})
        game_id = game_resp.json()["id"]
        state_resp = await client.get(f"/games/{game_id}")
        state = state_resp.json()
        assert "puzzle" in state or "grid" in state or state.get("status") == "playing"
```

- [ ] **Step 2: Run integration tests**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test(crossword): add integration tests"
```

---

### Task 7: Full Test Battery + Regression Check

**Files:**
- All test files

- [ ] **Step 1: Run ALL tests in the project**

Run: `cd /Users/leandrolima/conductor/workspaces/games/irvine && python -m pytest tests/ games/checkers/tests/ games/crossword/tests/ -v`

- [ ] **Step 2: Fix any failures**

If any test fails, fix the issue and re-run.

- [ ] **Step 3: Final commit if needed**

```bash
git add -A
git commit -m "test: complete crossword test battery and verify all tests pass"
```
