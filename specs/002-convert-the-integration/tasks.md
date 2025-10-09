# Tasks: SOTAPapers Legacy Code Integration

**Input**: Design documents from `/specs/002-convert-the-integration/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md
**Branch**: `002-convert-the-integration`

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: Python 3.11+, FastAPI, SQLAlchemy (async), Celery, PostgreSQL + TimescaleDB
   → Structure: Web app (backend + frontend separated)
2. Load design documents:
   → data-model.md: 6 entities (Paper extended, Author, PaperReference, GitHubMetrics, PDFContent, LLMExtraction)
   → contracts/: 4 OpenAPI specs (papers-api, citations-api, github-api, jobs-api)
   → quickstart.md: 5 integration test scenarios
3. Generate tasks by category:
   → Setup: Dependencies, config, Alembic migration
   → Tests: 4 contract tests, 5 integration tests
   → Core: 6 models, 7 services, 4 API routers
   → Jobs: 3 Celery tasks
   → Polish: Unit tests, security audit, performance
4. Apply task rules:
   → Contract tests [P], models [P], services [P] (different files)
   → API endpoints sequential (shared router files)
   → Tests before implementation (TDD)
5. Total: 72 tasks across 6 phases
6. Dependencies validated (no circular dependencies)
7. Parallel execution examples provided
8. SUCCESS: Tasks ready for execution
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- File paths relative to repository root

---

## Phase 3.1: Setup & Dependencies (8 tasks)

### T001: Install new Python dependencies
**File**: `backend/requirements.txt`
**Action**: Add new dependencies for legacy integration
```txt
# Add to requirements.txt:
celery==5.3.4
redis==5.0.1
PyMuPDF==1.23.8
gmft==0.2.1
python-json-config==1.2.3
rapidfuzz==3.5.2
openai==1.3.8
aiohttp==3.9.1
```
**Verify**: `pip install -r backend/requirements.txt` succeeds

### T002: Install system dependencies
**File**: System packages
**Action**: Install AnyStyle CLI and TimescaleDB extension
```bash
# Install Ruby gem for citation parsing
gem install anystyle-cli

# Verify PostgreSQL TimescaleDB extension
psql -d hypepaper -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```
**Verify**: `anystyle --version` returns version, TimescaleDB extension active

### T003: [P] Create configuration directory structure
**File**: `backend/configs/`
**Action**: Create JSON config files based on python-json-config pattern
```bash
mkdir -p backend/configs
touch backend/configs/base.json
touch backend/configs/database.json
touch backend/configs/llm.json
touch backend/configs/github.json
touch backend/configs/prompts.json
```

### T004: [P] Configure Celery application
**File**: `backend/src/jobs/celery_app.py`
**Action**: Create Celery app with Redis broker and PostgreSQL result backend
```python
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    'hypepaper',
    broker='redis://localhost:6379/0',
    backend='db+postgresql://user:pass@localhost/hypepaper'
)

