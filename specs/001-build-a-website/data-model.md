# Data Model: Trending Research Papers Tracker

**Phase**: 1 - Design & Contracts
**Date**: 2025-10-01

## Entities

### Paper
Represents a research paper from arXiv or conference venues.

**Fields**:
- `id` (UUID, PK): Internal unique identifier
- `arxiv_id` (string, unique, nullable): arXiv identifier (e.g., "2301.12345")
- `doi` (string, unique, nullable): Digital Object Identifier
- `title` (string, required): Paper title
- `authors` (string[], required): List of author names
- `abstract` (text, required): Paper abstract
- `published_date` (date, required): Publication date
- `venue` (string, nullable): Conference/journal name (e.g., "CVPR 2024", "arXiv")
- `github_url` (string, nullable): Link to GitHub repository
- `arxiv_url` (string, nullable): Link to arXiv page
- `pdf_url` (string, nullable): Link to PDF
- `created_at` (timestamp): Record creation time
- `updated_at` (timestamp): Last update time

**Validation Rules**:
- At least one of `arxiv_id` or `doi` must be present (canonical identifier)
- `title` length: 10-500 characters
- `authors` must have at least 1 entry
- `published_date` cannot be in the future
- URLs must be valid HTTP/HTTPS format

**Indexes**:
- Primary: `id`
- Unique: `arxiv_id`, `doi`
- Search: `title` (full-text), `published_date` (range queries)

### Topic
Represents a research area or domain that users can watch.

**Fields**:
- `id` (UUID, PK): Internal unique identifier
- `name` (string, required, unique): Topic name (e.g., "neural rendering")
- `description` (text, nullable): Optional detailed description
- `keywords` (string[], nullable): Related keywords for matching
- `created_at` (timestamp): Topic creation time

**Validation Rules**:
- `name` length: 3-100 characters
- `name` must be lowercase, alphanumeric + spaces/hyphens
- `keywords` each entry: 2-50 characters

**Indexes**:
- Primary: `id`
- Unique: `name`

**Note**: For MVP, topics are predefined (seeded in database). User-created topics deferred to post-MVP.

### MetricSnapshot
Daily capture of a paper's metrics for trend analysis (TimescaleDB hypertable).

**Fields**:
- `id` (bigint, PK): Auto-increment identifier
- `paper_id` (UUID, FK → Paper.id, required): Reference to paper
- `snapshot_date` (date, required): Date of metric capture
- `github_stars` (integer, nullable): GitHub star count (null if no repo)
- `citation_count` (integer, nullable): Citation count (null if unavailable)
- `created_at` (timestamp): Snapshot creation time

**Validation Rules**:
- `github_stars` >= 0 if present
- `citation_count` >= 0 if present
- `snapshot_date` cannot be in the future
- Unique constraint: (`paper_id`, `snapshot_date`) - one snapshot per paper per day

**Indexes**:
- Primary: `id`
- TimescaleDB: Partition by `snapshot_date` (hypertable)
- Foreign key: `paper_id`
- Composite: (`paper_id`, `snapshot_date`) for efficient time-series queries

**TimescaleDB Configuration**:
- Chunk interval: 30 days
- Compression: Enable after 7 days (compress older snapshots)
- Retention: 30 days minimum (MVP), expand to 1 year post-MVP

### PaperTopicMatch
Junction table linking papers to topics (many-to-many).

**Fields**:
- `id` (UUID, PK): Internal unique identifier
- `paper_id` (UUID, FK → Paper.id, required): Reference to paper
- `topic_id` (UUID, FK → Topic.id, required): Reference to topic
- `relevance_score` (float, required): LLM-generated relevance score (0.0-10.0)
- `matched_at` (timestamp): When match was created
- `matched_by` (enum, required): "llm" or "manual" (for future manual curation)

**Validation Rules**:
- `relevance_score` between 0.0 and 10.0
- Unique constraint: (`paper_id`, `topic_id`) - one match per paper-topic pair
- Only include matches with `relevance_score` >= 6.0 (threshold for "relevant")

**Indexes**:
- Primary: `id`
- Foreign keys: `paper_id`, `topic_id`
- Composite: (`topic_id`, `relevance_score` DESC) for fast topic filtering
- Unique: (`paper_id`, `topic_id`)

### HypeScore (Computed View)
Virtual entity computed from MetricSnapshot data, not stored directly.

**Computed Fields**:
- `paper_id` (UUID): Reference to paper
- `topic_id` (UUID, nullable): Specific topic context (null = global)
- `hype_score` (float): Calculated trending score (0.0-100.0)
- `star_growth_7d` (float): 7-day star growth rate
- `citation_growth_30d` (float): 30-day citation growth rate
- `trend_label` (enum): "rising", "stable", "declining"
- `computed_at` (timestamp): Calculation time

**Calculation Logic**:
```python
# From research.md formula
star_growth_rate_7d = (stars_today - stars_7d_ago) / max(stars_7d_ago, 1)
citation_growth_rate_30d = (citations_today - citations_30d_ago) / max(citations_30d_ago, 1)
absolute_stars_norm = log10(stars_today + 1) / log10(max_stars_in_topic + 1)

days_since_publish = (today - published_date).days
recency_bonus = 1.0 if days_since_publish < 30 else max(0.0, 1.0 - (days_since_publish - 30) / 30)

hype_score = (
    0.4 * star_growth_rate_7d +
    0.3 * citation_growth_rate_30d +
    0.2 * absolute_stars_norm +
    0.1 * recency_bonus
) * 100  # Scale to 0-100

trend_label = "rising" if star_growth_7d > 0.1 else ("declining" if star_growth_7d < -0.05 else "stable")
```

