from __future__ import annotations

import importlib.resources

from sqlalchemy import Engine
from sqlmodel import SQLModel

from simple_task import models as _models  # noqa: F401 — ensure tables are registered


def ensure_schema(engine: Engine) -> None:
    """Create all tables if they don't already exist."""
    SQLModel.metadata.create_all(engine)


def get_migration_sql() -> str:
    """Return the contents of the bundled SQL migration file."""
    return (
        importlib.resources.files("simple_task")
        .joinpath("migrations/001_initial.sql")
        .read_text(encoding="utf-8")
    )