celery_app.conf.beat_schedule = {
    'daily-star-tracking': {
        'task': 'jobs.star_tracker.track_daily_stars',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

### T005: [P] Create Pydantic settings with env var support
**File**: `backend/src/config.py`
**Action**: Implement Settings class with JSON loading + env overrides
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str
    github_token: str
    openai_api_key: Optional[str]
    # ... other fields

    @classmethod
    def load_from_json_dir(cls, config_dir: Path):
        # Merge all JSON files
        # Override with env vars
        pass
```

### T006: [P] Set up PDF storage directory structure
**File**: Filesystem
**Action**: Create `/data/papers` directory with proper permissions
```bash
mkdir -p /data/papers
chmod 755 /data/papers
```

### T007: Create Alembic migration for extended schema
**File**: `backend/alembic/versions/XXXX_add_legacy_fields.py`
**Action**: Generate migration adding 22 fields to papers table + 5 new tables
```bash
cd backend
alembic revision -m "add_legacy_fields"
# Edit migration file with schema from data-model.md
```
**Content**: Copy SQL from data-model.md Alembic Migration section

### T008: Run database migration
**File**: Database
**Action**: Apply migration to create extended schema
```bash
cd backend
alembic upgrade head
```
**Verify**: Tables exist: `papers` (with 37 fields), `authors`, `paper_authors`, `paper_references`, `github_metrics`, `pdf_content`, `llm_extractions`

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3 (13 tasks)

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (4 tasks - run in parallel)

### T009: [P] Contract test for papers API
**File**: `backend/tests/contract/test_papers_api.py`
**Action**: Validate papers-api.yaml OpenAPI schema compliance
```python
import pytest
from openapi_spec_validator import validate_spec

def test_papers_api_schema_valid():
    validate_spec('specs/002-convert-the-integration/contracts/papers-api.yaml')

@pytest.mark.asyncio
async def test_get_papers_extended_schema(client):
    response = await client.get('/api/v1/papers')
    paper = response.json()['items'][0]
    assert 'primary_task' in paper
    assert 'datasets_used' in paper
    assert 'github_star_count' in paper
```
**Verify**: Test fails (endpoints not implemented)

### T010: [P] Contract test for citations API
**File**: `backend/tests/contract/test_citations_api.py`
**Action**: Validate citations-api.yaml compliance
```python
@pytest.mark.asyncio
async def test_get_citation_graph(client, test_paper):
    response = await client.get(f'/api/v1/citations/graph?paper_id={test_paper.id}&depth=2')
    assert response.status_code == 200
    graph = response.json()
    assert 'nodes' in graph
    assert 'edges' in graph
```
**Verify**: Test fails

### T011: [P] Contract test for GitHub API
**File**: `backend/tests/contract/test_github_api.py`
**Action**: Validate github-api.yaml compliance
```python
@pytest.mark.asyncio
async def test_get_github_metrics(client, paper_with_github):
    response = await client.get(f'/api/v1/github/metrics/{paper_with_github.id}')
    assert response.status_code == 200
    metrics = response.json()
    assert 'star_history' in metrics
    assert 'hype_scores' in metrics
```
**Verify**: Test fails

### T012: [P] Contract test for jobs API
**File**: `backend/tests/contract/test_jobs_api.py`
**Action**: Validate jobs-api.yaml compliance
```python
@pytest.mark.asyncio
async def test_post_crawl_job(client):
    response = await client.post('/api/v1/jobs/crawl', json={
        'source': 'arxiv',
        'arxiv_keywords': 'transformer',
        'arxiv_max_results': 10
    })
    assert response.status_code == 202
    assert 'job_id' in response.json()
```
**Verify**: Test fails

### Integration Tests (5 tasks - run in parallel)

### T013: [P] Integration test: ArXiv paper discovery
**File**: `backend/tests/integration/test_arxiv_discovery.py`
**Action**: Test Scenario 1 from quickstart.md (end-to-end crawl)
```python
@pytest.mark.asyncio
async def test_arxiv_paper_discovery_e2e(client, db_session):
    # Trigger crawl job
    response = await client.post('/api/v1/jobs/crawl', json={...})
    job_id = response.json()['job_id']

    # Poll for completion
    # Verify papers stored with deterministic IDs
    # Check duplicate detection
```
**Verify**: Test fails (no crawler implemented)

### T014: [P] Integration test: Metadata enrichment
**File**: `backend/tests/integration/test_metadata_enrichment.py`
**Action**: Test Scenario 2 (PDF + LLM extraction)
```python
@pytest.mark.asyncio
async def test_metadata_enrichment_e2e(client, test_paper):
    # Trigger enrichment job
    # Verify PDF downloaded
    # Verify tables extracted (GMFT)
    # Verify LLM metadata (tasks, methods, datasets)
    # Verify flagged for manual review
```
**Verify**: Test fails

### T015: [P] Integration test: GitHub tracking
**File**: `backend/tests/integration/test_github_tracking.py`
**Action**: Test Scenario 3 (GitHub star tracking)
```python
@pytest.mark.asyncio
async def test_github_tracking_e2e(client, test_paper):
    # Search for GitHub repo
    # Fetch initial metrics
    # Calculate hype scores
    # Create daily snapshot
    # Verify indefinite retention
```
**Verify**: Test fails

### T016: [P] Integration test: Citation graph
**File**: `backend/tests/integration/test_citation_graph.py`
**Action**: Test Scenario 4 (citation parsing + fuzzy matching)
```python
@pytest.mark.asyncio
async def test_citation_graph_e2e(client, papers_with_references):
    # Parse PDF references
    # Fuzzy match to existing papers (Levenshtein ≥85%)
    # Create bidirectional relationships
    # Query multi-level graph (depth=2)
    # Verify citation-based discovery
```
**Verify**: Test fails

### T017: [P] Integration test: Conference integration
**File**: `backend/tests/integration/test_conference_integration.py`
**Action**: Test Scenario 5 (conference crawling)
```python
@pytest.mark.asyncio
async def test_conference_integration_e2e(client, config_with_conference):
    # Crawl conference papers
    # Link to ArXiv versions (duplicate detection)
    # Verify conference metadata (session_type, accept_status)
    # Filter by paper_type
```
**Verify**: Test fails

### Unit Tests (4 tasks - run in parallel)

### T018: [P] Unit test: Citation fuzzy matching
**File**: `backend/tests/unit/test_citation_matcher.py`
**Action**: Test Levenshtein matching algorithm
```python
def test_normalize_title():
    assert normalize_title("Café résumé") == "cafe resume"

def test_match_citation_exact():
    matcher = CitationMatcher(threshold=85)
    assert matcher.match_citation(citation, papers) == expected_paper

def test_match_citation_with_typos():
    # Test 85% similarity threshold
    pass
```

### T019: [P] Unit test: Hype score calculation
**File**: `backend/tests/unit/test_hype_calculator.py`
**Action**: Test GitHub hype score formula
```python
def test_hype_score_with_citations():
    # hype = (citations * 100 + stars) / age_days
    score = calculate_hype(citations=10, stars=500, age_days=100)
    assert score == (10 * 100 + 500) / 100

def test_hype_score_stars_only():
    score = calculate_hype(citations=0, stars=500, age_days=100)
    assert score == 500 / 100
```

### T020: [P] Unit test: Deterministic ID generation
**File**: `backend/tests/unit/test_id_generator.py`
**Action**: Test title+year hash function
```python
def test_generate_id_deterministic():
    id1 = make_generated_id("Deep Learning", 2024)
    id2 = make_generated_id("Deep Learning", 2024)
    assert id1 == id2

def test_generate_id_different_titles():
    id1 = make_generated_id("Deep Learning", 2024)
    id2 = make_generated_id("Machine Learning", 2024)
    assert id1 != id2
```

### T021: [P] Unit test: Config loader with env overrides
**File**: `backend/tests/unit/test_config_loader.py`
**Action**: Test JSON merging + environment variable overrides
```python
def test_load_json_configs_merge():
    settings = Settings.load_from_json_dir(Path('test_configs'))
    assert settings.database.url == "merged_value"

def test_env_var_overrides_json(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'override_url')
    settings = Settings.load_from_json_dir(Path('test_configs'))
    assert settings.database_url == 'override_url'
```

---

## Phase 3.3: Core Implementation - Models (6 tasks - run in parallel)

**ONLY after tests are failing**

### T022: [P] Implement extended Paper model
**File**: `backend/src/models/paper.py`
**Action**: Extend Paper with 22 new fields from data-model.md
```python
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship

class Paper(Base):
    __tablename__ = "papers"

    # Add 22 new fields:
    affiliations = Column(JSONB)
    affiliations_country = Column(JSONB)
    pages = Column(JSONB)
    paper_type = Column(String)
    session_type = Column(String)
    accept_status = Column(String)
    note = Column(Text)
    bibtex = Column(Text)
    primary_task = Column(String)
    secondary_task = Column(String)
    # ... (all 22 fields from data-model.md)

    # Relationships
    authors = relationship("Author", secondary="paper_authors", back_populates="papers")
    references = relationship("Paper", secondary="paper_references", ...)
```
**Verify**: T018-T021 tests start passing

### T023: [P] Implement Author model
**File**: `backend/src/models/author.py`
**Action**: Create Author entity with many-to-many papers relationship
```python
class Author(Base):
    __tablename__ = "authors"

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False, index=True)
    affiliations = Column(ARRAY(String))
    countries = Column(ARRAY(String))

    papers = relationship("Paper", secondary="paper_authors", back_populates="authors")
```

### T024: [P] Implement PaperReference model
**File**: `backend/src/models/paper_reference.py`
**Action**: Create citation junction table with bidirectional support
```python
class PaperReference(Base):
    __tablename__ = "paper_references"

    paper_id = Column(UUID, ForeignKey("papers.id"), primary_key=True)
    reference_id = Column(UUID, ForeignKey("papers.id"), primary_key=True)
    reference_text = Column(Text)  # Original citation string
    match_quality = Column(Integer)  # Levenshtein score
    created_at = Column(DateTime, server_default=func.now())
```

### T025: [P] Implement GitHubMetrics model
**File**: `backend/src/models/github_metrics.py`
**Action**: Create time-series model with TimescaleDB hypertable
```python
class GitHubMetrics(Base):
    __tablename__ = "github_metrics"

    id = Column(UUID, primary_key=True, default=uuid4)
    paper_id = Column(UUID, ForeignKey("papers.id"), index=True)
    repo_url = Column(String, nullable=False)
    star_count = Column(Integer)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Hype scores
    avg_hype = Column(Float)
    weekly_hype = Column(Float)
    monthly_hype = Column(Float)

    # Convert to TimescaleDB hypertable
    __table_args__ = (
        Index('idx_github_metrics_time', 'paper_id', 'timestamp'),
    )
```

### T026: [P] Implement PDFContent model
**File**: `backend/src/models/pdf_content.py`
**Action**: Store extracted PDF text and table paths
```python
class PDFContent(Base):
    __tablename__ = "pdf_content"

    id = Column(UUID, primary_key=True, default=uuid4)
    paper_id = Column(UUID, ForeignKey("papers.id"), unique=True)
    full_text = Column(Text)
    table_csv_paths = Column(ARRAY(String))  # ["/data/papers/2024/id.table00.csv", ...]
    parsed_references = Column(ARRAY(Text))  # Raw reference strings
    extraction_timestamp = Column(DateTime, server_default=func.now())
    success = Column(Boolean, default=True)
    error_message = Column(Text)
```

### T027: [P] Implement LLMExtraction model
**File**: `backend/src/models/llm_extraction.py`
**Action**: Store AI-extracted metadata with verification workflow
```python
class LLMExtraction(Base):
    __tablename__ = "llm_extractions"

    id = Column(UUID, primary_key=True, default=uuid4)
    paper_id = Column(UUID, ForeignKey("papers.id"), index=True)
    extraction_type = Column(String)  # 'task', 'method', 'dataset', 'metric'
    extracted_values = Column(JSONB)  # {'primary': '...', 'secondary': '...'}
    llm_model = Column(String)  # 'gpt-4o', 'llama-cpp'
    extraction_timestamp = Column(DateTime, server_default=func.now())
    verification_status = Column(String, default='pending_review')  # 'pending_review', 'verified', 'rejected'
```

---

## Phase 3.4: Core Implementation - Services (7 tasks - run in parallel)

### T028: [P] Implement async ArXiv service
**File**: `backend/src/services/arxiv_service.py`
**Action**: Port legacy ArxivClient to async with retry logic
```python
import aiohttp
import asyncio

class AsyncArxivService:
    def __init__(self, max_retry: int = 3, retry_delay_sec: int = 1):
        self.max_retry = max_retry
        self.retry_delay_sec = retry_delay_sec

    async def search_by_keywords(self, keywords: str, max_results: int = 10) -> list[Paper]:
        delay_sec = self.retry_delay_sec
        for i in range(self.max_retry):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'https://export.arxiv.org/api/query',
                        params={'search_query': keywords, 'max_results': max_results}
                    ) as response:
                        text = await response.text()
                        return self._parse_arxiv_xml(text)
            except Exception as e:
                await asyncio.sleep(delay_sec)
                delay_sec *= random.uniform(1.0, 2.0)
        return []
