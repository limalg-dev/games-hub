import importlib

def test_project_structure():
    import app.main
    assert hasattr(app.main, "app")
