# Cloudflare Workers + Upstash Redis Setup for Async Jobs

## Overview

This guide sets up Cloudflare Workers with Upstash Redis for running async crawler jobs.

**Architecture:**
- **Backend (Railway):** Creates jobs, stores in Upstash Redis queue
- **Cloudflare Workers:** Consumes jobs from queue, runs crawlers
- **Upstash Redis:** Job queue and cache (serverless, globally distributed)

## Step 1: Create Upstash Redis Database (2 minutes)

### 1.1 Sign Up / Login to Upstash
https://console.upstash.com/

### 1.2 Create Redis Database
1. Click **Create Database**
2. **Name:** `hypepaper-jobs`
3. **Type:** Choose **Regional** (faster) or **Global** (better availability)
   - **Recommended:** Regional in same region as your backend
4. **Primary Region:** Choose closest to your users
   - US East (N. Virginia) - `us-east-1`
   - EU (Ireland) - `eu-west-1`
   - Asia Pacific (Tokyo) - `ap-northeast-1`
5. **TLS:** Enable (recommended)
6. Click **Create**

### 1.3 Copy Redis Credentials

After creation, you'll see:
```
UPSTASH_REDIS_REST_URL=https://apn1-magical-name-12345.upstash.io
UPSTASH_REDIS_REST_TOKEN=AbCdEf123456...
```

**Save these!** You'll need them in Step 3.

## Step 2: Install Wrangler CLI (Cloudflare Workers CLI)

```bash
# Install globally
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Verify login
wrangler whoami
```

## Step 3: Create Cloudflare Worker Project

```bash
# Create worker directory
mkdir -p workers/crawler-worker
cd workers/crawler-worker

# Initialize Wrangler project
wrangler init

# Answer prompts:
# - Would you like to use TypeScript? Yes
# - Would you like to create a Worker at src/index.ts? Yes
# - Would you like us to write your first test with Vitest? Yes (optional)
```

## Step 4: Configure Worker

### 4.1 Update `wrangler.toml`

```toml
name = "hypepaper-crawler-worker"
main = "src/index.ts"
compatibility_date = "2024-01-01"

# Environment variables (add after creating secrets)
[vars]
BACKEND_API_URL = "https://api.hypepaper.app"

# Upstash Redis binding
[[unsafe.bindings]]
name = "UPSTASH_REDIS_REST_URL"
type = "secret"

[[unsafe.bindings]]
name = "UPSTASH_REDIS_REST_TOKEN"
type = "secret"

# Cron trigger - check for jobs every minute
[triggers]
crons = ["* * * * *"]

# Resource limits
[limits]
cpu_ms = 50000  # 50 seconds max execution time
```

### 4.2 Add Secrets to Cloudflare

```bash
# Add Upstash credentials as secrets
wrangler secret put UPSTASH_REDIS_REST_URL
# Paste: https://apn1-magical-name-12345.upstash.io

wrangler secret put UPSTASH_REDIS_REST_TOKEN
# Paste: AbCdEf123456...

# Add backend API key (if needed for authentication)
wrangler secret put BACKEND_API_KEY
# Paste: your_backend_api_key
```

## Step 5: Install Dependencies

```bash
cd workers/crawler-worker

# Install Upstash Redis SDK
npm install @upstash/redis

# Install other dependencies
npm install @types/node --save-dev
```

## Step 6: Create Worker Code

### 6.1 Create Job Processor

Create `workers/crawler-worker/src/index.ts`:

