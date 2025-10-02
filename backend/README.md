# HypePaper Backend

FastAPI backend for tracking trending research papers using GitHub stars and citations.

## Architecture

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 with TimescaleDB extension
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Background Jobs**: APScheduler with AsyncIO

## Project Structure

```
backend/
├── src/
│   ├── models/           # SQLAlchemy models
│   │   ├── paper.py      # Paper model
│   │   ├── topic.py      # Topic model
│   │   └── metrics.py    # MetricSnapshot & PaperTopicMatch models
│   ├── services/         # Business logic layer
│   │   ├── paper_service.py          # Paper CRUD operations
│   │   ├── topic_service.py          # Topic operations
│   │   ├── hype_score_service.py     # Hype score calculation
│   │   ├── metric_service.py         # Metric snapshots
│   │   └── topic_matching_service.py # LLM-based topic matching
│   ├── api/              # FastAPI routes
│   │   ├── main.py       # App initialization
│   │   ├── topics.py     # Topic endpoints
│   │   ├── papers.py     # Paper endpoints
│   │   └── cache.py      # Response caching (1-hour TTL)
│   ├── jobs/             # Background jobs
│   │   ├── discover_papers.py        # Daily arXiv paper discovery
│   │   ├── update_metrics.py         # Daily GitHub/citation updates
│   │   ├── match_topics.py           # Daily topic matching
│   │   ├── scheduler.py              # APScheduler configuration
│   │   ├── arxiv_client.py           # arXiv API client
│   │   ├── github_client.py          # GitHub API client
│   │   ├── semanticscholar_client.py # Semantic Scholar client
│   │   └── paperwithcode_client.py   # Papers With Code client
│   ├── llm/              # LLM integration
│   │   └── topic_matcher.py  # llama.cpp topic matching
│   ├── database.py       # Database connection & session
│   └── config.py         # Configuration settings
├── alembic/              # Database migrations
│   └── versions/
│       ├── 001_initial_schema_with_timescaledb.py
│       └── 002_add_performance_indexes.py
├── scripts/              # Utility scripts
│   ├── seed_topics.py    # Seed predefined topics
│   ├── seed_sample_data.py   # Seed sample papers
│   └── download_llm_model.sh # Download Mistral-7B model
├── tests/
│   ├── unit/             # Unit tests (66 tests, no Docker required)
│   ├── contract/         # API contract tests
│   └── integration/      # Integration tests
├── requirements.txt      # Python dependencies
└── pyproject.toml        # Project metadata & tools (ruff, mypy)
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15 with TimescaleDB extension
- Docker (for database) or local PostgreSQL installation

### Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start database:**
```bash
# Using Docker Compose (recommended)
docker compose up -d

# Or use local PostgreSQL and install TimescaleDB extension
psql -d hypepaper -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

3. **Run migrations:**
```bash
alembic upgrade head
```

4. **Seed database:**
```bash
# Add predefined topics (10 research topics)
python scripts/seed_topics.py

# Add sample papers (optional, for testing)
python scripts/seed_sample_data.py
```

5. **Download LLM model (optional, for topic matching):**
```bash
chmod +x scripts/download_llm_model.sh
./scripts/download_llm_model.sh
```

## Running the Application

### Development Server

```bash
# Start FastAPI development server with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc

### Background Jobs

Background jobs run daily at scheduled times (2 AM, 2:30 AM, 3 AM UTC).

**Start job scheduler:**
```bash
python -m src.jobs.scheduler
```

**Run jobs manually:**
```bash
# Discover new papers from arXiv
python -m src.jobs.discover_papers

# Update GitHub stars and citations
python -m src.jobs.update_metrics

