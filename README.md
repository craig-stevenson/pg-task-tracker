# pg-task-tracker

A simple Python library for tracking multi-step task progress in PostgreSQL (or SQLite).

## Installation

```bash
pip install pg-task-tracker
```

## Quick Start

```python
from sqlmodel import create_engine
import pg_task_tracker
from pg_task_tracker import create_task, get_task, ensure_schema

engine = create_engine("postgresql+psycopg2://user:pass@localhost/mydb")
ensure_schema(engine)
pg_task_tracker.init(engine)

task = create_task("etl-pipeline")

task.add_step("extract", status="running")
task.update_step("extract", status="completed", metadata={"rows": 5000})

task.add_step("transform", status="running")
task.update_step("transform", status="completed", metadata={"duration_s": 12.3})

task.add_step("load", status="running")
task.update_step("load", status="failed", metadata={"error": "connection timeout"})

task.update_status("failed")
```

## Resuming a Task

```python
task = get_task(task_id)

for step in task.get_steps():
    print(f"{step.name}: {step.status}")
```

## Decorator

Initialize the library once at startup, then use `@track()` to automatically create a task and track a function's execution:

```python
import pg_task_tracker
from pg_task_tracker import track

pg_task_tracker.init(engine)

@track()
def run_pipeline():
    extract_data()
    transform_data()
    load_data()

run_pipeline()  # Creates task "run_pipeline", sets status to completed or failed
```

The decorator:
- Creates a new task with status `"running"` when the function is called
- Sets the task to `"completed"` if the function returns normally
- Sets the task to `"failed"` if the function raises an exception (the exception is re-raised)

Override the task name with the `name` parameter:

```python
@track(name="nightly-etl")
def run_pipeline():
    ...
```

Calling `@track()` without first calling `pg_task_tracker.init(engine)` will raise a `RuntimeError`.

## Database Strategy

Every method that mutates state commits immediately — there is no batching or deferred writes. This means each call is a separate database round-trip. Plan accordingly if you are tracking a large number of steps.

| Method | DB Operations | Round-trips |
|---|---|---|
| `ensure_schema(engine)` | `CREATE TABLE IF NOT EXISTS` for each table | 1 |
| `create_task(name, ...)` | `INSERT` into `ptt_task` | 1 |
| `get_task(task_id)` | `SELECT` from `ptt_task` to verify existence | 1 |
| `task.add_step(...)` | `INSERT` into `ptt_task_step` | 1 |
| `task.update_step(...)` | `SELECT` + `UPDATE` on `ptt_task_step` | 2 |
| `task.update_status(...)` | `SELECT` + `UPDATE` on `ptt_task` | 2 |
| `task.get_steps()` | `SELECT` from `ptt_task_step` ordered by `created_at` | 1 |
| `get_migration_sql()` | None (reads bundled `.sql` file from package) | 0 |

For a typical task with N steps where each step transitions through `pending` -> `running` -> `completed`, expect roughly **2N + 2** round-trips: 1 to create the task, 1 per `add_step`, 2 per `update_step`, and 1 to update the final task status.

## Schema Management

Create tables automatically:

```python
ensure_schema(engine)
```

Or apply the bundled SQL migration manually:

```python
from pg_task_tracker import get_migration_sql

print(get_migration_sql())
# Copy and run with psql, or apply however you manage migrations
```

## Step Statuses

Steps and tasks use the same set of statuses: `pending`, `running`, `completed`, `failed`.

Timestamps are managed automatically:
- `started_at` is set when a step moves to `running`
- `completed_at` is set when a step moves to `completed` or `failed`

## Table Names

All tables are prefixed with `ptt_` to avoid conflicts:
- `ptt_task`
- `ptt_task_step`
