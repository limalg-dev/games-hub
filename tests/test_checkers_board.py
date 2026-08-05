"""Exercise the checkers canvas renderer without a browser.

drawBoard receives a `lastMove` that animateToBoard builds by diffing two
boards. A board sync that is not a move leaves `from` (or `to`) null, and the
renderer has to cope with that instead of throwing and killing the game view.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "games" / "checkers" / "static"

HARNESS = """
// Minimal stand-ins for the canvas APIs drawBoard touches.
const gradient = { addColorStop() {} };
function stubCtx() {
  return new Proxy({}, {
    get(_t, p) {
      if (p === 'canvas') return { width: 640, height: 640 };
      return (...args) => {
        if (p === 'getImageData') return { data: new Uint8ClampedArray(256 * 256 * 4) };
        if (String(p).startsWith('create')) return gradient;
        return undefined;
      };
    },
    set() { return true; },
  });
}
globalThis.document = {
  createElement: () => ({ width: 0, height: 0, getContext: () => stubCtx() }),
};

const { drawBoard } = await import('./board.js');
const { createInitialBoard } = await import('./logic.js');

const board = createInitialBoard();
const cases = {
  'no last move': undefined,
  'null last move': null,
  'sync with no origin': { from: null, to: [2, 3] },
  'sync with no destination': { from: [2, 3], to: null },
  'real move': { from: [2, 3], to: [3, 4] },
};

const problems = [];
for (const [name, lastMove] of Object.entries(cases)) {
  try {
    drawBoard(stubCtx(), board, { lastMove });
  } catch (e) {
    problems.push(`${name}: ${e.message}`);
  }
}
console.log(JSON.stringify(problems));
"""


@pytest.fixture(scope="module")
def draw_report(tmp_path_factory) -> list[str]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    work = tmp_path_factory.mktemp("checkers")
    for src in STATIC.glob("*.js"):
        shutil.copy(src, work / src.name)
    (work / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    (work / "harness.mjs").write_text(HARNESS, encoding="utf-8")

    proc = subprocess.run(
        [node, "harness.mjs"], cwd=work, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_draw_board_survives_partial_last_move(draw_report: list[str]) -> None:
    assert not draw_report, "drawBoard raised:\n" + "\n".join(draw_report)
