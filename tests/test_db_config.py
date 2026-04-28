import os
from importlib import reload
import sys
from pathlib import Path

# Ensure the repository root is on the import path for the app package
sys.path.append(str(Path(__file__).resolve().parents[1]))

def test_uses_database_url(monkeypatch):
    # Set full URL env var and clear component vars
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    for var in ["DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_HOST", "DATABASE_NAME"]:
        monkeypatch.delenv(var, raising=False)
    from app.db import base as db_base
    reload(db_base)
    assert db_base.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost/db"

def test_composes_postgres_url(monkeypatch):
    # Clear full URL and set components
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_USER", "user")
    monkeypatch.setenv("DATABASE_PASSWORD", "pass")
    monkeypatch.setenv("DATABASE_HOST", "host.example.com")
    monkeypatch.setenv("DATABASE_NAME", "mydb")
    from app.db import base as db_base
    reload(db_base)
    expected = "postgresql+asyncpg://user:pass@host.example.com/mydb"
    assert db_base.DATABASE_URL == expected
