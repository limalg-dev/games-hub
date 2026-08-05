"""Exercise the /play URL helpers the way the browser will."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

HARNESS = """
const { buildPlayUrl, parsePlayUrl, PLAYABLE_GAMES } = await import('./play-url.js');

const results = {
  games: PLAYABLE_GAMES,
  plain: buildPlayUrl('checkers'),
  defaults: buildPlayUrl('wordsearch', { difficulty: 'easy', category: 'random' }),
  configured: buildPlayUrl('wordsearch', { difficulty: 'hard', category: 'animals' }),
  crossword: buildPlayUrl('crossword', { difficulty: 'medium' }),
  parsedPlain: parsePlayUrl('/play/checkers'),
  parsedConfigured: parsePlayUrl('/play/wordsearch', '?difficulty=hard&category=animals'),
  parsedBogusValues: parsePlayUrl('/play/wordsearch', '?difficulty=impossivel&category=nada'),
  parsedLanding: parsePlayUrl('/'),
  parsedUnknown: parsePlayUrl('/play/xadrez'),
};
console.log(JSON.stringify(results));
"""


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    work = tmp_path_factory.mktemp("play_url")
    shutil.copy(STATIC / "play-url.js", work / "play-url.js")
    (work / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    (work / "harness.mjs").write_text(HARNESS, encoding="utf-8")

    proc = subprocess.run(
        [node, "harness.mjs"], cwd=work, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_lists_the_playable_games(result):
    assert result["games"] == ["checkers", "wordsearch", "crossword"]


def test_builds_a_bare_url_when_there_is_nothing_to_configure(result):
    assert result["plain"] == "/play/checkers"


def test_omits_values_that_match_the_defaults(result):
    assert result["defaults"] == "/play/wordsearch"


def test_includes_values_that_differ_from_the_defaults(result):
    assert result["configured"] == "/play/wordsearch?difficulty=hard&category=animals"
    assert result["crossword"] == "/play/crossword?difficulty=medium"


def test_parses_a_bare_url_into_defaults(result):
    assert result["parsedPlain"] == {
        "game": "checkers",
        "difficulty": "easy",
        "category": "random",
    }


def test_parses_a_configured_url(result):
    assert result["parsedConfigured"] == {
        "game": "wordsearch",
        "difficulty": "hard",
        "category": "animals",
    }


def test_falls_back_to_defaults_for_values_outside_the_allowed_set(result):
    assert result["parsedBogusValues"] == {
        "game": "wordsearch",
        "difficulty": "easy",
        "category": "random",
    }


def test_returns_null_outside_the_play_route(result):
    assert result["parsedLanding"] is None
    assert result["parsedUnknown"] is None
