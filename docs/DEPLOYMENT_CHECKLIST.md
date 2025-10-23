# 📋 HypePaper Deployment Checklist

Use this checklist when deploying HypePaper for the first time.

## ☁️ Before You Start

- [ ] GitHub account created
- [ ] Repository pushed to GitHub
- [ ] Supabase database already set up ✓

## 1️⃣ Cloudflare Pages Setup (Frontend)

### Create Account
- [ ] Sign up at https://dash.cloudflare.com
- [ ] Verify email
- [ ] Note your Account ID (found in dashboard URL)

### Connect Repository
- [ ] Go to Workers & Pages > Create Application > Pages
- [ ] Connect to GitHub
- [ ] Select `HypePaper` repository
- [ ] Configure build settings:
  - Framework: `Vite`
  - Build command: `npm run build`
  - Build output: `dist`
  - Root directory: `frontend`

### Set Environment Variables
Go to Pages project > Settings > Environment Variables > Production:

- [ ] `VITE_API_URL` = `https://hypepaper-backend.up.railway.app`
- [ ] `VITE_SUPABASE_URL` = Your Supabase project URL
- [ ] `VITE_SUPABASE_ANON_KEY` = Your Supabase anon key

### Get API Token
- [ ] Go to Profile > API Tokens
- [ ] Create token with "Edit Cloudflare Workers" template
- [ ] Save token securely (needed for GitHub Actions)

### Note Your URLs
- [ ] Production URL: `hypepaper.pages.dev`
- [ ] Custom domain (optional): `_________________`

## 2️⃣ Railway Setup (Backend)

### Create Account
- [ ] Go to https://railway.app
- [ ] Sign in with GitHub
- [ ] Note: Free tier includes $5/month credit

### Create Project
- [ ] Click New Project > Deploy from GitHub repo
- [ ] Select `HypePaper` repository
- [ ] Railway auto-detects Python
- [ ] Wait for initial deployment

### Set Environment Variables
Go to project > Variables > Add all of these:

#### Database
- [ ] `DATABASE_URL` = `postgresql+asyncpg://postgres:[password]@db.[ref].supabase.co:5432/postgres`

#### Supabase
- [ ] `SUPABASE_URL` = Your Supabase project URL
- [ ] `SUPABASE_ANON_KEY` = Your Supabase anon key
- [ ] `SUPABASE_SERVICE_KEY` = Your Supabase service role key

#### Security
- [ ] `JWT_SECRET` = Generate a secure random string (32+ chars)
- [ ] `ENVIRONMENT` = `production`
- [ ] `CORS_ORIGINS` = `https://hypepaper.pages.dev,http://localhost:5173`

#### GitHub Integration
- [ ] `GITHUB_TOKEN` = Your GitHub personal access token

#### Storage
- [ ] `PDF_STORAGE_PATH` = `/app/data/pdfs`

#### Optional: Redis (for background jobs)
- [ ] `REDIS_URL` = Redis connection URL
- [ ] `CELERY_BROKER_URL` = Same as REDIS_URL
- [ ] `CELERY_RESULT_BACKEND` = Same as REDIS_URL

#### Optional: LLM
- [ ] `LLM_PROVIDER` = `llamacpp`
- [ ] `LLAMACPP_SERVER` = Server URL if using

### Add Persistent Storage (Optional)
- [ ] Go to project > Add Volume
- [ ] Mount path: `/app/data/pdfs`
- [ ] Size: `10 GB`

### Get API Token
- [ ] Go to Account Settings > Tokens
- [ ] Create new token
- [ ] Save token securely (needed for GitHub Actions)

### Note Your URLs
- [ ] API URL: `hypepaper-backend.up.railway.app`

## 3️⃣ GitHub Secrets Setup

Go to GitHub repo > Settings > Secrets and variables > Actions

### Add Repository Secrets
- [ ] `CLOUDFLARE_API_TOKEN` = Token from Cloudflare
- [ ] `CLOUDFLARE_ACCOUNT_ID` = From Cloudflare dashboard URL
- [ ] `RAILWAY_TOKEN` = Token from Railway
- [ ] `VITE_API_URL` = `https://hypepaper-backend.up.railway.app`
- [ ] `VITE_SUPABASE_URL` = Your Supabase project URL
- [ ] `VITE_SUPABASE_ANON_KEY` = Your Supabase anon key

## 4️⃣ Database Setup

### Run Migrations
```bash
# In Railway dashboard, open shell
railway shell

# Run migrations
cd backend
python -m alembic upgrade head
```

Or use the Railway web terminal.

- [ ] Migrations executed successfully
- [ ] No errors in logs

### Verify Database
- [ ] Test connection from Railway
- [ ] Check tables exist in Supabase dashboard
- [ ] Verify system topics are seeded

## 5️⃣ Update CORS Settings

### Update Backend CORS
The backend is already configured to use Cloudflare Pages domain in production mode.

