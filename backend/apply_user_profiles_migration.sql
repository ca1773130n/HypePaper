-- User Profiles Migration for Supabase
-- Run this in Supabase SQL Editor

BEGIN;

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(200),
    avatar_url VARCHAR(500),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- Add comments for documentation
COMMENT ON TABLE user_profiles IS 'User profiles from Google Auth (Supabase auth.users)';
COMMENT ON COLUMN user_profiles.id IS 'User UUID from Google Auth (Supabase auth.users.id)';
COMMENT ON COLUMN user_profiles.email IS 'User email address from Google Auth';
COMMENT ON COLUMN user_profiles.display_name IS 'User display name (from Google or custom)';
COMMENT ON COLUMN user_profiles.avatar_url IS 'User avatar/profile picture URL';
COMMENT ON COLUMN user_profiles.preferences IS 'User preferences and settings (JSONB)';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);

-- Add user_id to crawler_jobs
ALTER TABLE crawler_jobs ADD COLUMN IF NOT EXISTS user_id UUID;

-- Add foreign key constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_crawler_jobs_user_id'
    ) THEN
        ALTER TABLE crawler_jobs
        ADD CONSTRAINT fk_crawler_jobs_user_id
        FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create indexes for crawler_jobs
CREATE INDEX IF NOT EXISTS idx_crawler_jobs_user_id ON crawler_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_crawler_jobs_user_status ON crawler_jobs(user_id, status);

-- Add foreign key to topics (user_id column already exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_topics_user_id'
    ) THEN
        ALTER TABLE topics
        ADD CONSTRAINT fk_topics_user_id
        FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create index for topics
CREATE INDEX IF NOT EXISTS idx_topics_user_id ON topics(user_id);

-- Update Alembic version
UPDATE alembic_version SET version_num = '20251101_0000' WHERE version_num = 'add_github_scraping';

COMMIT;

-- Verification queries
SELECT 'Tables created:' AS status;
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = 'user_profiles';

SELECT 'Columns in user_profiles:' AS status;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_profiles'
ORDER BY ordinal_position;

SELECT 'Foreign keys created:' AS status;
SELECT con.conname AS constraint_name,
       rel.relname AS table_name,
       att.attname AS column_name
FROM pg_constraint con
JOIN pg_class rel ON con.conrelid = rel.oid
JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ANY(con.conkey)
WHERE con.contype = 'f' AND rel.relname IN ('crawler_jobs', 'topics')
ORDER BY rel.relname, att.attname;
