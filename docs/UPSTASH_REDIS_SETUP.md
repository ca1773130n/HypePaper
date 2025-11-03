# 📦 Upstash Redis Setup for Async Crawler Jobs

This guide explains how to set up Upstash Redis for the async crawler job system.

## The Problem

When users create custom topics and click the crawler button, the system needs to queue background jobs for crawling papers. The error "name or service not known" occurs when the required Upstash Redis configuration is missing.

## What is Upstash Redis?

[Upstash](https://upstash.com/) is a serverless Redis platform that provides:
- ✅ **Serverless**: Pay only for what you use
- ✅ **Free Tier**: 10,000 requests/day
- ✅ **REST API**: Works with Cloudflare Workers and serverless functions
- ✅ **Global**: Low-latency worldwide
- ✅ **No Connection Limits**: Perfect for serverless deployments

## Why Upstash for HypePaper?

The async crawler system uses Upstash Redis because:
1. **Cloudflare Workers Integration**: The crawler runs on Cloudflare Workers, which need REST-based Redis
2. **Railway Compatibility**: Works perfectly with Railway's serverless nature
3. **Cost-Effective**: Free tier is sufficient for most use cases
4. **Reliable Queue**: Redis lists provide a reliable FIFO job queue

## Setup Instructions

### Step 1: Create Upstash Account

1. Go to https://upstash.com/
2. Sign up with GitHub or email
3. Verify your email address

### Step 2: Create Redis Database

1. Click **Create Database** in the Upstash Console
2. Configure your database:
   - **Name**: `hypepaper-jobs` (or any name you prefer)
   - **Type**: **Regional** (faster, recommended for single region)
   - **Region**: Choose closest to your Railway deployment
     - For US deployment: `us-east-1` or `us-west-1`
     - For EU deployment: `eu-west-1`
     - For Asia deployment: `ap-northeast-1` (Seoul)
   - **Eviction**: **No eviction** (we need job data to persist)
   - **TLS**: **Enabled** (recommended for security)

3. Click **Create**

### Step 3: Get REST API Credentials

After creating the database:

1. Go to your database dashboard
2. Click on **REST API** tab
3. Copy these values:
   - **UPSTASH_REDIS_REST_URL**: `https://your-database.upstash.io`
   - **UPSTASH_REDIS_REST_TOKEN**: `AXXXxxxxXXXXxxxxx`

### Step 4: Configure Railway

1. Go to your Railway project
2. Click on your service (backend)
3. Go to **Variables** tab
4. Add these environment variables:

```bash
UPSTASH_REDIS_REST_URL=https://your-database-name.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token-here
```

5. Click **Deploy** or wait for auto-redeploy

### Step 5: Verify Configuration

Test the crawler feature:

1. Visit your app (production or preview)
2. Sign in with Google OAuth
3. Go to Profile page
4. Create a custom topic with keywords
5. Return to home page
6. Select your custom topic from dropdown
7. Click the **Crawler** button
8. Should see: "Crawler job queued successfully!"

Check Railway logs for confirmation:
```
Job queue service initialized
Job queued: arxiv with query: your-keywords
```

## Local Development Setup

For local development, you have two options:

### Option A: Use Upstash (Recommended)

Use the same Upstash credentials locally:

```bash
# backend/.env
UPSTASH_REDIS_REST_URL=https://your-database-name.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token-here
```

### Option B: Use Local Redis

If you prefer local Redis for development:

1. Install Redis locally:
   ```bash
   # macOS
   brew install redis
   brew services start redis

   # Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis

   # Windows
   # Download from https://github.com/tporadowski/redis/releases
   ```

2. Create a wrapper service that uses local Redis instead of Upstash REST API

3. Set environment variable:
   ```bash
   USE_LOCAL_REDIS=true
   REDIS_URL=redis://localhost:6379/1
   ```

**Note**: The current implementation uses Upstash's REST API, so local Redis would require code modifications. It's recommended to use Upstash for both development and production for consistency.

## Understanding the Job Queue

### How It Works

1. **Job Creation**: User clicks crawler button → API creates job
2. **Queue**: Job added to Redis list (`crawler:queue`)
3. **Worker**: Cloudflare Worker polls queue every minute
4. **Processing**: Worker fetches papers from ArXiv/GitHub/SemanticScholar
5. **Results**: Stored in Redis (`crawler:result:{job_id}`)
6. **Retrieval**: Frontend polls status endpoint to get results

### Redis Keys Structure

```bash
# Job queue (FIFO list)
crawler:queue

# Job metadata (1 hour TTL)
crawler:job:{job_id}

# Job results (24 hour TTL)
crawler:result:{job_id}

# Job status tracking
crawler:status:{job_id}
```

### Job Lifecycle

```
QUEUED → PROCESSING → SUCCESS/FAILED
  ↓          ↓            ↓
  1min     varies      24h TTL
```

## Monitoring Jobs

### Check Queue Length

```bash
curl https://api.hypepaper.app/api/async-jobs/queue/stats
```

Response:
```json
{
  "queue_length": 3,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Check Job Status

```bash
curl https://api.hypepaper.app/api/async-jobs/status/{job_id}
```

Response:
```json
{
  "id": "uuid-here",
  "status": "success",
  "created_at": "2025-01-15T10:25:00Z",
  "processed_at": "2025-01-15T10:26:30Z"
}
```

### Get Job Results

```bash
curl https://api.hypepaper.app/api/async-jobs/result/{job_id}
```

Response:
```json
{
  "job_id": "uuid-here",
  "status": "success",
  "results": {
    "papers": [...],
    "count": 15
  },
  "processed_at": "2025-01-15T10:26:30Z"
}
```

### View Upstash Console

1. Go to Upstash Dashboard
2. Select your database
3. Click **Data Browser** tab
4. View real-time data:
   - See queued jobs
   - Monitor processing status
   - Check job results

## Cost Estimation

Upstash Redis pricing is based on requests:

### Free Tier
- **10,000 requests/day**
- **256 MB storage**
- **TLS encryption**

For HypePaper usage:
- Each crawler job: ~5-10 requests (queue, status checks, result storage)
- **~1,000 crawler jobs/day** fits within free tier
- For most users, this is more than enough

### Paid Tiers (if needed)

- **Pay-as-you-go**: $0.20 per 100,000 requests
- **Pro**: $10/month for 1M requests + dedicated resources

For a typical research app with moderate usage, the free tier should be sufficient.

## Troubleshooting

### Error: "name or service not known"

**Cause**: Upstash Redis environment variables not set or incorrect.

**Solution**:
1. Verify environment variables in Railway:
   ```bash
   UPSTASH_REDIS_REST_URL=https://...
   UPSTASH_REDIS_REST_TOKEN=...
   ```
2. Check for typos in the URL
3. Ensure no extra spaces or quotes
4. Redeploy after setting variables

### Error: "Invalid token"

**Cause**: Wrong REST token or token expired.

**Solution**:
1. Go to Upstash Console → Your Database → REST API
2. Copy the **current** token (regenerate if needed)
3. Update Railway environment variable
4. Redeploy

### Jobs Not Processing

**Cause**: Cloudflare Worker not running or can't connect to Upstash.

**Solution**:
1. Check Cloudflare Workers dashboard
2. Verify worker is deployed and running
3. Check worker logs for errors
4. Ensure worker has same Upstash credentials

### Queue Growing Without Processing

**Cause**: Worker not processing jobs fast enough or encountering errors.

**Solution**:
1. Check Upstash Console → Data Browser
2. Manually inspect failed jobs
3. Check worker error logs
4. Consider scaling worker (increase frequency)

### Results Not Appearing

**Cause**: Job completed but results TTL expired (24 hours).

**Solution**:
1. Check job was completed within last 24 hours
2. Increase TTL in `JobQueueService` if needed
3. Store important results in main database, not just Redis

## Advanced Configuration

### Adjust Queue Processing

Edit `backend/src/services/job_queue_service.py`:

```python
# Increase TTL for job results (default: 1 hour for metadata, 24 hours for results)
self.redis.setex(
    f"crawler:result:{job_id}",
    86400 * 7,  # 7 days instead of 24 hours
    json.dumps(result_data),
)
```

### Add Job Priority

```python
# High priority jobs go to front of queue (LPUSH instead of RPUSH)
if priority == "high":
    self.redis.lpush("crawler:queue", json.dumps(job_data))
else:
    self.redis.rpush("crawler:queue", json.dumps(job_data))
```

### Monitor Queue Metrics

```python
async def get_detailed_stats(self) -> Dict[str, Any]:
    """Get detailed queue statistics."""
    queue_length = await self.get_queue_length()

    # Get all job keys
    job_keys = self.redis.keys("crawler:job:*")

    # Count by status
    statuses = {}
    for key in job_keys:
        job_data = json.loads(self.redis.get(key))
        status = job_data.get("status", "unknown")
        statuses[status] = statuses.get(status, 0) + 1

    return {
        "queue_length": queue_length,
        "total_jobs": len(job_keys),
        "by_status": statuses,
        "timestamp": datetime.utcnow().isoformat(),
    }
```

## Alternative: Redis Cloud

If you prefer a different provider:

### Redis Labs Cloud
- Website: https://redis.com/try-free/
- Free tier: 30 MB
- Pros: Industry standard, reliable
- Cons: Smaller free tier, connection-based (not REST)

### Vercel KV (powered by Upstash)
- Website: https://vercel.com/docs/storage/vercel-kv
- Free tier: 256 MB, 10K requests/day
- Pros: Integrated with Vercel deployments
- Cons: Requires Vercel account

### AWS ElastiCache
- Website: https://aws.amazon.com/elasticache/
- Free tier: 750 hours/month (1 year)
- Pros: AWS integration, powerful
- Cons: Complex setup, requires VPC

**Recommendation**: Stick with Upstash for simplicity and serverless compatibility.

## Summary

✅ **Sign up**: https://upstash.com/
✅ **Create database**: Regional, no eviction, TLS enabled
✅ **Get credentials**: REST API tab in Upstash Console
✅ **Add to Railway**: `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`
✅ **Test crawler**: Create custom topic → click crawler button
✅ **Monitor**: Use Upstash Console → Data Browser

With Upstash Redis configured, your async crawler jobs will work perfectly! 🚀
