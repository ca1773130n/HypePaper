# HypePaper Codebase Overview

## Project Purpose
HypePaper is a research paper discovery platform that tracks trending papers using GitHub stars and citations. It combines arXiv papers with GitHub repositories to calculate "hype scores" based on community engagement.

## Technology Stack

### Backend (Python)
- **Framework**: FastAPI (async/await)
- **Database**: PostgreSQL 15 + TimescaleDB extension
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Task Queue**: Celery + Redis
- **Job Scheduling**: APScheduler
- **Auth**: Supabase Auth (Google OAuth)
- **Testing**: pytest, pytest-asyncio

### Frontend (Vue 3)
- **Framework**: Vue 3 + TypeScript + Composition API
- **Build Tool**: Vite
- **Routing**: Vue Router
- **State**: Pinia stores
- **Styling**: TailwindCSS
- **UI Components**: Reka UI, Lucide icons
- **Charts**: Chart.js
- **Testing**: Vitest, Vue Test Utils

### Infrastructure
- **Database**: Supabase PostgreSQL (production)
- **Backend Host**: Railway.app / Render
- **Frontend Host**: Vercel / Cloudflare Pages
- **Cache**: Redis (Upstash)
- **Storage**: File system for PDFs

## Architecture Pattern

### Backend Structure
```
backend/src/
├── models/          # SQLAlchemy ORM models (14 models)
├── services/        # Business logic layer (24 services)
├── api/             # FastAPI routes/endpoints
├── jobs/            # Background jobs (Celery tasks)
├── llm/             # LLM integration (optional topic matching)
├── middleware/      # Request/response middleware
├── utils/           # Helper utilities
├── database.py      # DB connection & session management
├── config.py        # Environment configuration
└── main.py          # FastAPI app initialization
```

### Frontend Structure
```
frontend/src/
├── pages/           # Route pages (7 pages)
├── components/      # Reusable UI (4 components)
├── stores/          # Pinia state stores
├── services/        # API client services
├── router/          # Vue Router config
├── lib/             # Utilities
└── assets/          # Static assets
```

## Core Database Models

1. **Paper** - Research papers from arXiv with metadata
2. **Author** - Paper authors with affiliations and stats
3. **Topic** - Research topics/areas
4. **GitHubMetrics** - GitHub repository metrics (1:1 with Paper)
5. **GitHubStarSnapshot** - Daily star tracking (TimescaleDB hypertable)
6. **CitationSnapshot** - Historical citation counts
7. **MetricSnapshot** - Combined metrics snapshots
8. **PaperTopicMatch** - Paper-topic relevance scores
9. **PaperReference** - Citation relationships
10. **Vote** - User votes on papers
11. **PDFContent** - Extracted PDF text
12. **LLMExtraction** - AI-extracted metadata
13. **CrawlerJob** - Background job tracking
14. **AdminTaskLog** - Admin task execution logs

## Key Services

### Discovery & Enrichment
- `arxiv_service.py` - Fetch papers from arXiv
- `github_service.py` - GitHub API integration
- `github_scraper.py` - Web scraping for GitHub
- `smart_github_detector.py` - Detect GitHub URLs in papers
- `citation_service.py` - Semantic Scholar citations
- `pdf_service.py` - PDF download and parsing
- `author_extractor.py` - Extract author metadata

### Metrics & Scoring
- `hype_score_service.py` - Calculate hype scores
- `metric_service.py` - Manage metric snapshots
- `topic_matching_service.py` - LLM-based topic matching

### Business Logic
- `paper_service.py` - Paper CRUD operations
- `topic_service.py` - Topic management
- `vote_service.py` - User voting
- `cache_service.py` - Redis caching

## Background Jobs

Daily scheduled jobs (APScheduler + Celery):

1. **discover_papers.py** - Fetch new papers from arXiv (2 AM UTC)
2. **update_metrics.py** - Update GitHub stars & citations (2:30 AM)
3. **match_topics.py** - Match papers to topics via LLM (3 AM)
4. **star_tracker.py** - Track GitHub star growth
5. **reference_crawler.py** - Build citation graph
6. **metadata_enricher.py** - Enrich paper metadata