# Match papers to topics
python -m src.jobs.match_topics
```

## API Endpoints

### Topics

- `GET /api/v1/topics` - List all topics
- `GET /api/v1/topics/{topic_id}` - Get topic details

### Papers

- `GET /api/v1/papers` - List papers with filtering & sorting
  - Query params: `topic_id`, `sort` (hype_score, recency, stars), `limit`, `offset`
  - **Cached for 1 hour** to improve performance
- `GET /api/v1/papers/{paper_id}` - Get paper details
- `GET /api/v1/papers/{paper_id}/metrics` - Get historical metrics

## Database Schema

### Core Tables

1. **papers** - Research papers
   - Unique constraints: `arxiv_id`, `doi`
   - Indexes: `published_date`, `arxiv_id`, `doi`

2. **topics** - Research topics
   - Contains: `name`, `description`, `keywords`
   - Index: `name`

3. **metric_snapshots** - Time-series metrics (TimescaleDB hypertable)
   - Partitioned by: `snapshot_date`
   - Compressed after: 7 days
   - Indexes: `snapshot_date`, `(paper_id, snapshot_date)`

4. **paper_topic_matches** - Paper-topic relevance
   - Constraint: `relevance_score >= 6.0` (threshold)
   - Unique: `(paper_id, topic_id)` pair
   - Indexes: `paper_id`, `(topic_id, relevance_score DESC)`

## Hype Score Algorithm

The hype score (0-10 scale) is calculated using:

```
hype_score = (
    0.4 × star_growth_rate +
    0.3 × citation_growth_rate +
    0.2 × absolute_metrics_normalized +
    0.1 × recency_bonus
) × 10
```

**Components:**
- **Star Growth (40%)**: `(current_stars - old_stars) / old_stars`
- **Citation Growth (30%)**: `(current_citations - old_citations) / old_citations`
- **Absolute Metrics (20%)**: Normalized stars + citations (max: 10k stars, 1k citations)
- **Recency Bonus (10%)**: Papers < 30 days get full bonus, decays to 0 at 365 days

See [docs/hype-score-algorithm.md](../docs/hype-score-algorithm.md) for details.

## Testing

### Unit Tests (No Docker Required)

```bash
# Run all unit tests (66 tests)
pytest tests/unit/ -v

# Test specific component
pytest tests/unit/test_hype_score.py -v
```

**Test Coverage:**
- Hype score calculation (11 tests)
- API client logic (14 tests)
- Topic matching (17 tests)
- Background job logic (24 tests)

### Integration Tests (Requires Database)

```bash
# Start database first
docker compose up -d

# Run contract tests (API endpoints)
pytest tests/contract/ -v

# Run integration tests (user scenarios)
pytest tests/integration/ -v
```

### Automated Testing

```bash
# Run comprehensive test suite
./scripts/run_tests.sh
```

## Configuration

Configuration is managed via environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/hypepaper

# API Keys (optional, for higher rate limits)
GITHUB_TOKEN=your_github_token
SEMANTIC_SCHOLAR_API_KEY=your_api_key

# LLM Model Path (for topic matching)
LLM_MODEL_PATH=./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Job Schedule (cron format)
DISCOVERY_JOB_SCHEDULE=0 2 * * *  # 2 AM daily
METRICS_JOB_SCHEDULE=30 2 * * *    # 2:30 AM daily
MATCHING_JOB_SCHEDULE=0 3 * * *    # 3 AM daily
```

## Performance

### Response Times (Target)

- `GET /papers`: < 500ms (with caching: < 50ms)
- `GET /papers/{id}`: < 200ms
- `GET /papers/{id}/metrics`: < 300ms

### Optimization Features

1. **API Response Caching**: 1-hour TTL for hype score calculations
2. **Database Indexes**: Optimized for common query patterns
3. **TimescaleDB Compression**: Automatic compression after 7 days
4. **Connection Pooling**: AsyncPG connection pool

### Scaling Considerations

- **Cache**: Replace in-memory cache with Redis for multi-instance deployments
- **Jobs**: Use Celery for distributed background job processing
- **Database**: Read replicas for separating API queries from job writes

## Development

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy src/
```

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"

# Review generated migration in alembic/versions/
# Edit if needed

# Apply migration
alembic upgrade head
```

### Adding New API Endpoints

1. Define response model in `src/api/{resource}.py`
2. Create route handler with appropriate dependencies
3. Add service layer logic in `src/services/`
4. Write contract tests in `tests/contract/`

## Troubleshooting

### Database Connection Issues

```bash
# Check database is running
docker ps | grep postgres

# Check connection
psql postgresql://user:pass@localhost:5432/hypepaper -c "SELECT 1"

# View logs
docker compose logs postgres
```

### Migration Errors

```bash
# Check current revision
alembic current

# Rollback one revision
alembic downgrade -1

# Re-run migrations
alembic upgrade head
```

### Background Job Failures

```bash
# Check job logs
tail -f logs/scheduler.log

# Test job manually
python -m src.jobs.discover_papers --dry-run
```

## License

MIT
