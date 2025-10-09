# Technical Research: SOTAPapers Legacy Integration

**Date**: 2025-10-08
**Feature**: 002-convert-the-integration
**Status**: Complete

## Research Questions & Decisions

### 1. Database Migration Strategy (SQLite → PostgreSQL)

**Decision**: Incremental Alembic migration with extended schema

**Rationale**:
- Legacy uses 37-field Paper model with SQLAlchemy ORM
- HypePaper already uses Alembic for PostgreSQL migrations
- Incremental approach minimizes risk, allows rollback

**Implementation**:
```python
# Alembic migration: Add legacy fields to existing papers table
def upgrade():
    # Add 22 new fields from legacy (15 already exist in HypePaper)
    op.add_column('papers', sa.Column('affiliations', JSONB))
    op.add_column('papers', sa.Column('affiliations_country', JSONB))
    op.add_column('papers', sa.Column('pages', JSONB))
    op.add_column('papers', sa.Column('paper_type', sa.String))
    op.add_column('papers', sa.Column('session_type', sa.String))
    op.add_column('papers', sa.Column('accept_status', sa.String))
    op.add_column('papers', sa.Column('note', sa.String))
    op.add_column('papers', sa.Column('bibtex', sa.String))
    op.add_column('papers', sa.Column('primary_task', sa.String))
    op.add_column('papers', sa.Column('secondary_task', sa.String))
    op.add_column('papers', sa.Column('tertiary_task', sa.String))
    op.add_column('papers', sa.Column('primary_method', sa.String))
    op.add_column('papers', sa.Column('secondary_method', sa.String))
    op.add_column('papers', sa.Column('tertiary_method', sa.String))
    op.add_column('papers', sa.Column('datasets_used', JSONB))
    op.add_column('papers', sa.Column('metrics_used', JSONB))
    op.add_column('papers', sa.Column('comparisons', JSONB))
    op.add_column('papers', sa.Column('limitations', sa.String))
    op.add_column('papers', sa.Column('youtube_url', sa.String))
    op.add_column('papers', sa.Column('project_page_url', sa.String))
    op.add_column('papers', sa.Column('github_star_tracking_start_date', sa.String))
    op.add_column('papers', sa.Column('github_star_tracking_latest_footprint', JSONB))

    # Create citation junction table
    op.create_table(
        'paper_references',
        sa.Column('paper_id', sa.String, sa.ForeignKey('papers.id'), primary_key=True),
        sa.Column('reference_id', sa.String, sa.ForeignKey('papers.id'), primary_key=True),
        sa.Column('reference_text', sa.String),  # Original citation string
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )

    # Performance indexes
    op.create_index('idx_papers_affiliations_gin', 'papers', ['affiliations'], postgresql_using='gin')
    op.create_index('idx_papers_datasets_gin', 'papers', ['datasets_used'], postgresql_using='gin')
    op.create_index('idx_papers_title_fts', 'papers',
                    [sa.text("to_tsvector('english', title)")], postgresql_using='gin')
```

**Alternatives Considered**:
- **Full data migration script**: Rejected due to risk of data loss, no rollback capability
- **Dual database approach**: Rejected due to synchronization complexity
- **Schema-per-source**: Rejected due to query complexity across schemas

---

### 2. Background Job Architecture

**Decision**: Celery with Redis broker + PostgreSQL result backend

**Rationale**:
- FastAPI already in stack (async-compatible)
- Celery handles distributed task queue, retries, scheduling
- Redis provides low-latency message broker
- PostgreSQL stores task results for audit trail

**Implementation**:
```python
# backend/src/jobs/celery_app.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    'hypepaper',
    broker='redis://localhost:6379/0',
    backend='db+postgresql://user:pass@localhost/hypepaper'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # One task at a time per worker
    beat_schedule={
        'daily-star-tracking': {
            'task': 'jobs.star_tracker.track_daily_stars',
            'schedule': crontab(hour=2, minute=0),  # 2 AM UTC daily
        },
    },
)
```

