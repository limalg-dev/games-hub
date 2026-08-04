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
