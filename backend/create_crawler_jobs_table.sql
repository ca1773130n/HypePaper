-- Create crawler_jobs table for persistent job tracking
CREATE TABLE IF NOT EXISTS crawler_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    keywords TEXT,
    reference_depth INTEGER NOT NULL DEFAULT 1,
    period VARCHAR(20),
    papers_crawled INTEGER NOT NULL DEFAULT 0,
    references_crawled INTEGER NOT NULL DEFAULT 0,
    logs JSONB NOT NULL DEFAULT '[]'::jsonb,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create index on job_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_crawler_jobs_job_id ON crawler_jobs(job_id);

-- Create index on status for filtering
CREATE INDEX IF NOT EXISTS idx_crawler_jobs_status ON crawler_jobs(status);

-- Create index on next_run for periodic job scheduling
CREATE INDEX IF NOT EXISTS idx_crawler_jobs_next_run ON crawler_jobs(next_run) WHERE next_run IS NOT NULL;

-- Add project_page_url column to papers table
ALTER TABLE papers ADD COLUMN IF NOT EXISTS project_page_url VARCHAR(500);

-- Add youtube_url column if not exists (already exists from earlier migration)
ALTER TABLE papers ADD COLUMN IF NOT EXISTS youtube_url VARCHAR(500);
