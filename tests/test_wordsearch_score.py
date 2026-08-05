"""Finishing a word search must record exactly one score, in seconds.

timer.js stores and formats scores in seconds (`formatTime(seconds)`,
`getTime()`), so a caller that saves milliseconds writes an entry a thousand
times too large — and a second caller writes a duplicate for the same win.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "games" / "wordsearch" / "static"

HARNESS = """
const store = new Map();
globalThis.localStorage = {
  getItem: k => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: k => store.delete(k),
};
globalThis.document = { getElementById: () => ({}) };

const { WordSearchGame } = await import('./board.js');

const game = new WordSearchGame({
  containerId: 'board-wrapper',
  gridSize: 10,
  wordCount: 6,
  directions: 4,
  category: 'animals',
  difficulty: 'easy',
});
game.render = () => {};
game.init();
game.start();

// Finish 90 seconds after the clock started.
game.startTime = Date.now() - 90_000;
game.completeGame();
clearInterval(game.timerInterval);

const entries = [];
for (const [key, value] of store) entries.push({ key, value: JSON.parse(value) });
console.log(JSON.stringify(entries));
"""


@pytest.fixture(scope="module")
def saved_scores(tmp_path_factory) -> list[dict]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    work = tmp_path_factory.mktemp("wordsearch_score")
    for src in STATIC.glob("*.js"):
        shutil.copy(src, work / src.name)
    (work / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    (work / "harness.mjs").write_text(HARNESS, encoding="utf-8")

    proc = subprocess.run(
        [node, "harness.mjs"], cwd=work, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_one_win_records_one_entry(saved_scores) -> None:
    total = sum(len(bucket["value"]) for bucket in saved_scores)
    assert total == 1, f"expected a single score, got {total}: {saved_scores}"


def test_the_score_is_stored_in_seconds(saved_scores) -> None:
    entry = saved_scores[0]["value"][0]
    # 90 seconds elapsed. Milliseconds would land near 90000.
    assert 89 <= entry["time"] <= 91, f"expected ~90 seconds, got {entry['time']}"


def test_app_js_does_not_save_the_score_a_second_time() -> None:
    # board.js's completeGame is the single writer; the landing script used to
    # save again, in milliseconds, producing a duplicate 1000x entry.
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    assert "saveScore" not in app_js
