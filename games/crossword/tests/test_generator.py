from games.crossword.generator import generate_crossword, CrosswordGrid

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

def test_word_count_targets():
    pool = [{"word": w, "hint": f"dica {i}"} for i, w in enumerate(["ALGORITHM", "DATABASE", "PYTHON", "BROWSER", "NETWORK", "MONITOR", "SERVER", "MOUSE", "BYTE", "LOOP", "PIXEL", "CLOUD", "WIFI", "JAVA", "FROG", "LION", "BEAR", "GOLF", "SWIM", "RUN", "JUDO", "SURF", "SKATE", "TENNIS"])]
    r1 = generate_crossword(pool, difficulty=1)
    r2 = generate_crossword(pool, difficulty=2)
    r3 = generate_crossword(pool, difficulty=3)
    assert 6 <= r1["words_placed"] <= 10
    assert 10 <= r2["words_placed"] <= 15
    assert 15 <= r3["words_placed"] <= 22


class TestCanPlaceWordEndpointIsolation:
    """Testa que can_place_word valida isolamento nas pontas da palavra"""

    def test_rejects_word_touching_existing_at_start(self):
        """Word placed across must not touch an existing letter before its start."""
        grid = CrosswordGrid(10)
        # Place 'AB' across at (5, 3)-(5, 4)
        grid.grid[5][3] = 'A'
        grid.grid[5][4] = 'B'
        # Try to place 'CD' across at (5, 5)-(5, 6) — adjacent to B at (5,4)
        # This should be rejected because cell (5, 4) is occupied
        # Actually this is within-bounds check. The endpoint issue is:
        # Place 'AB' at (5, 3)-(5, 4), then try 'XY' at (5, 5)-(5, 6)
        # Cell (5, 4) is 'B' which is right before 'X' — this IS an endpoint issue
        # But can_place_word only checks cells within the new word's bounds.
        # So 'XY' at (5,5)-(5,6) passes because (5,5) and (5,6) are empty.
        # The fix should reject this because (5,4) is occupied.
        result = grid.can_place_word('XY', 5, 5, 'across')
        assert result is False, (
            'Word touching existing letter at start endpoint should be rejected'
        )

    def test_rejects_word_touching_existing_at_end(self):
        """Word placed across must not touch an existing letter after its end."""
        grid = CrosswordGrid(10)
        # Place 'AB' at (5, 5)-(5, 6)
        grid.grid[5][5] = 'A'
        grid.grid[5][6] = 'B'
        # Try to place 'XY' at (5, 3)-(5, 4) — adjacent to A at (5, 5)
        result = grid.can_place_word('XY', 5, 3, 'across')
        assert result is False, (
            'Word touching existing letter at end endpoint should be rejected'
        )

    def test_rejects_word_touching_down_at_start(self):
        """Same check for down direction."""
        grid = CrosswordGrid(10)
        # Place 'AB' down at (3, 5)-(4, 5)
        grid.grid[3][5] = 'A'
        grid.grid[4][5] = 'B'
        # Try 'XY' down at (5, 5)-(6, 5) — adjacent to B at (4, 5)
        result = grid.can_place_word('XY', 5, 5, 'down')
        assert result is False

    def test_allows_word_with_empty_endpoints(self):
        """Word with empty cells before/after should be allowed."""
        grid = CrosswordGrid(10)
        # Place 'AB' across at (5, 3)-(5, 4)
        grid.grid[5][3] = 'A'
        grid.grid[5][4] = 'B'
        # Place 'XY' across at (5, 7)-(5, 8) — separated by empty cells
        result = grid.can_place_word('XY', 5, 7, 'across')
        assert result is True

    def test_allows_word_at_board_edge(self):
        """Word at board edge (no cell before/after) should be allowed."""
        grid = CrosswordGrid(10)
        # Place word starting at column 0 — no cell before
        result = grid.can_place_word('AB', 5, 0, 'across')
        assert result is True
        # Place word ending at last column — no cell after
        result2 = grid.can_place_word('CD', 5, 8, 'across')
        assert result2 is True

    def test_allows_word_at_board_edge_down(self):
        """Same for down direction at edges."""
        grid = CrosswordGrid(10)
        result = grid.can_place_word('AB', 0, 5, 'down')
        assert result is True
        result2 = grid.can_place_word('CD', 8, 5, 'down')
        assert result2 is True
