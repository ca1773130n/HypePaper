# Railway Environment Variables Fix

## ❌ Problem
Backend returning 401 Unauthorized when creating topics because Railway doesn't have `SUPABASE_ANON_KEY` configured.

## ✅ Solution

### Step 1: Add SUPABASE_ANON_KEY to Railway

1. Go to Railway Dashboard → Your Project → Backend Service
2. Click **Variables** tab
3. Add this variable:

```
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp2ZXN4bWtna2xkb3J4bGJ5aGNlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5ODk3MTksImV4cCI6MjA3NTU2NTcxOX0.3yxpsC3cQIxxrYOdH4s8L8i-v6h3pWw-z2HUsnlkggw
```

4. Click **Add**
5. Railway will automatically redeploy (~2-4 minutes)

### Step 2: Verify Railway Has All Required Env Vars

Make sure Railway has these variables:

```bash
DATABASE_URL=postgresql+asyncpg://postgres.zvesxmkgkldorxlbyhce:dlgPwls181920@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres
SUPABASE_URL=https://zvesxmkgkldorxlbyhce.supabase.co
SUPABASE_ANON_KEY=eyJhbGci... (see above)
SUPABASE_SERVICE_KEY=eyJhbGci... (your service key)
GITHUB_TOKEN=(your GitHub token)
```

### Step 3: Trigger Cloudflare Pages Rebuild

The frontend still has old code logging access tokens. Trigger a rebuild:

#### Option A: Push a dummy commit
```bash
cd /Users/edward.seo/dev/private/research/DeepResearch/HypePaper
git commit --allow-empty -m "chore: trigger rebuild to apply token logging fixes"
git push
```

#### Option B: Manually trigger rebuild in Cloudflare
1. Go to Cloudflare Pages Dashboard
2. Your HypePaper project
3. Click **Deployments**
4. Click **Retry deployment** (on latest deployment)

### Step 4: Wait for Both Deployments

- **Railway**: Wait ~2-4 minutes for backend to redeploy
- **Cloudflare**: Wait ~1-2 minutes for frontend to rebuild

### Step 5: Test Topics Creation

After both deploy:
1. Go to https://hypepaper.app
2. Login with Google
3. Go to Profile page
4. Try creating a custom topic
5. Should work without 401 error!

## 🔍 How to Verify

### Check Railway Deployment Status
```bash
# Railway will show deployment logs
# Look for: "Build successful" and "Deployment live"
```

### Check Frontend Console
After Cloudflare rebuilds, you should NOT see:
```
[DEBUG] Access token: eyJhbGci...
```

Instead you should see:
```
[DEBUG] Saving topic: {name: "...", description: "...", keywords: [...]}
[DEBUG] Topic created: {...}
```

### Test API Directly
```bash
# Get your access token from browser console (authStore.session.access_token)
TOKEN="your_access_token_here"

curl -X POST https://api.hypepaper.app/api/v1/topics \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test topic",
    "description": "testing",
    "keywords": ["test"]
  }'

# Should return 201 Created with topic data
# NOT 401 Unauthorized
```

## 🚨 Common Issues

### Issue 1: Still getting 401 after adding SUPABASE_ANON_KEY
**Cause**: Railway hasn't finished redeploying
**Solution**: Wait 2-4 minutes, check Railway deployment status

### Issue 2: Still seeing token logs in console
**Cause**: Cloudflare Pages using cached frontend code
**Solution**: Push empty commit or manually retry deployment

### Issue 3: Invalid SUPABASE_ANON_KEY
**Cause**: Wrong anon key value
**Solution**: Copy from backend/.env (the one that starts with eyJhbGci and has "role":"anon")

## ✅ Success Indicators

1. No more "[DEBUG] Access token: ..." in browser console
2. POST /api/v1/topics returns 201 Created
3. Custom topics appear in Profile page
4. No 401 errors in Network tab
