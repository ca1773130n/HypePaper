# HypePaper Deployment Guide

## Overview

HypePaper consists of three main components:
1. **Frontend**: Vue 3 + TypeScript (deployed on Vercel)
2. **Backend**: FastAPI + PostgreSQL (deployed on Render/Fly.io)
3. **Services**: Redis, Celery, TimescaleDB

## Prerequisites

- Supabase account (for authentication and database)
- Vercel account (for frontend hosting)
- Render/Fly.io account (for backend hosting)
- Redis instance (Upstash or managed Redis)
- GitHub OAuth app (configured in Supabase)

## Step 1: Supabase Setup

### 1.1 Create Supabase Project

```bash
# Go to https://supabase.com/dashboard
# Click "New Project"
# Name: hypepaper-prod
# Region: Choose closest to your users
# Database password: Generate secure password
```

### 1.2 Enable Google OAuth

```bash
# In Supabase Dashboard:
# 1. Go to Authentication > Providers
# 2. Enable Google provider
# 3. Add OAuth credentials:
#    - Client ID: from Google Cloud Console
#    - Client Secret: from Google Cloud Console
#    - Redirect URL: https://your-project.supabase.co/auth/v1/callback
```

### 1.3 Run Database Migrations

```bash
# Get your Supabase database URL from Settings > Database
# Format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres

cd backend
export DATABASE_URL="postgresql+asyncpg://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
python -m alembic upgrade head
```

### 1.4 Seed System Topics

```sql
-- Run in Supabase SQL Editor
INSERT INTO topics (name, description, keywords, is_system, created_at) VALUES
('machine learning', 'Machine Learning and AI', ARRAY['machine learning', 'ML', 'AI'], true, NOW()),
('computer vision', 'Computer Vision', ARRAY['computer vision', 'CV', 'image'], true, NOW()),
('natural language processing', 'NLP and Text Processing', ARRAY['NLP', 'text', 'language'], true, NOW()),
('reinforcement learning', 'Reinforcement Learning', ARRAY['RL', 'reinforcement'], true, NOW()),
('robotics', 'Robotics and Automation', ARRAY['robot', 'automation'], true, NOW());
```

## Step 2: Backend Deployment (Render)

### 2.1 Create Web Service

```bash
# Go to https://dashboard.render.com
# Click "New +" > "Web Service"
# Connect your GitHub repository
# Configure:
#   Name: hypepaper-backend
#   Environment: Python 3
#   Build Command: pip install -r backend/requirements.txt
#   Start Command: cd backend && uvicorn src.main:app --host 0.0.0.0 --port $PORT
#   Plan: Starter (or higher)
```

### 2.2 Configure Environment Variables

```bash
# In Render Dashboard > Environment
DATABASE_URL=postgresql+asyncpg://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_ANON_KEY=[anon key from Supabase Settings > API]
SUPABASE_SERVICE_KEY=[service_role key from Supabase Settings > API]
JWT_SECRET=[generate secure random string]
GITHUB_TOKEN=[GitHub personal access token]
PDF_STORAGE_PATH=/opt/render/project/data/pdfs
REDIS_URL=[Upstash Redis URL]
CELERY_BROKER_URL=[Upstash Redis URL]
CELERY_RESULT_BACKEND=[Upstash Redis URL]
LLM_PROVIDER=llamacpp
LLAMACPP_SERVER=http://localhost:10002/v1/chat/completions
```

### 2.3 Create Background Worker (for Celery)

```bash
# In Render Dashboard:
# Click "New +" > "Background Worker"
# Connect same repository
# Build Command: pip install -r backend/requirements.txt
# Start Command: cd backend && celery -A src.jobs.celery_app worker --loglevel=info
# Use same environment variables as web service
```

### 2.4 Add Persistent Disk (for PDF storage)

```bash
# In Render Dashboard > Service Settings:
# Click "Disks" > "Add Disk"
# Name: pdf-storage
# Mount Path: /opt/render/project/data/pdfs
# Size: 10 GB (adjust as needed)
```

## Step 3: Frontend Deployment (Vercel)

### 3.1 Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy from frontend directory
cd frontend
vercel --prod
```

### 3.2 Configure Environment Variables

```bash
# In Vercel Dashboard > Project Settings > Environment Variables
VITE_API_URL=https://hypepaper-backend.onrender.com
VITE_SUPABASE_URL=https://[project-ref].supabase.co
VITE_SUPABASE_ANON_KEY=[anon key from Supabase]
```

### 3.3 Configure Redirect for Auth Callback

```json
// frontend/vercel.json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://hypepaper-backend.onrender.com/api/:path*" }
  ]
}
```

## Step 4: Post-Deployment Setup

### 4.1 Update CORS Origins

```python
# backend/src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-app.vercel.app",
        "https://www.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.2 Configure Supabase Redirect URLs

```bash
# In Supabase Dashboard > Authentication > URL Configuration
# Site URL: https://your-app.vercel.app
# Redirect URLs:
#   https://your-app.vercel.app/auth/callback
#   http://localhost:5173/auth/callback (for local dev)
```

