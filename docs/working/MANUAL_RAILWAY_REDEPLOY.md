# Manual Railway Redeploy - Quick Guide

## Issue

Latest commit `3c9d43d` includes critical fixes:
- ✅ Profile router path fix (`/api/profile/*` instead of `/profile/*`)
- ✅ Supabase dependency upgrade (fixes proxy error)

But Railway hasn't auto-deployed yet. Currently running old code.

## Solution: Manual Redeploy (1 minute)

### Step 1: Go to Railway Dashboard
Open: https://railway.app/dashboard

### Step 2: Select Backend Service
Click on your **hypepaper-backend** service (or whatever it's named)

### Step 3: Trigger Redeploy
1. Click **Deployments** tab (in the service page)
2. Click **Deploy** button (top right corner)
3. Select **Redeploy**
4. Confirm the redeploy

### Step 4: Wait for Deployment
- Deployment takes ~2-3 minutes
- Watch the logs for:
  ```
  INFO: Started server process [1]
  INFO: Waiting for application startup.
  INFO: Application startup complete.
  INFO: Uvicorn running on http://0.0.0.0:8000
  ```

### Step 5: Verify Fix

After deployment completes (logs show "Application startup complete"), check:

```bash
# Check if endpoints are at correct path now
curl -s https://api.hypepaper.app/openapi.json | \
  python3 -c "import sys, json; api_profile=[p for p in json.load(sys.stdin)['paths'].keys() if p.startswith('/api/profile')]; print(f'✅ {len(api_profile)} endpoints at /api/profile/*' if api_profile else '❌ Still at wrong path'); [print(f'  - {p}') for p in sorted(api_profile)]"

# Expected output:
# ✅ 5 endpoints at /api/profile/*
#   - /api/profile/me
#   - /api/profile/me/crawler-jobs
#   - /api/profile/me/preferences
#   - /api/profile/me/stats
#   - /api/profile/me/topics
```

### Step 6: Test Profile Endpoint

```bash
# Get your JWT token from browser
# DevTools → Application → Local Storage → sb-zvesxmkgkldorxlbyhce-auth-token → access_token

TOKEN="your_token_here"

# Test profile endpoint (should return 200 now, not 404)
curl -s https://api.hypepaper.app/api/profile/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Expected: Profile data (or error about missing table if migration not applied)
# Not expected: 404 Not Found
```

## What Got Fixed

### Fix 1: Profile Router Path
**Before:**
```python
# backend/src/main.py line 88
app.include_router(profile.router)  # Wrong: /profile/me
```

**After:**
```python
# backend/src/main.py line 88
app.include_router(profile.router, prefix="/api")  # Correct: /api/profile/me
```

**Impact:**
- Frontend requests: `GET /api/profile/me` ✅
- Old backend responded: 404 (no route matched) ❌
- New backend will respond: 200 or database error ✅

### Fix 2: Supabase Proxy Error
**Before:**
```
requirements.prod.txt:
  supabase==2.3.4  # Old version
  httpx==0.25.1    # Incompatible
```

**Error in logs:**
```
TypeError: Client.__init__() got an unexpected keyword argument 'proxy'
```

**After:**
```
requirements.prod.txt:
  supabase==2.9.1  # Latest stable
  httpx==0.27.2    # Compatible
```

**Impact:**
- Authentication will work without proxy errors
- Supabase client creation succeeds
- JWT token verification works properly

## Current vs. Expected State

### Current (Before Redeploy)
- Endpoints at: `/profile/me` (wrong)
- Supabase errors: `TypeError: proxy parameter`
- Frontend requests: 404 errors
- Commit deployed: `182fb08` or earlier

### Expected (After Redeploy)
- Endpoints at: `/api/profile/me` (correct)
- Supabase errors: None (or table missing if no migration)
- Frontend requests: 200 or 500 (table error)
- Commit deployed: `3c9d43d` (latest)

## After Redeploy

Once Railway redeploys with commit `3c9d43d`:

1. **Profile endpoints will respond** (no more 404)
2. **But may return database errors** (table missing)
3. **Next step:** Apply Supabase migration
   - See: `backend/apply_user_profiles_migration.sql`
   - Run in: https://supabase.com/dashboard/project/zvesxmkgkldorxlbyhce/sql/new

## Timeline

- ✅ **Code fixed:** Commit `3c9d43d` pushed
- ⏳ **Deployment:** Waiting for Railway redeploy
- ⏭️ **Migration:** After deployment, apply to Supabase
- ⏭️ **Testing:** Verify endpoints work end-to-end

## Troubleshooting

### Still showing /profile/* instead of /api/profile/*
- Railway hasn't redeployed with latest code
- Check Railway deployment logs for commit hash
- Should show: `3c9d43d` or later
- If not: Trigger manual redeploy again

### Still getting proxy errors
- Dependencies didn't upgrade
- Check Railway build logs for pip install
- Should show: `supabase-2.9.1` and `httpx-0.27.2`
- If not: Clear Railway cache and redeploy

### Getting "table not found" errors
- This is expected! Migration not applied yet
- See: `COMPLETE_PROFILE_DEPLOYMENT.md`
- Run: `backend/apply_user_profiles_migration.sql` in Supabase

## Quick Reference

- **Railway Dashboard:** https://railway.app/dashboard
- **Supabase SQL Editor:** https://supabase.com/dashboard/project/zvesxmkgkldorxlbyhce/sql/new
- **Migration SQL:** `backend/apply_user_profiles_migration.sql`
- **Latest Commit:** `3c9d43d`
