-- This script must be run after the initial setup (creating schema 'api' and role 'api_role').

-- 1. Create the Task table in the 'api' schema
CREATE TABLE api.tasks (
    -- Unique identifier for the task
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The name or description of the task (required)
    name TEXT NOT NULL,

    -- The completion status of the task
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,

    -- Optional: Timestamp for when the task was created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Grant specific permissions for the new table to the 'api_role'.
--    (We grant them explicitly here, even though ALTER DEFAULT PRIVILEGES was used,
--     to ensure immediate permission setup for this specific table).
GRANT SELECT, INSERT, UPDATE, DELETE ON api.tasks TO api_role;

-- 3. Grant usage on sequences (needed if you use serial/bigserial, but good practice for UUID)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA api TO api_role;

-- 4. Insert initial dummy data
INSERT INTO api.tasks (name, is_completed) VALUES
    ('Configure PostgREST endpoint URL in index.js', FALSE),
    ('Test adding a new task via POST request', FALSE),
    ('Verify task completion status updates via PATCH', FALSE),
    ('Load database schema into PostgREST configuration', TRUE),
    ('Finalize design review for fixed header/footer', FALSE);

-- Select all tasks to verify the data was inserted
SELECT * FROM api.tasks;