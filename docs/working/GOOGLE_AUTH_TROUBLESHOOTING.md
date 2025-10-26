# Google OAuth Login Troubleshooting

## 🚨 Issue: Can't Login with Google Account

### Symptoms
- Click "Sign in with Google" button
- Redirected to Google login
- After authorizing, redirect back fails or shows error
- Not signed in to the app

## ✅ Solutions Implemented

### 1. Fixed AuthCallbackPage.vue

**Problem**: Original callback page was too simple:
- Only waited 1 second
- Didn't check for OAuth errors
- Didn't properly wait for session exchange
- No error handling or debugging

**Solution**: Rewrote callback page with:
- ✅ OAuth error detection from URL params
- ✅ Exponential backoff for session checking (up to 10 attempts)
- ✅ Proper error messages to user
- ✅ Console logging for debugging
- ✅ Better UX with loading/error states

### 2. Supabase Client Configuration

The Supabase client in `frontend/src/lib/supabase.ts` is correctly configured:
```typescript
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,  // ← Handles OAuth callback automatically
    storageKey: 'hypepaper-auth',
  },
})
```

## 🔧 Required Supabase Dashboard Configuration

### Step 1: Enable Google OAuth Provider

1. Go to **Supabase Dashboard** → Your Project
2. Click **Authentication** (left sidebar)
3. Click **Providers** tab
4. Find **Google** in the list
5. Toggle it to **Enabled**

### Step 2: Configure Google OAuth Credentials

You need to create OAuth credentials in Google Cloud Console:

#### A. Create Google Cloud Project
1. Go to https://console.cloud.google.com
2. Create a new project or select existing one
3. Enable **Google+ API** (required for OAuth)

#### B. Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `HypePaper` (or anything)
5. **Authorized JavaScript origins**:
   ```
   https://hypepaper.app
   https://www.hypepaper.app
   http://localhost:5173
   ```

6. **Authorized redirect URIs**:
   ```
   https://zvesxmkgkldorxlbyhce.supabase.co/auth/v1/callback
   http://localhost:54321/auth/v1/callback
   ```

   **Important**: Use YOUR Supabase project URL! Format:
   ```
   https://[YOUR-PROJECT-REF].supabase.co/auth/v1/callback
   ```

7. Click **CREATE**
8. Copy the **Client ID** and **Client secret**

#### C. Add Credentials to Supabase
1. Back in Supabase Dashboard → Authentication → Providers → Google
2. Paste **Client ID** (from Google Console)
3. Paste **Client Secret** (from Google Console)
4. Click **Save**

### Step 3: Configure Site URL and Redirect URLs

In Supabase Dashboard → Authentication → **URL Configuration**:

1. **Site URL**:
   ```
   https://hypepaper.app
   ```

2. **Redirect URLs** (add all of these):
   ```
   https://hypepaper.app/auth/callback
   https://www.hypepaper.app/auth/callback
   http://localhost:5173/auth/callback
   ```

3. Click **Save**

## 🧪 Testing Google Login

### Local Testing
```bash
# Start frontend
cd frontend
npm run dev

# Visit http://localhost:5173
# Click "Sign in with Google"
# Should redirect to Google, authorize, then back to /auth/callback
# Should see "Completing sign in..." then redirect to home
```

### Production Testing
```
1. Visit https://hypepaper.app
2. Click "Sign in with Google"
3. Authorize with Google account
4. Should redirect back and sign in successfully
```

### Check Browser Console
Open browser developer tools (F12) and check Console tab:
```
✅ Good messages:
"Waiting for OAuth session exchange..."
"Session established: user@gmail.com"
"Redirecting to home..."

❌ Bad messages:
"OAuth error: ..."
"Session error: ..."
"No session established after 10 attempts"
```

## 🔍 Common Issues

### Issue 1: "Redirect URI mismatch"

**Error**: Google shows "Error 400: redirect_uri_mismatch"

**Cause**: Redirect URI in Google Console doesn't match Supabase callback URL

**Solution**:
1. Check your Supabase URL: `https://zvesxmkgkldorxlbyhce.supabase.co`
2. Add this exact redirect URI to Google Console:
   ```
   https://zvesxmkgkldorxlbyhce.supabase.co/auth/v1/callback
   ```
3. Must match exactly (no trailing slash, correct project ref)

