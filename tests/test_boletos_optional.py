import sys
import pytest
from fastapi import FastAPI

import app.main as main


def test_include_optional_boletos_registers_when_dependency_present():
    fresh = FastAPI()
    assert main._include_optional_boletos(fresh) is True
    paths = {route.path for route in fresh.routes}
    assert "/boletos/api/login" in paths


def test_include_optional_boletos_skips_when_module_unimportable(monkeypatch):
    # Setting the sys.modules entry to None forces `import app.boletos`
    # to raise ImportError (documented CPython behavior), simulating a
    # missing optional dependency like reportlab.
    monkeypatch.setitem(sys.modules, "app.boletos", None)
    fresh = FastAPI()
    assert main._include_optional_boletos(fresh) is False
    paths = {route.path for route in fresh.routes}
    assert not any(p.startswith("/boletos") for p in paths)


def test_app_module_imports_without_boletos(monkeypatch):
    # Importing app.main must never fail because boletos is unavailable.
    monkeypatch.setitem(sys.modules, "app.boletos", None)
    import importlib
    reloaded = importlib.reload(main)
    assert hasattr(reloaded, "app")
    # restore a clean module for later tests in the session
    importlib.reload(reloaded)
