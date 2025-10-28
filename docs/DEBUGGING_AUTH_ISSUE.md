# Debugging Authentication Issue

## Current Status

You're experiencing "Authentication required" errors when trying to add custom topics on the profile page, even after implementing the authentication fixes.

## What We've Done So Far

1. ✅ Added axios request interceptor to inject Supabase token
2. ✅ Updated ProfilePage to use authenticated api instance
3. ✅ Added detailed logging to backend authentication flow

## Next Steps to Debug

### 1. Check Backend Logs

After deploying the latest code, try to add a topic and check the Railway backend logs for output like:

```
[AUTH DEBUG] No credentials provided
# OR
[AUTH DEBUG] Token received: eyJhbGciOiJIUzI1NiIs...
[AUTH DEBUG] Anon client created
[AUTH DEBUG] User response: <response>
[AUTH DEBUG] User authenticated: <user_id>
# OR
[AUTH DEBUG] Exception during authentication: <error>
```

This will tell us:
- Is the token being sent from frontend?
- Is the token format correct?
- Is Supabase token validation failing?
- What error is occurring?

### 2. Check Frontend Browser Console

Open browser DevTools (F12) → Network tab, then try to add a topic:

1. Look for the POST request to `/api/v1/topics`
2. Check the "Request Headers" section
3. Verify you see: `Authorization: Bearer <long-token>`

If there's NO Authorization header, the problem is in the frontend.
If there IS an Authorization header, the problem is in the backend token validation.

### 3. Check Environment Variables

Verify these are set correctly:

**Frontend** (check browser console or .env):
```javascript
console.log('API URL:', import.meta.env.VITE_API_URL)
console.log('Supabase URL:', import.meta.env.VITE_SUPABASE_URL)
console.log('Supabase Key:', import.meta.env.VITE_SUPABASE_ANON_KEY ? 'SET' : 'NOT SET')
```

**Backend** (Railway environment variables):
- `SUPABASE_URL` - Should match frontend VITE_SUPABASE_URL
- `SUPABASE_ANON_KEY` - Should match frontend VITE_SUPABASE_ANON_KEY
- `SUPABASE_SERVICE_KEY` - Admin key (different from anon key)

### 4. Test with curl

Get your token from browser:
```javascript
// In browser console on profile page:
const { data: { session } } = await supabase.auth.getSession()
console.log('Token:', session.access_token)
```

Then test the API directly:
```bash
TOKEN="<your-token>"

# Test topic creation
curl -X POST http://your-backend-url/api/v1/topics \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-topic",
    "description": "Test description",
    "keywords": ["test", "debug"]
  }'
```

Expected responses:
- **Success**: 201 with topic data
- **Auth error**: 401 with "Authentication required"
- **Other error**: Check the response message

### 5. Common Issues

#### Issue: No Authorization Header in Requests
**Cause**: Frontend not sending token
**Fix**:
- Verify user is logged in: `console.log(authStore.isAuthenticated)`
- Check session exists: `supabase.auth.getSession()`
- Ensure api interceptor is loaded before ProfilePage

#### Issue: Backend Logs Show "No credentials provided"
**Cause**: Authorization header not reaching backend
**Fix**:
- Check CORS settings
- Verify API_URL matches backend URL
- Check if proxy/CDN is stripping headers

#### Issue: Backend Logs Show Exception
**Cause**: Token validation failing
**Fix**:
- Verify SUPABASE_URL matches between frontend/backend
- Verify SUPABASE_ANON_KEY matches between frontend/backend
- Check if token is expired (tokens expire after 1 hour)
- Try logging out and logging back in to get fresh token

#### Issue: Token Format Wrong
**Cause**: Environment variable mismatch
**Fix**:
- Redeploy frontend with correct VITE_SUPABASE_URL
- Redeploy backend with correct SUPABASE_URL and SUPABASE_ANON_KEY
- Ensure all three match your Supabase project settings

### 6. Quick Test Script

Add this to ProfilePage.vue for debugging:

```vue
<script setup lang="ts">
// ... existing code ...

// Add debugging function
async function debugAuth() {
  console.log('=== AUTH DEBUG ===')

  // Check session
  const { data: { session } } = await supabase.auth.getSession()
  console.log('Session exists:', !!session)
  console.log('Token:', session?.access_token?.substring(0, 20) + '...')
  console.log('User ID:', session?.user?.id)

  // Check API base URL
  console.log('API Base URL:', import.meta.env.VITE_API_URL)

  // Test authenticated request
  try {
    const response = await api.get('/api/v1/topics')
    console.log('Topics request succeeded:', response.status)
  } catch (error) {
    console.error('Topics request failed:', error.response?.status, error.response?.data)
  }
}

// Call on mount for debugging
onMounted(() => {
  loadTopics()
  debugAuth()  // ADD THIS LINE
})
</script>
```

Then check browser console for the debug output.

## Need More Help?

Share the following information:
1. Backend logs output (the [AUTH DEBUG] lines)
2. Browser Network tab screenshot showing the request headers
3. Any error messages from browser console
4. Environment variable configuration (VITE_API_URL, SUPABASE_URL)

This will help identify exactly where the authentication is failing.
