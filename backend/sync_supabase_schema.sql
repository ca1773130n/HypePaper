-- Sync Supabase schema with current models
-- Run this in Supabase SQL Editor

-- ============================================================
-- PART 1: Add missing columns to existing tables
-- ============================================================

-- Add missing columns to papers table
ALTER TABLE papers ADD COLUMN IF NOT EXISTS legacy_id VARCHAR(100);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS affiliations JSONB;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS affiliations_country VARCHAR(100);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS year INTEGER;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS pages VARCHAR(50);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS paper_type VARCHAR(50);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS session_type VARCHAR(50);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS accept_status VARCHAR(50);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS bibtex TEXT;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS primary_task VARCHAR(200);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS secondary_task VARCHAR(200);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS tertiary_task VARCHAR(200);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS primary_method VARCHAR(200);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS secondary_method VARCHAR(200);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS tertiary_method VARCHAR(200);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS datasets_used JSONB;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS metrics_used JSONB;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS comparisons TEXT;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS limitations TEXT;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS youtube_url VARCHAR(500);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS project_page_url VARCHAR(500);
ALTER TABLE papers ADD COLUMN IF NOT EXISTS github_star_tracking_start_date DATE;
ALTER TABLE papers ADD COLUMN IF NOT EXISTS github_star_tracking_latest_footprint TIMESTAMP;

-- Add missing columns to paper_references
ALTER TABLE paper_references ADD COLUMN IF NOT EXISTS match_score FLOAT;
ALTER TABLE paper_references ADD COLUMN IF NOT EXISTS match_method VARCHAR(50);
ALTER TABLE paper_references ADD COLUMN IF NOT EXISTS reference_text TEXT;
ALTER TABLE paper_references ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP;

-- ============================================================
-- PART 2: Add constraints to existing tables
-- ============================================================

-- Add constraints for paper_references
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'match_score_valid_range'
    ) THEN
        ALTER TABLE paper_references
        ADD CONSTRAINT match_score_valid_range
        CHECK (match_score >= 0 AND match_score <= 100 OR match_score IS NULL);
    END IF;
END $$;

-- ============================================================
-- PART 3: Add indexes to existing tables
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_citations_match_score ON paper_references (match_score DESC);
CREATE INDEX IF NOT EXISTS ix_papers_legacy_id ON papers (legacy_id);
CREATE INDEX IF NOT EXISTS ix_papers_year ON papers (year);
CREATE INDEX IF NOT EXISTS ix_papers_primary_task ON papers (primary_task);

-- ============================================================
-- PART 4: Create new tables
-- ============================================================

-- Authors table
CREATE TABLE IF NOT EXISTS authors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    affiliations JSONB,
    h_index INTEGER,
    citation_count INTEGER,
    paper_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_authors_name ON authors (name);

-- Paper-Author junction table
CREATE TABLE IF NOT EXISTS paper_authors (
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    author_position INTEGER,
    PRIMARY KEY (paper_id, author_id)
);

CREATE INDEX IF NOT EXISTS idx_paper_authors_paper ON paper_authors (paper_id);
CREATE INDEX IF NOT EXISTS idx_paper_authors_author ON paper_authors (author_id);

-- GitHub star snapshots table
CREATE TABLE IF NOT EXISTS github_star_snapshots (
    id SERIAL PRIMARY KEY,
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    star_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_star_snapshots_paper_date ON github_star_snapshots (paper_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_star_snapshots_date ON github_star_snapshots (snapshot_date);

-- PDF contents table
CREATE TABLE IF NOT EXISTS pdf_contents (
    paper_id UUID PRIMARY KEY REFERENCES papers(id) ON DELETE CASCADE,
    full_text TEXT,
    references_section TEXT,
    extracted_at TIMESTAMP DEFAULT NOW()
);

-- LLM extractions table
CREATE TABLE IF NOT EXISTS llm_extractions (
    id SERIAL PRIMARY KEY,
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    extraction_type VARCHAR(50) NOT NULL,
    primary_value TEXT,
    secondary_value TEXT,
    tertiary_value TEXT,
    all_values JSONB,
    llm_provider VARCHAR(50) NOT NULL,
    llm_model VARCHAR(100) NOT NULL,
    prompt_version VARCHAR(20),
    raw_response TEXT,
    verification_status VARCHAR(50) DEFAULT 'pending',
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,
    verification_notes TEXT,
    extracted_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_llm_extractions_paper ON llm_extractions (paper_id);
CREATE INDEX IF NOT EXISTS idx_llm_extractions_type_status ON llm_extractions (extraction_type, verification_status);

-- Admin task logs table
CREATE TABLE IF NOT EXISTS admin_task_logs (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(200) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);

-- ============================================================
-- PART 5: Add comments
-- ============================================================

COMMENT ON TABLE papers IS 'Research papers with metadata';
COMMENT ON TABLE paper_references IS 'Citation relationships between papers';
COMMENT ON COLUMN paper_references.match_score IS 'Similarity score for fuzzy citation matching (0-100)';
COMMENT ON COLUMN paper_references.match_method IS 'Method used for citation matching';