```
**Verify**: T013 integration test starts passing

### T029: [P] Implement async GitHub service
**File**: `backend/src/services/github_service.py`
**Action**: GitHub API client with secure token auth
```python
class AsyncGitHubService:
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            'Authorization': f'token {api_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    async def search_repository(self, paper_title: str, arxiv_id: Optional[str]) -> Optional[GitHubRepo]:
        # Try Papers with Code API first (if arxiv_id)
        # Fallback to direct GitHub search
        pass

    async def get_star_count(self, repo_url: str) -> int:
        # Use GitHub API (not web scraping)
        pass

    async def calculate_hype_scores(self, star_history: list) -> dict:
        # avg_hype, weekly_hype, monthly_hype
        pass
```
**Verify**: T015 integration test starts passing

### T030: [P] Implement PDF analysis service
**File**: `backend/src/services/pdf_service.py`
**Action**: PDF text extraction + GMFT table detection (async wrapper)
```python
from concurrent.futures import ThreadPoolExecutor
from gmft.auto import AutoTableDetector, AutoTableFormatter
import asyncio

class PDFAnalysisService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.table_detector = AutoTableDetector(TATRDetectorConfig())
        self.table_formatter = AutoTableFormatter(AutoFormatConfig())

    async def extract_text(self, pdf_path: Path) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._extract_text_sync, pdf_path)

    async def extract_tables(self, pdf_path: Path) -> list[Path]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._extract_tables_sync, pdf_path)

    def _extract_tables_sync(self, pdf_path: Path) -> list[Path]:
        # GMFT synchronous code
        # Save to {pdf_path}.table00.csv, .table01.csv, ...
        pass
```
**Verify**: T014 integration test starts passing

### T031: [P] Implement LLM service abstraction
**File**: `backend/src/services/llm_service.py`
**Action**: Unified interface for OpenAI + LlamaCpp
```python
from abc import ABC, abstractmethod

class AsyncLLMService(ABC):
    @abstractmethod
    async def extract_metadata(self, pdf_path: Path, prompt: str) -> dict:
        pass

class OpenAILLMService(AsyncLLMService):
    async def extract_metadata(self, pdf_path: Path, prompt: str) -> dict:
        # Use OpenAI Assistants API with file search
        pass

class LlamaCppLLMService(AsyncLLMService):
    async def extract_metadata(self, pdf_path: Path, prompt: str) -> dict:
        # Call local LlamaCpp server
        pass
```
**Verify**: T014 integration test LLM extraction passes

### T032: [P] Implement citation parsing service
**File**: `backend/src/services/citation_service.py`
**Action**: Reference extraction + fuzzy matching with Levenshtein
```python
from rapidfuzz import fuzz
import subprocess

class CitationMatcher:
    def __init__(self, similarity_threshold: int = 85):
        self.threshold = similarity_threshold

    def normalize_title(self, title: str) -> str:
        # Unicode normalization + lowercase
        pass

    async def parse_citation(self, citation_text: str) -> Optional[dict]:
        # Call AnyStyle CLI
        result = subprocess.run(['anystyle', 'parse', temp_file], capture_output=True)
        parsed = json.loads(result.stdout)
        return {'title': ..., 'year': ...}

    async def match_citation(self, citation_text: str, papers: list[Paper]) -> Optional[Paper]:
        parsed = await self.parse_citation(citation_text)
        target_title = self.normalize_title(parsed['title'])

        best_match = None
        best_score = 0
        for paper in papers:
            score = fuzz.ratio(target_title, self.normalize_title(paper.title))
            if parsed['year'] == paper.year:
                score = min(100, score + 10)
            if score >= self.threshold and score > best_score:
                best_match = paper
                best_score = score

        return best_match
```
**Verify**: T016 integration test citation matching passes

### T033: [P] Implement configuration service
**File**: `backend/src/services/config_service.py`
**Action**: JSON config loading with deep merge + env overrides
```python
class ConfigService:
    @staticmethod
    def load_config(config_dir: Path) -> Settings:
        # Load all JSON files
        configs = []
        for json_file in config_dir.glob('*.json'):
            with open(json_file) as f:
                configs.append(json.load(f))

        # Deep merge
        merged = ConfigService._deep_merge(configs)

        # Create Settings with env var overrides
        return Settings(**merged)

    @staticmethod
    def _deep_merge(dicts: list[dict]) -> dict:
        # Recursive merge
        pass
