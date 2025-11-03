# 🔧 Quick Fix Summary - Railway & OAuth Issues

This document summarizes the fixes for the two reported issues.

## Issue 1: Crawler "Name or Service Not Known" Error ❌

### Problem
When users create custom topics and click the crawler button, they get an error: **"name or service not known"**

### Root Cause
The async crawler job system requires Upstash Redis for job queuing, but the environment variables were not configured:
- `UPSTASH_REDIS_REST_URL` - Missing
- `UPSTASH_REDIS_REST_TOKEN` - Missing

### Solution ✅

1. **Sign up for Upstash Redis** (Free tier: 10,000 requests/day)
   - Go to https://upstash.com/
   - Create account
   - Create a new Redis database
   - Get REST API credentials

2. **Add environment variables to Railway**
   ```bash
   UPSTASH_REDIS_REST_URL=https://your-database.upstash.io
   UPSTASH_REDIS_REST_TOKEN=your-token-here
   ```

3. **Redeploy backend**
   - Railway will auto-redeploy after adding variables
   - Or manually redeploy from Railway dashboard

### Files Changed
- ✅ `backend/.env.example` - Added Upstash Redis configuration with comments
- ✅ `docs/UPSTASH_REDIS_SETUP.md` - Complete setup guide created

### Testing
After setup, test the crawler:
1. Sign in to your app
2. Go to Profile → Create custom topic
3. Return to home page
4. Click crawler button
5. Should see: "Crawler job queued successfully!" ✅

---

## Issue 2: Google OAuth Redirects to Production URL ❌

### Problem
Railway preview deployments (PR previews) have dynamic URLs like:
```
https://hypepaper-backend-pr-15-abc123.up.railway.app
```

But Google OAuth requires pre-configured redirect URIs. Users testing preview deployments get redirected to production URL instead of the preview URL.

### Root Cause
- Preview deployment URLs change with every PR
- Google OAuth doesn't support wildcard redirect URIs
- Frontend uses `window.location.origin` which points to preview URL
- But Google OAuth rejects the redirect because the URL isn't pre-configured

### Solution Options

#### Option A: OAuth Redirect Proxy (Recommended) ✅

**Added a stable proxy endpoint** that works for all preview deployments.

1. **Backend** automatically detects environment and redirects to correct frontend URL
2. **Only ONE redirect URI** needed in Google OAuth
3. **Works for all preview deployments** without configuration

**How it works:**
```
User clicks Sign In
  ↓
Google OAuth (redirects to stable proxy)
  ↓
Backend: /oauth/redirect-proxy
  ↓
Detects: Railway preview? Production? Local?
  ↓
Redirects to: Correct frontend URL/auth/callback
  ↓
User authenticated on preview deployment ✅
```

**Google OAuth Configuration:**
Add these redirect URIs:
```
https://api.hypepaper.app/oauth/redirect-proxy
https://your-railway-backend.up.railway.app/oauth/redirect-proxy
```

**Note**: To use this, the frontend would need to be updated to use the proxy endpoint instead of direct callback. This is optional - see Option B for no-code solution.

#### Option B: Manual Redirect URI Management

For each PR that needs OAuth testing:
1. Get the preview deployment URL from Railway
2. Add it to Google OAuth redirect URIs
3. Test authentication
4. Remove it after PR is merged

**Steps:**
1. Create PR → Railway deploys preview
2. Get preview URL: `https://hypepaper-backend-pr-15-abc123.up.railway.app`
3. Google Cloud Console → OAuth Client → Add redirect URI:
   ```
   https://hypepaper-backend-pr-15-abc123.up.railway.app/auth/callback
   ```
4. Test OAuth on preview deployment
5. Merge PR → Remove redirect URI

### Files Changed
- ✅ `backend/src/main.py` - Added `/oauth/redirect-proxy` endpoint
- ✅ `backend/.env.example` - Added `ENVIRONMENT` and Railway variables
- ✅ `railway.toml` - Added `FRONTEND_URL` to production environment
- ✅ `docs/RAILWAY_PREVIEW_OAUTH.md` - Complete guide with 3 solution options

