-- Add citation tracking columns and tables

-- Add citation_count column to papers table
ALTER TABLE papers ADD COLUMN IF NOT EXISTS citation_count INTEGER DEFAULT 0;

-- Create citation_snapshots table for historical tracking
CREATE TABLE IF NOT EXISTS citation_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    citation_count INTEGER NOT NULL,
    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,
    source VARCHAR(50) NOT NULL DEFAULT 'google_scholar', -- google_scholar, semantic_scholar, etc.
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_paper_citation_snapshot UNIQUE (paper_id, snapshot_date, source)
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_citation_snapshots_paper_id ON citation_snapshots(paper_id);
CREATE INDEX IF NOT EXISTS idx_citation_snapshots_date ON citation_snapshots(snapshot_date DESC);

-- Make sure all the URL columns exist in papers table
ALTER TABLE papers ADD COLUMN IF NOT EXISTS project_page_url VARCHAR(500);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS youtube_url VARCHAR(500);

COMMENT ON COLUMN papers.citation_count IS 'Latest citation count from Google Scholar or other sources';
COMMENT ON TABLE citation_snapshots IS 'Historical citation counts for tracking paper citation growth over time';