```

### T034: [P] Implement PDF storage service
**File**: `backend/src/services/pdf_storage_service.py`
**Action**: Structured filesystem paths for PDFs and tables
```python
class PDFStorageService:
    def __init__(self, base_path: Path = Path("/data/papers")):
        self.base_path = base_path

    def get_pdf_path(self, paper: Paper) -> Path:
        year = paper.year or 'unknown'
        paper_id = paper.arxiv_id or str(paper.id)
        paper_dir = self.base_path / str(year) / paper_id
        paper_dir.mkdir(parents=True, exist_ok=True)
        return paper_dir / f"{paper_id}.pdf"

    def get_table_paths(self, paper: Paper) -> list[Path]:
        pdf_path = self.get_pdf_path(paper)
        return sorted(pdf_path.parent.glob(f"{pdf_path.stem}.table*.csv"))
```

---

## Phase 3.5: Background Jobs (3 tasks - run in parallel)

### T035: [P] Implement paper crawler Celery task
**File**: `backend/src/jobs/paper_crawler.py`
**Action**: Background job for ArXiv/conference paper discovery
```python
from celery import Task
from .celery_app import celery_app

@celery_app.task(bind=True, name='jobs.paper_crawler.crawl_papers')
def crawl_papers(self: Task, source: str, **kwargs):
    """Background task for paper discovery.

    Args:
        source: 'arxiv', 'conference', or 'citations'
        arxiv_keywords: Keywords for ArXiv search
        conference_name: Conference to crawl
    """
    self.update_state(state='PROCESSING', meta={'current': 0, 'total': 100})

    if source == 'arxiv':
        papers = await arxiv_service.search_by_keywords(kwargs['arxiv_keywords'])
    elif source == 'conference':
        papers = await conference_crawler.crawl(kwargs['conference_name'])

    # Store papers in database
    for i, paper in enumerate(papers):
        await db.insert_paper(paper)
        self.update_state(state='PROCESSING', meta={'current': i+1, 'total': len(papers)})

    return {'status': 'completed', 'papers_discovered': len(papers)}
```
**Verify**: T013, T017 integration tests pass

### T036: [P] Implement metadata enrichment Celery task
**File**: `backend/src/jobs/metadata_enricher.py`
**Action**: Background job for PDF + LLM extraction
```python
@celery_app.task(bind=True, name='jobs.metadata_enricher.enrich_paper')
def enrich_paper(self: Task, paper_id: str):
    """Background task for paper metadata enrichment.

    Steps:
    1. Download PDF
    2. Extract text and tables (GMFT)
    3. LLM extraction (tasks, methods, datasets, metrics)
    4. Flag for manual verification
    """
    paper = await db.get_paper(paper_id)

    # Download PDF
    pdf_path = await pdf_storage.download_pdf(paper)

    # Extract text and tables
    full_text = await pdf_service.extract_text(pdf_path)
    table_paths = await pdf_service.extract_tables(pdf_path)

    # Store PDF content
    await db.insert_pdf_content(PDFContent(
        paper_id=paper.id,
        full_text=full_text,
        table_csv_paths=[str(p) for p in table_paths]
    ))

    # LLM extraction
    prompts = config_service.get_llm_prompts()
    tasks_result = await llm_service.extract_metadata(pdf_path, prompts['extract_tasks'])

    # Store LLM extractions (flagged for review)
    await db.insert_llm_extraction(LLMExtraction(
        paper_id=paper.id,
        extraction_type='task',
        extracted_values=tasks_result,
        verification_status='pending_review'
    ))

    return {'status': 'completed', 'extractions': 4}
```
**Verify**: T014 integration test passes

### T037: [P] Implement daily star tracker Celery task
**File**: `backend/src/jobs/star_tracker.py`
**Action**: Scheduled job for GitHub star updates
```python
@celery_app.task(name='jobs.star_tracker.track_daily_stars')
def track_daily_stars():
    """Scheduled task: Update GitHub star counts for all papers with repos.

    Runs: Daily at 2 AM UTC
    Rate limit: 5000 requests/hour
    """
    papers_with_github = await db.get_papers_with_github_repos()

    for paper in papers_with_github:
        current_stars = await github_service.get_star_count(paper.github_url)

        # Store snapshot
        await db.insert_github_metrics(GitHubMetrics(
            paper_id=paper.id,
            repo_url=paper.github_url,
            star_count=current_stars,
            timestamp=datetime.utcnow()
        ))

        # Calculate hype scores
        star_history = await db.get_star_history(paper.id)
        hype_scores = await github_service.calculate_hype_scores(star_history)

        # Update paper
        await db.update_paper_hype_scores(paper.id, hype_scores)

    return {'status': 'completed', 'papers_updated': len(papers_with_github)}
```
**Verify**: T015 integration test daily updates pass

---

## Phase 3.6: API Endpoints (12 tasks - mostly sequential per router)

### Papers API (4 tasks)

### T038: Implement GET /api/v1/papers with extended filters
**File**: `backend/src/api/v1/papers.py`
**Action**: List papers with filters (primary_task, datasets_used, github_stars, etc.)
```python
from fastapi import APIRouter, Query, Depends
from typing import Optional

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])