**Alternatives Considered**:
- **APScheduler**: Already in requirements.txt, but less scalable (single-process)
- **RQ (Redis Queue)**: Simpler but less features (no cron, limited retries)
- **Temporal.io**: Over-engineered for current needs, steeper learning curve

---

### 3. LLM Service Abstraction

**Decision**: Unified async LLM interface supporting OpenAI + LlamaCpp

**Rationale**:
- Legacy has good abstraction pattern (LLMClient ABC)
- Need async support for non-blocking API calls
- Support both cloud (OpenAI) and local (LlamaCpp) for cost control

**Implementation**:
```python
# backend/src/services/llm_service.py
from abc import ABC, abstractmethod
from typing import Optional

class AsyncLLMService(ABC):
    @abstractmethod
    async def extract_metadata(self, pdf_path: Path, prompt: str) -> dict:
        pass

    @abstractmethod
    async def extract_tasks(self, full_text: str) -> list[str]:
        pass

class OpenAILLMService(AsyncLLMService):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def extract_metadata(self, pdf_path: Path, prompt: str) -> dict:
        # Upload file to OpenAI
        file = await self.client.files.create(
            file=open(pdf_path, "rb"),
            purpose="assistants"
        )

        # Use Assistants API with file search
        thread = await self.client.beta.threads.create()
        await self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt,
            attachments=[{"file_id": file.id, "tools": [{"type": "file_search"}]}]
        )

        run = await self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=self.assistant_id,
            timeout=300
        )

        messages = await self.client.beta.threads.messages.list(thread_id=thread.id)
        response = messages.data[0].content[0].text.value

        return self._parse_json_response(response)

class LlamaCppLLMService(AsyncLLMService):
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session = aiohttp.ClientSession()

    async def extract_metadata(self, pdf_path: Path, prompt: str) -> dict:
        # Extract text locally
        full_text = await self._extract_pdf_text(pdf_path)

        # Call local LLM server
        async with self.session.post(
            f"{self.server_url}/v1/chat/completions",
            json={
                "model": "Polaris-7B-preview",
                "messages": [
                    {"role": "system", "content": "Extract metadata from research papers."},
                    {"role": "user", "content": f"{full_text}\n\n{prompt}"}
                ],
                "temperature": 0.7
            }
        ) as response:
            data = await response.json()
            return self._parse_json_response(data['choices'][0]['message']['content'])
```

**Prompt Storage**:
- Store prompts in JSON config files (legacy pattern)
- Version prompts with git for reproducibility
- Load at service initialization

---

### 4. Citation Matching Algorithm

**Decision**: Port legacy fuzzy matching with Levenshtein distance upgrade

**Rationale**:
- Legacy uses title+year matching with 2-character tolerance
- Hamming distance (current) too strict (requires equal length)
- Levenshtein distance allows insertions/deletions

**Implementation**:
```python
# backend/src/services/citation_service.py
from rapidfuzz import fuzz
import unicodedata

class CitationMatcher:
    def __init__(self, similarity_threshold: int = 85):
        self.threshold = similarity_threshold

    def normalize_title(self, title: str) -> str:
        # Remove unicode, lowercase, strip whitespace
        normalized = unicodedata.normalize('NFKD', title)
        ascii_str = ''.join(c for c in normalized if ord(c) < 128)
        return ascii_str.lower().strip()

    def match_citation(self, citation_text: str, papers: list[Paper]) -> Optional[Paper]:
        # Parse title and year from citation string
        parsed = self._parse_citation(citation_text)
        if not parsed:
            return None

        target_title = self.normalize_title(parsed['title'])
        target_year = parsed.get('year')

        best_match = None
        best_score = 0

        for paper in papers:
            paper_title = self.normalize_title(paper.title)

            # Levenshtein ratio (0-100)
            title_score = fuzz.ratio(target_title, paper_title)

            # Boost score if years match
            if target_year and paper.year == target_year:
                title_score = min(100, title_score + 10)

            if title_score > best_score and title_score >= self.threshold:
                best_score = title_score
                best_match = paper

        return best_match

    def _parse_citation(self, citation_text: str) -> Optional[dict]:
        # Use AnyStyle CLI (Ruby gem) for bibliographic parsing
        # Write to temp file, call anystyle parse, read JSON
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(citation_text)
            temp_path = f.name

        try:
            result = subprocess.run(
                ['anystyle', 'parse', temp_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            parsed = json.loads(result.stdout)
            if len(parsed) > 0:
                return {
                    'title': ' '.join(parsed[0].get('title', [])),
                    'year': int(parsed[0].get('date', [None])[0]) if parsed[0].get('date') else None
                }
        finally:
            os.unlink(temp_path)

        return None
```

