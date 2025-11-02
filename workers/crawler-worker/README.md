# HypePaper Crawler Worker

Cloudflare Worker for processing async crawler jobs using Upstash Redis.

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure secrets:**
   ```bash
   wrangler secret put UPSTASH_REDIS_REST_URL
   wrangler secret put UPSTASH_REDIS_REST_TOKEN
   ```

3. **Deploy:**
   ```bash
   npm run deploy
   ```

## Development

```bash
# Start local development server
npm run dev

# Watch logs from deployed worker
npm run tail
```

## Architecture

```
Backend (Railway)
    ↓ Enqueue job
Upstash Redis Queue
    ↓ Cron trigger (every minute)
Cloudflare Worker
    ↓ Process job
    ↓ Update backend
Backend (Railway)
```

## Job Types

- **arxiv**: Crawl papers from arXiv
- **github**: Crawl repositories from GitHub
- **semantic_scholar**: Crawl papers from Semantic Scholar

## Endpoints

- `GET /health` - Health check
- `GET /status` - Queue statistics
- `POST /submit` - Manual job submission (for testing)

## Environment Variables

- `UPSTASH_REDIS_REST_URL` - Upstash Redis REST API URL
- `UPSTASH_REDIS_REST_TOKEN` - Upstash Redis REST API token
- `BACKEND_API_URL` - Backend API URL (e.g., https://api.hypepaper.app)
- `BACKEND_API_KEY` - Backend API key (optional)

## Monitoring

View logs in real-time:
```bash
npm run tail
```

View metrics in Cloudflare dashboard:
https://dash.cloudflare.com/ → Workers & Pages → hypepaper-crawler-worker