```typescript
import { Redis } from '@upstash/redis/cloudflare';

// Job types
interface CrawlerJob {
  id: string;
  type: 'arxiv' | 'github' | 'semantic_scholar';
  params: {
    query?: string;
    url?: string;
    limit?: number;
  };
  created_at: string;
  retry_count: number;
}

interface Env {
  UPSTASH_REDIS_REST_URL: string;
  UPSTASH_REDIS_REST_TOKEN: string;
  BACKEND_API_URL: string;
  BACKEND_API_KEY?: string;
}

export default {
  // Cron trigger - runs every minute
  async scheduled(
    controller: ScheduledController,
    env: Env,
    ctx: ExecutionContext
  ): Promise<void> {
    const redis = new Redis({
      url: env.UPSTASH_REDIS_REST_URL,
      token: env.UPSTASH_REDIS_REST_TOKEN,
    });

    console.log('Checking for pending crawler jobs...');

    // Process up to 10 jobs per execution
    for (let i = 0; i < 10; i++) {
      // Pop job from queue (FIFO)
      const jobData = await redis.lpop<CrawlerJob>('crawler:queue');

      if (!jobData) {
        console.log('No more jobs in queue');
        break;
      }

      console.log(`Processing job ${jobData.id}`, jobData);

      // Process job asynchronously
      ctx.waitUntil(processJob(jobData, env, redis));
    }
  },

  // HTTP endpoint for manual job submission
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext
  ): Promise<Response> {
    const redis = new Redis({
      url: env.UPSTASH_REDIS_REST_URL,
      token: env.UPSTASH_REDIS_REST_TOKEN,
    });

    const url = new URL(request.url);

    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok' }), {
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Get queue status
    if (url.pathname === '/status') {
      const queueLength = await redis.llen('crawler:queue');
      const processing = await redis.scard('crawler:processing');

      return new Response(
        JSON.stringify({
          queue_length: queueLength,
          processing_count: processing,
        }),
        { headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Submit job manually
    if (url.pathname === '/submit' && request.method === 'POST') {
      const job: CrawlerJob = await request.json();

      // Add to queue
      await redis.rpush('crawler:queue', job);

      return new Response(
        JSON.stringify({ message: 'Job queued', job_id: job.id }),
        { headers: { 'Content-Type': 'application/json' } }
      );
    }

    return new Response('Not found', { status: 404 });
  },
};

// Process a single crawler job
async function processJob(
  job: CrawlerJob,
  env: Env,
  redis: Redis
): Promise<void> {
  try {
    // Mark as processing
    await redis.sadd('crawler:processing', job.id);
    await redis.setex(`crawler:job:${job.id}`, 3600, JSON.stringify({ ...job, status: 'processing' }));

    console.log(`Starting ${job.type} crawler for job ${job.id}`);

    // Call appropriate crawler
    let result;
    switch (job.type) {
      case 'arxiv':
        result = await crawlArxiv(job.params, env);
        break;
      case 'github':
        result = await crawlGitHub(job.params, env);
        break;
      case 'semantic_scholar':
        result = await crawlSemanticScholar(job.params, env);
        break;
      default:
        throw new Error(`Unknown job type: ${job.type}`);
    }

    // Update backend with results
    await updateBackend(job.id, result, env);

    // Mark as completed
    await redis.srem('crawler:processing', job.id);
    await redis.setex(`crawler:job:${job.id}`, 86400, JSON.stringify({
      ...job,
      status: 'completed',
      result,
      completed_at: new Date().toISOString()
    }));

    console.log(`Job ${job.id} completed successfully`);

  } catch (error) {
    console.error(`Job ${job.id} failed:`, error);

    // Handle retry
    if (job.retry_count < 3) {
      job.retry_count++;
      console.log(`Retrying job ${job.id} (attempt ${job.retry_count})`);

      // Re-queue with delay
      await redis.rpush('crawler:queue', job);
    } else {
      console.error(`Job ${job.id} failed after 3 retries`);

      // Mark as failed
      await redis.srem('crawler:processing', job.id);
      await redis.setex(`crawler:job:${job.id}`, 86400, JSON.stringify({
        ...job,
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unknown error',
        failed_at: new Date().toISOString()
      }));

      // Notify backend of failure
      await notifyBackendOfFailure(job.id, error, env);
    }
  }
}

// Crawler implementations
async function crawlArxiv(params: any, env: Env): Promise<any> {
  const { query, limit = 10 } = params;

  console.log(`Crawling arXiv: ${query}`);

  // Make request to arXiv API
  const response = await fetch(
    `http://export.arxiv.org/api/query?search_query=${encodeURIComponent(query)}&max_results=${limit}`
  );

  if (!response.ok) {
    throw new Error(`arXiv API error: ${response.status}`);
  }

  const xml = await response.text();

  // Parse XML and extract papers (simplified)
  const papers = parseArxivXML(xml);

  return { papers, count: papers.length };
}

async function crawlGitHub(params: any, env: Env): Promise<any> {
  const { query } = params;

  console.log(`Crawling GitHub: ${query}`);

  // Use GitHub API to search repositories
  const response = await fetch(
    `https://api.github.com/search/repositories?q=${encodeURIComponent(query)}`,
    {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'HypePaper-Crawler'
      }
    }
  );

  if (!response.ok) {
    throw new Error(`GitHub API error: ${response.status}`);
  }

  const data = await response.json();

  return { repositories: data.items, count: data.items.length };
}

async function crawlSemanticScholar(params: any, env: Env): Promise<any> {
  const { query, limit = 10 } = params;

  console.log(`Crawling Semantic Scholar: ${query}`);

  const response = await fetch(
    `https://api.semanticscholar.org/graph/v1/paper/search?query=${encodeURIComponent(query)}&limit=${limit}`
  );

  if (!response.ok) {
    throw new Error(`Semantic Scholar API error: ${response.status}`);
  }

  const data = await response.json();

  return { papers: data.data, count: data.data.length };
}

