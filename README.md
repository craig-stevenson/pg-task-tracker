# pg-task-tracker

A simple Python library for tracking multi-step task progress in PostgreSQL.

## Installation

```bash
pip install pg-task-tracker
```

## Setup

```python
from sqlmodel import create_engine
import pg_task_tracker
from pg_task_tracker import ensure_schema

engine = create_engine("postgresql+psycopg2://user:pass@localhost/mydb")
ensure_schema(engine)
pg_task_tracker.init(engine)
```

`ensure_schema(engine)` creates the tables if they don't exist. `pg_task_tracker.init(engine)` stores the engine so you don't have to pass it to every call. Both are one-time setup.

## Decorator

The simplest way to track a function:

```python
from pg_task_tracker import track

@track()
def run_pipeline():
    extract_data()
    transform_data()
    load_data()

run_pipeline()
```

This creates a task named `"run_pipeline"` and sets its status to `"completed"` or `"failed"` based on whether the function raises an exception. The exception is always re-raised.

Override the task name:

```python
@track(name="nightly-etl")
def run_pipeline():
    ...
```

## Manual Tracking

For more control, create tasks and steps explicitly:

```python
from pg_task_tracker import create_task, get_task

task = create_task("etl-pipeline")

task.add_step("extract", status="running")
task.update_step("extract", status="completed", metadata={"rows": 5000})

task.add_step("transform", status="running")
task.update_step("transform", status="completed", metadata={"duration_s": 12.3})

task.add_step("load", status="running")
task.update_step("load", status="failed", metadata={"error": "connection timeout"})

task.update_status("failed")
```

Resume an existing task by ID:

```python
task = get_task(task_id)

for step in task.get_steps():
    print(f"{step.name}: {step.status}")
```

Both `create_task` and `get_task` accept an optional `engine=` parameter to override the initialized engine.

## Step Statuses

Steps and tasks use the same set of statuses: `pending`, `running`, `completed`, `failed`.

Timestamps are managed automatically:
- `started_at` is set when a step moves to `running`
- `completed_at` is set when a step moves to `completed` or `failed`

## Database Strategy

Every method that mutates state commits immediately — there is no batching or deferred writes. Each call is a separate database round-trip.

| Method | DB Operations | Round-trips |
|---|---|---|
| `ensure_schema(engine)` | `CREATE TABLE IF NOT EXISTS` for each table | 1 |
| `create_task(name)` | `INSERT` into `ptt_task` | 1 |
| `get_task(task_id)` | `SELECT` from `ptt_task` to verify existence | 1 |
| `task.add_step(...)` | `INSERT` into `ptt_task_step` | 1 |
| `task.update_step(...)` | `SELECT` + `UPDATE` on `ptt_task_step` | 2 |
| `task.update_status(...)` | `SELECT` + `UPDATE` on `ptt_task` | 2 |
| `task.get_steps()` | `SELECT` from `ptt_task_step` ordered by `created_at` | 1 |
| `@track()` | `INSERT` + `SELECT` + `UPDATE` (create task + update status) | 3 |
| `get_migration_sql()` | None (reads bundled `.sql` file from package) | 0 |

For manual tracking with N steps where each transitions through `running` -> `completed`, expect roughly **2N + 2** round-trips.

## Schema Management

Create tables automatically:

```python
ensure_schema(engine)
```

Or apply the bundled SQL migration manually:

```python
from pg_task_tracker import get_migration_sql

print(get_migration_sql())
# Apply with psql or your preferred migration tool
```

## Table Names

All tables are prefixed with `ptt_` to avoid conflicts:
- `ptt_task`
- `ptt_task_step`
