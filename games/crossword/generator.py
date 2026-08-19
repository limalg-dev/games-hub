import random
from typing import List, Optional, Dict, Any

DIFFICULTY_CONFIG = {
    1: {"max_size": 8, "min_words": 6, "max_words": 10, "max_word_len": 8},
    2: {"max_size": 12, "min_words": 10, "max_words": 15, "max_word_len": 12},
    3: {"max_size": 15, "min_words": 15, "max_words": 22, "max_word_len": 15},
}

class CrosswordGrid:
    def __init__(self, size: int):
        self.size = size
        self.grid: List[List[Optional[str]]] = [[None for _ in range(size)] for _ in range(size)]
        self.placed_words: List[Dict[str, Any]] = []

    def _is_on_board(self, r: int, c: int) -> bool:
        return 0 <= r < self.size and 0 <= c < self.size

    def can_place_word(self, word: str, row: int, col: int, direction: str) -> bool:
        dr = 1 if direction == "down" else 0
        dc = 1 if direction == "across" else 0
        end_row = row + dr * (len(word) - 1)
        end_col = col + dc * (len(word) - 1)
        if end_row >= self.size or end_col >= self.size or row < 0 or col < 0:
            return False

        # Endpoint isolation: cell before the word start must be empty or off-board
        before_r, before_c = row - dr, col - dc
        if self._is_on_board(before_r, before_c) and self.grid[before_r][before_c] is not None:
            return False

        # Endpoint isolation: cell after the word end must be empty or off-board
        after_r, after_c = end_row + dr, end_col + dc
        if self._is_on_board(after_r, after_c) and self.grid[after_r][after_c] is not None:
            return False

        for i, letter in enumerate(word):
            r, c = row + dr * i, col + dc * i
            existing = self.grid[r][c]
            if existing is not None and existing != letter:
                return False
        return True

    def place_word(self, word: str, row: int, col: int, direction: str, hint: str, number: int):
        dr = 1 if direction == "down" else 0
        dc = 1 if direction == "across" else 0
        for i, letter in enumerate(word):
            self.grid[row + dr * i][col + dc * i] = letter
        self.placed_words.append({"word": word, "row": row, "col": col, "direction": direction, "hint": hint, "number": number})

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
                            intersections.append({"row": new_row, "col": new_col, "direction": new_dir})
        return intersections

def _place_attempt(words: List[Dict[str, str]], max_size: int) -> CrosswordGrid:
    crossword = CrosswordGrid(max_size)
    word_number = 1
    if not words:
        return crossword
    first = random.choice(words)
    start_row = max_size // 2
    start_col = (max_size - len(first["word"])) // 2
    crossword.place_word(first["word"].upper(), start_row, start_col, "across", first.get("hint", ""), word_number)
    word_number += 1
    remaining = [w for w in words if w is not first]
    random.shuffle(remaining)
    for word_data in remaining:
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
    return crossword

def generate_crossword(words: List[Dict[str, str]], difficulty: int = 1) -> Dict[str, Any]:
    config = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG[1])
    max_size = config["max_size"]
    max_words = min(len(words), config["max_words"])
    eligible = [w for w in words if len(w["word"]) <= config["max_word_len"]]
    if not eligible:
        eligible = words
    sorted_words = sorted(eligible, key=lambda w: len(w["word"]), reverse=True)
    selected = sorted_words[:max_words]

    best: Optional[CrosswordGrid] = None
    best_score = -1
    attempts = 30
    for _ in range(attempts):
        crossword = _place_attempt(selected, max_size)
        score = len(crossword.placed_words)
        if score > best_score:
            best_score = score
            best = crossword
            if score >= config["min_words"]:
                break

    # Fix Bug #3: Handle case where no words could be placed (empty/bad grid)
    if best is None or len(best.placed_words) == 0:
        # Fallback: create a minimal valid grid with at least one word
        fallback_grid = CrosswordGrid(max_size)
        if eligible:
            first_word = eligible[0]["word"].upper()
            start_row = max_size // 2
            start_col = max(0, (max_size - len(first_word)) // 2)
            if start_col + len(first_word) <= max_size:
                fallback_grid.place_word(first_word, start_row, start_col, "across", eligible[0].get("hint", ""), 1)
                best = fallback_grid
            else:
                # Word too long for grid, use single letter
                fallback_grid.place_word("A", start_row, start_col, "across", "Single letter", 1)
                best = fallback_grid
        else:
            # No words available, create empty grid with at least one cell
            fallback_grid.place_word("A", max_size // 2, max_size // 2, "across", "Default", 1)
            best = fallback_grid

    crossword = best
    clues = {"across": [], "down": []}
    for pw in crossword.placed_words:
        clue_entry = {"number": pw["number"], "row": pw["row"], "col": pw["col"], "clue": pw["hint"], "length": len(pw["word"])}
        clues[pw["direction"]].append(clue_entry)
    clues["across"].sort(key=lambda c: (c["row"], c["col"]))
    clues["down"].sort(key=lambda c: (c["row"], c["col"]))
    return {"grid": crossword.grid, "clues": clues, "size": max_size, "words_placed": len(crossword.placed_words)}
