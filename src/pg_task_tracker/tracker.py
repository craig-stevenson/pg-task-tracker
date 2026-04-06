from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine
from sqlmodel import Session, select

from pg_task_tracker._types import StepStatus, TaskStatus
from pg_task_tracker.models import Task, TaskStep, _utcnow


class TaskHandle:
    """Handle to a single task. Provides methods to add and update steps."""

    def __init__(self, task_id: UUID, engine: Engine) -> None:
        self._task_id = task_id
        self._engine = engine

    @property
    def task_id(self) -> UUID:
        return self._task_id

    def add_step(
        self,
        name: str,
        *,
        status: StepStatus = "pending",
        metadata: dict[str, Any] | None = None,
    ) -> TaskStep:
        """Append a new step to this task."""
        now = _utcnow()
        step = TaskStep(
            task_id=self._task_id,
            name=name,
            status=status,
            started_at=now if status == "running" else None,
            step_metadata=metadata,
        )
        with Session(self._engine) as session:
            session.add(step)
            session.commit()
            session.refresh(step)
        return step

    def update_step(
        self,
        name: str,
        *,
        status: StepStatus | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskStep:
        """Update an existing step by name."""
        with Session(self._engine) as session:
            step = session.exec(
                select(TaskStep).where(
                    TaskStep.task_id == self._task_id,
                    TaskStep.name == name,
                )
            ).one()

            if status is not None:
                step.status = status
                now = _utcnow()
                if status == "running":
                    step.started_at = now
                elif status in ("completed", "failed"):
                    step.completed_at = now

            if metadata is not None:
                step.step_metadata = metadata

            session.commit()
            session.refresh(step)
        return step

    def get_steps(self) -> list[TaskStep]:
        """Return all steps for this task, ordered by creation time."""
        with Session(self._engine) as session:
            return list(
                session.exec(
                    select(TaskStep)
                    .where(TaskStep.task_id == self._task_id)
                    .order_by(TaskStep.created_at)  # ty: ignore[invalid-argument-type]
                ).all()
            )

    def update_status(self, status: TaskStatus) -> None:
        """Update the task's own status."""
        with Session(self._engine) as session:
            task = session.get_one(Task, self._task_id)
            task.status = status
            task.updated_at = _utcnow()
            session.commit()


def create_task(
    engine: Engine,
    name: str,
    *,
    status: TaskStatus = "pending",
    metadata: dict[str, Any] | None = None,
) -> TaskHandle:
    """Create a new task and return a handle to it."""
    task = Task(name=name, status=status, task_metadata=metadata)
    with Session(engine) as session:
        session.add(task)
        session.commit()
        session.refresh(task)
        task_id = task.id
    return TaskHandle(task_id, engine)


def get_task(engine: Engine, task_id: UUID) -> TaskHandle:
    """Resume working with an existing task by its UUID."""
    with Session(engine) as session:
        session.get_one(Task, task_id)
    return TaskHandle(task_id, engine)
