# HypePaper Cloudflare Deployment Guide

## 🚀 Quick Start

Your app is configured for:
- **Frontend**: Cloudflare Pages (Vue 3 + Vite)
- **Backend**: Railway.app (FastAPI + Python)
- **Database**: Supabase (PostgreSQL)

All deployments are automatic via git push! Just commit and push your changes.

## 📱 Managing from iPhone

You can update your app from anywhere using:

1. **GitHub Mobile App**:
   - Edit files directly in GitHub
   - Commit changes
   - Auto-deploys to both platforms

2. **Chat with Claude** (this conversation):
   - Tell me what to change
   - I'll make the changes and commit
   - Auto-deploys automatically

## 🎯 Step 1: Deploy Frontend to Cloudflare Pages

### 1.1 Create Cloudflare Account
1. Go to https://dash.cloudflare.com/sign-up
2. Sign up (free tier available)
3. Verify your email

### 1.2 Connect GitHub Repository
1. Go to **Workers & Pages** > **Create Application** > **Pages**
2. Connect to GitHub and select your `HypePaper` repository
3. Configure build settings:
   ```
   Framework preset: Vite
   Build command: npm run build
   Build output directory: dist
   Root directory: frontend
   ```

### 1.3 Add Environment Variables
In Cloudflare Pages settings > Environment Variables:

```bash
# Production Environment
VITE_API_URL=https://hypepaper-backend.up.railway.app
VITE_SUPABASE_URL=your-supabase-project-url
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### 1.4 Get Your Cloudflare API Token

1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Create Token > Use template "Edit Cloudflare Workers"
3. Save token for GitHub Actions

## 🎯 Step 2: Deploy Backend to Railway

### 2.1 Create Railway Account
1. Go to https://railway.app/
2. Sign in with GitHub
3. Free tier includes $5/month credit

### 2.2 Create New Project
1. Click **New Project** > **Deploy from GitHub repo**
2. Select your `HypePaper` repository
3. Railway will auto-detect Python and deploy

### 2.3 Configure Environment Variables

In Railway project settings > Variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:[password]@db.[project-ref].supabase.co:5432/postgres

# Supabase
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Security
JWT_SECRET=your-secure-random-string-here

# GitHub Integration
GITHUB_TOKEN=your-github-personal-access-token

# Storage
PDF_STORAGE_PATH=/app/data/pdfs

# Optional: Redis (if using background jobs)
REDIS_URL=redis://default:password@redis-host:6379
CELERY_BROKER_URL=redis://default:password@redis-host:6379
CELERY_RESULT_BACKEND=redis://default:password@redis-host:6379

# LLM Configuration
LLM_PROVIDER=llamacpp
LLAMACPP_SERVER=http://localhost:10002/v1/chat/completions
```

### 2.4 Get Your Railway API Token

1. Go to Railway Account Settings > Tokens
2. Create new token
3. Save for GitHub Actions

### 2.5 Add Persistent Storage (for PDFs)

1. In Railway project > New > Database > Add Volume
2. Mount path: `/app/data/pdfs`
3. Size: 5-10 GB

## 🎯 Step 3: Configure GitHub Secrets

Go to your GitHub repo > Settings > Secrets and variables > Actions

Add these secrets:

```bash
# Cloudflare
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id

# Railway
RAILWAY_TOKEN=your-railway-api-token

# Frontend Environment Variables
VITE_API_URL=https://hypepaper-backend.up.railway.app
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

To find your Cloudflare Account ID:
1. Go to Cloudflare Dashboard
2. Click on Pages
3. URL will be: `dash.cloudflare.com/{account-id}/pages`

## 🎯 Step 4: Update CORS Settings

Update backend CORS to allow your Cloudflare domain:

```python
# backend/src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hypepaper.pages.dev",  # Cloudflare Pages
        "https://yourdomain.com",       # Custom domain (optional)
        "http://localhost:5173",        # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🎯 Step 5: Test Deployment

### 5.1 Make a Test Change