// Helper: Update backend with results
async function updateBackend(jobId: string, result: any, env: Env): Promise<void> {
  const response = await fetch(
    `${env.BACKEND_API_URL}/api/v1/jobs/${jobId}/complete`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(env.BACKEND_API_KEY && { 'X-API-Key': env.BACKEND_API_KEY })
      },
      body: JSON.stringify({ result })
    }
  );

  if (!response.ok) {
    console.error(`Failed to update backend for job ${jobId}: ${response.status}`);
  }
}

// Helper: Notify backend of failure
async function notifyBackendOfFailure(jobId: string, error: any, env: Env): Promise<void> {
  await fetch(
    `${env.BACKEND_API_URL}/api/v1/jobs/${jobId}/fail`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(env.BACKEND_API_KEY && { 'X-API-Key': env.BACKEND_API_KEY })
      },
      body: JSON.stringify({
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  );
}

// Helper: Parse arXiv XML (simplified)
function parseArxivXML(xml: string): any[] {
  // This is a simplified parser - you may want to use a proper XML parser
  const papers: any[] = [];

  // Extract entries using regex (basic implementation)
  const entryRegex = /<entry>([\s\S]*?)<\/entry>/g;
  let match;

  while ((match = entryRegex.exec(xml)) !== null) {
    const entry = match[1];

    // Extract title
    const titleMatch = /<title>(.*?)<\/title>/.exec(entry);
    const title = titleMatch ? titleMatch[1].trim() : '';

    // Extract summary
    const summaryMatch = /<summary>(.*?)<\/summary>/.exec(entry);
    const summary = summaryMatch ? summaryMatch[1].trim() : '';

    // Extract arXiv ID
    const idMatch = /<id>.*?\/abs\/(.*?)<\/id>/.exec(entry);
    const arxivId = idMatch ? idMatch[1] : '';

    papers.push({ title, summary, arxiv_id: arxivId });
  }

  return papers;
}
```

## Step 7: Deploy Worker

```bash
cd workers/crawler-worker

# Deploy to Cloudflare
wrangler deploy

# You'll get a URL like:
# https://hypepaper-crawler-worker.your-subdomain.workers.dev
```

## Step 8: Update Backend to Use Upstash

### 8.1 Install Upstash in Backend

```bash
cd backend
pip install upstash-redis
```

Add to `backend/requirements.txt` and `backend/requirements.prod.txt`:
```
upstash-redis==0.15.0
```

### 8.2 Create Job Service

Create `backend/src/services/job_queue_service.py`:

```python
"""Job queue service using Upstash Redis."""
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from upstash_redis import Redis


class JobQueueService:
    """Service for managing async job queue with Upstash Redis."""

    def __init__(self):
        """Initialize Upstash Redis client."""
        self.redis = Redis(
            url=os.getenv("UPSTASH_REDIS_REST_URL"),
            token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
        )

    async def enqueue_crawler_job(
        self,
        job_type: str,
        params: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> str:
        """Enqueue a crawler job.

        Args:
            job_type: Type of crawler (arxiv, github, semantic_scholar)
            params: Job parameters (query, url, limit, etc.)
            user_id: Optional user ID

        Returns:
            Job ID
        """
        job_id = str(uuid4())

        job_data = {
            "id": job_id,
            "type": job_type,
            "params": params,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "retry_count": 0,
        }

        # Add to queue
        self.redis.rpush("crawler:queue", json.dumps(job_data))

        # Store job metadata
        self.redis.setex(
            f"crawler:job:{job_id}",
            3600,  # 1 hour TTL
            json.dumps({**job_data, "status": "queued"}),
        )

        return job_id

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status.

        Args:
            job_id: Job ID

        Returns:
            Job data with status
        """
        data = self.redis.get(f"crawler:job:{job_id}")

        if data:
            return json.loads(data)

        return None

    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics.

        Returns:
            Dict with queue_length and processing_count
        """
        queue_length = self.redis.llen("crawler:queue")
        processing_count = self.redis.scard("crawler:processing")

        return {
            "queue_length": queue_length,
            "processing_count": processing_count,
        }
```

### 8.3 Create Job API Endpoint

Create `backend/src/api/v1/crawler_jobs.py`:

```python
"""API endpoints for crawler jobs."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...services.job_queue_service import JobQueueService
from ..dependencies import get_current_user

router = APIRouter(prefix="/crawler-jobs", tags=["Crawler Jobs"])


class CrawlerJobRequest(BaseModel):
    """Crawler job request."""

    type: str  # arxiv, github, semantic_scholar
    query: str
    limit: int = 10


class CrawlerJobResponse(BaseModel):
    """Crawler job response."""

    job_id: str
    status: str
    message: str


@router.post("/submit", response_model=CrawlerJobResponse)
async def submit_crawler_job(
    request: CrawlerJobRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a new crawler job.

    Requires authentication. Job will be processed by Cloudflare Worker.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Enqueue job
    job_service = JobQueueService()
    job_id = await job_service.enqueue_crawler_job(
        job_type=request.type,
        params={"query": request.query, "limit": request.limit},
        user_id=current_user["id"],
    )

    return CrawlerJobResponse(
        job_id=job_id,
        status="queued",
        message="Job submitted successfully",
    )


@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get job status.

    Requires authentication.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    job_service = JobQueueService()
    job_data = await job_service.get_job_status(job_id)

    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return job_data


@router.get("/stats")
async def get_queue_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get queue statistics.

    Requires authentication.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    job_service = JobQueueService()
    stats = await job_service.get_queue_stats()

    return stats
```

### 8.4 Register Router in Main App

Add to `backend/src/main.py`:

```python
from .api.v1 import crawler_jobs

# Add with other routers
app.include_router(crawler_jobs.router, prefix="/api/v1")
```

## Step 9: Add Environment Variables

### 9.1 Railway (Backend)

Add these secrets to Railway:

```bash
UPSTASH_REDIS_REST_URL=https://apn1-magical-name-12345.upstash.io
UPSTASH_REDIS_REST_TOKEN=AbCdEf123456...
```

### 9.2 Cloudflare Workers

Already added in Step 4.2

## Step 10: Test the Setup

### 10.1 Test Backend Job Submission

```bash
# Get your JWT token
TOKEN="your_jwt_token"

# Submit crawler job
curl -X POST https://api.hypepaper.app/api/v1/crawler-jobs/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "arxiv",
    "query": "machine learning",
    "limit": 5
  }'

# Response:
# {
#   "job_id": "abc-123-def",
#   "status": "queued",
#   "message": "Job submitted successfully"
# }
```

### 10.2 Check Job Status

```bash
JOB_ID="abc-123-def"

curl https://api.hypepaper.app/api/v1/crawler-jobs/${JOB_ID}/status \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "id": "abc-123-def",
#   "type": "arxiv",
#   "status": "processing",  # or "completed"
#   "created_at": "2025-11-01T10:00:00",
#   ...
# }
```

### 10.3 Check Queue Stats

```bash
curl https://api.hypepaper.app/api/v1/crawler-jobs/stats \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "queue_length": 5,
#   "processing_count": 2
# }
```

### 10.4 Test Worker Directly

```bash
# Check worker health
curl https://hypepaper-crawler-worker.your-subdomain.workers.dev/health

# Check queue status
curl https://hypepaper-crawler-worker.your-subdomain.workers.dev/status
```

## Monitoring and Debugging

### View Worker Logs

```bash
wrangler tail
```

### Check Upstash Dashboard

https://console.upstash.com/redis/{your-database-id}

- Monitor queue length
- View Redis commands
- Check memory usage

### View Cloudflare Dashboard

https://dash.cloudflare.com/ → Workers & Pages → hypepaper-crawler-worker

- View metrics
- Check error rates
- Monitor invocations

## Cost Estimation

### Upstash Redis
- **Free Tier:** 10,000 commands/day
- **Pay-as-you-go:** $0.2 per 100K commands
- **Typical usage:** ~1M commands/month = $2/month

### Cloudflare Workers
- **Free Tier:** 100,000 requests/day
- **Paid plan:** $5/month for 10M requests
- **Cron triggers:** Free (included in requests)

**Total estimated cost:** $2-7/month for moderate usage

## Next Steps

1. ✅ Set up Upstash Redis
2. ✅ Deploy Cloudflare Worker
3. ✅ Update backend with job queue
4. ⏭️ Test job submission and processing
5. ⏭️ Add error handling and monitoring
6. ⏭️ Implement result webhooks
7. ⏭️ Add job cancellation support

## Troubleshooting

### Worker not processing jobs
- Check cron trigger is enabled
- Verify Upstash credentials are correct
- Check worker logs: `wrangler tail`

### Jobs stuck in queue
- Check worker is deployed and running
- Verify Redis connection in Upstash dashboard
- Check Cloudflare Workers dashboard for errors

### Backend can't connect to Upstash
- Verify environment variables in Railway
- Check Upstash REST API URL format
- Test connection with `upstash-redis` CLI

## References

- Upstash Docs: https://docs.upstash.com/redis
- Cloudflare Workers: https://developers.cloudflare.com/workers/
- Wrangler CLI: https://developers.cloudflare.com/workers/wrangler/