### Issue 2: "Access blocked: This app's request is invalid"

**Error**: Google shows "Access blocked" error

**Cause**: OAuth consent screen not configured or app not published

**Solution**:
1. Google Cloud Console → **OAuth consent screen**
2. Fill in required fields (app name, support email)
3. Add test users OR publish the app
4. Save

### Issue 3: Session not established

**Symptoms**:
- Redirects back to app
- Shows "Completing sign in..." forever
- Console shows "No session established after 10 attempts"

**Possible Causes**:
1. **Wrong Site URL** in Supabase
   - Check: Supabase → Auth → URL Configuration → Site URL
   - Should be: `https://hypepaper.app` (NOT localhost in production)

2. **Wrong Redirect URLs** in Supabase
   - Check: Supabase → Auth → URL Configuration → Redirect URLs
   - Must include: `https://hypepaper.app/auth/callback`

3. **CORS issues**
   - Check browser console for CORS errors
   - Supabase should allow requests from hypepaper.app

4. **Environment variables not set**
   - Check Cloudflare Pages env vars:
   ```
   VITE_SUPABASE_URL=https://zvesxmkgkldorxlbyhce.supabase.co
   VITE_SUPABASE_ANON_KEY=eyJhbGci...
   ```

### Issue 4: Works locally but not in production

**Cause**: Environment variables or redirect URLs misconfigured

**Check**:
1. Cloudflare Pages environment variables are set correctly
2. Google Console has production redirect URIs
3. Supabase has production Site URL and Redirect URLs
4. Frontend is rebuilt after env var changes

## 📋 Complete Checklist

### Supabase Configuration
- [ ] Google provider enabled in Authentication → Providers
- [ ] Google Client ID added
- [ ] Google Client Secret added
- [ ] Site URL set to `https://hypepaper.app`
- [ ] Redirect URL `https://hypepaper.app/auth/callback` added
- [ ] Redirect URL `https://www.hypepaper.app/auth/callback` added

### Google Cloud Console
- [ ] OAuth consent screen configured
- [ ] OAuth Client ID created (Web application)
- [ ] Authorized JavaScript origins include `https://hypepaper.app`
- [ ] Authorized redirect URI: `https://[your-project].supabase.co/auth/v1/callback`
- [ ] Test users added OR app published

### Cloudflare Pages
- [ ] `VITE_SUPABASE_URL` environment variable set
- [ ] `VITE_SUPABASE_ANON_KEY` environment variable set
- [ ] Environment variables set in Production environment
- [ ] Frontend rebuilt after env var changes

### Code
- [x] AuthCallbackPage.vue updated with better error handling
- [x] Supabase client configured with `detectSessionInUrl: true`
- [x] Auth store properly set up

## 🔐 Security Notes

1. **Never commit secrets**:
   - Don't commit `.env` files with Supabase keys
   - Use Cloudflare Pages environment variables

2. **Anon key is safe to expose**:
   - The `VITE_SUPABASE_ANON_KEY` is public (used in frontend)
   - Row Level Security (RLS) in Supabase protects your data
   - Service role key should NEVER be in frontend

3. **HTTPS required**:
   - OAuth only works over HTTPS in production
   - Google rejects non-HTTPS redirect URIs
   - Local development can use HTTP

## 🆘 Still Not Working?

1. **Check Supabase logs**:
   - Supabase Dashboard → Logs → Auth logs
   - Look for OAuth-related errors

2. **Check browser console**:
   - Look for JavaScript errors
   - Check Network tab for failed requests

3. **Verify Supabase project URL**:
   ```bash
   # In frontend directory
   cat .env
   # Should show: VITE_SUPABASE_URL=https://zvesxmkgkldorxlbyhce.supabase.co
   ```

4. **Test with a different browser**:
   - Clear cache and cookies
   - Try incognito mode
   - Try different browser

5. **Check Google OAuth quotas**:
   - Google Cloud Console → APIs & Services → Dashboard
   - Verify Google+ API is enabled
   - Check for quota limits or API restrictions

## 📞 Next Steps

After fixing AuthCallbackPage.vue:
1. Commit and push changes
2. Wait for Cloudflare Pages to rebuild
3. Test Google login on production site
4. If still failing, check Supabase Dashboard configuration

The most common issue is **redirect URI mismatch** - make sure URLs match exactly in both Google Console and Supabase Dashboard!
