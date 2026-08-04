from games.crossword.generator import generate_crossword

def test_generate_returns_dict():
    words = [{"word": "PYTHON", "hint": "Linguagem de prog"}, {"word": "JAVA", "hint": "Linguagem de prog"}, {"word": "CODING", "hint": "Atividade de programar"}]
    result = generate_crossword(words, difficulty=1)
    assert "grid" in result
    assert "clues" in result
    assert "size" in result

def test_grid_is_2d():
    words = [{"word": "PYTHON", "hint": "Linguagem de prog"}, {"word": "JAVA", "hint": "Linguagem de prog"}]
    result = generate_crossword(words, difficulty=1)
    grid = result["grid"]
    assert isinstance(grid, list)
    assert all(isinstance(row, list) for row in grid)

def test_grid_has_letters():
    words = [{"word": "PYTHON", "hint": "Linguagem de prog"}, {"word": "JAVA", "hint": "Linguagem de prog"}, {"word": "CODING", "hint": "Atividade de programar"}]
    result = generate_crossword(words, difficulty=1)
    letters_found = sum(1 for row in result["grid"] for cell in row if cell is not None)
    assert letters_found > 0

def test_difficulty_sizes():
    words_short = [{"word": "AAA", "hint": "x"} for _ in range(5)]
    words_medium = [{"word": "AAAAA", "hint": "x"} for _ in range(10)]
    words_long = [{"word": "AAAAAAA", "hint": "x"} for _ in range(15)]
    r1 = generate_crossword(words_short, difficulty=1)
    r2 = generate_crossword(words_medium, difficulty=2)
    r3 = generate_crossword(words_long, difficulty=3)
    assert r1["size"] <= 10
    assert r2["size"] <= 14
    assert r3["size"] <= 18

def test_clues_have_required_fields():
    words = [{"word": "PYTHON", "hint": "Linguagem de prog"}, {"word": "JAVA", "hint": "Linguagem de prog"}, {"word": "CODING", "hint": "Atividade de programar"}]
    result = generate_crossword(words, difficulty=1)
    for direction in ["across", "down"]:
        for clue in result["clues"][direction]:
            assert "number" in clue
            assert "row" in clue
            assert "col" in clue
            assert "clue" in clue
            assert "length" in clue

def test_words_are_placed():
    words = [{"word": "PYTHON", "hint": "Linguagem de prog"}, {"word": "JAVA", "hint": "Linguagem de prog"}, {"word": "CODING", "hint": "Atividade de programar"}]
    result = generate_crossword(words, difficulty=1)
    grid_text = "".join(cell or "" for row in result["grid"] for cell in row)
    assert "PYTHON" in grid_text or "JAVA" in grid_text or "CODING" in grid_text