**Dependencies**:
- `rapidfuzz`: Fast Levenshtein distance implementation
- `anystyle-cli`: Ruby gem for citation parsing (external dependency)

---

### 5. PDF Storage Strategy

**Decision**: Local filesystem with structured paths, future S3 migration

**Rationale**:
- MVP: Local storage is simpler, faster for single-server deployment
- Structured path: `/data/papers/{year}/{arxiv_id}/{arxiv_id}.pdf`
- Table CSVs alongside PDF: `/data/papers/{year}/{arxiv_id}/{arxiv_id}.table00.csv`
- Future: Migrate to S3/MinIO for distributed storage

**Implementation**:
```python
# backend/src/services/pdf_service.py
from pathlib import Path

class PDFStorageService:
    def __init__(self, base_path: Path = Path("/data/papers")):
        self.base_path = base_path

    def get_pdf_path(self, paper: Paper) -> Path:
        year = paper.year or 'unknown'
        paper_id = paper.arxiv_id or paper.id

        paper_dir = self.base_path / str(year) / paper_id
        paper_dir.mkdir(parents=True, exist_ok=True)

        return paper_dir / f"{paper_id}.pdf"

    def get_table_paths(self, paper: Paper) -> list[Path]:
        pdf_path = self.get_pdf_path(paper)
        parent_dir = pdf_path.parent

        # Find all table CSV files
        return sorted(parent_dir.glob(f"{pdf_path.stem}.table*.csv"))
```

**Docker Volume Mount**:
```yaml
# docker-compose.yml
services:
  backend:
    volumes:
      - ./data/papers:/data/papers
```

---

### 6. GMFT Table Extraction Integration

**Decision**: Async wrapper around sync GMFT library with executor

**Rationale**:
- GMFT (AutoTableDetector) is synchronous library
- PDF parsing is CPU-bound, benefits from thread pool
- Async wrapper maintains non-blocking API

**Implementation**:
```python
# backend/src/services/pdf_service.py
from concurrent.futures import ThreadPoolExecutor
from gmft.auto import TATRDetectorConfig, AutoTableDetector, AutoTableFormatter, AutoFormatConfig
from gmft.pdf_bindings import PyPDFium2Document
import asyncio

class PDFAnalysisService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Initialize GMFT detectors (reusable)
        detector_config = TATRDetectorConfig()
        detector_config.detector_base_threshold = 0.75
        self.table_detector = AutoTableDetector(detector_config)

        formatter_config = AutoFormatConfig()
        formatter_config.verbosity = 3
        formatter_config.enable_multi_header = True
        formatter_config.semantic_spanning_cells = True
        self.table_formatter = AutoTableFormatter(config=formatter_config)

    async def extract_tables(self, pdf_path: Path) -> list[Path]:
        loop = asyncio.get_event_loop()

        # Run synchronous GMFT in thread pool
        return await loop.run_in_executor(
            self.executor,
            self._extract_tables_sync,
            pdf_path
        )

    def _extract_tables_sync(self, pdf_path: Path) -> list[Path]:
        doc = PyPDFium2Document(pdf_path)
        table_paths = []
        table_index = 0

        for page in doc:
            tables = self.table_detector.extract(page)

            for table in tables:
                extracted = self.table_formatter.extract(table)
                df = extracted.df()

                # Save CSV with zero-padded index
                csv_path = pdf_path.with_suffix(f'.table{table_index:02d}.csv')
                df.to_csv(csv_path, index=False)

                table_paths.append(csv_path)
                table_index += 1

        doc.close()
        return table_paths
```

