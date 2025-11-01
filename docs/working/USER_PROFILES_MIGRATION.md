# User Profiles Table Migration

## Overview
This document describes the user_profiles table structure and how to apply the migration to Supabase.

## Table Schema

### user_profiles Table
```sql
CREATE TABLE user_profiles (
    -- Primary key (from Supabase auth.users.id)
    id UUID PRIMARY KEY,

    -- User information
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(200),
    avatar_url VARCHAR(500),

    -- Preferences and settings
    preferences JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_user_profiles_email ON user_profiles(email);
CREATE INDEX idx_user_profiles_created_at ON user_profiles(created_at);
```

### Related Table Updates

#### crawler_jobs Table
```sql
-- Add user_id foreign key
ALTER TABLE crawler_jobs ADD COLUMN user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE;
CREATE INDEX idx_crawler_jobs_user_id ON crawler_jobs(user_id);
CREATE INDEX idx_crawler_jobs_user_status ON crawler_jobs(user_id, status);
```

#### topics Table
```sql
-- Add foreign key constraint (user_id column already exists)
ALTER TABLE topics ADD CONSTRAINT fk_topics_user_id
    FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE;
CREATE INDEX idx_topics_user_id ON topics(user_id);
```

## Features

### 1. User Authentication Integration
- **Google Auth UUID**: Primary key comes from Supabase `auth.users.id`
- **Email**: User email from Google authentication
- **Display Name**: User's display name (customizable)
- **Avatar URL**: Profile picture from Google or custom

### 2. Crawler Job Management
- Users can have multiple crawler jobs (active and inactive)
- Crawler jobs are linked via `user_id` foreign key
- Jobs are automatically deleted when user is deleted (CASCADE)
- Query active jobs: `SELECT * FROM crawler_jobs WHERE user_id = ? AND status = 'processing'`
- Query inactive jobs: `SELECT * FROM crawler_jobs WHERE user_id = ? AND status IN ('completed', 'failed')`

### 3. Custom Topics
- Users can create custom topics with:
  - Topic name (unique, lowercase, 3-100 characters)
  - Description (optional)
  - Keywords (array of strings)
- System topics have `user_id = NULL`
- Custom topics have `user_id` set to the creator
- Topics are automatically deleted when user is deleted (CASCADE)

### 4. User Preferences
- Stored as JSONB for flexibility
- Can include any user-specific settings:
  ```json
  {
    "theme": "dark",
    "notifications": {
      "email": true,
      "push": false
    },
    "default_filters": {
      "min_year": 2020,
      "has_github": true
    }
  }
  ```

## SQLAlchemy Model

Location: `backend/src/models/user_profile.py`

Key relationships:
- `crawler_jobs`: List of user's crawler jobs
- `custom_topics`: List of topics created by user

Computed properties:
- `active_crawler_jobs`: Filter jobs by status='processing'
- `inactive_crawler_jobs`: Filter jobs by status in ('completed', 'failed')
- `crawler_job_count`: Dictionary with counts by status

## Applying the Migration

### Option 1: Using Alembic (Recommended)
```bash
# Set DATABASE_URL to Supabase
export DATABASE_URL="postgresql+asyncpg://postgres.zvesxmkgkldorxlbyhce:dlgPwls181920@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"

# Apply migration
cd backend
alembic upgrade 20251101_0000
```

### Option 2: Direct SQL (Supabase SQL Editor)
If Alembic fails due to missing intermediate migrations, use the Supabase SQL Editor:

1. Go to Supabase Dashboard → SQL Editor
2. Run the following SQL:

```sql
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

COMMENT ON COLUMN user_profiles.id IS 'User UUID from Google Auth (Supabase auth.users.id)';
COMMENT ON COLUMN user_profiles.email IS 'User email address from Google Auth';
COMMENT ON COLUMN user_profiles.preferences IS 'User preferences and settings (JSONB)';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON user_profiles(created_at);

-- Add user_id to crawler_jobs
ALTER TABLE crawler_jobs ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE crawler_jobs ADD CONSTRAINT fk_crawler_jobs_user_id
    FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_crawler_jobs_user_id ON crawler_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_crawler_jobs_user_status ON crawler_jobs(user_id, status);

-- Add foreign key to topics
ALTER TABLE topics ADD CONSTRAINT fk_topics_user_id
    FOREIGN KEY (user_id) REFERENCES user_profiles(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_topics_user_id ON topics(user_id);

-- Update Alembic version (if using Alembic)
UPDATE alembic_version SET version_num = '20251101_0000';
```

## Verification

After applying the migration, verify the table exists:

```sql
-- Check table exists
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = 'user_profiles';

-- Check columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_profiles';

-- Check foreign keys
SELECT con.conname AS constraint_name,
       rel.relname AS table_name,
       att.attname AS column_name
FROM pg_constraint con
JOIN pg_class rel ON con.conrelid = rel.oid
JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ANY(con.conkey)
WHERE con.contype = 'f' AND rel.relname IN ('crawler_jobs', 'topics');
```

## Usage Examples

### Create User Profile
```python
from models import UserProfile

# Create new user profile (typically after Google Auth)
user = UserProfile(
    id=auth_user_id,  # From Supabase auth.users.id
    email="user@example.com",
    display_name="John Doe",
    avatar_url="https://lh3.googleusercontent.com/...",
    preferences={"theme": "dark"}
)
session.add(user)
await session.commit()
```

### Query User's Crawler Jobs
```python
# Get user with jobs
user = await session.get(UserProfile, user_id, options=[
    selectinload(UserProfile.crawler_jobs)
])

# Access active jobs
active_jobs = user.active_crawler_jobs
print(f"Active jobs: {len(active_jobs)}")

# Access job counts
counts = user.crawler_job_count
print(f"Total: {counts['total']}, Active: {counts['active']}, Inactive: {counts['inactive']}")
```

### Query User's Custom Topics
```python
# Get user with custom topics
user = await session.get(UserProfile, user_id, options=[
    selectinload(UserProfile.custom_topics)
])

# List custom topics
for topic in user.custom_topics:
    print(f"{topic.name}: {topic.description}")
    print(f"  Keywords: {', '.join(topic.keywords)}")
```

## Next Steps

After applying the migration:

1. **Test Google Auth Integration**
   - Create user profile when user signs in via Google
   - Populate id, email, display_name, avatar_url from Google Auth

2. **Update Crawler Job Creation**
   - Add user_id when creating crawler jobs
   - Filter jobs by user_id in API endpoints

3. **Update Topic Management**
   - Add user_id when users create custom topics
   - Filter topics to show system + user's custom topics

4. **Add API Endpoints**
   - GET /api/profile - Get current user's profile
   - PUT /api/profile - Update profile settings
   - GET /api/profile/crawler-jobs - Get user's crawler jobs
   - GET /api/profile/topics - Get user's custom topics
