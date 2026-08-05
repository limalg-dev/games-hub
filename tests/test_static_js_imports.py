"""Guard the browser ES module graph.

A named import that no module exports is a link-time error in the browser:
it aborts the whole graph, so a single missing `export` blanks the landing
page for every game. These checks run without a browser.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

IMPORT_RE = re.compile(
    r"""import\s*(?:(?P<names>\{[^}]*\})|(?P<star>\*\s+as\s+\w+)|(?P<default>\w+))?\s*"""
    r"""(?:,\s*(?P<names2>\{[^}]*\}))?\s*from\s*['"](?P<src>[^'"]+)['"]""",
    re.MULTILINE,
)
EXPORT_DECL_RE = re.compile(
    r"^export\s+(?:async\s+)?(?:function\s*\*?|class|const|let|var)\s+(\w+)", re.MULTILINE
)
EXPORT_LIST_RE = re.compile(r"^export\s*\{([^}]*)\}", re.MULTILINE)


def js_sources() -> list[Path]:
    files = sorted((ROOT / "static").rglob("*.js"))
    files += sorted(ROOT.glob("games/*/static/*.js"))
    return files


def resolve(spec: str, importer: Path) -> Path | None:
    if spec.startswith("/"):
        return ROOT / spec.lstrip("/")
    if spec.startswith("."):
        return (importer.parent / spec).resolve()
    return None  # bare specifier: not served from this repo


def exported_names(path: Path) -> set[str]:
    src = path.read_text(encoding="utf-8")
    names = set(EXPORT_DECL_RE.findall(src))
    for group in EXPORT_LIST_RE.findall(src):
        for entry in group.split(","):
            entry = entry.strip()
            if not entry:
                continue
            # `foo as bar` exports the name `bar`
            names.add(entry.split(" as ")[-1].strip())
    return names


def imports_of(path: Path) -> list[tuple[str, list[str]]]:
    src = path.read_text(encoding="utf-8")
    out = []
    for m in IMPORT_RE.finditer(src):
        braces = m.group("names") or m.group("names2")
        names = []
        if braces:
            for entry in braces.strip("{}").split(","):
                entry = entry.strip()
                if entry:
                    # `foo as bar` imports the exported name `foo`
                    names.append(entry.split(" as ")[0].strip())
        out.append((m.group("src"), names))
    return out


@pytest.mark.parametrize("path", js_sources(), ids=lambda p: str(p.relative_to(ROOT)))
def test_named_imports_are_exported(path: Path) -> None:
    for spec, names in imports_of(path):
        target = resolve(spec, path)
        if target is None:
            continue
        rel = path.relative_to(ROOT)
        assert target.is_file(), f"{rel} imports '{spec}', which does not exist"
        if not names:
            continue
        available = exported_names(target)
        missing = [n for n in names if n not in available]
        assert not missing, (
            f"{rel} imports {missing} from '{spec}', "
            f"but {target.relative_to(ROOT)} does not export them"
        )
