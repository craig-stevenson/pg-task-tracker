import os
from collections.abc import Generator

import pytest
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

DEFAULT_DB_URL = "sqlite:///test.db"


@pytest.fixture(scope="session")
def db_url() -> str:
    return os.environ.get("TEST_DATABASE_URL", DEFAULT_DB_URL)


@pytest.fixture()
def engine(db_url: str) -> Generator[Engine, None, None]:
    eng = create_engine(db_url)
    SQLModel.metadata.create_all(eng)
    yield eng
    SQLModel.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine: Engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
