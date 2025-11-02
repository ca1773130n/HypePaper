import { Redis } from '@upstash/redis/cloudflare';

// Environment interface for TypeScript
export interface Env {
  UPSTASH_REDIS_REST_URL: string;
  UPSTASH_REDIS_REST_TOKEN: string;
  BACKEND_API_URL: string;
  BACKEND_API_KEY?: string;
}

// Job types
export interface CrawlerJob {
  id: string;
  type: 'arxiv' | 'github' | 'semantic_scholar';
  params: {
    query?: string;
    url?: string;
    limit?: number;
    [key: string]: any;
  };
  user_id?: string;
  created_at: string;
  retry_count: number;
}

export interface JobResult {
  job_id: string;
  status: 'success' | 'failed';
  results?: any;
  error?: string;
  processed_at: string;
}

// Process a single crawler job
async function processJob(job: CrawlerJob, env: Env, redis: Redis): Promise<void> {
  console.log(`Processing job ${job.id} of type ${job.type}`);

  try {
    // Update job status to processing
    await redis.setex(
      `crawler:job:${job.id}`,
      3600,
      JSON.stringify({ ...job, status: 'processing', started_at: new Date().toISOString() })
    );

    let results: any;

    // Process based on job type
    switch (job.type) {
      case 'arxiv':
        results = await processArxivJob(job, env);
        break;
      case 'github':
        results = await processGithubJob(job, env);
        break;
      case 'semantic_scholar':
        results = await processSemanticScholarJob(job, env);
        break;
      default:
        throw new Error(`Unknown job type: ${job.type}`);
    }

    // Store results
    const jobResult: JobResult = {
      job_id: job.id,
      status: 'success',
      results,
      processed_at: new Date().toISOString(),
    };

    await redis.setex(`crawler:result:${job.id}`, 86400, JSON.stringify(jobResult));

    // Update backend
    await notifyBackend(jobResult, env);

    console.log(`Job ${job.id} completed successfully`);
  } catch (error) {
    console.error(`Job ${job.id} failed:`, error);

    // Retry logic
    if (job.retry_count < 3) {
      job.retry_count++;
      await redis.rpush('crawler:queue', JSON.stringify(job));
      console.log(`Job ${job.id} requeued for retry ${job.retry_count}`);
    } else {
      // Max retries reached, mark as failed
      const jobResult: JobResult = {
        job_id: job.id,
        status: 'failed',
        error: error instanceof Error ? error.message : String(error),
        processed_at: new Date().toISOString(),
      };

      await redis.setex(`crawler:result:${job.id}`, 86400, JSON.stringify(jobResult));
      await notifyBackend(jobResult, env);
    }
  }
}

// Process arXiv crawler job
async function processArxivJob(job: CrawlerJob, env: Env): Promise<any> {
  const { query, limit = 10 } = job.params;

  if (!query) {
    throw new Error('arXiv job requires query parameter');
  }

  // Call backend API to trigger arXiv crawl
  const response = await fetch(`${env.BACKEND_API_URL}/api/crawlers/arxiv/crawl`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(env.BACKEND_API_KEY && { 'X-API-Key': env.BACKEND_API_KEY }),
    },
    body: JSON.stringify({
      query,
      max_results: limit,
    }),
  });

  if (!response.ok) {
    throw new Error(`Backend API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data;
}

// Process GitHub crawler job
async function processGithubJob(job: CrawlerJob, env: Env): Promise<any> {
  const { url } = job.params;

  if (!url) {
    throw new Error('GitHub job requires url parameter');
  }

  // Call backend API to trigger GitHub crawl
  const response = await fetch(`${env.BACKEND_API_URL}/api/crawlers/github/validate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(env.BACKEND_API_KEY && { 'X-API-Key': env.BACKEND_API_KEY }),
    },
    body: JSON.stringify({
      github_url: url,
    }),
  });

  if (!response.ok) {
    throw new Error(`Backend API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data;
}

// Process Semantic Scholar crawler job
async function processSemanticScholarJob(job: CrawlerJob, env: Env): Promise<any> {
  const { query, limit = 10 } = job.params;

  if (!query) {
    throw new Error('Semantic Scholar job requires query parameter');
  }

  // Call backend API to trigger Semantic Scholar crawl
  const response = await fetch(`${env.BACKEND_API_URL}/api/crawlers/semantic-scholar/crawl`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(env.BACKEND_API_KEY && { 'X-API-Key': env.BACKEND_API_KEY }),
    },
    body: JSON.stringify({
      query,
      limit,
    }),
  });

  if (!response.ok) {
    throw new Error(`Backend API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data;
}

// Notify backend of job completion
async function notifyBackend(result: JobResult, env: Env): Promise<void> {
  try {
    const response = await fetch(`${env.BACKEND_API_URL}/api/jobs/webhook`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(env.BACKEND_API_KEY && { 'X-API-Key': env.BACKEND_API_KEY }),
      },
      body: JSON.stringify(result),
    });

    if (!response.ok) {
      console.warn(`Failed to notify backend: ${response.status}`);
    }
  } catch (error) {
    console.warn('Failed to notify backend:', error);
  }
}

// Cloudflare Worker export
export default {
  // Scheduled event (cron trigger)
  async scheduled(
    controller: ScheduledController,
    env: Env,
    ctx: ExecutionContext
  ): Promise<void> {
    console.log('Cron trigger executed');

    const redis = new Redis({
      url: env.UPSTASH_REDIS_REST_URL,
      token: env.UPSTASH_REDIS_REST_TOKEN,
    });

    // Process up to 10 jobs per execution
    for (let i = 0; i < 10; i++) {
      const jobData = await redis.lpop<CrawlerJob>('crawler:queue');

      if (!jobData) {
        console.log('No more jobs in queue');
        break;
      }

      console.log(`Found job: ${jobData.id}`);

      // Process job asynchronously
      ctx.waitUntil(processJob(jobData, env, redis));
    }
  },

  // HTTP fetch handler
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const redis = new Redis({
      url: env.UPSTASH_REDIS_REST_URL,
      token: env.UPSTASH_REDIS_REST_TOKEN,
    });

    // Health check endpoint
    if (url.pathname === '/health' && request.method === 'GET') {
      return new Response(
        JSON.stringify({
          status: 'healthy',
          timestamp: new Date().toISOString(),
        }),
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Queue status endpoint
    if (url.pathname === '/status' && request.method === 'GET') {
      const queueLength = await redis.llen('crawler:queue');

      return new Response(
        JSON.stringify({
          queue_length: queueLength,
          timestamp: new Date().toISOString(),
        }),
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Manual job submission endpoint (for testing)
    if (url.pathname === '/submit' && request.method === 'POST') {
      try {
        const job = await request.json<CrawlerJob>();

        if (!job.id) {
          job.id = crypto.randomUUID();
        }
        if (!job.created_at) {
          job.created_at = new Date().toISOString();
        }
        if (job.retry_count === undefined) {
          job.retry_count = 0;
        }

        await redis.rpush('crawler:queue', JSON.stringify(job));

        return new Response(
          JSON.stringify({
            success: true,
            job_id: job.id,
            message: 'Job queued successfully',
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      } catch (error) {
        return new Response(
          JSON.stringify({
            success: false,
            error: error instanceof Error ? error.message : 'Invalid request',
          }),
          {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    return new Response('Not Found', { status: 404 });
  },
};
