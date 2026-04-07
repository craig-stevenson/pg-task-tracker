from functools import wraps
from typing import Any

from pg_task_tracker._state import get_engine
from pg_task_tracker.tracker import create_task


def track(*, name: str | None = None) -> Any:
    """Decorator that creates a task and tracks the function's execution."""

    def decorator(func: Any) -> Any:
        task_name = name or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            engine = get_engine()
            task = create_task(task_name, engine=engine, status="running")
            try:
                result = func(*args, **kwargs)
            except Exception:
                task.update_status("failed")
                raise
            else:
                task.update_status("completed")
                return result

        return wrapper

    return decorator