**Implementation**:
- Computed on-demand via backend service (not materialized view for MVP)
- Cache results for 1 hour (acceptable staleness)
- Pre-calculate for top 100 papers per topic daily

## Relationships

```
Paper 1──N MetricSnapshot
  ├─ Daily snapshots track metrics over time
  └─ TimescaleDB optimizes time-series queries

Paper N──N Topic (via PaperTopicMatch)
  ├─ Papers can match multiple topics
  ├─ Topics contain multiple papers
  └─ Relevance score determines match strength

Topic 1──N PaperTopicMatch
  └─ Fast lookup of papers for a topic

MetricSnapshot N──1 Paper
  └─ Query historical metrics for hype score calculation
```

## Database Schema (SQL)

```sql
-- Papers table
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arxiv_id VARCHAR(20) UNIQUE,
    doi VARCHAR(100) UNIQUE,
    title VARCHAR(500) NOT NULL,
    authors TEXT[] NOT NULL,
    abstract TEXT NOT NULL,
    published_date DATE NOT NULL,
    venue VARCHAR(200),
    github_url VARCHAR(500),
    arxiv_url VARCHAR(500),
    pdf_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT at_least_one_id CHECK (arxiv_id IS NOT NULL OR doi IS NOT NULL)
);

CREATE INDEX idx_papers_published_date ON papers(published_date DESC);
CREATE INDEX idx_papers_title_fts ON papers USING gin(to_tsvector('english', title));

-- Topics table
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    keywords TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Metric snapshots (TimescaleDB hypertable)
CREATE TABLE metric_snapshots (
    id BIGSERIAL PRIMARY KEY,
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    github_stars INTEGER CHECK (github_stars >= 0),
    citation_count INTEGER CHECK (citation_count >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(paper_id, snapshot_date)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('metric_snapshots', 'snapshot_date', chunk_time_interval => INTERVAL '30 days');

-- Enable compression after 7 days
ALTER TABLE metric_snapshots SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'paper_id'
);

SELECT add_compression_policy('metric_snapshots', INTERVAL '7 days');

-- Paper-Topic matches
CREATE TABLE paper_topic_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    relevance_score FLOAT NOT NULL CHECK (relevance_score >= 0.0 AND relevance_score <= 10.0),
    matched_at TIMESTAMPTZ DEFAULT NOW(),
    matched_by VARCHAR(20) NOT NULL DEFAULT 'llm',
    UNIQUE(paper_id, topic_id)
);

CREATE INDEX idx_paper_topic_matches_topic ON paper_topic_matches(topic_id, relevance_score DESC);
CREATE INDEX idx_paper_topic_matches_paper ON paper_topic_matches(paper_id);
```

## State Transitions

### Paper Lifecycle
1. **Discovered**: Scraped from arXiv/Papers With Code, basic metadata stored
2. **Matched**: LLM assigns to relevant topics (PaperTopicMatch created)
3. **Tracked**: Daily MetricSnapshot records created
4. **Trending**: HypeScore calculated, appears in topic lists
5. **Archived** (future): Stops receiving daily updates after 1 year of inactivity

### MetricSnapshot Lifecycle
1. **Created**: Daily job fetches current metrics, creates snapshot
2. **Compressed**: After 7 days, TimescaleDB compresses older data
3. **Retained**: Kept for 30 days minimum (MVP), 1 year post-MVP
4. **Archived/Deleted** (future): Old snapshots moved to cold storage

## Data Volume Estimates (MVP)

**Assumptions**:
- 10 topics tracked
- 1,000 papers per topic (with overlap)
- Total unique papers: ~5,000
- 30-day metric retention

**Storage Calculations**:
- Papers: 5,000 × 2 KB = 10 MB
- Topics: 10 × 1 KB = 10 KB
- PaperTopicMatches: 10,000 × 0.1 KB = 1 MB
- MetricSnapshots: 5,000 papers × 30 days × 0.05 KB = 7.5 MB
- **Total**: ~20 MB (negligible, scales linearly)

**Query Performance Targets**:
- Get papers for topic: <100ms (indexed by topic_id)
- Calculate hype score: <200ms (TimescaleDB optimized)
- Full page render: <500ms (API) + <1.5s (frontend) = <2s total

## Validation & Constraints Summary

| Entity | Key Constraints |
|--------|----------------|
| Paper | At least one of arxiv_id/doi; title 10-500 chars; future dates forbidden |
| Topic | Name 3-100 chars, lowercase, unique; keywords 2-50 chars each |
| MetricSnapshot | Unique (paper, date); non-negative metrics; no future dates |
| PaperTopicMatch | Unique (paper, topic); relevance 0-10; threshold >= 6.0 for inclusion |
| HypeScore | Computed only; cached 1 hour; pre-calculated for top 100/topic |

**Status**: ✅ Data model complete, ready for contract generation
