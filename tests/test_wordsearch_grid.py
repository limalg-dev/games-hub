"""Exercise the word search grid builder the way the browser does.

createGrid picks a random origin per word, so placement bugs surface only on
some seeds. Running every difficulty many times keeps that from being flaky in
the direction that matters: a broken build fails reliably, a correct one passes.
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
import { createGrid } from './logic.js';
import { CATEGORIES, DIFFICULTIES, getWordsForCategory } from './words.js';

const problems = [];
for (const [name, config] of Object.entries(DIFFICULTIES)) {
  for (const category of Object.keys(CATEGORIES)) {
   for (let run = 0; run < 20; run++) {
    const words = getWordsForCategory(category, config.wordCount);
    let result;
    try {
      result = createGrid({ ...config, words });
    } catch (e) {
      problems.push(`${name}/${category} run ${run}: threw ${e.message}`);
      continue;
    }
    const { grid, placedWords } = result;
    for (const p of placedWords) {
      for (let i = 0; i < p.word.length; i++) {
        const r = p.row + p.dr * i;
        const c = p.col + p.dc * i;
        if (r < 0 || r >= config.gridSize || c < 0 || c >= config.gridSize) {
          problems.push(`${name}/${category}: '${p.word}' leaves the grid at (${r},${c})`);
          break;
        }
        if (grid[r][c] !== p.word[i]) {
          problems.push(`${name}/${category}: '${p.word}' letter ${i} missing at (${r},${c})`);
          break;
        }
      }
    }
   }
  }
}
console.log(JSON.stringify(problems));
"""


@pytest.fixture(scope="module")
def grid_report(tmp_path_factory) -> list[str]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    # The repo ships no package.json, so node would read these .js files as
    # CommonJS and choke on `export`. A scratch copy marked as ESM avoids that
    # without adding a package.json to the repo.
    work = tmp_path_factory.mktemp("wordsearch")
    for src in STATIC.glob("*.js"):
        shutil.copy(src, work / src.name)
    (work / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    (work / "harness.mjs").write_text(HARNESS, encoding="utf-8")

    proc = subprocess.run(
        [node, "harness.mjs"], cwd=work, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_placed_words_stay_inside_the_grid(grid_report: list[str]) -> None:
    assert not grid_report, "grid placement problems:\n" + "\n".join(grid_report[:15])