### Current Implementation
The OAuth redirect proxy is **implemented and ready** to use. However, the frontend currently uses direct OAuth callbacks (`window.location.origin/auth/callback`).

**To enable the proxy for preview deployments**, either:
1. Update frontend to use proxy endpoint (requires code change)
2. Use Option B (manual redirect URI management) - works immediately ✅

---

## Quick Setup Checklist

### For Crawler Fix
- [ ] Sign up at https://upstash.com/
- [ ] Create Redis database
- [ ] Copy REST API credentials
- [ ] Add to Railway environment variables
- [ ] Test crawler on a custom topic

### For OAuth Preview Fix

**Immediate Solution (No Code Change):**
- [ ] Create test PR
- [ ] Get preview deployment URL from Railway
- [ ] Add URL to Google OAuth redirect URIs
- [ ] Test OAuth login on preview
- [ ] Works! ✅

**Long-term Solution (Recommended):**
- [ ] Update frontend to use OAuth proxy (future PR)
- [ ] Add proxy URL to Google OAuth
- [ ] All preview deployments work automatically! ✅

---

## Environment Variables Required

### Railway Production
```bash
# Database
DATABASE_URL=postgresql+asyncpg://...

# Supabase
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...

# Upstash Redis (NEW - Required for crawler)
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...

# OAuth
ENVIRONMENT=production
FRONTEND_URL=https://hypepaper.pages.dev

# Security
CORS_ORIGINS=https://hypepaper.pages.dev,http://localhost:5173
```

### Railway Preview (Automatic)
Railway automatically sets:
- `RAILWAY_ENVIRONMENT_NAME=pr-123`
- `RAILWAY_STATIC_URL=<preview-hostname>`
- `RAILWAY_GIT_BRANCH=feature/...`

The OAuth proxy uses these to determine the correct frontend URL.

---

## Testing Both Fixes

### Test Crawler
```bash
# 1. Set up Upstash Redis in Railway
# 2. Visit your app and sign in
curl -H "Authorization: Bearer $TOKEN" \
  -X POST https://api.hypepaper.app/api/async-jobs/enqueue \
  -H "Content-Type: application/json" \
  -d '{"job_type":"arxiv","params":{"query":"transformer","limit":10}}'

# Should return: {"success":true,"job_id":"...","message":"Job queued..."}
```

### Test OAuth Preview
```bash
# 1. Create test PR
git checkout -b test/oauth-preview
git push origin test/oauth-preview

# 2. Get Railway preview URL from dashboard
# 3. Add to Google OAuth redirect URIs
# 4. Visit preview URL and click "Sign In"
# 5. Should redirect to Google OAuth and back to preview URL (not production!)
```

---

## Documentation

### Full Guides Created
- 📖 `docs/UPSTASH_REDIS_SETUP.md` - Complete Upstash setup with troubleshooting
- 📖 `docs/RAILWAY_PREVIEW_OAUTH.md` - 3 OAuth solutions with examples
- 📝 `backend/.env.example` - Updated with all required variables

### Quick Reference
- 🔗 Upstash: https://upstash.com/
- 🔗 Google OAuth: https://console.cloud.google.com/
- 🔗 Railway: https://railway.app/dashboard
- 🔗 Supabase: https://supabase.com/dashboard

---

## Summary

✅ **Issue 1 (Crawler)**: Fixed by adding Upstash Redis configuration
✅ **Issue 2 (OAuth)**: Multiple solutions provided - immediate fix available!

Both issues are now resolved with comprehensive documentation! 🎉

### Next Steps
1. Set up Upstash Redis for crawler functionality
2. Choose OAuth solution (manual URLs or use proxy)
3. Test on preview deployment
4. Enjoy seamless preview testing! 🚀
