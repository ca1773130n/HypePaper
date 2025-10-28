# Authentication Troubleshooting Guide

## Common Authentication Issues

### 1. "Invalid or expired token" Error

**Symptoms:**
- Authentication fails with "Invalid or expired token"
- Error message mentions "frontend and backend are using the same Supabase project"
- 401 Unauthorized responses from `/api/v1/auth/me`

**Root Cause:**
Frontend and backend are using **different Supabase instances**, causing JWT token validation to fail.

**Solution:**
Ensure both frontend and backend use the **same Supabase project credentials**.

#### Check Current Configuration

**Backend (check environment variables):**
```bash
cd backend
env | grep SUPABASE
```

**Frontend (check environment variables):**
```bash
cd frontend
env | grep VITE_SUPABASE
```

**Both should have:**
- Same `SUPABASE_URL` / `VITE_SUPABASE_URL`
- Same `SUPABASE_ANON_KEY` / `VITE_SUPABASE_ANON_KEY`

#### Fix Configuration

**1. Get Supabase Credentials:**
Visit your Supabase project dashboard:
- URL: `https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api`
- Copy:
  - Project URL (e.g., `https://abc123.supabase.co`)
  - Anon/Public key
  - Service Role key (for backend only)

**2. Set Backend Environment Variables:**
```bash
export SUPABASE_URL=https://your-project-ref.supabase.co
export SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
export SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Or create `backend/.env`:
```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

**3. Set Frontend Environment Variables:**
```bash
export VITE_SUPABASE_URL=https://your-project-ref.supabase.co
export VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Or create `frontend/.env`:
```bash
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

**4. Rebuild Frontend:**
```bash
cd frontend
npm run build  # or npm run dev for development
```

**5. Restart Backend:**
```bash
cd backend
uvicorn src.main:app --reload
```

### 2. Environment Variables Not Loading

**Symptoms:**
- Frontend shows "Supabase configuration missing!" error
- Console shows environment variables are "(not set)"

**Root Cause:**
- Environment variables not set in shell
- Frontend not rebuilt after changing `.env`
- Vite not picking up environment variables

**Solution:**

**For Development:**
```bash
cd frontend
# Create .env file
cat > .env << EOF
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000
EOF

# Restart dev server
npm run dev
```

**For Production Build:**
```bash
cd frontend
# Export variables before build
export VITE_SUPABASE_URL=https://your-project-ref.supabase.co
export VITE_SUPABASE_ANON_KEY=your-anon-key

# Build with variables
npm run build

# Serve build
npm run preview
```

### 3. Token Issuer Mismatch

**Symptoms:**
- Backend logs show: "Token issuer mismatch! Token from X but backend expects Y"
- Authentication fails even with correct credentials

**Root Cause:**
JWT token was issued by a different Supabase project than the backend is configured to validate.

**Solution:**
1. Clear frontend localStorage (delete old tokens):
```javascript
// In browser console:
localStorage.clear()
```

2. Sign out and sign in again to get new token from correct Supabase instance

3. Verify token issuer matches backend:
```bash
# Decode token (don't include signature validation)
cd backend
python3 << EOF
import base64
import json

token = "YOUR_TOKEN_HERE"
payload = token.split('.')[1]
payload += '=' * (4 - len(payload) % 4)
decoded = json.loads(base64.urlsafe_b64decode(payload))
print(f"Token issuer: {decoded.get('iss')}")
print(f"Token audience: {decoded.get('aud')}")
EOF
```

### 4. Backend Can't Validate Tokens

**Symptoms:**
- Backend logs show authentication exceptions
- `get_anon_client()` fails

**Root Cause:**
Backend Supabase credentials not configured or incorrect.

**Solution:**
```bash
cd backend
# Test Supabase connection
python3 << EOF
from src.config import get_settings
settings = get_settings()
print(f"SUPABASE_URL: {settings.supabase_url}")
print(f"SUPABASE_ANON_KEY set: {bool(settings.supabase_anon_key)}")
print(f"SUPABASE_SERVICE_KEY set: {bool(settings.supabase_service_key)}")
EOF
```

If any values are missing, set environment variables and restart backend.

## Debugging Authentication Flow

### Enable Debug Logging

**Backend:**
Already has comprehensive debug logging in `backend/src/api/dependencies.py`.

View logs:
```bash
cd backend
uvicorn src.main:app --log-level debug
```

Look for lines with `[AUTH DEBUG]` or `[AUTH ERROR]`.

**Frontend:**
Open browser console and check for:
- Supabase client initialization messages
- Authentication state changes
- Network requests to `/api/v1/auth/me`

### Test Authentication Manually

**1. Get Access Token:**
```javascript
// In browser console after signing in:
const { data } = await supabase.auth.getSession()
console.log('Access Token:', data.session?.access_token)
```

**2. Test Token with Backend:**
```bash
# Copy token from above
TOKEN="your-access-token-here"

# Test /me endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/auth/me | python3 -m json.tool
```

**Expected Response (Success):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "user_metadata": {}
}
```

**Expected Response (Failure):**
```json
{
  "detail": "Authentication failed: Invalid or expired token..."
}
```

### Verify Supabase Project Configuration

**1. Check Google OAuth is enabled:**
- Visit: `https://supabase.com/dashboard/project/YOUR_PROJECT/auth/providers`
- Ensure Google provider is enabled
- Verify redirect URLs include your frontend URL

**2. Check Site URL:**
- Visit: `https://supabase.com/dashboard/project/YOUR_PROJECT/auth/url-configuration`
- Site URL should match your frontend URL
- Redirect URLs should include `/auth/callback` path

**3. Check JWT Settings:**
- Visit: `https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api`
- JWT expiry should be reasonable (default: 3600 seconds)

## Quick Fixes Checklist

- [ ] Frontend and backend use same `SUPABASE_URL`
- [ ] Frontend and backend use same `SUPABASE_ANON_KEY`
- [ ] Environment variables are set before building/running
- [ ] Frontend was rebuilt after changing environment variables
- [ ] Backend was restarted after changing environment variables
- [ ] Old tokens cleared from localStorage
- [ ] Google OAuth enabled in Supabase
- [ ] Correct redirect URLs configured in Supabase

## Still Having Issues?

1. **Check server logs:** Backend logs in `[AUTH DEBUG]` contain detailed token validation info
2. **Verify token:** Decode JWT to check issuer matches backend Supabase URL
3. **Test with curl:** Manually test authentication with curl commands above
4. **Create new Supabase project:** If nothing works, create fresh project and migrate

## References

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [FastAPI Authentication](https://fastapi.tiangolo.com/tutorial/security/)
