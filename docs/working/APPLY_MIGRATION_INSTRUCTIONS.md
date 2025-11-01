# Apply User Profiles Migration to Supabase

## Quick Start

The easiest way to apply the migration is through the Supabase Dashboard SQL Editor.

## Steps

### 1. Open Supabase SQL Editor

1. Go to your Supabase project: https://supabase.com/dashboard/project/zvesxmkgkldorxlbyhce
2. Navigate to **SQL Editor** in the left sidebar
3. Click **New Query**

### 2. Copy and Run Migration SQL

Copy the entire contents of `backend/apply_user_profiles_migration.sql` and paste into the SQL Editor.

**Or copy this SQL directly:**

```sql
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
```

### 3. Run the Query

Click **Run** or press `Ctrl+Enter` (Windows/Linux) / `Cmd+Enter` (Mac)

### 4. Verify Results

You should see output showing:
- "Tables created:" with `user_profiles` listed
- All column definitions
- Foreign keys created for `crawler_jobs` and `topics`

**Expected Output:**
```
Tables created:
user_profiles

Columns in user_profiles:
id              | uuid                     | NO
email           | character varying        | NO
display_name    | character varying        | YES
avatar_url      | character varying        | YES
preferences     | jsonb                    | YES
created_at      | timestamp with time zone | NO
updated_at      | timestamp with time zone | NO
last_login_at   | timestamp with time zone | YES

Foreign keys created:
fk_crawler_jobs_user_id | crawler_jobs | user_id
fk_topics_user_id       | topics       | user_id
```

### 5. Verify in Table Editor (Optional)

1. Go to **Table Editor** in left sidebar
2. You should see `user_profiles` in the list of tables
3. Click on it to see the schema

## What Was Created

### Tables
- ✅ `user_profiles` - Main user profile table

### Columns Added
- ✅ `crawler_jobs.user_id` - Links jobs to users
- ✅ Foreign key already exists on `topics.user_id`

### Indexes Created
- ✅ `idx_user_profiles_email` - Fast email lookups
- ✅ `idx_user_profiles_created_at` - Sort by join date
- ✅ `idx_crawler_jobs_user_id` - Fast user job queries
- ✅ `idx_crawler_jobs_user_status` - Composite index for filtering
- ✅ `idx_topics_user_id` - Fast user topics queries

### Foreign Keys
- ✅ `crawler_jobs.user_id` → `user_profiles.id` (CASCADE DELETE)
- ✅ `topics.user_id` → `user_profiles.id` (CASCADE DELETE)

## Troubleshooting

### Error: relation "user_profiles" already exists
This is fine - it means the table was already created. The migration is idempotent.

### Error: column "user_id" already exists
This is fine - the migration uses `IF NOT EXISTS` to avoid duplicates.

### Error: constraint already exists
This is fine - constraints are only added if they don't exist.

## Next Steps

After applying the migration:

1. **Test Profile API**
   ```bash
   # Get your JWT token from Google Auth
   TOKEN="your_token_here"

   # Test profile endpoint
   curl http://localhost:8000/api/profile/me \
     -H "Authorization: Bearer $TOKEN"
   ```

2. **Update Frontend**
   - Add profile page component
   - Display user info from `/api/profile/me`
   - Show crawler jobs and topics

3. **Update Job Creation**
   - Add `user_id` when creating crawler jobs
   - Filter jobs by current user

## Rollback (If Needed)

If you need to undo this migration:

```sql
BEGIN;

-- Drop foreign keys
ALTER TABLE crawler_jobs DROP CONSTRAINT IF EXISTS fk_crawler_jobs_user_id;
ALTER TABLE topics DROP CONSTRAINT IF EXISTS fk_topics_user_id;

-- Drop indexes
DROP INDEX IF EXISTS idx_user_profiles_email;
DROP INDEX IF EXISTS idx_user_profiles_created_at;
DROP INDEX IF EXISTS idx_crawler_jobs_user_id;
DROP INDEX IF EXISTS idx_crawler_jobs_user_status;
DROP INDEX IF EXISTS idx_topics_user_id;

-- Drop user_id column
ALTER TABLE crawler_jobs DROP COLUMN IF EXISTS user_id;

-- Drop table
DROP TABLE IF EXISTS user_profiles CASCADE;

-- Revert Alembic version
UPDATE alembic_version SET version_num = 'add_github_scraping' WHERE version_num = '20251101_0000';

COMMIT;
```

## Support

If you encounter any issues:
1. Check the Supabase logs in the Dashboard
2. Verify your database permissions
3. Make sure you're connected to the correct project
