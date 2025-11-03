# 🚀 Railway Preview Deployments with Google OAuth

This guide explains how to configure Google OAuth to work with Railway's dynamic preview deployment URLs.

## The Problem

Railway creates preview deployments for every pull request, each with a unique URL like:
```
https://hypepaper-backend-pr-123-abc123.up.railway.app
```

These URLs change for every PR, but Google OAuth requires pre-configured redirect URIs. This means preview deployments can't authenticate users unless we configure OAuth correctly.

## Solutions

### Solution 1: Configure Multiple Redirect URIs (Recommended)

Google OAuth allows up to 500 redirect URIs per OAuth client. While we can't use wildcards, we can add Railway's common patterns.

#### Step 1: Get Your Railway Project Domain Pattern

Railway preview deployments follow this pattern:
```
https://<service-name>-pr-<pr-number>-<hash>.up.railway.app
```

For example:
```
https://hypepaper-backend-pr-15-a1b2c3.up.railway.app
```

#### Step 2: Add Redirect URIs to Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** → **Credentials**
4. Click on your OAuth 2.0 Client ID
5. Under **Authorized redirect URIs**, add:

```
# Production
https://api.hypepaper.app/auth/callback
https://zvesxmkgkldorxlbyhce.supabase.co/auth/v1/callback

# Railway Production
https://hypepaper-backend.up.railway.app/auth/callback
https://hypepaper-backend-production.up.railway.app/auth/callback

# Preview Deployments (add as needed when creating PRs)
https://hypepaper-backend-pr-1-*.up.railway.app/auth/callback
https://hypepaper-backend-pr-2-*.up.railway.app/auth/callback
# Note: You need to add specific URLs - wildcards don't work in Google OAuth
```

**Important**: Every time you create a new PR that needs OAuth testing, add its specific redirect URI to Google OAuth.

#### Step 3: Update Supabase Redirect URLs

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Authentication** → **URL Configuration**
4. Under **Redirect URLs**, add:

```
# Production
https://hypepaper.pages.dev/auth/callback
https://www.hypepaper.app/auth/callback

# Local Development
http://localhost:5173/auth/callback

# Railway Preview Deployments
https://*.up.railway.app/auth/callback

# You can use wildcards in Supabase!
```

### Solution 2: Use a Stable Redirect Proxy

Instead of adding every preview URL, use a stable proxy endpoint that redirects to the correct preview URL.

#### Create Redirect Proxy Endpoint

Add this to `backend/src/main.py`:

```python
@app.get("/oauth/callback-proxy")
async def oauth_callback_proxy(
    access_token: str = None,
    refresh_token: str = None,
    error: str = None,
    error_description: str = None,
    state: str = None,
):
    """
    OAuth callback proxy that redirects to the correct environment.

    This allows preview deployments to work with a single Google OAuth redirect URI.
    """
    import os
    import urllib.parse

    # Determine target URL based on environment
    railway_env = os.getenv("RAILWAY_ENVIRONMENT_NAME", "production")
    railway_url = os.getenv("RAILWAY_STATIC_URL", "")

    # Build frontend URL
    if railway_env == "production":
        frontend_url = "https://hypepaper.pages.dev"
    elif railway_url:
        # Preview deployment
        frontend_url = f"https://{railway_url}"
    else:
        # Fallback
        frontend_url = "http://localhost:5173"

    # Build callback URL with OAuth parameters
    callback_url = f"{frontend_url}/auth/callback"

    # Forward OAuth parameters
    params = []
    if access_token:
        params.append(f"access_token={urllib.parse.quote(access_token)}")
    if refresh_token:
        params.append(f"refresh_token={urllib.parse.quote(refresh_token)}")
    if error:
        params.append(f"error={urllib.parse.quote(error)}")
    if error_description:
        params.append(f"error_description={urllib.parse.quote(error_description)}")
    if state:
        params.append(f"state={urllib.parse.quote(state)}")

    if params:
        callback_url += "#" + "&".join(params)

    return RedirectResponse(url=callback_url)
```

#### Update Auth Store to Use Proxy

In `frontend/src/stores/auth.ts`, update the `signInWithGoogle` function:

```typescript
async function signInWithGoogle() {
  loading.value = true
  try {
    // Use stable proxy endpoint instead of dynamic preview URL
    const apiUrl = import.meta.env.VITE_API_URL || window.location.origin
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${apiUrl}/oauth/callback-proxy`
      }
    })
    if (error) throw error
    return data
  } finally {
    loading.value = false
  }
}
```

#### Add Single Redirect URI to Google OAuth

Now you only need ONE redirect URI in Google OAuth:
```
https://api.hypepaper.app/oauth/callback-proxy
```

This works for all environments because the proxy redirects to the correct frontend URL.

### Solution 3: Environment-Specific Supabase Configuration

Configure Supabase to use different redirect URLs based on the environment.

#### Update Frontend Supabase Client

In `frontend/src/lib/supabase.ts`:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// Detect environment
const isProduction = import.meta.env.PROD && window.location.hostname !== 'localhost'
const isRailwayPreview = window.location.hostname.includes('railway.app')

// Configure redirect URLs
let redirectTo = `${window.location.origin}/auth/callback`

if (isRailwayPreview) {
  console.log('🔧 Railway preview deployment detected')
  console.log('📍 Redirect URL:', redirectTo)
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    storageKey: 'hypepaper-auth',
    redirectTo: redirectTo, // Use dynamic redirect URL
  },
})
```

