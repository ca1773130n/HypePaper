# Complete Profile System Deployment Guide

## Current Status

✅ **Code Ready**: All profile code committed and pushed to GitHub
✅ **Router Fixed**: Profile router properly included in main.py
❌ **Backend Not Deployed**: Railway hasn't auto-deployed the new code
❌ **Migration Not Applied**: Database schema not yet created in Supabase

## Why Profile Endpoints Return 404

The production backend is still running old code (before commit `b7d01d0`). Railway's auto-deploy hasn't triggered, possibly due to:
- GitHub Actions workflow failures (missing RAILWAY_TOKEN secret)
- Railway not configured for auto-deploy from GitHub
- Deployment webhook not triggering

## Step-by-Step Deployment

### 1. Deploy Backend to Railway (2 minutes)

**Option A: Railway Dashboard (Recommended)**
1. Go to https://railway.app/dashboard
2. Select your **hypepaper-backend** service
3. Click **Deploy** → **Redeploy**
4. Wait 2-3 minutes for deployment to complete
5. Check logs for "Application startup complete"

**Option B: Railway CLI**
```bash
# Login to Railway
railway login

# Deploy backend
railway up --service hypepaper-backend --detach

# Watch logs
railway logs --service hypepaper-backend
```

**Option C: Fix GitHub Actions (Advanced)**
1. Go to https://github.com/ca1773130n/HypePaper/settings/secrets/actions
2. Add secret: `RAILWAY_TOKEN` (get from Railway dashboard → Settings → Tokens)
3. Re-run failed workflow: https://github.com/ca1773130n/HypePaper/actions

### 2. Apply Database Migration to Supabase (2 minutes)

**Go to Supabase SQL Editor:**
1. Open https://supabase.com/dashboard/project/zvesxmkgkldorxlbyhce/sql/new
2. Copy and paste this SQL:

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

-- Add comments
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

-- Add foreign key to topics
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

3. Click **Run** (Cmd+Enter)
4. Verify output shows:
   - ✅ Tables created: user_profiles
   - ✅ 8 columns defined
   - ✅ 2 foreign keys created

### 3. Verify Deployment (1 minute)

**Check Profile Endpoints:**
```bash
# Health check
curl https://api.hypepaper.app/health
# Should return: {"status":"ok"}

# Check OpenAPI spec for profile endpoints
curl -s https://api.hypepaper.app/openapi.json | \
  python3 -c "import sys, json; paths=[p for p in json.load(sys.stdin)['paths'].keys() if 'profile' in p]; print('\n'.join(sorted(paths)))"
# Should show 7 endpoints:
# /api/profile/me
# /api/profile/me/crawler-jobs
# /api/profile/me/preferences
# /api/profile/me/stats
# /api/profile/me/topics
```

**Test with Authentication:**
```bash
# Get your JWT token from browser:
# 1. Open browser DevTools → Application → Local Storage
# 2. Find: sb-zvesxmkgkldorxlbyhce-auth-token
# 3. Copy the "access_token" value

TOKEN="your_token_here"

# Test profile endpoint
curl https://api.hypepaper.app/api/profile/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Should return your profile:
# {
#   "id": "...",
#   "email": "your-email@gmail.com",
#   "display_name": "Your Name",
#   "avatar_url": "...",
#   "preferences": {},
#   "created_at": "...",
#   "updated_at": "...",
#   "last_login_at": "..."
# }
```

### 4. Test Frontend (1 minute)

1. **Refresh your browser** (Ctrl+Shift+R / Cmd+Shift+R)
2. **Navigate to Profile page**
3. **Verify** no more 404 errors in console
4. **Check** profile data loads correctly

## Troubleshooting

### Profile Endpoints Still Return 404

**Check if backend redeployed:**
```bash
# Check deployment commit
curl -s https://api.hypepaper.app/openapi.json | python3 -c "import sys, json; print('Profile endpoints:', len([p for p in json.load(sys.stdin)['paths'].keys() if 'profile' in p]))"
# Should show: Profile endpoints: 7
# If shows 0, backend didn't redeploy yet
```

**Solution**: Manually redeploy from Railway dashboard (Step 1)

### Database Migration Errors

**Error: relation "user_profiles" already exists**
- This is fine - migration is idempotent

**Error: column "user_id" already exists**
- This is fine - uses IF NOT EXISTS

**Error: constraint already exists**
- This is fine - checks before creating

### GitHub Actions Workflow Failures

**Root Cause**: Missing or invalid RAILWAY_TOKEN secret

**Solution**:
1. Get Railway token: https://railway.app/account/tokens
2. Add to GitHub secrets: https://github.com/ca1773130n/HypePaper/settings/secrets/actions
3. Re-run workflow: https://github.com/ca1773130n/HypePaper/actions

## What Was Built

### Backend Components
- ✅ `backend/src/models/user_profile.py` - SQLAlchemy model
- ✅ `backend/src/services/user_profile_service.py` - Service layer (10 methods)
- ✅ `backend/src/api/v1/profile.py` - REST API (7 endpoints)
- ✅ `backend/src/main.py` - Router integration (line 88)
- ✅ `backend/alembic/versions/20251101_0000_create_user_profiles.py` - Migration

### Frontend Components
- ✅ `frontend/src/services/api.ts` - Profile API client
- ✅ `frontend/src/pages/ProfilePage.vue` - Profile UI

### Database Schema
- ✅ `user_profiles` table with Google Auth UUID
- ✅ Foreign keys: crawler_jobs.user_id, topics.user_id
- ✅ CASCADE DELETE for data cleanup
- ✅ Indexes for performance

## Git Commits

All code is committed and pushed:
- `267f6e5` - feat: add user_profiles table with Google Auth integration
- `64922b4` - feat: add user profile API endpoints and service layer
- `e8e901a` - feat: enhance profile page with comprehensive user management UI
- `b7d01d0` - fix: add profile router to main FastAPI app
- `a268ccb` - chore: trigger Railway redeploy for profile endpoints

## API Documentation

Once deployed, full API docs available at:
- https://api.hypepaper.app/docs

Profile endpoints:
- `GET /api/profile/me` - Get current user profile
- `PUT /api/profile/me` - Update profile (display_name, avatar_url)
- `PUT /api/profile/me/preferences` - Update preferences
- `GET /api/profile/me/crawler-jobs` - Get user's crawler jobs
- `GET /api/profile/me/topics` - Get user's custom topics
- `GET /api/profile/me/stats` - Get user statistics
- `DELETE /api/profile/me` - Delete profile (CASCADE deletes all data)

## Next Steps After Deployment

1. ✅ Profile system fully functional
2. 🔄 Update crawler job creation to set `user_id`
3. 🔄 Update topic creation to set `user_id`
4. 🔄 Add profile page link to navigation
5. 🔄 Add user avatar to header
6. 🔄 Add "My Papers" filtered view (papers from user's jobs)

## Support

If you encounter issues:
1. Check Railway logs: https://railway.app/dashboard → hypepaper-backend → Logs
2. Check Supabase logs: https://supabase.com/dashboard/project/zvesxmkgkldorxlbyhce/logs
3. Check browser console for frontend errors
4. Verify JWT token is valid (check expiration)
