import uuid as _uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, JSON, String, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskStep(SQLModel, table=True):
    __tablename__ = "st_task_step"
    __table_args__ = (UniqueConstraint("task_id", "name"),)

    id: _uuid.UUID = Field(default_factory=_uuid.uuid4, primary_key=True)
    task_id: _uuid.UUID = Field(foreign_key="st_task.id", index=True)
    name: str = Field(max_length=255)
    status: str = Field(default="pending", sa_column=Column(String(20), nullable=False, server_default="pending"))
    step_order: int
    created_at: datetime = Field(default_factory=_utcnow)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    step_metadata: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON, nullable=True)
    )

    task: "Task" = Relationship(back_populates="steps")


class Task(SQLModel, table=True):
    __tablename__ = "st_task"

    id: _uuid.UUID = Field(default_factory=_uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    status: str = Field(default="pending", sa_column=Column(String(20), nullable=False, server_default="pending"))
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    task_metadata: dict[str, Any] | None = Field(
        default=None, sa_column=Column("metadata", JSON, nullable=True)
    )

    steps: list[TaskStep] = Relationship(back_populates="task")
