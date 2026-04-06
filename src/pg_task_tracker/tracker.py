from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import Engine, func
from sqlmodel import Session, select

from pg_task_tracker._types import StepStatus, TaskStatus
from pg_task_tracker.models import Task, TaskStep, _utcnow


class TaskHandle:
    """Handle to a single task. Provides methods to add and update steps."""

    def __init__(self, task_id: UUID, session: Session) -> None:
        self._task_id = task_id
        self._session = session

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
        current_max = self._session.exec(
            select(func.max(TaskStep.step_order)).where(
                TaskStep.task_id == self._task_id
            )
        ).one()
        next_order = (current_max or 0) + 1

        now = _utcnow()
        step = TaskStep(
            task_id=self._task_id,
            name=name,
            status=status,
            step_order=next_order,
            started_at=now if status == "running" else None,
            step_metadata=metadata,
        )
        self._session.add(step)
        self._session.commit()
        self._session.refresh(step)
        return step

    def update_step(
        self,
        name: str,
        *,
        status: StepStatus | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TaskStep:
        """Update an existing step by name."""
        step = self._session.exec(
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

        self._session.commit()
        self._session.refresh(step)
        return step

    def get_steps(self) -> list[TaskStep]:
        """Return all steps for this task, ordered by step_order."""
        return list(
            self._session.exec(
                select(TaskStep)
                .where(TaskStep.task_id == self._task_id)
                .order_by(TaskStep.step_order)  # ty: ignore[invalid-argument-type]
            ).all()
        )

    def update_status(self, status: TaskStatus) -> None:
        """Update the task's own status."""
        task = self._session.get_one(Task, self._task_id)
        task.status = status
        task.updated_at = _utcnow()
        self._session.commit()


class TaskTracker:
    """Entry point for tracking multi-step tasks in PostgreSQL."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def _get_session(self) -> Session:
        return Session(self._engine)

    def create_task(
        self,
        name: str,
        *,
        status: TaskStatus = "pending",
        metadata: dict[str, Any] | None = None,
    ) -> TaskHandle:
        """Create a new task and return a handle to it."""
        session = self._get_session()
        task = Task(name=name, status=status, task_metadata=metadata)
        session.add(task)
        session.commit()
        session.refresh(task)
        return TaskHandle(task.id, session)

    def get_task(self, task_id: UUID) -> TaskHandle:
        """Resume working with an existing task by its UUID."""
        session = self._get_session()
        session.get_one(Task, task_id)
        return TaskHandle(task_id, session)

    def get_task_by_name(self, name: str) -> TaskHandle:
        """Look up a task by name. Raises if not found or if multiple match."""
        session = self._get_session()
        task = session.exec(select(Task).where(Task.name == name)).one()
        return TaskHandle(task.id, session)
