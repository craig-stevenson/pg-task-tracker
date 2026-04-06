-- pg_task_tracker: initial schema
-- Apply with: psql -f 001_initial.sql your_database

BEGIN;

CREATE TABLE IF NOT EXISTS ptt_task (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    metadata    JSONB
);

CREATE INDEX IF NOT EXISTS ix_ptt_task_name   ON ptt_task (name);
CREATE INDEX IF NOT EXISTS ix_ptt_task_status ON ptt_task (status);

CREATE TABLE IF NOT EXISTS ptt_task_step (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id       UUID         NOT NULL REFERENCES ptt_task(id) ON DELETE CASCADE,
    name          VARCHAR(255) NOT NULL,
    status        VARCHAR(20)  NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    metadata      JSONB,
    UNIQUE (task_id, name)
);

CREATE INDEX IF NOT EXISTS ix_ptt_task_step_task_id ON ptt_task_step (task_id);

COMMIT;
