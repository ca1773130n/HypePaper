# ⚡ Quick Setup - OAuth Redirect Proxy for Preview Deployments

## What We Fixed

OAuth now works with Railway preview deployments! Instead of redirecting to production, users will be redirected to the correct preview URL.

## How It Works

1. **Backend Proxy**: We added `/oauth/redirect-proxy` endpoint that:
   - Returns an HTML page with JavaScript
   - Detects the correct frontend URL (production/preview/dev)
   - Redirects to the correct frontend while preserving OAuth tokens

2. **Frontend Update**: Changed OAuth to use the proxy:
   ```typescript
   // Before: redirectTo: window.location.origin/auth/callback
   // After: redirectTo: backendProxy/oauth/redirect-proxy
   ```

3. **Token Preservation**: Since OAuth tokens are in the URL hash (`#access_token=...`), we use JavaScript to preserve them during redirect.

## Setup Steps (One-Time Configuration)

### Step 1: Configure Supabase Redirect URLs

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Authentication** → **URL Configuration**
4. Under **Redirect URLs**, add:

```
# Production Backend
https://api.hypepaper.app/oauth/redirect-proxy

# Railway Backend (if different)
https://your-railway-backend.up.railway.app/oauth/redirect-proxy

# Wildcard for all Railway preview deployments (if Supabase supports it)
https://*.up.railway.app/oauth/redirect-proxy

# Local development
http://localhost:8000/oauth/redirect-proxy
```

5. Click **Save**

### Step 2: Test on Preview Deployment

1. **Create a PR** and wait for Railway to deploy
2. **Visit preview URL** (e.g., `https://frontend-pr-15-abc123.railway.app`)
3. **Click "Sign In"**
4. **Authenticate with Google**
5. **You'll see**: "Completing sign in..." page (the proxy)
6. **Then redirected to**: Your preview URL (NOT production!) ✅

## What Changed

### Backend (`backend/src/main.py`)
```python
@app.get("/oauth/redirect-proxy")
async def oauth_redirect_proxy(request: Request, frontend_callback: str = None):
    # Returns HTML page with JavaScript that:
    # 1. Detects correct frontend URL (preview/production/dev)
    # 2. Preserves OAuth tokens from URL hash
    # 3. Redirects to frontend /auth/callback
```

### Frontend (`frontend/src/stores/auth.ts`)
```typescript
async function signInWithGoogle() {
  const apiUrl = import.meta.env.VITE_API_URL
  const backendRedirectProxy = `${apiUrl}/oauth/redirect-proxy`
  const frontendCallback = `${window.location.origin}/auth/callback`

  await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${backendRedirectProxy}?frontend_callback=${frontendCallback}`
    }
  })
}
```

## How Railway Detection Works

The proxy automatically detects the environment:

```python
# Check Railway environment variable
railway_env = os.getenv("RAILWAY_ENVIRONMENT_NAME", "")

if railway_env.startswith("pr-"):
    # This is a preview deployment
    # Use RAILWAY_STATIC_URL to build frontend URL
    frontend_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}"
elif os.getenv("ENVIRONMENT") == "production":
    # Production
    frontend_url = "https://hypepaper.pages.dev"
else:
    # Development
    frontend_url = "http://localhost:5173"
```

Railway automatically provides:
- `RAILWAY_ENVIRONMENT_NAME=pr-123` for preview deployments
- `RAILWAY_STATIC_URL=frontend-pr-123-abc.railway.app` for the frontend URL

## Troubleshooting

### Still Redirecting to Production?

**Check 1**: Verify Supabase redirect URLs include the proxy endpoint
```bash
# Should include:
https://api.hypepaper.app/oauth/redirect-proxy
```

**Check 2**: Check Railway environment variables
```bash
# In Railway dashboard, verify:
ENVIRONMENT=production  # For production
FRONTEND_URL=https://hypepaper.pages.dev  # For production

# Railway auto-sets for previews:
RAILWAY_ENVIRONMENT_NAME=pr-123
RAILWAY_STATIC_URL=frontend-pr-123-abc.railway.app
```

**Check 3**: Check browser console logs
```javascript
// Should see in console:
"OAuth Redirect Proxy"
"Original URL: https://api.hypepaper.app/oauth/redirect-proxy#access_token=..."
"Callback URL: https://frontend-pr-123-abc.railway.app/auth/callback"
"Final URL: https://frontend-pr-123-abc.railway.app/auth/callback#access_token=..."
```

### OAuth Error: "redirect_uri_mismatch"

**Cause**: Supabase redirect URL list doesn't include the proxy endpoint.

**Solution**: Add the proxy URL to Supabase:
```
https://api.hypepaper.app/oauth/redirect-proxy
```

### Preview Deployment Not Detected

**Cause**: Railway environment variables not set or backend can't determine frontend URL.

**Solution 1**: Pass frontend callback explicitly (already implemented):
```typescript
// Frontend automatically passes its callback URL
redirectTo: `${backendProxy}?frontend_callback=${window.location.origin}/auth/callback`
```

**Solution 2**: Check Railway dashboard for environment variables:
- `RAILWAY_ENVIRONMENT_NAME` should be `pr-{number}` for previews
- `RAILWAY_STATIC_URL` should be set to the preview hostname

### OAuth Tokens Lost During Redirect

**Cause**: Hash fragments were stripped during redirect.

**Solution**: This is why we use JavaScript in the HTML page. The JavaScript runs in the browser and can access `window.location.hash`, then includes it in the redirect.

If tokens are still lost, check:
1. Browser console for JavaScript errors
2. Network tab to see if hash is preserved in final redirect
3. Enable debug output in the proxy HTML (uncomment debug div)

## Testing Checklist

- [ ] Add proxy URL to Supabase redirect URLs
- [ ] Create test PR
- [ ] Visit preview deployment
- [ ] Click "Sign In"
- [ ] See "Completing sign in..." page briefly
- [ ] Redirected to preview URL (check address bar!)
- [ ] Authenticated successfully (see user profile)
- [ ] Check browser console logs for debug info

## Benefits

✅ **One-time setup**: Configure Supabase once, works for all preview deployments
✅ **Automatic detection**: No manual configuration per PR
✅ **Token preservation**: OAuth tokens preserved through redirect
✅ **Works everywhere**: Production, preview, and local development
✅ **Beautiful UX**: Smooth transition with loading animation

## Summary

**Before**: OAuth redirected to production URL for preview deployments
**After**: OAuth automatically redirects to the correct preview URL

**Required Action**: Add `/oauth/redirect-proxy` to Supabase redirect URLs (one-time setup)

Once configured, all preview deployments will work seamlessly with OAuth! 🎉
