# 🚀 Quick Start: Deploy HypePaper in 10 Minutes

## What You're Deploying

- **Frontend**: Vue 3 app → Cloudflare Pages (free, global CDN)
- **Backend**: FastAPI Python → Railway.app (free tier, $5/month credit)
- **Database**: Already on Supabase ✓

## 🎯 Step-by-Step (10 minutes)

### 1. Setup Cloudflare Pages (3 min)

```bash
# 1. Go to https://dash.cloudflare.com/sign-up
# 2. Sign up (free account)
# 3. Workers & Pages > Create > Pages > Connect to Git
# 4. Select this repository
# 5. Configure:
Framework preset: Vite
Build command: npm run build
Build output: dist
Root directory: frontend

# 6. Add environment variables (Pages settings):
VITE_API_URL=https://api.hypepaper.app
VITE_SUPABASE_URL=[your-supabase-url]
VITE_SUPABASE_ANON_KEY=[your-supabase-anon-key]

# 7. Deploy!
```

**Result**: Frontend live at `https://hypepaper.pages.dev` ✓

### 2. Setup Railway (3 min)

```bash
# 1. Go to https://railway.app
# 2. Sign in with GitHub
# 3. New Project > Deploy from GitHub repo > Select HypePaper
# 4. Railway auto-deploys the backend!

# 5. Add environment variables (Railway project > Variables):
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres
SUPABASE_URL=[your-supabase-url]
SUPABASE_ANON_KEY=[your-anon-key]
SUPABASE_SERVICE_KEY=[your-service-key]
JWT_SECRET=[generate-random-32-chars]
ENVIRONMENT=production
GITHUB_TOKEN=[your-github-token]
PDF_STORAGE_PATH=/app/data/pdfs
```

**Result**: Backend live at `https://api.hypepaper.app` ✓

### 3. Setup GitHub Actions (2 min)

```bash
# Go to: GitHub repo > Settings > Secrets > Actions
# Add these secrets:

CLOUDFLARE_API_TOKEN     # Get from Cloudflare dashboard
CLOUDFLARE_ACCOUNT_ID    # In Cloudflare dashboard URL
RAILWAY_TOKEN            # Get from Railway account settings
VITE_API_URL             # https://api.hypepaper.app
VITE_SUPABASE_URL        # Your Supabase project URL
VITE_SUPABASE_ANON_KEY   # Your Supabase anon key
```

**Result**: Auto-deploy on every git push! ✓

### 4. Test Deployment (2 min)

```bash
# Test frontend
curl https://hypepaper.pages.dev

# Test backend
curl https://api.hypepaper.app/api/v1/health

# Test integration
# Visit https://hypepaper.pages.dev in browser
# Check if data loads from backend
```

**Result**: Everything working! ✓

## ✅ You're Done!

Your app is now deployed and will auto-update whenever you push to GitHub!

## 📱 Update from iPhone

**Method 1: Chat with Claude (Easiest)**
```
You: "Add a dark mode feature"
Claude: *implements, commits, pushes*
✓ Auto-deploys in 2 minutes!
```

**Method 2: GitHub App**
```
1. Open GitHub app on iPhone
2. Edit any file
3. Commit
4. ✓ Auto-deploys!
```

## 🔧 Useful Commands

```bash
# Deploy both frontend and backend
./scripts/deploy.sh

# Test local build
cd frontend && npm run build

# View logs
# Railway: https://railway.app/dashboard
# Cloudflare: https://dash.cloudflare.com
```

## 📚 Full Documentation

- **Complete Guide**: [docs/CLOUDFLARE_DEPLOYMENT.md](docs/CLOUDFLARE_DEPLOYMENT.md)
- **iPhone Workflow**: [docs/IPHONE_WORKFLOW.md](docs/IPHONE_WORKFLOW.md)
- **Deployment Checklist**: [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)

## 💡 Pro Tips

1. **Custom Domain**: Add your domain in Cloudflare Pages settings
2. **Monitoring**: Bookmark Railway and Cloudflare dashboards
3. **Staging**: Create a `develop` branch for testing before production
4. **Rollback**: Use GitHub to revert commits if needed

## 🆘 Troubleshooting

**Frontend not loading?**
- Check Cloudflare Pages build logs
- Verify environment variables are set

**Backend errors?**
- Check Railway logs
- Verify DATABASE_URL is correct
- Test Supabase connection

**CORS errors?**
- Verify ENVIRONMENT=production in Railway
- Check frontend domain in backend CORS settings

## 🎯 What's Next?

Your app is live! Now you can:
- Add custom domain
- Set up monitoring alerts
- Implement new features (just push to GitHub!)
- Manage everything from your iPhone

---

**Need Help?** Ask Claude in this chat or check the full documentation!
