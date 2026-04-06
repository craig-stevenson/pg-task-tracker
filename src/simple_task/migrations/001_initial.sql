-- simple_task: initial schema
-- Apply with: psql -f 001_initial.sql your_database

BEGIN;

CREATE TABLE IF NOT EXISTS st_task (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    metadata    JSONB
);

CREATE INDEX IF NOT EXISTS ix_st_task_name   ON st_task (name);
CREATE INDEX IF NOT EXISTS ix_st_task_status ON st_task (status);

CREATE TABLE IF NOT EXISTS st_task_step (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id       UUID         NOT NULL REFERENCES st_task(id) ON DELETE CASCADE,
    name          VARCHAR(255) NOT NULL,
    status        VARCHAR(20)  NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    step_order    INTEGER      NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    metadata      JSONB,
    UNIQUE (task_id, name)
);

CREATE INDEX IF NOT EXISTS ix_st_task_step_task_id ON st_task_step (task_id);

COMMIT;