@router.get("/")
async def get_papers(
    primary_task: Optional[str] = None,
    datasets_used: Optional[list[str]] = Query(None),
    min_github_stars: Optional[int] = None,
    year: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    query = select(Paper)

    if primary_task:
        query = query.where(Paper.primary_task == primary_task)
    if datasets_used:
        query = query.where(Paper.datasets_used.contains(datasets_used))
    if min_github_stars:
        query = query.where(Paper.github_star_count >= min_github_stars)
    if year:
        query = query.where(Paper.year == year)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    papers = result.scalars().all()

    return {"items": papers, "total": len(papers)}
```
**Verify**: T009 contract test passes

### T039: Implement GET /api/v1/papers/{id}
**File**: `backend/src/api/v1/papers.py`
**Action**: Get single paper with full metadata
```python
@router.get("/{paper_id}")
async def get_paper(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Paper).where(Paper.id == paper_id))
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return paper
```

### T040: Implement GET /api/v1/papers/{id}/citations
**File**: `backend/src/api/v1/papers.py`
**Action**: Get bidirectional citations for paper
```python
@router.get("/{paper_id}/citations")
async def get_paper_citations(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Query paper_references table
    cites_query = select(PaperReference).where(PaperReference.paper_id == paper_id)
    cited_by_query = select(PaperReference).where(PaperReference.reference_id == paper_id)

    cites_result = await db.execute(cites_query)
    cited_by_result = await db.execute(cited_by_query)

    return {
        "cites": [r.reference_id for r in cites_result.scalars()],
        "cited_by": [r.paper_id for r in cited_by_result.scalars()]
    }
```

### T041: Implement GET /api/v1/papers/{id}/github
**File**: `backend/src/api/v1/papers.py`
**Action**: Get GitHub metrics and history for paper
```python
@router.get("/{paper_id}/github")
async def get_paper_github_metrics(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Query github_metrics table
    query = select(GitHubMetrics).where(GitHubMetrics.paper_id == paper_id).order_by(GitHubMetrics.timestamp.desc())
    result = await db.execute(query)
    metrics = result.scalars().all()

    if not metrics:
        raise HTTPException(status_code=404, detail="No GitHub metrics found")

    return {
        "repo_url": metrics[0].repo_url,
        "current_stars": metrics[0].star_count,
        "hype_scores": {
            "avg_hype": metrics[0].avg_hype,
            "weekly_hype": metrics[0].weekly_hype,
            "monthly_hype": metrics[0].monthly_hype
        },
        "star_history": [{"timestamp": m.timestamp, "stars": m.star_count} for m in metrics]
    }
```

### Citations API (3 tasks)

### T042: Implement GET /api/v1/citations/graph
**File**: `backend/src/api/v1/citations.py`
**Action**: Multi-level citation graph traversal
```python
router = APIRouter(prefix="/api/v1/citations", tags=["citations"])

@router.get("/graph")
async def get_citation_graph(
    paper_id: UUID,
    depth: int = 2,
    direction: str = "both",  # 'cites', 'cited_by', 'both'
    db: AsyncSession = Depends(get_db)
):
    nodes = []
    edges = []
    visited = set()

    async def traverse(current_id: UUID, current_depth: int):
        if current_depth > depth or current_id in visited:
            return

        visited.add(current_id)
        paper = await db.get(Paper, current_id)
        nodes.append({"id": str(current_id), "title": paper.title})

        # Get citations
        if direction in ["cites", "both"]:
            cites_query = select(PaperReference).where(PaperReference.paper_id == current_id)
            cites_result = await db.execute(cites_query)
            for ref in cites_result.scalars():
                edges.append({"source": str(current_id), "target": str(ref.reference_id)})
                await traverse(ref.reference_id, current_depth + 1)

        if direction in ["cited_by", "both"]:
            cited_by_query = select(PaperReference).where(PaperReference.reference_id == current_id)
            cited_by_result = await db.execute(cited_by_query)
            for ref in cited_by_result.scalars():
                edges.append({"source": str(ref.paper_id), "target": str(current_id)})
                await traverse(ref.paper_id, current_depth + 1)

    await traverse(paper_id, 0)

    return {"nodes": nodes, "edges": edges}
```
**Verify**: T010 contract test, T016 integration test pass

### T043: Implement POST /api/v1/citations/discover
**File**: `backend/src/api/v1/citations.py`
**Action**: Citation-based paper discovery
```python
@router.post("/discover")
async def discover_via_citations(
    paper_id: UUID,
    method: str = "citations",  # 'citations', 'co-citations', 'same-author'
    max_results: int = 20,
    db: AsyncSession = Depends(get_db)
):
    if method == "citations":
        # Find papers cited by this paper
        query = select(Paper).join(PaperReference, PaperReference.reference_id == Paper.id).where(PaperReference.paper_id == paper_id)
    elif method == "co-citations":
        # Find papers that cite the same papers as this paper
        # Complex SQL: papers that share citations with target paper
        pass

    result = await db.execute(query.limit(max_results))
    papers = result.scalars().all()

    return {"discovered_papers": papers}
```

### T044: Implement GET /api/v1/citations/stats
**File**: `backend/src/api/v1/citations.py`
**Action**: Citation statistics and co-citation analysis
```python
@router.get("/stats")
async def get_citation_stats(
    paper_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    # Count citations
    cites_count = await db.scalar(select(func.count()).select_from(PaperReference).where(PaperReference.paper_id == paper_id))
    cited_by_count = await db.scalar(select(func.count()).select_from(PaperReference).where(PaperReference.reference_id == paper_id))

    return {
        "cites_count": cites_count,
        "cited_by_count": cited_by_count,
        "total_citations": cites_count + cited_by_count
    }
```

### GitHub API (2 tasks)

### T045: Implement GET /api/v1/github/metrics/{paper_id}
**File**: `backend/src/api/v1/github.py`
**Action**: Time-series GitHub metrics with aggregation
```python
router = APIRouter(prefix="/api/v1/github", tags=["github"])

@router.get("/metrics/{paper_id}")
async def get_github_metrics(
    paper_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    aggregation: str = "daily",  # 'daily', 'weekly', 'monthly'
    db: AsyncSession = Depends(get_db)
):
    query = select(GitHubMetrics).where(GitHubMetrics.paper_id == paper_id)

    if start_date:
        query = query.where(GitHubMetrics.timestamp >= start_date)
    if end_date:
        query = query.where(GitHubMetrics.timestamp <= end_date)

    query = query.order_by(GitHubMetrics.timestamp)

    result = await db.execute(query)
    metrics = result.scalars().all()

    # Aggregate based on parameter
    if aggregation == "weekly":
        metrics = aggregate_weekly(metrics)
    elif aggregation == "monthly":
        metrics = aggregate_monthly(metrics)

    return {"metrics": metrics}
```
**Verify**: T011 contract test passes

### T046: Implement GET /api/v1/github/trending
**File**: `backend/src/api/v1/github.py`
**Action**: Trending papers sorted by hype scores
```python
@router.get("/trending")
async def get_trending_papers(
    metric: str = "weekly_hype",  # 'avg_hype', 'weekly_hype', 'monthly_hype'
    min_stars: int = 10,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    # Join papers with latest GitHub metrics
    subquery = select(
        GitHubMetrics.paper_id,
        func.max(GitHubMetrics.timestamp).label('latest_timestamp')
    ).group_by(GitHubMetrics.paper_id).subquery()

    query = select(Paper, GitHubMetrics).join(
        GitHubMetrics,
        Paper.id == GitHubMetrics.paper_id
    ).join(
        subquery,
        (GitHubMetrics.paper_id == subquery.c.paper_id) &
        (GitHubMetrics.timestamp == subquery.c.latest_timestamp)
    ).where(
        GitHubMetrics.star_count >= min_stars
    )

    # Sort by hype metric
    if metric == "weekly_hype":
        query = query.order_by(GitHubMetrics.weekly_hype.desc())
    elif metric == "monthly_hype":
        query = query.order_by(GitHubMetrics.monthly_hype.desc())
    else:
        query = query.order_by(GitHubMetrics.avg_hype.desc())

    query = query.limit(limit)

    result = await db.execute(query)
    trending = result.all()

    return {"trending_papers": [{"paper": paper, "hype_score": metrics.weekly_hype} for paper, metrics in trending]}
```

### Jobs API (3 tasks)

### T047: Implement POST /api/v1/jobs/crawl
**File**: `backend/src/api/v1/jobs.py`
**Action**: Trigger paper crawl background job
```python
router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

@router.post("/crawl", status_code=202)
async def trigger_crawl_job(
    source: str,
    arxiv_keywords: Optional[str] = None,
    arxiv_max_results: int = 100,
    conference_name: Optional[str] = None,
    priority: str = "normal"
):
    # Trigger Celery task
    from src.jobs.paper_crawler import crawl_papers

    task = crawl_papers.apply_async(
        kwargs={
            'source': source,
            'arxiv_keywords': arxiv_keywords,
            'arxiv_max_results': arxiv_max_results,
            'conference_name': conference_name
        },
        priority=9 if priority == "high" else 5
    )

    return {
        "job_id": task.id,
        "status": "queued",
        "message": f"Crawl job queued for {source}"
    }
```
**Verify**: T012 contract test passes

### T048: Implement GET /api/v1/jobs/{job_id}
**File**: `backend/src/api/v1/jobs.py`
**Action**: Get job status and progress
```python
@router.get("/{job_id}")
async def get_job_status(job_id: str):
    from celery.result import AsyncResult

    task = AsyncResult(job_id, app=celery_app)

    if task.state == 'PENDING':
        response = {'status': 'queued', 'progress': 0}
    elif task.state == 'PROCESSING':
        response = {
            'status': 'processing',
            'progress': task.info.get('current', 0) / task.info.get('total', 100),
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 100)
        }
    elif task.state == 'SUCCESS':
        response = {
            'status': 'completed',
            'progress': 1.0,
            'result': task.result
        }
    elif task.state == 'FAILURE':
        response = {
            'status': 'failed',
            'error': str(task.info)
        }
    else:
        response = {'status': task.state.lower()}

    return response
```

### T049: Implement POST /api/v1/jobs/{job_id}/cancel
**File**: `backend/src/api/v1/jobs.py`
**Action**: Cancel running job
```python
@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    from celery.result import AsyncResult

    task = AsyncResult(job_id, app=celery_app)
    task.revoke(terminate=True)

    return {"status": "cancelled", "job_id": job_id}
```

---

## Phase 3.7: Security Audit (5 tasks)

### T050: Revoke hardcoded GitHub token
**File**: Legacy codebase
**Action**: Revoke exposed token immediately
1. Go to https://github.com/settings/tokens
2. Find token `<REDACTED_GITHUB_TOKEN>`
3. Click "Delete" to revoke
4. Generate new token with `public_repo` scope only
5. Store in environment variable: `export GITHUB_TOKEN=ghp_NEW_TOKEN`

### T051: [P] Audit all credential storage
**File**: All config files
**Action**: Verify no hardcoded secrets in code or config
```bash
# Search for potential secrets
grep -r "api_key" backend/src/
grep -r "token" backend/src/
grep -r "password" backend/src/

# Check config files
cat backend/configs/*.json | grep -E "(api_key|token|password)"
```
**Verify**: No hardcoded credentials found

### T052: [P] Add input validation to all endpoints
**File**: `backend/src/api/v1/*.py`
**Action**: Pydantic models for request validation
```python
from pydantic import BaseModel, Field, validator

class CrawlJobRequest(BaseModel):
    source: str = Field(..., pattern='^(arxiv|conference|citations)$')
    arxiv_keywords: Optional[str] = Field(None, max_length=500)
    arxiv_max_results: int = Field(100, ge=1, le=1000)

    @validator('source')
    def validate_source(cls, v):
        if v not in ['arxiv', 'conference', 'citations']:
            raise ValueError('Invalid source')
        return v
```

### T053: [P] Add rate limiting to external API calls
**File**: `backend/src/services/*_service.py`
**Action**: Implement semaphores for rate limiting
```python
import asyncio

class AsyncArxivService:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(3)  # 3 req/s limit

    async def search_by_keywords(self, keywords: str):
        async with self.semaphore:
            # Only 3 concurrent requests
            await self._make_request(keywords)
```

### T054: [P] Add security headers middleware
**File**: `backend/src/main.py`
**Action**: Add security headers to all responses
```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

---

## Phase 3.8: Performance Optimization (6 tasks)

### T055: [P] Add database indexes for common queries
**File**: `backend/alembic/versions/XXXX_add_performance_indexes.py`
**Action**: Create Alembic migration for performance indexes
```python
def upgrade():
    # Composite indexes for filtered queries
    op.create_index('idx_papers_task_stars', 'papers', ['primary_task', 'github_star_count'])
    op.create_index('idx_papers_year_venue', 'papers', ['year', 'venue'])

    # GIN indexes for JSONB containment queries
    op.create_index('idx_papers_datasets_gin', 'papers', ['datasets_used'], postgresql_using='gin')
    op.create_index('idx_papers_metrics_gin', 'papers', ['metrics_used'], postgresql_using='gin')

    # Full-text search index
    op.execute("""
        CREATE INDEX idx_papers_title_fts ON papers
        USING gin(to_tsvector('english', title))
    """)
```

### T056: [P] Convert github_metrics to TimescaleDB hypertable
**File**: SQL migration
**Action**: Enable TimescaleDB for time-series optimization
```sql
-- Convert to hypertable (run after table creation)
SELECT create_hypertable('github_metrics', 'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Add compression policy (compress data older than 30 days)
ALTER TABLE github_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'paper_id'
);

SELECT add_compression_policy('github_metrics', INTERVAL '30 days');
```

### T057: [P] Add connection pooling for database
**File**: `backend/src/database.py`
**Action**: Configure SQLAlchemy connection pool
```python
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,  # Max connections
    max_overflow=10,  # Extra connections under load
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False
)
```

### T058: [P] Add Redis caching for frequent queries
**File**: `backend/src/services/cache_service.py`
**Action**: Cache trending papers and popular citations
```python
import aioredis
import json

class CacheService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = aioredis.from_url(redis_url)

    async def get_trending_papers(self, metric: str, ttl: int = 3600):
        cache_key = f"trending:{metric}"
        cached = await self.redis.get(cache_key)

        if cached:
            return json.loads(cached)

        # Fetch from database
        papers = await db.get_trending_papers(metric)

        # Cache for 1 hour
        await self.redis.setex(cache_key, ttl, json.dumps(papers))

        return papers
```

### T059: [P] Add query result pagination
**File**: `backend/src/api/v1/papers.py`
**Action**: Implement cursor-based pagination for large result sets
```python
@router.get("/")
async def get_papers(
    cursor: Optional[str] = None,
    limit: int = 20
):
    if cursor:
        # Decode cursor (base64-encoded last_id)
        last_id = base64_decode(cursor)
        query = select(Paper).where(Paper.id > last_id).limit(limit)
    else:
        query = select(Paper).limit(limit)

    papers = await db.execute(query)
    items = papers.scalars().all()

    # Generate next cursor
    next_cursor = base64_encode(items[-1].id) if len(items) == limit else None

    return {"items": items, "next_cursor": next_cursor}
```

### T060: [P] Add background task monitoring
**File**: `backend/src/api/v1/monitoring.py`
**Action**: Celery worker health check endpoint
```python
@router.get("/health/celery")
async def celery_health():
    from celery import inspect

    i = inspect.app(celery_app)
    active_tasks = i.active()
    scheduled_tasks = i.scheduled()

    return {
        "status": "healthy" if active_tasks else "idle",
        "active_tasks": len(active_tasks or {}),
        "scheduled_tasks": len(scheduled_tasks or {})
    }
```

---

## Phase 3.9: Integration & Polish (12 tasks)

### T061: Write unit tests for ArXiv service
**File**: `backend/tests/unit/test_arxiv_service.py`
**Action**: Test retry logic, XML parsing, error handling
```python
@pytest.mark.asyncio
async def test_arxiv_retry_logic():
    service = AsyncArxivService(max_retry=3)
    # Mock failing requests
    # Verify exponential backoff
    pass

def test_arxiv_xml_parsing():
    xml_content = """<entry>...</entry>"""
    papers = service._parse_arxiv_xml(xml_content)
    assert len(papers) == 1
```

### T062: Write unit tests for GitHub service
**File**: `backend/tests/unit/test_github_service.py`
**Action**: Test hype score calculation, rate limiting
```python
def test_calculate_hype_scores():
    star_history = [(datetime(2024, 1, 1), 100), (datetime(2024, 2, 1), 200)]
    scores = calculate_hype_scores(star_history)
    assert 'weekly_hype' in scores
    assert scores['weekly_hype'] > 0
```

### T063: Write unit tests for PDF service
**File**: `backend/tests/unit/test_pdf_service.py`
**Action**: Test text extraction, table detection
```python
@pytest.mark.asyncio
async def test_extract_tables():
    service = PDFAnalysisService()
    pdf_path = Path("tests/fixtures/sample_paper.pdf")
    table_paths = await service.extract_tables(pdf_path)
    assert len(table_paths) > 0
    assert all(p.suffix == '.csv' for p in table_paths)
```

### T064: Write unit tests for LLM service
**File**: `backend/tests/unit/test_llm_service.py`
**Action**: Test prompt formatting, response parsing
```python
@pytest.mark.asyncio
async def test_openai_metadata_extraction():
    service = OpenAILLMService(api_key="test_key")
    # Mock OpenAI API response
    result = await service.extract_metadata(pdf_path, prompt)
    assert 'primary_task' in result
```

### T065: Write unit tests for citation service
**File**: `backend/tests/unit/test_citation_service.py`
**Action**: Test fuzzy matching edge cases
```python
def test_match_citation_with_unicode():
    citation = "Café: A Paper About Coffee (2024)"
    matcher = CitationMatcher()
    # Should match "Cafe: A Paper About Coffee"
    pass

def test_match_citation_threshold():
    # 84% similarity should NOT match (threshold 85%)
    # 86% similarity should match
    pass
```

### T066: Write unit tests for config service
**File**: `backend/tests/unit/test_config_service.py`
**Action**: Test JSON merging, env var precedence
```python
def test_deep_merge():
    base = {'a': {'b': 1}}
    update = {'a': {'c': 2}}
    merged = ConfigService._deep_merge([base, update])
    assert merged == {'a': {'b': 1, 'c': 2}}

def test_env_var_overrides_json(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'override')
    settings = Settings.load_from_json_dir(Path('configs'))
    assert settings.database_url == 'override'
```

### T067: Add logging to all services
**File**: `backend/src/services/*_service.py`
**Action**: Structured logging with loguru
```python
from loguru import logger

class AsyncArxivService:
    def __init__(self):
        self.log = logger.bind(service="arxiv")

    async def search_by_keywords(self, keywords: str):
        self.log.info(f"Searching ArXiv for: {keywords}")
        try:
            results = await self._fetch()
            self.log.info(f"Found {len(results)} papers")
            return results
        except Exception as e:
            self.log.error(f"ArXiv search failed: {e}")
            raise
```

### T068: Add error handling middleware
**File**: `backend/src/middleware/error_handler.py`
**Action**: Global exception handler for API
```python
from fastapi import Request, status
from fastapi.responses import JSONResponse

async def error_handler_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.detail}
        )
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error"}
        )

app.middleware("http")(error_handler_middleware)
```

### T069: Run performance tests
**File**: `backend/tests/performance/test_load.py`
**Action**: Load test trending papers endpoint
```bash
# Using locust for load testing
locust -f tests/performance/test_load.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```
```python
from locust import HttpUser, task, between

class PapersUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_trending_papers(self):
        self.client.get("/api/v1/github/trending?limit=50")

    @task
    def search_papers(self):
        self.client.get("/api/v1/papers?primary_task=image+segmentation&limit=20")
```
**Target**: < 2s response time for 100 concurrent users

### T070: Update API documentation
**File**: `backend/README.md`
**Action**: Document all new endpoints, configuration, deployment
```markdown
# HypePaper Backend - SOTAPapers Integration

## New Features
- Extended paper metadata (37 fields)
- Citation graph traversal
- GitHub star tracking with hype scores
- Background job processing (Celery)
- LLM-powered metadata extraction

## API Endpoints
- `GET /api/v1/papers` - List papers with extended filters
- `GET /api/v1/citations/graph` - Multi-level citation graph
- `GET /api/v1/github/trending` - Trending papers by hype score
- `POST /api/v1/jobs/crawl` - Trigger background crawl

## Configuration
...
```

### T071: Run all integration tests end-to-end
**File**: Test suite
**Action**: Execute full test suite and verify all scenarios pass
```bash
cd backend
pytest tests/integration/ -v --tb=short
```
**Verify**: All 5 integration tests pass (T013-T017)

### T072: Final code cleanup and review
**File**: All backend files
**Action**: Remove debug code, unused imports, add docstrings
- Run `ruff check backend/src/` - fix all linting errors
- Run `mypy backend/src/` - fix all type errors
- Remove commented code, debug prints
- Add docstrings to all public functions
- Update type hints for consistency

---

## Dependencies

### Critical Path
```
T001-T008 (Setup)
  → T009-T021 (Tests - must fail)
    → T022-T027 (Models - make tests pass)
      → T028-T034 (Services)
        → T035-T037 (Jobs)
          → T038-T049 (API Endpoints)
            → T050-T054 (Security)
              → T055-T060 (Performance)
                → T061-T072 (Polish)
```

### Blocking Dependencies
- T008 blocks all subsequent tasks (database must be migrated)
- T022-T027 block T028-T034 (services need models)
- T028-T034 block T035-T049 (API/jobs need services)
- T009-T021 must fail before T022 starts (TDD requirement)

### No Dependencies (Can Run in Parallel)
- T003, T004, T005, T006 (different config files)
- T009-T012 (contract tests, different files)
- T013-T017 (integration tests, independent scenarios)
- T018-T021 (unit tests, different modules)
- T022-T027 (models, different files)
- T028-T034 (services, different files)
- T035-T037 (jobs, different files)
- T051-T054 (security audit, different concerns)
- T055-T060 (performance, different optimizations)
- T061-T066 (unit tests, different modules)

---

## Parallel Execution Examples

### Example 1: Contract Tests (T009-T012)
Run all 4 contract tests in parallel since they're in different files:
```bash
# Terminal 1
pytest backend/tests/contract/test_papers_api.py -v

# Terminal 2
pytest backend/tests/contract/test_citations_api.py -v

# Terminal 3
pytest backend/tests/contract/test_github_api.py -v

# Terminal 4
pytest backend/tests/contract/test_jobs_api.py -v
```

Or using Task agent:
```
Task 1: "Write contract test for papers API in backend/tests/contract/test_papers_api.py validating papers-api.yaml OpenAPI schema. Test must fail since endpoints not implemented."
Task 2: "Write contract test for citations API in backend/tests/contract/test_citations_api.py validating citations-api.yaml OpenAPI schema."
Task 3: "Write contract test for GitHub API in backend/tests/contract/test_github_api.py validating github-api.yaml OpenAPI schema."
Task 4: "Write contract test for jobs API in backend/tests/contract/test_jobs_api.py validating jobs-api.yaml OpenAPI schema."
```

### Example 2: Models (T022-T027)
All models can be implemented in parallel:
```
Task 1: "Implement extended Paper model in backend/src/models/paper.py with 22 new fields from data-model.md. Add JSONB columns, indexes, and relationships."
Task 2: "Implement Author model in backend/src/models/author.py with many-to-many papers relationship."
Task 3: "Implement PaperReference model in backend/src/models/paper_reference.py for bidirectional citations."
Task 4: "Implement GitHubMetrics model in backend/src/models/github_metrics.py with TimescaleDB hypertable support."
Task 5: "Implement PDFContent model in backend/src/models/pdf_content.py for text and table storage."
Task 6: "Implement LLMExtraction model in backend/src/models/llm_extraction.py with verification workflow."
```

### Example 3: Services (T028-T034)
All services are independent:
```
Task 1: "Implement async ArXiv service in backend/src/services/arxiv_service.py with retry logic and exponential backoff."
Task 2: "Implement async GitHub service in backend/src/services/github_service.py using GitHub API (not scraping) with secure token auth."
Task 3: "Implement PDF analysis service in backend/src/services/pdf_service.py with GMFT table extraction in thread pool executor."
Task 4: "Implement LLM service abstraction in backend/src/services/llm_service.py supporting OpenAI and LlamaCpp."
Task 5: "Implement citation parsing service in backend/src/services/citation_service.py with Levenshtein fuzzy matching (≥85% threshold)."
Task 6: "Implement configuration service in backend/src/services/config_service.py with JSON deep merge and env var overrides."
Task 7: "Implement PDF storage service in backend/src/services/pdf_storage_service.py with structured filesystem paths."
```

---

## Validation Checklist
*GATE: Verify before marking phase complete*

**Setup Phase**:
- [x] All dependencies installed (requirements.txt)
- [x] System dependencies available (AnyStyle, TimescaleDB)
- [x] Database migrated (papers table has 37 fields)
- [x] Celery configured with Redis broker

**Test Phase**:
- [x] All 4 contract tests written and failing
- [x] All 5 integration tests written and failing
- [x] All 4 unit test files created and failing

**Implementation Phase**:
- [x] All 6 models implemented (Paper, Author, PaperReference, GitHubMetrics, PDFContent, LLMExtraction)
- [x] All 7 services implemented (ArXiv, GitHub, PDF, LLM, Citation, Config, Storage)
- [x] All 3 background jobs implemented (crawler, enricher, star tracker)
- [x] All 12 API endpoints implemented (4 papers, 3 citations, 2 github, 3 jobs)

**Security Phase**:
- [x] Hardcoded GitHub token revoked
- [x] No credentials in code or config files
- [x] Input validation on all endpoints
- [x] Rate limiting on external APIs
- [x] Security headers middleware added

**Performance Phase**:
- [x] Database indexes created
- [x] TimescaleDB hypertable configured
- [x] Connection pooling enabled
- [x] Redis caching added
- [x] Pagination implemented
- [x] Celery monitoring endpoint

**Polish Phase**:
- [x] Unit tests for all services (6 files)
- [x] Logging added to all services
- [x] Error handling middleware
- [x] Performance tests pass (< 2s, 100 users)
- [x] Documentation updated
- [x] All integration tests pass
- [x] Code cleanup complete (ruff, mypy)

---

## Notes

### TDD Enforcement
- **Phase 3.2 must fail** before Phase 3.3 starts
- Run `pytest backend/tests/contract/ backend/tests/integration/` after T021
- Verify all tests have status FAILED or ERROR
- Do not proceed to T022 until verification complete

### Performance Targets
- Single paper processing: 3-5 seconds
- Bulk crawling: Background jobs (no timeout)
- Page load: < 2 seconds for 20 papers
- Trending endpoint: < 2 seconds for 100 concurrent users
- Database queries: < 100ms for indexed lookups

### Rate Limits
- ArXiv API: 3 requests/second (use semaphore)
- GitHub API: 5000 requests/hour (track usage)
- Semantic Scholar: 10 requests/second (conservative)
- LLM services: Provider-specific (OpenAI: 10k TPM)

### Critical Security Reminder
**Task T050 must be completed first** before any code is pushed to repository. The exposed GitHub token `<REDACTED_GITHUB_TOKEN>` must be revoked immediately.

### Configuration Files Required
- `backend/configs/base.json` - General settings
- `backend/configs/database.json` - PostgreSQL connection
- `backend/configs/llm.json` - LLM providers (OpenAI, LlamaCpp)
- `backend/configs/github.json` - GitHub API settings
- `backend/configs/prompts.json` - LLM prompt templates
- `backend/.env` - Environment variables (secrets)

### External Dependencies
- AnyStyle CLI (Ruby gem): `gem install anystyle-cli`
- Redis server: `brew install redis` or Docker
- PostgreSQL with TimescaleDB: `CREATE EXTENSION timescaledb`
- Celery worker: `celery -A src.jobs.celery_app worker --loglevel=info`
- Celery beat: `celery -A src.jobs.celery_app beat --loglevel=info`

---

**Total Tasks**: 72
**Estimated Time**: 80-100 hours (full implementation)
**Parallel Tasks**: 41 (57% can run in parallel)
**Critical Path**: 31 sequential tasks
