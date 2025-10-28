# Authentication Troubleshooting Guide

## Overview

This guide explains common authentication issues in HypePaper and how to resolve them.

## Common Issue: 401 Unauthorized When Creating Topics

### Symptom

- GET requests to `/api/v1/topics` work fine (return 200 OK)
- POST requests to `/api/v1/topics` fail with 401 Unauthorized
- Browser console shows: `POST https://api.hypepaper.app/api/v1/topics 401 (Unauthorized)`
- Error response: `{detail: 'Authentication required'}`

### Root Cause

**Frontend and backend are using different Supabase projects**, causing JWT token validation to fail.

### How Authentication Works

1. **Frontend**: User logs in via Supabase → receives JWT token from Supabase Project A
2. **Frontend**: Sends JWT token in `Authorization: Bearer <token>` header
3. **Backend**: Receives token → validates it using Supabase Project B credentials
4. **Result**: If Project A ≠ Project B, validation fails → 401 error

### Why GET Works But POST Doesn't

- `GET /api/v1/topics` uses `get_current_user()` which allows **optional** authentication
  - Returns system topics if not authenticated
  - Returns system + user topics if authenticated
- `POST /api/v1/topics` uses `get_user_id()` which **requires** authentication
  - Fails with 401 if token is invalid or can't be verified

## Diagnostic Steps

### Step 1: Check Backend Configuration

Call the authentication diagnostic endpoint:

```bash
curl https://api.hypepaper.app/api/v1/health/auth-config
```

Expected output:
```json
{
  "timestamp": "2025-10-28T12:00:00",
  "supabase_configured": true,
  "supabase_url": "https://xxxxx.supabase.co",
  "supabase_anon_key_set": true,
  "supabase_service_key_set": true,
  "supabase_anon_key_prefix": "eyJhbGciOiJIUzI1NiIs...",
  "status": "configured",
  "message": "Supabase authentication is properly configured"
}
```

### Step 2: Check Frontend Configuration

1. Open browser console on https://hypepaper.app
2. Run:
```javascript
console.log('Frontend Supabase URL:', import.meta.env.VITE_SUPABASE_URL);
```

3. Compare with backend `supabase_url` from Step 1

### Step 3: Check Token Details

The backend logs will show detailed token information when POST fails:

```
[AUTH DEBUG] Token received: eyJhbGciOiJIUzI1NiIs...
[AUTH DEBUG] Backend Supabase URL: https://backend-project.supabase.co
[AUTH DEBUG] Backend Anon Key (prefix): eyJhbGciOiJIUzI1NiIs...
[AUTH DEBUG] Token issuer (iss): https://frontend-project.supabase.co/auth/v1
[AUTH DEBUG] Token audience (aud): authenticated
[AUTH ERROR] Token issuer mismatch! Token from https://frontend-project.supabase.co/auth/v1 but backend expects https://backend-project.supabase.co
[AUTH ERROR] Frontend and backend are using DIFFERENT Supabase projects!
```

## Solution

### Option 1: Update Backend Credentials (Recommended)

Set backend environment variables to match frontend's Supabase project:

```bash
# On production server or deployment platform
export SUPABASE_URL="https://xxxxx.supabase.co"  # Same as frontend's VITE_SUPABASE_URL
export SUPABASE_ANON_KEY="eyJ..."                 # Same as frontend's VITE_SUPABASE_ANON_KEY
export SUPABASE_SERVICE_KEY="eyJ..."              # Service key from same project

# Restart backend service
```

### Option 2: Update Frontend Credentials

If backend is already using the correct project, update frontend:

```bash
# In frontend/.env or deployment config
VITE_SUPABASE_URL="https://xxxxx.supabase.co"  # Same as backend's SUPABASE_URL
VITE_SUPABASE_ANON_KEY="eyJ..."                # Same as backend's SUPABASE_ANON_KEY

# Rebuild and redeploy frontend
npm run build
```

### Finding Supabase Credentials

1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Settings → API
4. Copy:
   - **Project URL** → Use for `SUPABASE_URL` / `VITE_SUPABASE_URL`
   - **anon public** key → Use for `SUPABASE_ANON_KEY` / `VITE_SUPABASE_ANON_KEY`
   - **service_role** key → Use for `SUPABASE_SERVICE_KEY` (backend only)

## Verification

After updating credentials:

1. Restart backend service
2. Clear frontend cache and reload
3. Call diagnostic endpoint:
```bash
curl https://api.hypepaper.app/api/v1/health/auth-config
```

4. Try creating a topic in the UI
5. Check that POST request succeeds (200/201 status)

## Deployment Configuration

### Railway

```bash
railway variables set SUPABASE_URL="https://xxxxx.supabase.co"
railway variables set SUPABASE_ANON_KEY="eyJ..."
railway variables set SUPABASE_SERVICE_KEY="eyJ..."
```

### Cloudflare Workers (Frontend)

Update `wrangler.toml`:
```toml
[env.production.vars]
VITE_SUPABASE_URL = "https://xxxxx.supabase.co"
VITE_SUPABASE_ANON_KEY = "eyJ..."
```

### Docker

Update `docker-compose.yml`:
```yaml
environment:
  - SUPABASE_URL=https://xxxxx.supabase.co
  - SUPABASE_ANON_KEY=eyJ...
  - SUPABASE_SERVICE_KEY=eyJ...
```

## Enhanced Debugging

The backend now includes comprehensive logging that shows:

1. **Token Receipt**: Confirms token is received from frontend
2. **Backend Config**: Shows what Supabase project backend is using
3. **Token Inspection**: Decodes token to show issuer, audience, expiry
4. **Mismatch Detection**: Highlights if frontend/backend use different projects
5. **Validation Result**: Shows whether Supabase accepted the token

These logs appear in your backend service logs and help diagnose the exact failure point.

## Prevention

To prevent this issue in the future:

1. **Use single source of truth**: Store Supabase credentials in one place (e.g., secret manager)
2. **Document credentials**: Keep a record of which Supabase project is used
3. **Monitor health endpoint**: Set up monitoring on `/api/v1/health/auth-config`
4. **Test after deployment**: Always test authentication after deploying either frontend or backend

## Related Files

- Backend authentication: `backend/src/api/dependencies.py`
- Backend config: `backend/src/config.py`
- Backend health checks: `backend/src/api/v1/health.py`
- Frontend API client: `frontend/src/services/api.ts`
- Frontend Supabase client: `frontend/src/lib/supabase.ts`
