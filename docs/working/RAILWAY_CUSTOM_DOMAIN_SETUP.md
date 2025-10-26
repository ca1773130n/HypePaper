# Railway Custom Domain Setup for api.hypepaper.app

## ✅ What's Already Done

All code and documentation have been updated to use the new API URL:
- **Old URL**: `https://hypepaper-production.up.railway.app` (or `hypepaper-backend.up.railway.app`)
- **New URL**: `https://api.hypepaper.app`

## 🔧 Railway Configuration Required

### Step 1: Add Custom Domain in Railway Dashboard

1. Go to your Railway project: https://railway.app/dashboard
2. Click on your backend service
3. Go to **Settings** > **Domains**
4. Click **+ Add Domain**
5. Enter: `api.hypepaper.app`
6. Railway will provide DNS records to configure

### Step 2: Configure DNS Records

Railway will show you the DNS records needed. Typically:

```
Type: CNAME
Name: api
Value: [provided-by-railway].up.railway.app
```

Add this CNAME record in your domain registrar's DNS settings (where hypepaper.app is registered).

### Step 3: Wait for DNS Propagation

- DNS changes can take 5 minutes to 48 hours
- Railway will automatically provision SSL certificate once DNS is verified

## 🌍 Environment Variables - NO CHANGES NEEDED

**Good news**: You do **NOT** need to change any environment variables in Railway!

The backend environment variables (DATABASE_URL, SUPABASE_URL, etc.) are all for the backend's own configuration. They don't need to know about the custom domain.

### Current Railway Environment Variables (Keep as-is)

✅ These are already correct and don't need updating:
- `DATABASE_URL` - Your Supabase PostgreSQL connection
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `JWT_SECRET` - Your JWT secret
- `ENVIRONMENT=production` - Production mode
- `GITHUB_TOKEN` - GitHub API access
- `PDF_STORAGE_PATH=/app/data/pdfs` - Storage path
- `REDIS_URL` - Redis connection (if using background jobs)
- `CELERY_BROKER_URL` - Celery broker (if using background jobs)
- `CELERY_RESULT_BACKEND` - Celery results (if using background jobs)

### Frontend Environment Variables (Cloudflare Pages)

⚠️ **YOU NEED TO UPDATE THESE** in Cloudflare Pages dashboard:

Go to: Cloudflare Dashboard > Pages > hypepaper > Settings > Environment Variables

Update:
```bash
VITE_API_URL=https://api.hypepaper.app
```

This tells the frontend where to find the backend API.

## 🔍 Verification Steps

Once DNS is configured and propagated:

1. **Test Health Endpoint**:
   ```bash
   curl https://api.hypepaper.app/health
   ```
   Should return: `{"status":"ok"}`

2. **Test API Endpoint**:
   ```bash
   curl https://api.hypepaper.app/api/v1/health
   ```
   Should return: `{"status":"healthy", ...}`

3. **Test CORS** (from browser at hypepaper.app):
   - Open browser console
   - Try making an API call
   - Should work without CORS errors (already configured in backend)

## 📝 Summary

**What You Need to Do**:
1. ✅ Code updated (already done)
2. ⚠️ Add custom domain in Railway dashboard → Get DNS records
3. ⚠️ Add CNAME record in your domain registrar
4. ⚠️ Update `VITE_API_URL` in Cloudflare Pages to `https://api.hypepaper.app`
5. ⏳ Wait for DNS propagation
6. ✅ Test endpoints

**What You DON'T Need to Do**:
- ❌ No Railway environment variables need updating
- ❌ No backend code changes needed
- ❌ No database changes needed

The backend doesn't need to know its own external URL - it just needs to respond to requests and allow CORS from your frontend domains (already configured).
