-- Add email/password auth fields and server-side sessions table.
-- This migration intentionally deletes legacy user data.
-- Safe to run multiple times.

BEGIN;

-- 1) Users: add new auth columns
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email VARCHAR(255),
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- 2) Delete all existing users and dependent rows.
--    CASCADE removes related records in goals/chat/transactions/sessions.
TRUNCATE TABLE users CASCADE;

-- 3) Enforce constraints expected by the application model
ALTER TABLE users
    ALTER COLUMN email SET NOT NULL,
    ALTER COLUMN password_hash SET NOT NULL;

-- 4) Ensure email uniqueness/indexing
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

-- 5) Sessions table for server-side auth sessions
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(128) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_sessions_user_id ON sessions (user_id);
CREATE INDEX IF NOT EXISTS ix_sessions_expires_at ON sessions (expires_at);

COMMIT;
