import os
import subprocess
import time
from collections.abc import Generator

import pytest
from sqlalchemy import Engine, text
from sqlmodel import Session, SQLModel, create_engine

POSTGRES_PORT = "15432"
POSTGRES_PASSWORD = "testpass"
POSTGRES_DB = "ptt_test"
POSTGRES_CONTAINER = "ptt-test-postgres"
DEFAULT_DB_URL = (
    f"postgresql+psycopg2://postgres:{POSTGRES_PASSWORD}"
    f"@localhost:{POSTGRES_PORT}/{POSTGRES_DB}"
)


def _start_postgres() -> str:
    """Start a Postgres container if one isn't already running. Returns the DB URL."""
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", POSTGRES_CONTAINER],
        capture_output=True,
        text=True,
    )
    if result.stdout.strip() == "true":
        return DEFAULT_DB_URL

    # Remove stopped container if it exists
    subprocess.run(
        ["docker", "rm", "-f", POSTGRES_CONTAINER],
        capture_output=True,
    )

    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", POSTGRES_CONTAINER,
            "-e", f"POSTGRES_PASSWORD={POSTGRES_PASSWORD}",
            "-e", f"POSTGRES_DB={POSTGRES_DB}",
            "-p", f"{POSTGRES_PORT}:5432",
            "postgres:17-alpine",
        ],
        check=True,
        capture_output=True,
    )

    # Wait for Postgres to accept connections
    engine = create_engine(DEFAULT_DB_URL)
    for _ in range(30):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return DEFAULT_DB_URL
        except Exception:
            time.sleep(0.5)
    engine.dispose()
    raise RuntimeError("Postgres container failed to start")


def _stop_postgres() -> None:
    subprocess.run(
        ["docker", "rm", "-f", POSTGRES_CONTAINER],
        capture_output=True,
    )


@pytest.fixture(scope="session")
def db_url() -> Generator[str, None, None]:
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        yield url
    else:
        yield _start_postgres()
        _stop_postgres()


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
