"""Tests for the @track decorator."""

import pytest
from sqlalchemy import Engine
from sqlmodel import Session, select

import pg_task_tracker
from pg_task_tracker import Task, track
from pg_task_tracker import _state


@pytest.fixture(autouse=True)
def _init_tracker(engine: Engine) -> None:
    pg_task_tracker.init(engine)


def test_track_success(engine: Engine) -> None:
    @track()
    def my_func() -> None:
        pass

    my_func()

    with Session(engine) as session:
        task = session.exec(
            select(Task).where(Task.name == "my_func")
        ).one()
        assert task.status == "completed"


def test_track_failure(engine: Engine) -> None:
    @track()
    def failing_func() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        failing_func()

    with Session(engine) as session:
        task = session.exec(
            select(Task).where(Task.name == "failing_func")
        ).one()
        assert task.status == "failed"


def test_track_custom_name(engine: Engine) -> None:
    @track(name="custom-name")
    def my_func() -> None:
        pass

    my_func()

    with Session(engine) as session:
        task = session.exec(
            select(Task).where(Task.name == "custom-name")
        ).one()
        assert task.status == "completed"


def test_track_preserves_return_value() -> None:
    @track()
    def add(a: int, b: int) -> int:
        return a + b

    result = add(2, 3)
    assert result == 5


def test_track_not_initialized() -> None:
    _state._engine = None

    @track()
    def my_func() -> None:
        pass

    with pytest.raises(RuntimeError, match="not initialized"):
        my_func()
