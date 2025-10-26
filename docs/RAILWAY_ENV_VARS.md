# Railway Environment Variables Configuration

> **Note:** This project uses automatic deployment via GitHub Actions → Railway. No local `.env` files needed.

## 🚀 Backend Service (Railway)

Configure these environment variables in **Railway Dashboard → Backend Service → Variables**:

### Required Variables

```bash
# Database (Supabase Connection)
DATABASE_URL=postgresql+asyncpg://postgres.zvesxmkgkldorxlbyhce:YOUR_PASSWORD@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres

# Supabase Authentication
SUPABASE_URL=https://zvesxmkgkldorxlbyhce.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...  # Your Supabase publishable/anon key
SUPABASE_SERVICE_KEY=eyJhbGci...  # Your Supabase service role key

# GitHub API
GITHUB_TOKEN=ghp_...  # Your GitHub Personal Access Token
```

### Optional Variables

```bash
# LLM Provider (default: llamacpp)
LLM_PROVIDER=llamacpp
LLAMACPP_SERVER=http://localhost:10002/v1/chat/completions

# OpenAI (if using OpenAI instead of llamacpp)
OPENAI_API_KEY=sk-...
```

---

## 🌐 Frontend Service (Cloudflare Pages)

Configure these environment variables in **Cloudflare Pages → Settings → Environment Variables**:

### Production Environment

```bash
VITE_API_URL=https://api.hypepaper.app
VITE_SUPABASE_URL=https://zvesxmkgkldorxlbyhce.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...  # Same as backend SUPABASE_ANON_KEY
```

### Preview Environment (Optional)

```bash
VITE_API_URL=https://api.hypepaper.app
VITE_SUPABASE_URL=https://zvesxmkgkldorxlbyhce.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
```

---

## 🔑 Where to Get These Keys

### Supabase Keys

1. Go to **Supabase Dashboard** → Your Project → **Settings** → **API**
2. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon/public key** → `SUPABASE_ANON_KEY` (also called "publishable key")
   - **service_role key** → `SUPABASE_SERVICE_KEY` (⚠️ Keep secret!)

> **Important:** `SUPABASE_ANON_KEY` and "publishable key" are the same thing. Use the anon/public key, NOT the legacy key.

### Database URL

1. Go to **Supabase Dashboard** → **Settings** → **Database**
2. Under **Connection string**, select **Transaction Pooling**
3. Copy connection string and change:
   ```
   postgresql://... → postgresql+asyncpg://...
   ```
4. Replace `[YOUR-PASSWORD]` with your actual database password

### GitHub Token

1. Go to **GitHub** → **Settings** → **Developer settings** → **Personal access tokens**
2. Click **Generate new token (classic)**
3. Select scopes:
   - ✅ `public_repo` (for public repositories)
   - ✅ `repo` (if you need private repos)
4. Generate and copy token

---

## 🔄 Deployment Flow

```
Local Code Change
    ↓
git commit && git push
    ↓
GitHub Actions (optional)
    ↓
├── Railway (Backend) ← Auto-deploys from main branch
└── Cloudflare Pages (Frontend) ← Auto-deploys from main branch
```

**No local environment setup needed!** Everything deploys automatically.

---

## ✅ Verification Checklist

### Backend (Railway)
- [ ] `DATABASE_URL` set and valid
- [ ] `SUPABASE_URL` matches your Supabase project
- [ ] `SUPABASE_ANON_KEY` is the anon/public key (not legacy)
- [ ] `SUPABASE_SERVICE_KEY` is the service role key
- [ ] `GITHUB_TOKEN` is valid and has repo access
- [ ] Deployment shows "Success"
- [ ] Health check returns 200: `curl https://api.hypepaper.app/health`

### Frontend (Cloudflare Pages)
- [ ] `VITE_API_URL` points to Railway backend
- [ ] `VITE_SUPABASE_URL` matches backend
- [ ] `VITE_SUPABASE_ANON_KEY` matches backend anon key
- [ ] Deployment shows "Success"
- [ ] Website loads: https://hypepaper.app

---

## 🐛 Common Issues

### Issue: 401 Unauthorized when creating topics
**Cause:** `SUPABASE_ANON_KEY` missing or wrong in Railway
**Solution:** Add/update the anon key in Railway Variables

### Issue: Database connection failed
**Cause:** Wrong `DATABASE_URL` format or password
**Solution:**
1. Use `postgresql+asyncpg://` (not just `postgresql://`)
2. Use Transaction Pooling connection string from Supabase
3. Verify password is correct

### Issue: Frontend can't connect to backend
**Cause:** Wrong `VITE_API_URL` in Cloudflare Pages
**Solution:** Should be `https://api.hypepaper.app` (not Railway URL)

### Issue: CORS errors
**Cause:** Backend CORS not configured for frontend domain
**Solution:** Already configured in backend `main.py` for hypepaper.app

---

## 📝 Notes

- **No `.env` files in git repository** - All configuration is in Railway/Cloudflare dashboards
- **Secrets are safe** - Environment variables are encrypted by Railway and Cloudflare
- **Auto-deployment** - Push to GitHub main branch triggers automatic deployment
- **Same keys in both places** - Frontend and backend both need the Supabase anon key

---

## 🔒 Security Best Practices

1. ✅ Never commit `.env` files (already in `.gitignore`)
2. ✅ Use Supabase anon key for frontend (safe to expose)
3. ❌ Never expose service role key in frontend
4. ✅ Rotate GitHub token if compromised
5. ✅ Use Railway's secret variables for sensitive data
6. ✅ Enable 2FA on Railway, Cloudflare, and Supabase accounts