```bash
# Edit a file
echo "# Test deployment" >> README.md

# Commit and push
git add .
git commit -m "test: trigger deployment"
git push origin main
```

### 5.2 Monitor Deployments

**Cloudflare Pages**:
- Go to https://dash.cloudflare.com/
- Click Workers & Pages > Your project
- See deployment logs in real-time

**Railway**:
- Go to https://railway.app/dashboard
- Click your project
- See deployment logs and status

### 5.3 Verify Endpoints

```bash
# Frontend (Cloudflare Pages)
curl https://hypepaper.pages.dev

# Backend (Railway)
curl https://hypepaper-backend.up.railway.app/api/v1/health

# Test API connection
curl https://hypepaper-backend.up.railway.app/api/v1/topics
```

## 📱 Updating from iPhone

### Option 1: GitHub Mobile App
1. Open GitHub app
2. Navigate to your repo
3. Edit any file
4. Commit changes
5. ✅ Auto-deploys to both platforms!

### Option 2: Chat with Claude
Just tell me what you want to change:
- "Add a new feature to show paper statistics"
- "Fix the navigation bar styling"
- "Update the API endpoint for topics"

I'll make the changes, commit, and push automatically!

### Option 3: Working Copy App (iOS)
1. Install Working Copy from App Store
2. Clone your repo
3. Edit files
4. Commit and push
5. ✅ Auto-deploys!

## 🔧 Custom Domains (Optional)

### Cloudflare Pages
1. Go to project settings > Custom domains
2. Add your domain (e.g., hypepaper.com)
3. Update DNS records as instructed
4. SSL automatically enabled ✓

### Railway Backend
1. Go to project settings > Domains
2. Add custom domain (e.g., api.hypepaper.com)
3. Update DNS:
   ```
   Type: CNAME
   Name: api
   Value: your-app.up.railway.app
   ```

## 💰 Costs

### Free Tier Limits
- **Cloudflare Pages**: Unlimited static requests, 500 builds/month
- **Railway**: $5/month credit, ~550 hours runtime
- **Supabase**: 500MB database, 2GB bandwidth

### Estimated Monthly (if exceeding free tier)
- Cloudflare Pages: Free (very generous)
- Railway: $5-20 (depends on usage)
- Supabase: $25 (Pro plan if needed)
- **Total**: $0-45/month

## 🚨 Troubleshooting

### Frontend not loading
1. Check build logs in Cloudflare Pages
2. Verify environment variables are set
3. Check `frontend/dist` folder is being built

### Backend errors
1. Check Railway logs
2. Verify DATABASE_URL is correct
3. Test Supabase connection

### CORS errors
1. Update `backend/src/main.py` with your Cloudflare domain
2. Redeploy backend

### Database migrations
```bash
# Run migrations on Railway
railway run python -m alembic upgrade head
```

## 🎉 Success Checklist

- [ ] Frontend deployed to Cloudflare Pages
- [ ] Backend deployed to Railway
- [ ] Environment variables configured
- [ ] GitHub Actions running successfully
- [ ] Custom domains configured (optional)
- [ ] CORS settings updated
- [ ] Database migrations run
- [ ] Test API endpoints working
- [ ] Frontend can connect to backend
- [ ] Authentication flow working

## 📚 Useful Commands

```bash
# View Railway logs
railway logs

# Connect to Railway shell
railway shell

# Run database migrations
railway run python -m alembic upgrade head

# Test local build
cd frontend && npm run build && npm run preview

# Check production API
curl https://your-backend.up.railway.app/api/v1/health
```

## 🔗 Quick Links

- **Frontend**: https://hypepaper.pages.dev
- **Backend**: https://hypepaper-backend.up.railway.app
- **Supabase Dashboard**: https://supabase.com/dashboard
- **Cloudflare Dashboard**: https://dash.cloudflare.com
- **Railway Dashboard**: https://railway.app/dashboard

---

**Need help?** Just ask me in this chat! I can:
- Make code changes
- Update configurations
- Fix deployment issues
- Add new features
- Debug errors

All from your iPhone! 📱✨
