# Setting Up Google OAuth in Supabase

To enable user login with Google accounts, follow these steps:

## 1. Configure Google OAuth Provider in Supabase

### Step 1: Go to Supabase Dashboard
1. Open https://supabase.com/dashboard
2. Select your project: `zvesxmkgkldorxlbyhce`
3. Navigate to **Authentication** → **Providers**

### Step 2: Enable Google Provider
1. Find "Google" in the providers list
2. Click to enable it
3. You'll need to create Google OAuth credentials

## 2. Create Google OAuth Credentials

### Step 1: Go to Google Cloud Console
1. Visit https://console.cloud.google.com/
2. Create a new project or select existing one
3. Navigate to **APIs & Services** → **Credentials**

### Step 2: Create OAuth 2.0 Client ID
1. Click **Create Credentials** → **OAuth client ID**
2. Select **Application type**: Web application
3. Name it: `HypePaper`

### Step 3: Configure Authorized Redirect URIs
Add these redirect URIs:

```
https://zvesxmkgkldorxlbyhce.supabase.co/auth/v1/callback
http://localhost:5173/auth/callback
```

**Important**: The first URL is your Supabase callback URL. The format is:
```
https://<your-project-ref>.supabase.co/auth/v1/callback
```

### Step 4: Get Client ID and Secret
After creating, you'll receive:
- **Client ID**: `xxxxx.apps.googleusercontent.com`
- **Client Secret**: `xxxxxxxxxxxxxxxx`

Copy both values.

## 3. Configure Supabase with Google Credentials

### Back in Supabase Dashboard:
1. Go to **Authentication** → **Providers** → **Google**
2. Paste **Client ID** into the field
3. Paste **Client Secret** into the field
4. **Authorized Client IDs**: Leave empty or add your Client ID
5. Click **Save**

## 4. Configure OAuth Consent Screen (if not done)

### In Google Cloud Console:
1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type
3. Fill in required fields:
   - App name: `HypePaper`
   - User support email: Your email
   - Developer contact: Your email
4. Add scopes (minimum required):
   - `userinfo.email`
   - `userinfo.profile`
5. Add test users (your email) if app is in testing mode
6. Click **Save and Continue**

## 5. Test Authentication Flow

### Local Testing:
1. Make sure frontend is running: `cd frontend && npm run dev`
2. Visit http://localhost:5173
3. Click "Sign In" button
4. You should see Google OAuth popup
5. Select your Google account
6. Grant permissions
7. You'll be redirected back to the app with authentication

### What Happens After Login:
1. User is redirected to `/auth/callback`
2. AuthCallbackPage processes the OAuth tokens
3. User session is stored in browser localStorage
4. User is redirected to home page
5. "Sign In" button changes to "Profile" and "Sign Out"
6. User can now access `/profile` to manage custom topics

## 6. Verify User in Supabase

### After first login:
1. Go to Supabase Dashboard → **Authentication** → **Users**
2. You should see your Google account listed
3. Note the user ID - this will be used for `user_id` in topics table

## 7. Testing Custom Topics

Once logged in:
1. Click "Profile" button
2. You'll see the profile page with custom topics management
3. Add a new topic with keywords
4. The topic will be stored with your `user_id`
5. Return to home page - your custom topic should appear in the dropdown

## Troubleshooting

### Error: "redirect_uri_mismatch"
- Make sure the redirect URI in Google Console exactly matches Supabase callback URL
- Format: `https://zvesxmkgkldorxlbyhce.supabase.co/auth/v1/callback`

### Error: "Access blocked: This app's request is invalid"
- Configure OAuth consent screen in Google Cloud Console
- Add test users if app is in testing mode

### Error: "Invalid client"
- Check Client ID and Secret are correctly copied to Supabase
- No extra spaces or line breaks

### Session not persisting
- Check browser localStorage has `hypepaper-auth` key
- Check Supabase URL and Anon Key in frontend/.env
- Clear browser cache and try again

## Current Configuration

**Frontend** (`frontend/.env`):
```bash
VITE_SUPABASE_URL=https://zvesxmkgkldorxlbyhce.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Supabase Project**: `zvesxmkgkldorxlbyhce`
**Region**: Asia Pacific (Northeast 2) - Seoul

## Next Steps After Setup

1. ✅ Enable Google OAuth in Supabase
2. ✅ Test login flow
3. ✅ Create a custom topic via Profile page
4. ✅ Verify topic appears in database
5. ✅ Test topic filtering on home page

## Production Deployment Notes

When deploying to production (Vercel, etc.):

1. **Update Google OAuth Redirect URIs**:
   ```
   https://your-app-domain.com/auth/callback
   https://zvesxmkgkldorxlbyhce.supabase.co/auth/v1/callback
   ```

2. **Update Frontend Environment Variables**:
   - Keep same `VITE_SUPABASE_URL`
   - Keep same `VITE_SUPABASE_ANON_KEY`
   - Update `VITE_API_URL` to your production backend URL

3. **OAuth Consent Screen**:
   - Move from "Testing" to "In Production" mode
   - Remove test user restrictions
   - Complete verification if needed (for public use)

---

**Status**: Waiting for Google OAuth to be configured in Supabase Dashboard
**Last Updated**: 2025-10-09
