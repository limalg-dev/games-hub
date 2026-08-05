"""A degenerate puzzle must not take the crossword view down.

firstPlayable returns null when every cell is black. init() used to read .row
off that null, so an empty grid replaced the board with a blank screen and an
uncaught TypeError. The server now refuses to build such a puzzle, but the
renderer should not be the only thing standing between a bad grid and a dead
page.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "games" / "crossword" / "static"

HARNESS = """
globalThis.document = { getElementById: () => ({}) };

const { CrosswordGame } = await import('./board.js');

function makeGame() {
  const game = new CrosswordGame('board-wrapper');
  // The DOM painting is not what this test is about.
  game.render = () => {};
  game.renderClues = () => {};
  game.focusCell = () => { game._focused = true; };
  game.startTimer = () => {};
  return game;
}

const size = 5;
const allBlack = {
  size,
  num_grid: Array.from({ length: size }, () => Array(size).fill(null)),
  filled: Array.from({ length: size }, () => Array(size).fill(true)),
  across_clues: [],
  down_clues: [],
};
const oneWord = {
  size,
  num_grid: Array.from({ length: size }, () => Array(size).fill(null)),
  filled: Array.from({ length: size }, (_, r) =>
    Array.from({ length: size }, (_, c) => !(r === 1 && c < 3))
  ),
  across_clues: [],
  down_clues: [],
};

const result = {};
for (const [name, msg] of Object.entries({ allBlack, oneWord })) {
  const game = makeGame();
  try {
    game.init(msg);
    result[name] = { threw: null, focused: !!game._focused, total: game.total };
  } catch (e) {
    result[name] = { threw: e.message };
  }
}
console.log(JSON.stringify(result));
"""


@pytest.fixture(scope="module")
def init_report(tmp_path_factory) -> dict:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    work = tmp_path_factory.mktemp("crossword_guard")
    for src in STATIC.glob("*.js"):
        shutil.copy(src, work / src.name)
    (work / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    (work / "harness.mjs").write_text(HARNESS, encoding="utf-8")

    proc = subprocess.run(
        [node, "harness.mjs"], cwd=work, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_an_all_black_grid_does_not_throw(init_report) -> None:
    assert init_report["allBlack"]["threw"] is None


def test_an_all_black_grid_focuses_nothing(init_report) -> None:
    assert init_report["allBlack"]["focused"] is False
    assert init_report["allBlack"]["total"] == 0


def test_a_normal_grid_still_focuses_its_first_cell(init_report) -> None:
    assert init_report["oneWord"]["threw"] is None
    assert init_report["oneWord"]["focused"] is True
    assert init_report["oneWord"]["total"] == 3