### 4.3 Set up Monitoring

```bash
# In Render Dashboard:
# Enable "Auto-Deploy" from main branch
# Configure health check endpoint: /api/v1/health

# In Vercel Dashboard:
# Enable "Automatically expose System Environment Variables"
# Configure deployment notifications
```

## Step 5: Testing Production Deployment

### 5.1 Health Checks

```bash
# Backend health
curl https://hypepaper-backend.onrender.com/api/v1/health

# Frontend
curl https://your-app.vercel.app

# Database connection
curl https://hypepaper-backend.onrender.com/api/v1/topics
```

### 5.2 Authentication Flow

1. Navigate to https://your-app.vercel.app/login
2. Click "Sign in with Google"
3. Verify redirect to Supabase OAuth
4. Verify redirect back to /auth/callback
5. Verify redirect to homepage with user session

### 5.3 Test CRUD Operations

```bash
# Create custom topic (requires auth)
curl -X POST https://hypepaper-backend.onrender.com/api/v1/topics \
  -H "Authorization: Bearer [access_token]" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "quantum computing",
    "description": "Quantum Computing Research",
    "keywords": ["quantum", "qubit", "entanglement"]
  }'

# Trigger ArXiv crawl (admin only)
curl -X POST https://hypepaper-backend.onrender.com/api/v1/admin/crawl/arxiv \
  -H "Authorization: Bearer [access_token]" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "limit": 50
  }'
```

## Step 6: Performance Optimization

### 6.1 Enable Caching

```python
# backend/src/services/cache_service.py
# Redis caching is already implemented
# Adjust TTL based on usage patterns
```

### 6.2 Database Indexes

```sql
-- Add indexes for common queries
CREATE INDEX idx_papers_published_date ON papers(published_date DESC);
CREATE INDEX idx_papers_github_stars ON papers(github_stars DESC);
CREATE INDEX idx_paper_topic_matches_relevance ON paper_topic_matches(relevance_score DESC);
CREATE INDEX idx_github_star_snapshots_date ON github_star_snapshots(snapshot_date DESC);
```

### 6.3 CDN Configuration

```bash
# Vercel automatically serves assets via CDN
# Configure cache headers in vercel.json:
{
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

## Step 7: Monitoring and Maintenance

### 7.1 Set up Logging

```bash
# Render automatically collects logs
# Access via Dashboard > Logs

# Set up log aggregation (optional):
# - Datadog
# - Sentry
# - LogRocket
```

### 7.2 Background Jobs Monitoring

```bash
# Monitor Celery tasks via Flower (optional)
pip install flower

# Add flower service in Render:
celery -A src.jobs.celery_app flower --port=5555
```

### 7.3 Database Backups

```bash
# Supabase provides automatic daily backups
# Configure backup retention in Supabase Dashboard > Settings > Backups
# Recommended: Enable Point-in-Time Recovery (PITR) for production
```

## Troubleshooting

### Issue: CORS errors in production

**Solution**: Verify CORS origins in `backend/src/main.py` match your Vercel domain

### Issue: Authentication redirects fail

**Solution**: Check Supabase redirect URLs include your production domain

### Issue: PDF downloads fail

**Solution**: Verify persistent disk is mounted and PDF_STORAGE_PATH is correct

### Issue: Celery tasks not running

**Solution**: Check Redis connection and ensure background worker is deployed

### Issue: Database connection timeouts

**Solution**: Increase connection pool size in `backend/src/config.py`

## Costs Estimation (Monthly)

- **Supabase**: Free tier (500MB DB, 2GB bandwidth) - Upgrade to Pro ($25) for production
- **Render**: Starter plan ($7/service) × 2 (web + worker) = $14
- **Vercel**: Free tier (100GB bandwidth) - Upgrade to Pro ($20) if needed
- **Upstash Redis**: Free tier (10k commands/day) - Upgrade to Pay-as-you-go ($0.20/100k)

**Total**: $14-59/month depending on scale

## Scaling Recommendations

### For 1000+ users:
- Upgrade Supabase to Pro plan
- Add Render autoscaling (Standard plan)
- Enable Redis persistence
- Add CDN for PDF files (Cloudflare R2 or AWS S3)

### For 10000+ users:
- Migrate to dedicated PostgreSQL (AWS RDS, GCP Cloud SQL)
- Use multiple Celery workers
- Implement horizontal scaling with load balancer
- Add full-text search (Elasticsearch or Typesense)

## Security Checklist

- [ ] Enable Supabase RLS (Row Level Security) policies
- [ ] Configure rate limiting in FastAPI
- [ ] Use HTTPS for all endpoints
- [ ] Rotate JWT secrets regularly
- [ ] Enable Supabase 2FA for admin accounts
- [ ] Configure CSP headers in Vercel
- [ ] Regular dependency updates (Dependabot)
- [ ] Monitor for security vulnerabilities (Snyk)

## Support

For deployment issues:
- Backend: Check Render logs in Dashboard
- Frontend: Check Vercel deployment logs
- Database: Check Supabase logs in Dashboard
- GitHub Issues: https://github.com/yourusername/hypepaper/issues
