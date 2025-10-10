# HypePaper Deployment Guide

Complete guide for deploying HypePaper to production.

## Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Browser   │─────▶│   Frontend   │─────▶│    Backend API  │
│  (Client)   │      │  (React/Vite)│      │   (FastAPI)     │
└─────────────┘      └──────────────┘      └────────┬────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │   PostgreSQL    │
                                            │  + TimescaleDB  │
                                            └─────────────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │ Background Jobs │
                                            │  (APScheduler)  │
                                            └─────────────────┘
```

## Deployment Options

### Option 1: Docker Compose (Recommended for MVP)

**Pros:**
- Simple setup
- All services in one place
- Easy local development
- Good for low-traffic production

**Cons:**
- Single-server limitation
- Manual scaling required

### Option 2: Kubernetes (Production Scale)

**Pros:**
- Auto-scaling
- High availability
- Load balancing
- Rolling updates

**Cons:**
- Complex setup
- Higher operational overhead

### Option 3: Platform-as-a-Service

**Pros:**
- Minimal DevOps
- Quick deployment
- Managed infrastructure

**Cons:**
- Higher cost
- Less control
- Vendor lock-in

## Option 1: Docker Compose Deployment

### Prerequisites

- Ubuntu 22.04 LTS or similar
- Docker 24+ and Docker Compose v2
- 2+ CPU cores, 4GB+ RAM, 20GB+ disk
- Domain name with DNS configured

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Step 2: Clone Repository

```bash
# SSH into server
ssh user@your-server.com

# Clone repo
git clone https://github.com/your-org/hypepaper.git
cd hypepaper

# Switch to production branch
git checkout main
```

### Step 3: Configure Environment

```bash
# Create production environment file
cp .env.example .env
```

**Edit `.env`:**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://hypepaper:STRONG_PASSWORD@postgres:5432/hypepaper
POSTGRES_USER=hypepaper
POSTGRES_PASSWORD=STRONG_PASSWORD
POSTGRES_DB=hypepaper

# API Keys (for higher rate limits)
GITHUB_TOKEN=ghp_yourGitHubPersonalAccessToken
SEMANTIC_SCHOLAR_API_KEY=your_api_key  # Optional

# Backend
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info

# Frontend
VITE_API_BASE_URL=https://api.hypepaper.com

# Job Schedule (UTC times)
DISCOVERY_JOB_SCHEDULE=0 2 * * *   # 2 AM UTC
METRICS_JOB_SCHEDULE=30 2 * * *    # 2:30 AM UTC
MATCHING_JOB_SCHEDULE=0 3 * * *    # 3 AM UTC

# LLM Model (optional, for topic matching)
LLM_MODEL_PATH=/app/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

### Step 4: Create Production Docker Compose

**Create `docker-compose.prod.yml`:**

```yaml
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    container_name: hypepaper-db
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/db/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: hypepaper-backend
    environment:
      DATABASE_URL: ${DATABASE_URL}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      SEMANTIC_SCHOLAR_API_KEY: ${SEMANTIC_SCHOLAR_API_KEY}
      API_HOST: ${API_HOST}
      API_PORT: ${API_PORT}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./backend/logs:/app/logs
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000

  scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: hypepaper-scheduler
    environment:
      DATABASE_URL: ${DATABASE_URL}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      DISCOVERY_JOB_SCHEDULE: ${DISCOVERY_JOB_SCHEDULE}
      METRICS_JOB_SCHEDULE: ${METRICS_JOB_SCHEDULE}
      MATCHING_JOB_SCHEDULE: ${MATCHING_JOB_SCHEDULE}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./backend/logs:/app/logs
    command: python -m src.jobs.scheduler

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        VITE_API_BASE_URL: ${VITE_API_BASE_URL}
    container_name: hypepaper-frontend
    ports:
      - "3000:80"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: hypepaper-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./certbot/www:/var/www/certbot:ro
      - ./certbot/conf:/etc/letsencrypt:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
```

### Step 5: Create Dockerfiles

**Backend Dockerfile (`backend/Dockerfile.prod`):**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create logs directory
RUN mkdir -p logs

# Run migrations on startup
CMD alembic upgrade head && \
    python scripts/seed_topics.py && \
    exec uvicorn src.main:app --host 0.0.0.0 --port 8000
```

**Frontend Dockerfile (`frontend/Dockerfile.prod`):**

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build app
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Production image
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Step 6: Configure Nginx

