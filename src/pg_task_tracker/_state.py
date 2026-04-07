from sqlalchemy import Engine

_engine: Engine | None = None


def init(engine: Engine) -> None:
    """Initialize pg_task_tracker with an engine."""
    global _engine
    _engine = engine


def get_engine(engine: Engine | None = None) -> Engine:
    """Return the provided engine, or fall back to the initialized one."""
    if engine is not None:
        return engine
    if _engine is not None:
        return _engine
    raise RuntimeError(
        "No engine provided and pg_task_tracker not initialized."
        " Call pg_task_tracker.init(engine) first or pass engine= explicitly."
    )
