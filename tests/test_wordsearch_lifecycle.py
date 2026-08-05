"""init() must lay out the puzzle without starting the clock."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "games" / "wordsearch" / "static"

HARNESS = """
globalThis.document = { getElementById: () => ({}) };
globalThis.localStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
};

const { WordSearchGame } = await import('./board.js');

const game = new WordSearchGame({
  containerId: 'board-wrapper',
  gridSize: 10,
  wordCount: 6,
  directions: 4,
  category: 'animals',
});
// The DOM painting is not what this test is about.
game.render = () => {};

game.init();
const afterInit = { isPlaying: game.isPlaying, hasTimer: game.timerInterval !== null,
                    hasGrid: Array.isArray(game.grid) && game.grid.length === 10 };

game.start();
const afterStart = { isPlaying: game.isPlaying, hasTimer: game.timerInterval !== null };
clearInterval(game.timerInterval);

console.log(JSON.stringify({ afterInit, afterStart }));
process.exit(0);
"""


@pytest.fixture(scope="module")
def lifecycle(tmp_path_factory):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    work = tmp_path_factory.mktemp("wordsearch_lifecycle")
    for src in STATIC.glob("*.js"):
        shutil.copy(src, work / src.name)
    (work / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    (work / "harness.mjs").write_text(HARNESS, encoding="utf-8")

    proc = subprocess.run(
        [node, "harness.mjs"], cwd=work, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_init_lays_out_the_grid(lifecycle):
    assert lifecycle["afterInit"]["hasGrid"] is True


def test_init_does_not_start_the_clock(lifecycle):
    assert lifecycle["afterInit"]["isPlaying"] is False
    assert lifecycle["afterInit"]["hasTimer"] is False


def test_start_begins_play(lifecycle):
    assert lifecycle["afterStart"]["isPlaying"] is True
    assert lifecycle["afterStart"]["hasTimer"] is True