---

### 7. Configuration Management

**Decision**: JSON files with environment variable overrides via Pydantic

**Rationale**:
- Legacy uses `python-json-config` (deep merge pattern)
- Pydantic adds type safety, validation, env var support
- Maintains legacy JSON file compatibility

**Implementation**:
```python
# backend/src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from pathlib import Path

class DatabaseConfig(BaseSettings):
    url: str = Field(..., validation_alias='DATABASE_URL')
    pool_size: int = 20
    max_overflow: int = 10

class LLMConfig(BaseSettings):
    provider: str = Field('llamacpp', validation_alias='LLM_PROVIDER')
    openai_api_key: Optional[str] = Field(None, validation_alias='OPENAI_API_KEY')
    llamacpp_server: str = Field('http://localhost:10002', validation_alias='LLAMACPP_SERVER')

class GitHubConfig(BaseSettings):
    api_token: str = Field(..., validation_alias='GITHUB_TOKEN')
    rate_limit_per_hour: int = 5000

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        json_file='configs/base.json'
    )

    database: DatabaseConfig
    llm: LLMConfig
    github: GitHubConfig

    @classmethod
    def load_from_json_dir(cls, config_dir: Path) -> 'Settings':
        # Load and merge all JSON files (legacy pattern)
        merged = {}
        for json_file in config_dir.glob('*.json'):
            with open(json_file) as f:
                data = json.load(f)
                merged = deep_merge(merged, data)

        # Create settings from merged JSON + env vars
        return cls(**merged)

def deep_merge(base: dict, update: dict) -> dict:
    for key, value in update.items():
        if isinstance(value, dict) and key in base:
            base[key] = deep_merge(base[key], value)
        else:
            base[key] = value
    return base
```

**Configuration Files**:
```
backend/configs/
├── base.json          # Shared settings
├── database.json      # Database config
├── llm.json          # LLM providers
├── github.json       # GitHub API config
└── prompts.json      # LLM prompt templates
```

**Environment Variables Override**:
```bash
# .env file
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/hypepaper
OPENAI_API_KEY=sk-proj-...
GITHUB_TOKEN=ghp_...
LLM_PROVIDER=openai
```

---

### 8. Testing Strategy

**Decision**: Three-tier testing (contract → integration → unit)

**Rationale**:
- Contract tests validate API schemas (OpenAPI compliance)
- Integration tests validate end-to-end scenarios (acceptance criteria)
- Unit tests validate business logic in isolation

**Test Structure**:
```
backend/tests/
├── contract/
│   ├── test_papers_api.py          # Validate OpenAPI schema
│   ├── test_citations_api.py       # Validate graph endpoints
│   └── test_github_api.py          # Validate metrics endpoints
├── integration/
│   ├── test_arxiv_discovery.py     # Scenario 1: ArXiv paper discovery
│   ├── test_metadata_enrichment.py # Scenario 2: AI metadata extraction
│   ├── test_citation_graph.py      # Scenario 4: Citation relationships
│   └── test_github_tracking.py     # Scenario 3: GitHub star tracking
└── unit/
    ├── test_citation_matcher.py    # Fuzzy matching logic
    ├── test_hype_calculator.py     # Hype score algorithm
    └── test_config_loader.py       # Configuration merging
```

**Contract Test Example**:
```python
# tests/contract/test_papers_api.py
import pytest
from openapi_spec_validator import validate_spec
from openapi_spec_validator.readers import read_from_filename

def test_papers_api_schema_valid():
    spec_dict, spec_url = read_from_filename('specs/002-convert-the-integration/contracts/papers-api.yaml')
    validate_spec(spec_dict)  # Raises if invalid

@pytest.mark.asyncio
async def test_get_papers_returns_extended_schema(client):
    response = await client.get('/api/v1/papers')
    assert response.status_code == 200

    data = response.json()
    paper = data['items'][0]

    # Validate extended fields from legacy
    assert 'primary_task' in paper
    assert 'datasets_used' in paper
    assert 'github_star_count' in paper
    assert 'citations_total' in paper
```

---

