import uuid

from pg_task_tracker import (
    Task,
    TaskStep,
    StepStatus,
    TaskStatus,
    get_migration_sql,
)


def test_task_defaults() -> None:
    task = Task(name="test-task")
    assert task.name == "test-task"
    assert task.status == "pending"
    assert task.id is not None
    assert task.created_at is not None
    assert task.task_metadata is None


def test_task_step_defaults() -> None:
    task_id = uuid.uuid4()
    step = TaskStep(name="step-1", task_id=task_id)
    assert step.name == "step-1"
    assert step.status == "pending"
    assert step.started_at is None
    assert step.completed_at is None
    assert step.step_metadata is None


def test_get_migration_sql() -> None:
    sql = get_migration_sql()
    assert "CREATE TABLE IF NOT EXISTS st_task" in sql
    assert "CREATE TABLE IF NOT EXISTS st_task_step" in sql


def test_status_types() -> None:
    statuses: list[StepStatus] = ["pending", "running", "completed", "failed"]
    assert len(statuses) == 4

    task_statuses: list[TaskStatus] = ["pending", "running", "completed", "failed"]
    assert len(task_statuses) == 4
