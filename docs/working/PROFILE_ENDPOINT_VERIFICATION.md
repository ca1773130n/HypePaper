# Profile Endpoint Verification Guide

## Current Status

✅ **Endpoints ARE deployed at correct path** (`/api/profile/*`)
✅ **Router path fixed** (commit `3c9d43d` deployed)
✅ **Supabase dependencies upgraded** (proxy error fixed)
⏳ **Database migration needed** (user_profiles table doesn't exist yet)

## Quick Test

### Test 1: Verify Endpoints Exist

```bash
curl -s https://api.hypepaper.app/openapi.json | \
  python3 -c "import sys, json; paths=[p for p in json.load(sys.stdin)['paths'].keys() if 'profile' in p]; print('\n'.join(sorted(paths)))"
```

**Expected Output:**
```
/api/profile/me
/api/profile/me/crawler-jobs
/api/profile/me/preferences
/api/profile/me/stats
/api/profile/me/topics
```

✅ **Result:** All 5 endpoints found at `/api/profile/*`

### Test 2: Test Without Authentication

```bash
curl -s https://api.hypepaper.app/api/profile/me/stats
```

**Expected Output:**
```json
{"detail":"Not authenticated"}
```

✅ **Result:** Endpoint exists, requires authentication

### Test 3: Test With Valid Token

Get your JWT token from browser:
1. Open DevTools (F12)
2. Application → Local Storage
3. Find: `sb-zvesxmkgkldorxlbyhce-auth-token`
4. Copy the `access_token` value

```bash
TOKEN="your_access_token_here"

curl -s https://api.hypepaper.app/api/profile/me/stats \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Possible Outputs:**

**A) Database table doesn't exist (migration not applied):**
```json
{
  "detail": "Internal server error"
}
```
Or database error in Railway logs.

**B) Migration applied, profile doesn't exist:**
```json
{
  "detail": "Profile not found"
}
```

**C) Success (migration applied, profile created):**
```json
{
  "total_crawler_jobs": 0,
  "active_crawler_jobs": 0,
  "inactive_crawler_jobs": 0,
  "custom_topics": 0,
  "member_since": "2025-11-01T...",
  "last_login": null
}
```

## If You're Getting 404 Errors

### Issue 1: Browser Cache

**Symptom:** Frontend still shows 404 errors in console

**Solution:**
1. **Hard refresh** browser: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. **Clear browser cache:**
   - DevTools → Application → Storage → Clear site data
3. **Restart browser**

### Issue 2: Frontend Using Old Build

**Symptom:** Deployed frontend is cached

**Solution:**
1. Check Cloudflare Pages dashboard
2. Verify latest deployment is active
3. May need to purge Cloudflare cache

### Issue 3: Wrong API URL in Frontend

**Check:** `frontend/.env` or environment variables:
```bash
cat frontend/.env | grep VITE_API_URL
# Should show: VITE_API_URL=https://api.hypepaper.app
```

### Issue 4: Database Table Doesn't Exist

**This is the most likely issue!**

**Check Railway logs for:**
```
relation "user_profiles" does not exist
```

**Solution:** Apply Supabase migration (see Step 2 below)

## Step 1: ✅ Verify Deployment (Already Done!)

Endpoints are deployed at correct path:
```bash
curl -s https://api.hypepaper.app/api/profile/me \
  -H "Authorization: Bearer fake_token"

# Returns: {"detail":"Not authenticated"}
# This proves endpoint exists!
```

## Step 2: 🔴 Apply Database Migration (REQUIRED)

**You MUST run this to create the `user_profiles` table:**

1. **Open Supabase SQL Editor:**
   https://supabase.com/dashboard/project/zvesxmkgkldorxlbyhce/sql/new

2. **Copy SQL from:**
   `backend/apply_user_profiles_migration.sql`

   Or use this SQL:

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

COMMIT;

-- Verification
SELECT 'user_profiles table created' AS status;
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = 'user_profiles';
```

3. **Run:** Press `Cmd+Enter` (Mac) or `Ctrl+Enter` (Windows/Linux)

4. **Verify:** Should see output:
```
user_profiles table created
user_profiles
```

## Step 3: Test Profile System End-to-End

### 3a. Get Fresh JWT Token

1. Open your app: https://hypepaper.app (or localhost)
2. **Sign in with Google** (if not already signed in)
3. Open DevTools → Application → Local Storage
4. Find: `sb-zvesxmkgkldorxlbyhce-auth-token`
5. Copy the `access_token` value

### 3b. Test Profile Endpoints

```bash
TOKEN="your_fresh_token_here"

# Test 1: Get profile (will auto-create on first access)
curl -s https://api.hypepaper.app/api/profile/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Expected: Profile data with your email

# Test 2: Get stats
curl -s https://api.hypepaper.app/api/profile/me/stats \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Expected: Stats showing 0 jobs, 0 topics

# Test 3: Get crawler jobs
curl -s https://api.hypepaper.app/api/profile/me/crawler-jobs \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Expected: Empty array []

# Test 4: Get topics
curl -s https://api.hypepaper.app/api/profile/me/topics \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Expected: Empty array []
```

### 3c. Test Frontend

1. **Hard refresh browser:** `Cmd+Shift+R` or `Ctrl+Shift+R`
2. **Navigate to Profile page** (if you have a link)
3. **Check browser console** - should be no 404 errors
4. **Profile data should load**

## Debugging Checklist

### Frontend Shows 404

- [ ] Hard refreshed browser
- [ ] Cleared browser cache
- [ ] Checked `VITE_API_URL` is correct
- [ ] Verified frontend build is latest
- [ ] Checked network tab for actual request URL

### Backend Returns 500/Error

- [ ] Applied Supabase migration
- [ ] Verified `user_profiles` table exists
- [ ] Checked Railway logs for database errors
- [ ] Verified Supabase connection string is correct

### Authentication Fails

- [ ] JWT token is fresh (not expired)
- [ ] Token is from correct Supabase project
- [ ] Token has `access_token` field
- [ ] Supabase URL/keys match in frontend and backend

## Success Criteria

When everything works:

✅ All 5 profile endpoints at `/api/profile/*`
✅ Endpoints return 401 without auth (not 404)
✅ Endpoints return data with valid auth
✅ `user_profiles` table exists in Supabase
✅ Profile auto-created on first access
✅ Frontend loads profile data without 404 errors

## Common Errors and Solutions

### "relation user_profiles does not exist"
**Cause:** Migration not applied
**Fix:** Run migration SQL in Supabase SQL Editor

### "Not authenticated"
**Cause:** Missing or invalid JWT token
**Fix:** Get fresh token from browser local storage

### "Profile not found" (404)
**Cause:** Profile doesn't exist in database
**Fix:** Make first request to `/api/profile/me` to auto-create

### "Invalid token"
**Cause:** Token expired or from wrong project
**Fix:** Sign out and sign in again to get fresh token

### Frontend still shows 404
**Cause:** Browser cache or old frontend build
**Fix:** Hard refresh + clear cache

## Next Steps

After verification:

1. ✅ Test profile page in frontend
2. ✅ Verify auto-creation works
3. ✅ Test updating profile (display name, avatar)
4. ✅ Add crawler jobs and see them in profile
5. ✅ Create custom topics and see them in profile

## Reference

- **API Docs:** https://api.hypepaper.app/docs
- **Supabase Dashboard:** https://supabase.com/dashboard/project/zvesxmkgkldorxlbyhce
- **Railway Logs:** https://railway.app/dashboard
- **Migration SQL:** `backend/apply_user_profiles_migration.sql`
