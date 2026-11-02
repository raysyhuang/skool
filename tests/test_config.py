import pytest

from app.config import Settings


@pytest.mark.parametrize("raw", [
    "postgres://u:p@h:5432/d",    # what Heroku sets
    "postgresql://u:p@h:5432/d",
])
def test_heroku_database_url_uses_psycopg2(monkeypatch, raw):
    monkeypatch.setenv("DATABASE_URL", raw)
    assert Settings().database_url == "postgresql+psycopg2://u:p@h:5432/d"


def test_sqlite_url_unchanged(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./skool.db")
    assert Settings().database_url == "sqlite:///./skool.db"
