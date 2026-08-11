"""Guard the landing game data and filtering logic using the real module.

The harness runs the actual browser script (static/games.js) under Node,
so these checks track the module the browser loads — not a reimplementation.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

HARNESS = """
import { GAMES, allGames, categories, categoryLabel, gamesByCategory, gameCard } from './games.js';

const GAME_IDS = Object.keys(GAMES);
const games = allGames();

const results = {
  ids: GAME_IDS,
  games,
  categoryList: categories(),
  labels: Object.fromEntries(categories().map(cat => [cat, categoryLabel(cat)])),
  byAll: gamesByCategory('all'),
  byUnknown: gamesByCategory('inexistente'),
  cards: Object.fromEntries(GAME_IDS.map(id => [id, gameCard(GAMES[id])])),
  groupedByCategory: Object.fromEntries(
    categories().map(cat => [cat, gamesByCategory(cat).map(g => g.id)])
  ),
};

// Duplication check: every category group must have unique ids.
results.byCategoryHasDuplicates = Object.fromEntries(
  categories().map(cat => {
    const ids = gamesByCategory(cat).map(g => g.id);
    return [cat, new Set(ids).size !== ids.length];
  })
);

// Badge/featured/collection leakage check on rendered cards.
results.cardLeaks = Object.fromEntries(
  GAME_IDS.map(id => ({
    badge: /game-badges|badge-novo|badge-popular|badge-destaque|Novo|Popular|Em Destaque/.test(gameCard(GAMES[id])),
    featured: /featured/.test(gameCard(GAMES[id])),
    collection: /collection/.test(gameCard(GAMES[id])),
  }))
);

console.log(JSON.stringify(results));
"""


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    work = tmp_path_factory.mktemp("games_list")
    shutil.copy(STATIC / "games.js", work / "games.js")
    (work / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    (work / "harness.mjs").write_text(HARNESS, encoding="utf-8")

    proc = subprocess.run(
        [node, "harness.mjs"], cwd=work, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_exports_exactly_the_six_games(result):
    assert set(result["ids"]) == {
        "checkers", "wordsearch", "crossword", "snake", "ant_defense", "tower_defense",
    }


def test_all_games_has_each_id_exactly_once(result):
    ids = [g["id"] for g in result["games"]]
    assert len(ids) == 6
    assert len(set(ids)) == 6


def test_all_games_sorted_by_rating_descending(result):
    ratings = [g["rating"] for g in result["games"]]
    assert ratings == sorted(ratings, reverse=True)


def test_categories_cover_every_game_category(result):
    used = {c for g in result["games"] for c in g["category"]}
    assert set(result["categoryList"]) == used


def test_by_all_returns_every_game(result):
    assert len(result["byAll"]) == 6
    assert set(g["id"] for g in result["byAll"]) == set(result["ids"])


def test_by_unknown_category_is_empty(result):
    assert result["byUnknown"] == []


def test_category_labels_are_localized(result):
    for cat, label in result["labels"].items():
        assert cat != label, f"{cat} borrowed the raw id as its tab label"


def test_each_category_has_unique_games(result):
    assert all(not v for v in result["byCategoryHasDuplicates"].values())


def test_every_game_belongs_to_a_known_category(result):
    known = set(result["categoryList"])
    for g in result["games"]:
        assert set(g["category"]).issubset(known)


def test_cards_have_no_badge_featured_or_collection_markup(result):
    for id, leaks in result["cardLeaks"].items():
        assert not leaks["badge"], f"{id} leaked badge markup"
        assert not leaks["featured"], f"{id} leaked featured markup"
        assert not leaks["collection"], f"{id} leaked collection markup"


def test_cards_reference_only_their_own_game(result):
    import re
    for id, html in result["cards"].items():
        referenced = set(re.findall(r'data-game="([^"]+)"', html))
        assert referenced == {id}