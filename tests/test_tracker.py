"""Integration tests — require TEST_DATABASE_URL to be set."""

import uuid

import pytest
from sqlalchemy import Engine

from pg_task_tracker import create_task, get_task, ensure_schema


def test_create_task(engine: Engine) -> None:
    handle = create_task(engine, "my-pipeline")
    assert handle.task_id is not None
    assert isinstance(handle.task_id, uuid.UUID)


def test_add_step(engine: Engine) -> None:
    handle = create_task(engine, "pipeline")
    step = handle.add_step("extract", status="running")
    assert step.name == "extract"
    assert step.status == "running"
    assert step.started_at is not None
    assert step.created_at is not None


def test_update_step_status(engine: Engine) -> None:
    handle = create_task(engine, "pipeline")
    handle.add_step("load", status="pending")
    step = handle.update_step("load", status="running")
    assert step.started_at is not None

    step = handle.update_step("load", status="completed")
    assert step.completed_at is not None


def test_update_step_metadata(engine: Engine) -> None:
    handle = create_task(engine, "pipeline")
    handle.add_step("extract")
    step = handle.update_step("extract", metadata={"rows": 1000})
    assert step.step_metadata == {"rows": 1000}


def test_step_ordering(engine: Engine) -> None:
    handle = create_task(engine, "pipeline")
    handle.add_step("step-a")
    handle.add_step("step-b")
    handle.add_step("step-c")
    steps = handle.get_steps()
    assert [s.name for s in steps] == ["step-a", "step-b", "step-c"]
    assert steps[0].created_at <= steps[1].created_at <= steps[2].created_at


def test_duplicate_step_name_raises(engine: Engine) -> None:
    handle = create_task(engine, "pipeline")
    handle.add_step("extract")
    with pytest.raises(Exception):
        handle.add_step("extract")


def test_get_task_not_found(engine: Engine) -> None:
    with pytest.raises(Exception):
        get_task(engine, uuid.uuid4())


def test_update_task_status(engine: Engine) -> None:
    handle = create_task(engine, "pipeline")
    handle.update_status("running")
    found = get_task(engine, handle.task_id)
    steps = found.get_steps()
    assert steps == []


def test_ensure_schema_idempotent(engine: Engine) -> None:
    ensure_schema(engine)
    ensure_schema(engine)


def test_task_with_metadata(engine: Engine) -> None:
    handle = create_task(
        engine, "pipeline", metadata={"source": "s3", "priority": 1}
    )
    found = get_task(engine, handle.task_id)
    assert found.task_id == handle.task_id
