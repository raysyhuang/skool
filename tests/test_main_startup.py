import pytest
from starlette.testclient import TestClient

from app.main import create_app
import app.main as main_module


def test_lifespan_surfaces_database_initialization_errors(monkeypatch):
    app = create_app()

    def boom(*args, **kwargs):
        raise RuntimeError("database init failed")

    monkeypatch.setattr(main_module.Base.metadata, "create_all", boom)

    with pytest.raises(RuntimeError, match="database init failed"):
        with TestClient(app):
            pass
