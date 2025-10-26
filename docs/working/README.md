# Working Documentation (Archived)

> **⚠️ Note:** These documents are from troubleshooting sessions and may contain outdated information.

For current production deployment configuration, see:
- **[Railway Environment Variables](../RAILWAY_ENV_VARS.md)** - Current deployment setup

---

## Archived Troubleshooting Guides

These documents are kept for reference but may reference obsolete workflows (local development, old environment variable names, etc.):

- `CLOUDFLARE_DEPLOYMENT.md` - Cloudflare Pages setup (may be outdated)
- `CLOUDFLARE_PROXY_SETUP.md` - DNS proxy configuration
- `GOOGLE_AUTH_TROUBLESHOOTING.md` - Google OAuth setup
- `PERFORMANCE_OPTIMIZATION.md` - Database and rate limiting setup
- `RAILWAY_CUSTOM_DOMAIN_SETUP.md` - Custom domain configuration
- `RAILWAY_DEPLOYMENT_VERIFICATION.md` - Deployment verification steps
- `RAILWAY_ENV_VARS_FIX.md` - Environment variable troubleshooting

**For current information, always check:**
1. Main documentation in `/docs` (not `/docs/working`)
2. Railway dashboard for actual environment variables
3. Cloudflare Pages dashboard for frontend configuration

---

## Current Production Setup (2025-01-26)

### ✅ What Works

- **Automatic deployment:** Push to GitHub → Railway/Cloudflare auto-deploy
- **No local .env files:** All config in Railway/Cloudflare dashboards
- **Supabase authentication:** Using anon key (publishable key)
- **Database:** Supabase PostgreSQL with indexes
- **Custom domain:** api.hypepaper.app (backend), hypepaper.app (frontend)

### 🔧 Key Configuration

**Backend (Railway):**
- `SUPABASE_ANON_KEY` = Supabase publishable/anon key
- `SUPABASE_SERVICE_KEY` = Supabase service role key
- `DATABASE_URL` = PostgreSQL connection string with `+asyncpg`

**Frontend (Cloudflare Pages):**
- `VITE_API_URL` = https://api.hypepaper.app
- `VITE_SUPABASE_URL` = Supabase project URL
- `VITE_SUPABASE_ANON_KEY` = Same as backend anon key

See **[RAILWAY_ENV_VARS.md](../RAILWAY_ENV_VARS.md)** for complete setup.