## API Endpoints

### Public
- `GET /api/v1/topics` - List topics
- `GET /api/v1/papers` - List papers (filterable, sortable, cached)
- `GET /api/v1/papers/{id}` - Paper details
- `GET /api/v1/papers/{id}/metrics` - Historical metrics
- `GET /api/v1/authors/{id}` - Author details
- `POST /api/v1/votes` - Vote on paper

### Admin (Protected)
- `POST /api/v1/admin/crawl/arxiv` - Trigger arXiv crawl
- `POST /api/v1/admin/enrich/{id}` - Enrich paper metadata
- `GET /api/v1/admin/tasks` - List task logs

## Hype Score Algorithm

```python
hype_score = (
    0.4 × star_growth_rate +
    0.3 × citation_growth_rate +
    0.2 × absolute_metrics_normalized +
    0.1 × recency_bonus
) × 10  # Scale to 0-10
```

Components:
- **Star Growth (40%)**: Recent GitHub star velocity
- **Citation Growth (30%)**: Citation count growth
- **Absolute Metrics (20%)**: Current stars + citations
- **Recency Bonus (10%)**: Papers <30 days get boost

## Frontend Pages

1. **HomePage** - Browse papers by topic, sort, filter
2. **PaperDetailPage** - Full paper info + metrics chart
3. **LoginPage** - Google OAuth login
4. **ProfilePage** - User profile & settings
5. **AuthCallbackPage** - OAuth redirect handler
6. **CrawlerPage** - Admin crawler interface
7. **AdminDashboard** - Admin task management

## Testing Strategy

### Backend Tests
- **Unit Tests**: 66 tests (no Docker required)
  - Hype score calculation (11 tests)
  - API client logic (14 tests)
  - Topic matching (17 tests)
  - Background jobs (24 tests)
- **Integration Tests**: Database + API tests
- **Contract Tests**: API endpoint validation

### Frontend Tests
- **Unit Tests**: Component logic (Vitest)
- **Component Tests**: Vue Test Utils
- **E2E Tests**: (Planned - Playwright)

## Deployment

### Current Stack
- **Backend**: Railway.app (Nixpacks builder)
- **Frontend**: Vercel
- **Database**: Supabase PostgreSQL
- **Cache**: Upstash Redis
- **Auth**: Supabase Auth

### Environment Variables
Backend: DATABASE_URL, SUPABASE_*, GITHUB_TOKEN, REDIS_URL
Frontend: VITE_API_URL, VITE_SUPABASE_*

## Recent Git Status

Modified files:
- `.claude/settings.json` - Claude Code config
- `.mcp.json` - MCP server config

Untracked:
- `.serena/` - Serena MCP cache
- `backend/arxiv_response.xml`, `backend/debug_arxiv.xml` - Debug files
- `docs/working/` - Temporary docs
- `frontend/.vite/` - Vite cache

## Key Features

1. **Topic-Based Discovery** - Filter papers by research area
2. **Hype Score Ranking** - Sort by community engagement
3. **GitHub Integration** - Track repository stars & activity
4. **Citation Tracking** - Monitor academic impact
5. **Historical Metrics** - Time-series visualization
6. **User Voting** - Community curation
7. **Author Profiles** - Track researcher output
8. **PDF Content** - Extract and search paper text
9. **LLM Metadata** - AI-extracted insights
10. **Background Crawlers** - Automated data collection

## Performance Optimizations

1. **API Caching** - 1-hour TTL for expensive queries
2. **TimescaleDB** - Efficient time-series storage
3. **Database Indexes** - Optimized query patterns
4. **Connection Pooling** - AsyncPG pools
5. **Code Splitting** - Lazy-loaded Vue components
6. **CDN Delivery** - Static assets via Vercel Edge

## Known Issues & TODOs

1. LLM topic matching is optional (requires local llama.cpp)
2. PDF storage needs S3/R2 for production scaling
3. Rate limiting not yet implemented
4. Full-text search needs Elasticsearch/Typesense
5. Real-time updates need WebSocket support
