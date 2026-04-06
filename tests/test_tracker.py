"""Integration tests — require TEST_DATABASE_URL to be set."""

import uuid

import pytest
from sqlalchemy import Engine

from simple_task import TaskTracker, ensure_schema


@pytest.fixture()
def tracker(engine: Engine) -> TaskTracker:
    return TaskTracker(engine)


def test_create_task(tracker: TaskTracker) -> None:
    handle = tracker.create_task("my-pipeline")
    assert handle.task_id is not None
    assert isinstance(handle.task_id, uuid.UUID)


def test_add_step(tracker: TaskTracker) -> None:
    handle = tracker.create_task("pipeline")
    step = handle.add_step("extract", status="running")
    assert step.name == "extract"
    assert step.status == "running"
    assert step.started_at is not None
    assert step.step_order == 1


def test_update_step_status(tracker: TaskTracker) -> None:
    handle = tracker.create_task("pipeline")
    handle.add_step("load", status="pending")
    step = handle.update_step("load", status="running")
    assert step.started_at is not None

    step = handle.update_step("load", status="completed")
    assert step.completed_at is not None


def test_update_step_metadata(tracker: TaskTracker) -> None:
    handle = tracker.create_task("pipeline")
    handle.add_step("extract")
    step = handle.update_step("extract", metadata={"rows": 1000})
    assert step.step_metadata == {"rows": 1000}


def test_step_ordering(tracker: TaskTracker) -> None:
    handle = tracker.create_task("pipeline")
    handle.add_step("step-a")
    handle.add_step("step-b")
    handle.add_step("step-c")
    steps = handle.get_steps()
    assert [s.name for s in steps] == ["step-a", "step-b", "step-c"]
    assert [s.step_order for s in steps] == [1, 2, 3]


def test_duplicate_step_name_raises(tracker: TaskTracker) -> None:
    handle = tracker.create_task("pipeline")
    handle.add_step("extract")
    with pytest.raises(Exception):
        handle.add_step("extract")


def test_get_task_by_name(tracker: TaskTracker) -> None:
    handle = tracker.create_task("unique-name")
    found = tracker.get_task_by_name("unique-name")
    assert found.task_id == handle.task_id


def test_get_task_not_found(tracker: TaskTracker) -> None:
    with pytest.raises(Exception):
        tracker.get_task(uuid.uuid4())


def test_update_task_status(tracker: TaskTracker) -> None:
    handle = tracker.create_task("pipeline")
    handle.update_status("running")
    found = tracker.get_task(handle.task_id)
    steps = found.get_steps()
    assert steps == []


def test_ensure_schema_idempotent(engine: Engine) -> None:
    ensure_schema(engine)
    ensure_schema(engine)


def test_task_with_metadata(tracker: TaskTracker) -> None:
    handle = tracker.create_task(
        "pipeline", metadata={"source": "s3", "priority": 1}
    )
    found = tracker.get_task(handle.task_id)
    assert found.task_id == handle.task_id