## Testing Preview Deployments

### Step 1: Create a Test PR

```bash
git checkout -b test/oauth-preview
echo "# OAuth Preview Test" >> README.md
git add README.md
git commit -m "test: verify OAuth with preview deployment"
git push origin test/oauth-preview
```

### Step 2: Get Preview Deployment URL

1. Go to Railway dashboard
2. Find your PR deployment
3. Copy the deployment URL (e.g., `https://hypepaper-backend-pr-15-abc123.up.railway.app`)

### Step 3: Add to Google OAuth

1. Go to Google Cloud Console → Credentials
2. Edit OAuth 2.0 Client ID
3. Add the preview URL as redirect URI:
   ```
   https://hypepaper-backend-pr-15-abc123.up.railway.app/auth/callback
   ```

### Step 4: Test Authentication

1. Visit your preview deployment frontend URL
2. Click "Sign In"
3. Select Google account
4. Should redirect back to preview deployment (not production!)

## Railway Environment Variables

Railway provides these environment variables for preview deployments:

- `RAILWAY_ENVIRONMENT_NAME`: `pr-xxx` for previews, `production` for production
- `RAILWAY_STATIC_URL`: The static URL for the deployment
- `RAILWAY_PUBLIC_DOMAIN`: Public domain if configured
- `RAILWAY_GIT_BRANCH`: Git branch name
- `RAILWAY_GIT_COMMIT_SHA`: Commit SHA

Use these in your backend to detect preview deployments:

```python
import os

def is_preview_deployment():
    return os.getenv("RAILWAY_ENVIRONMENT_NAME", "").startswith("pr-")

def get_frontend_url():
    if is_preview_deployment():
        # For preview, use Railway's static URL
        railway_url = os.getenv("RAILWAY_STATIC_URL", "")
        return f"https://{railway_url}" if railway_url else "http://localhost:5173"
    else:
        # Production
        return "https://hypepaper.pages.dev"
```

## Troubleshooting

### Error: "redirect_uri_mismatch"

**Cause**: The redirect URI in your OAuth request doesn't match any configured in Google OAuth.

**Solution**:
1. Check the exact URL in the error message
2. Add it to Google OAuth redirect URIs
3. Wait a few minutes for changes to propagate

### Error: "Access blocked: This app's request is invalid"

**Cause**: OAuth consent screen not configured or app in testing mode without test users.

**Solution**:
1. Configure OAuth consent screen in Google Cloud Console
2. Add your email as a test user
3. Or publish the app (removes testing restrictions)

### Preview Deployment Redirects to Production

**Cause**: Frontend is using hardcoded production URL for redirect.

**Solution**: Use `window.location.origin` for dynamic redirect URLs (already implemented in the codebase).

### Session Not Persisting After OAuth

**Cause**: Supabase redirect URL configuration doesn't include preview URL.

**Solution**:
1. Add preview URL pattern to Supabase → Authentication → URL Configuration
2. Use wildcard: `https://*.up.railway.app/auth/callback`

## Recommended Setup

For the best developer experience:

1. **Use Solution 2 (Redirect Proxy)** - Only requires ONE Google OAuth redirect URI
2. **Configure Supabase wildcards** - Supports all preview deployments automatically
3. **Document the proxy endpoint** - Make it clear in team docs
4. **Add CI/CD checks** - Verify OAuth config before merging PRs

## Example Railway Configuration

Add to `railway.toml`:

```toml
[deploy]
startCommand = "uvicorn src.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[environments.production]
variables = { ENVIRONMENT = "production", FRONTEND_URL = "https://hypepaper.pages.dev" }

[environments.preview]
# Preview environment inherits these variables
variables = { ENVIRONMENT = "preview" }
```

Railway automatically sets `RAILWAY_STATIC_URL` for preview deployments, which you can use to build the frontend URL dynamically.

## Summary

✅ **Easiest**: Use redirect proxy (Solution 2) - one redirect URI in Google OAuth
✅ **Most Flexible**: Add wildcard in Supabase, specific URLs in Google OAuth (Solution 1)
✅ **Best Practice**: Combine both solutions for maximum compatibility

With these configurations, your preview deployments will work seamlessly with Google OAuth! 🎉