- [ ] Verify `ENVIRONMENT=production` is set in Railway
- [ ] Check CORS_ORIGINS includes your Cloudflare domain
- [ ] Redeploy if needed

### Update Supabase Settings
Go to Supabase Dashboard > Authentication > URL Configuration:

- [ ] Site URL: `https://hypepaper.pages.dev`
- [ ] Redirect URLs:
  - [ ] `https://hypepaper.pages.dev/auth/callback`
  - [ ] `http://localhost:5173/auth/callback` (for development)

## 6️⃣ Test Deployment

### Test Frontend
- [ ] Visit `https://hypepaper.pages.dev`
- [ ] Page loads without errors
- [ ] Check browser console (F12) - no errors
- [ ] Test navigation between pages

### Test Backend
```bash
# Health check
curl https://hypepaper-backend.up.railway.app/api/v1/health

# Test topics endpoint
curl https://hypepaper-backend.up.railway.app/api/v1/topics
```

- [ ] Health endpoint returns 200 OK
- [ ] Topics endpoint returns data
- [ ] No 500 errors in logs

### Test Integration
- [ ] Frontend can fetch data from backend
- [ ] Search functionality works
- [ ] Paper listing loads
- [ ] No CORS errors in console

### Test Authentication
- [ ] Click login on frontend
- [ ] Google OAuth redirects correctly
- [ ] Callback returns to app
- [ ] User session persists

## 7️⃣ GitHub Actions Workflow

### Verify Workflow
- [ ] Go to GitHub repo > Actions tab
- [ ] See "Deploy to Cloudflare Pages and Railway" workflow
- [ ] Make a test commit to trigger workflow

### Test Auto-Deploy
```bash
# Make a small change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "test: verify auto-deployment"
git push origin main
```

- [ ] Workflow starts automatically
- [ ] Frontend deployment succeeds
- [ ] Backend deployment succeeds
- [ ] Changes visible in production

## 8️⃣ Monitoring Setup

### Set Up Alerts (Optional)
- [ ] Configure Cloudflare email alerts
- [ ] Set up Railway notifications
- [ ] Enable GitHub Actions notifications

### Bookmark Dashboards
- [ ] Cloudflare Pages: https://dash.cloudflare.com
- [ ] Railway: https://railway.app/dashboard
- [ ] Supabase: https://supabase.com/dashboard
- [ ] GitHub Actions: [your-repo]/actions

## 9️⃣ Custom Domain (Optional)

### Frontend Custom Domain
If you want `hypepaper.com` instead of `hypepaper.pages.dev`:

- [ ] Go to Cloudflare Pages > Custom domains
- [ ] Add domain
- [ ] Update DNS records as instructed
- [ ] Wait for SSL certificate (automatic)
- [ ] Update Supabase redirect URLs

### Backend Custom Domain
If you want `api.hypepaper.com`:

- [ ] Go to Railway project > Settings > Domains
- [ ] Add custom domain
- [ ] Update DNS CNAME record
- [ ] Update frontend `VITE_API_URL`
- [ ] Update CORS settings

## 🎯 Final Verification

### Production Checklist
- [ ] Frontend loads at production URL
- [ ] Backend API responds correctly
- [ ] Database queries work
- [ ] Authentication flow works
- [ ] Search functionality works
- [ ] Paper details page loads
- [ ] No console errors
- [ ] No CORS errors
- [ ] SSL certificate valid (https://)
- [ ] Mobile responsive (test on phone)

### Performance Check
- [ ] Frontend loads in < 3 seconds
- [ ] API responses in < 1 second
- [ ] Images load properly
- [ ] No JavaScript errors

### Security Check
- [ ] HTTPS enabled on all domains
- [ ] Security headers present (check _headers file)
- [ ] API keys not exposed in frontend
- [ ] CORS properly configured
- [ ] Authentication required for protected routes

## 📱 Mobile Management Setup

### Install Apps
- [ ] GitHub app on iPhone
- [ ] Add production URLs to Safari bookmarks
- [ ] Test making a change via GitHub app

### Test Mobile Workflow
- [ ] Edit a file on iPhone via GitHub
- [ ] Commit change
- [ ] Verify auto-deployment
- [ ] Check production site updated

## 🎉 You're Done!

Your HypePaper app is now deployed and accessible from anywhere!

### Quick Reference
- **Frontend**: https://hypepaper.pages.dev
- **Backend API**: https://hypepaper-backend.up.railway.app
- **Database**: Supabase Dashboard

### To Deploy Changes
Just push to GitHub:
```bash
git add .
git commit -m "feat: your changes"
git push origin main
```

Both frontend and backend will automatically deploy! 🚀

### Need Help?
- Check docs/CLOUDFLARE_DEPLOYMENT.md
- Check docs/IPHONE_WORKFLOW.md
- Ask Claude in this chat!