**Create `nginx/nginx.conf`:**

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:80;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name hypepaper.com www.hypepaper.com;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name hypepaper.com www.hypepaper.com;

        ssl_certificate /etc/letsencrypt/live/hypepaper.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/hypepaper.com/privkey.pem;

        # API backend
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend app
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            try_files $uri $uri/ /index.html;
        }

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Compression
        gzip on;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    }
}
```

### Step 7: SSL Certificate with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot

# Get SSL certificate
sudo certbot certonly --webroot \
    -w ./certbot/www \
    -d hypepaper.com \
    -d www.hypepaper.com \
    --email your@email.com \
    --agree-tos \
    --no-eff-email

# Setup auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Step 8: Deploy

```bash
# Build and start all services
docker compose -f docker-compose.prod.yml up -d --build

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Verify services are running
docker compose -f docker-compose.prod.yml ps
```

### Step 9: Initialize Database

```bash
# Run migrations
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Seed topics
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_topics.py

# Optional: Seed sample data
docker compose -f docker-compose.prod.yml exec backend python scripts/seed_sample_data.py
```

### Step 10: Verify Deployment

```bash
# Check API health
curl https://api.hypepaper.com/health

# Check topics endpoint
curl https://api.hypepaper.com/api/v1/topics

# Visit frontend
open https://hypepaper.com
```

## Monitoring

### Application Logs

```bash
# View backend logs
docker compose logs -f backend

# View scheduler logs
docker compose logs -f scheduler

# View nginx logs
docker compose logs -f nginx
```

### Database Monitoring

```bash
# Connect to database
docker compose exec postgres psql -U hypepaper -d hypepaper

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check active connections
SELECT count(*) FROM pg_stat_activity;
```

### Performance Monitoring

**Install monitoring stack (optional):**

```bash
# Prometheus + Grafana
docker compose -f docker-compose.monitoring.yml up -d
```

## Backup & Recovery

### Database Backup

```bash
# Create backup script (backup.sh)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
docker compose exec postgres pg_dump -U hypepaper hypepaper | gzip > $BACKUP_DIR/hypepaper_$DATE.sql.gz

# Keep last 7 days
find $BACKUP_DIR -name "hypepaper_*.sql.gz" -mtime +7 -delete
```

```bash
# Add to crontab
0 4 * * * /path/to/backup.sh
```

### Database Restore

```bash
# Restore from backup
gunzip < hypepaper_20251002_040000.sql.gz | \
  docker compose exec -T postgres psql -U hypepaper -d hypepaper
```

## Scaling Considerations

### Horizontal Scaling

```yaml
# Add more backend instances
services:
  backend:
    deploy:
      replicas: 3

  # Add load balancer
  nginx:
    # Configure upstream with multiple backends
```

### Vertical Scaling

```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Caching Layer (Redis)

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

## Security Checklist

- [ ] Change default passwords
- [ ] Enable firewall (ufw)
- [ ] Limit SSH access
- [ ] Configure SSL/TLS
- [ ] Set up rate limiting
- [ ] Enable CORS properly
- [ ] Use secrets management
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Set up intrusion detection

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs backend

# Rebuild image
docker compose build --no-cache backend
```

### Database connection issues

```bash
# Check postgres is healthy
docker compose exec postgres pg_isready

# Test connection from backend
docker compose exec backend python -c "from src.database import engine; print('OK')"
```

### High memory usage

```bash
# Check container stats
docker stats

# Adjust resource limits in docker-compose.yml
```

## Maintenance

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Run new migrations
docker compose exec backend alembic upgrade head
```

### Database Maintenance

```bash
# Vacuum database
docker compose exec postgres psql -U hypepaper -d hypepaper -c "VACUUM ANALYZE;"

# Reindex
docker compose exec postgres psql -U hypepaper -d hypepaper -c "REINDEX DATABASE hypepaper;"
```

## Cost Estimation

### Small Deployment (< 1000 users)

- **VPS**: $10-20/month (DigitalOcean, Linode)
- **Domain**: $10/year
- **Total**: ~$15/month

### Medium Deployment (1000-10000 users)

- **VPS**: $40-80/month (4GB RAM, 2 CPU)
- **Managed DB**: $15-30/month (optional)
- **CDN**: $5-10/month
- **Total**: ~$60-120/month

### Large Deployment (10000+ users)

- **Kubernetes Cluster**: $200-500/month
- **Managed DB**: $50-100/month
- **CDN + Cache**: $50-100/month
- **Monitoring**: $20-50/month
- **Total**: ~$320-750/month

## Support

For deployment issues, refer to:
- [Backend README](../backend/README.md)
- [Frontend README](../frontend/README.md)
- [TESTING.md](../TESTING.md)
- GitHub Issues: https://github.com/your-org/hypepaper/issues
