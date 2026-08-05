"""The server and the browser must lay out the same starting position.

The client renders its own initial board, then reconciles against the board the
server pushes over the WebSocket. If the two disagree, that reconciliation is
read as a move: the history gains a phantom entry and pieces jump squares.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from games.checkers.game import Board

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "games" / "checkers" / "static"

HARNESS = """
const { createInitialBoard } = await import('./logic.js');
const board = createInitialBoard().map(row =>
  row.map(cell => (cell ? cell.color : ''))
);
console.log(JSON.stringify(board));
"""


@pytest.fixture(scope="module")
def client_board(tmp_path_factory) -> list[list[str]]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")

    work = tmp_path_factory.mktemp("checkers_init")
    for src in STATIC.glob("*.js"):
        shutil.copy(src, work / src.name)
    (work / "package.json").write_text('{"type":"module"}', encoding="utf-8")
    (work / "harness.mjs").write_text(HARNESS, encoding="utf-8")

    proc = subprocess.run(
        [node, "harness.mjs"], cwd=work, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"harness failed:\n{proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_server_and_client_start_from_the_same_position(client_board) -> None:
    server_board = Board().board
    mismatches = [
        f"({r},{c}): server={server_board[r][c]!r} client={client_board[r][c]!r}"
        for r in range(8)
        for c in range(8)
        if server_board[r][c] != client_board[r][c]
    ]
    assert not mismatches, "initial board disagrees:\n" + "\n".join(mismatches[:10])


def test_pieces_sit_on_dark_squares() -> None:
    # drawBoard paints (r + c) % 2 == 0 as the dark squares, and checkers is
    # played entirely on those.
    server_board = Board().board
    stray = [
        f"({r},{c})={server_board[r][c]!r}"
        for r in range(8)
        for c in range(8)
        if server_board[r][c] and (r + c) % 2 != 0
    ]
    assert not stray, "pieces placed on light squares: " + ", ".join(stray[:10])