## Security Audit Findings

### Critical: Hardcoded GitHub Token

**Location**: `3rdparty/SOTAPapers/sotapapers/modules/github_repo_searcher.py:75`

```python
headers = {
    'Authorization': 'token <REDACTED_GITHUB_TOKEN>'  # EXPOSED!
}
```

**Action Required**:
1. **Immediately revoke token** at https://github.com/settings/tokens
2. Generate new token with `public_repo` scope only
3. Store in environment variable: `GITHUB_TOKEN=ghp_...`
4. Update code to read from env: `os.getenv('GITHUB_TOKEN')`

**Implementation**:
```python
# backend/src/services/github_service.py
import os

class GitHubService:
    def __init__(self):
        self.api_token = os.getenv('GITHUB_TOKEN')
        if not self.api_token:
            raise ValueError("GITHUB_TOKEN environment variable not set")

        self.headers = {
            'Authorization': f'token {self.api_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
```

---

## Dependencies Added

### Backend (requirements.txt)
```txt
# Already in HypePaper:
fastapi==0.104.1
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.12.1
httpx==0.25.1

# New for legacy integration:
celery==5.3.4              # Background job processing
redis==5.0.1               # Celery broker
PyMuPDF==1.23.8            # PDF text extraction (fitz)
gmft==0.2.1                # Table extraction
python-json-config==1.2.3  # Legacy config format
rapidfuzz==3.5.2           # Fuzzy string matching
openai==1.3.8              # OpenAI API client
aiohttp==3.9.1             # Async HTTP client
```

### System Dependencies
```bash
# AnyStyle CLI (Ruby gem for citation parsing)
gem install anystyle-cli

# TimescaleDB extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

---

## Performance Targets

### Single Paper Processing
- **Target**: 3-5 seconds for on-demand processing
- **Breakdown**:
  - PDF download: 1-2s
  - Text extraction: 0.5-1s
  - Table extraction: 1-2s
  - Database insert: 0.1s

### Bulk Processing
- **Target**: 1000 papers in 2 hours (background)
- **Concurrency**: 10 concurrent workers
- **Rate limits respected**:
  - ArXiv: 3 req/s → 10,800 req/hour
  - GitHub: 5000 req/hour → 1.4 req/s
  - Semantic Scholar: No explicit limit, use 10 req/s

### Daily Star Tracking
- **Target**: Update 10,000 papers in 1 hour
- **Rate**: 2.8 papers/second
- **Scheduled**: 2 AM UTC daily (low traffic)

---

## Migration Risks & Mitigation

### Risk 1: AnyStyle Dependency (External Ruby Gem)
**Impact**: Citation parsing fails if Ruby not installed
**Probability**: Medium
**Mitigation**:
- Dockerize with Ruby included
- Add health check: `anystyle --version`
- Fallback: Store unparsed citation text, manual review

### Risk 2: GMFT Table Extraction Accuracy
**Impact**: Missing or incorrect table data
**Probability**: High (complex tables)
**Mitigation**:
- Store confidence thresholds in config
- Manual verification workflow
- Store original PDF for human review

### Risk 3: LLM API Costs
**Impact**: High OpenAI API costs for bulk processing
**Probability**: High
**Mitigation**:
- Default to LlamaCpp (local, free)
- OpenAI only for critical extractions
- Cache all LLM responses
- Cost monitoring dashboard

### Risk 4: Multiprocessing → Async Migration Complexity
**Impact**: Bugs, performance regression during migration
**Probability**: Medium
**Mitigation**:
- Phased migration (Phase 1: HTTP clients, Phase 2: DB, Phase 3: Pipeline)
- A/B testing with feature flag
- Comprehensive integration tests
- Performance benchmarking

---

## Next Phase: Design & Contracts

With all technical decisions resolved, proceed to Phase 1:
1. Generate data-model.md (extended Paper schema)
2. Create OpenAPI contracts (papers-api.yaml, citations-api.yaml, github-api.yaml)
3. Generate failing contract tests
4. Create quickstart.md (integration test scenarios)
5. Update CLAUDE.md with new context
