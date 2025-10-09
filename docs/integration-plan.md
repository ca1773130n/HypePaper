# SOTAPapers → HypePaper Integration Plan

## Executive Summary

This document outlines the strategy for integrating SOTAPapers legacy code into the HypePaper project. The integration focuses on backend functionality: paper discovery, PDF analysis, GitHub tracking, and citation graphs. The plan prioritizes production-ready components, refactors fragile code, and discards over-engineered abstractions.

**Integration Timeline:** 4-6 weeks (120-160 hours)
**Risk Level:** Medium (web scraping dependencies, multiprocessing complexity)
**Value Proposition:** Comprehensive paper discovery + LLM metadata extraction + GitHub hype tracking

---

## Migration Strategy

### Keep (High Value)
1. **Database Schema** - Papers, references, metrics
2. **ArXiv Client** - Well-tested API wrapper
3. **Paper ID Generation** - Deterministic hashing
4. **LLM Extraction Logic** - Task/method/dataset prompts
5. **PDF Text Extraction** - Simple PyMuPDF wrapper
6. **GitHub Metrics Calculation** - Hype score algorithm
7. **Conference Metadata** - CVPR/ICLR field mappings

### Refactor (Needs Work)
1. **Paper Crawler** - Extract to async task queue
2. **GitHub Searcher** - Remove hardcoded token, add caching
3. **Reference Parser** - Simplify and add tests
4. **Database Layer** - Add repository pattern
5. **Settings System** - Migrate to Pydantic Settings
6. **Web Scraper** - Move to Playwright (async)
7. **FastAPI Endpoints** - Add auth, validation, pagination

### Discard (Not Needed)
1. **Google Scholar Scraper** - Use Semantic Scholar API instead
2. **Agent/Action System** - Over-engineered for simple use case
3. **Streamlit App** - HypePaper has its own frontend
4. **User Management** - HypePaper has auth system
5. **Registry/Action Abstractions** - Unused complexity
6. **tRPC Endpoint** - Use standard REST/GraphQL

---

## Component Mapping

### SOTAPapers → HypePaper Architecture

| SOTAPapers Component | HypePaper Destination | Changes Required |
|---------------------|----------------------|------------------|
| `core/models.py` (PaperORM) | `app/models/paper.py` | Merge with existing Paper model |
| `core/schemas.py` (Paper) | `app/schemas/paper.py` | Add new fields to existing schema |
| `core/database.py` (DataBase) | `app/db/repositories/paper.py` | Repository pattern |
| `modules/arxiv_client.py` | `app/services/arxiv.py` | Async refactor |
| `modules/paper_reader.py` | `app/services/pdf_analyzer.py` | Extract to service layer |
| `modules/github_repo_searcher.py` | `app/services/github.py` | Remove token, add caching |
| `pipelines/paper_crawler.py` | `app/tasks/paper_crawler.py` | Celery task |
| `pipelines/update_database_by_llm.py` | `app/tasks/llm_enrichment.py` | Celery task |
| `backend/webserver_main.py` | `app/api/v1/papers.py` | Merge endpoints |
| `utils/pdf_utils.py` | `app/utils/pdf.py` | Keep as-is |
| `configs/*.json` | `.env` + `app/config.py` | Pydantic Settings |

---

## Database Migration Plan

### Schema Differences

**SOTAPapers has (HypePaper missing):**
- `affiliations`, `affiliations_country`
- `primary_task`, `secondary_task`, `tertiary_task`
- `primary_method`, `secondary_method`, `tertiary_method`
- `datasets_used`, `metrics_used`, `comparisons`, `limitations`
- `github_star_avg_hype`, `github_star_weekly_hype`, `github_star_monthly_hype`
- `github_star_tracking_start_date`, `github_star_tracking_latest_footprint`
- `session_type`, `accept_status`, `note`
- `paper_references` many-to-many table

**HypePaper has (SOTAPapers missing):**
- `description` - Can map from `abstract`
- `published_at` - Can map from `year`
- `updated_at`, `created_at` - Timestamps
- Likely has different relationship structure

### Migration Steps

#### Phase 1: Schema Extension (Week 1)
1. **Create Alembic migration** to add SOTAPapers fields:
   ```python
   # Add to existing papers table
   op.add_column('papers', sa.Column('arxiv_id', sa.String(50), index=True))
   op.add_column('papers', sa.Column('affiliations', sa.JSON()))
   op.add_column('papers', sa.Column('primary_task', sa.String(200)))
   # ... etc
   ```

2. **Create paper_references table:**
   ```python
   op.create_table(
       'paper_references',
       sa.Column('paper_id', sa.String(), sa.ForeignKey('papers.id')),
       sa.Column('reference_id', sa.String(), sa.ForeignKey('papers.id')),
       sa.PrimaryKeyConstraint('paper_id', 'reference_id')
   )
   ```

3. **Update Paper model** (`app/models/paper.py`):
   ```python
   class Paper(Base):
       # Existing fields
       id: Mapped[str] = mapped_column(String, primary_key=True)
       title: Mapped[str] = mapped_column(String(500))

       # Add SOTAPapers fields
       arxiv_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
       affiliations: Mapped[Optional[List[str]]] = mapped_column(JSON)
       primary_task: Mapped[Optional[str]] = mapped_column(String(200))
       # ...

       # Add relationships
       references: Mapped[List["Paper"]] = relationship(
           "Paper",
           secondary="paper_references",
           primaryjoin="Paper.id == paper_references.c.paper_id",
           secondaryjoin="Paper.id == paper_references.c.reference_id",
           backref="cited_by"
       )
   ```

4. **Update Pydantic schemas** (`app/schemas/paper.py`):
   ```python
   class PaperBase(BaseModel):
       # Existing fields
       title: str
       url: Optional[str]

       # Add nested schemas
       content: Optional[PaperContent]
       media: Optional[PaperMedia]
       metrics: Optional[PaperMetrics]

   class PaperContent(BaseModel):
       abstract: Optional[str]
       bibtex: Optional[str]
       primary_task: Optional[str]
       # ...
   ```

#### Phase 2: Data Migration (Week 2)
1. **Write migration script** (`scripts/migrate_sotapapers.py`):
   ```python
   def migrate_sotapapers_data():
       # Connect to both databases
       sota_db = create_engine('sqlite:///sotapapers.db')
       hype_db = create_engine(settings.DATABASE_URL)

       # For each paper in sotapapers.db:
       for sota_paper in sota_session.query(PaperORM).all():
           # Generate ID using same hash function
           paper_id = make_generated_id(sota_paper.title, sota_paper.year)

           # Check if exists in HypePaper
           existing = hype_session.query(Paper).filter_by(id=paper_id).first()

           if existing:
               # Update with SOTAPapers data
               existing.arxiv_id = sota_paper.arxiv_id
               existing.primary_task = sota_paper.primary_task
               # ...
           else:
               # Create new paper
               new_paper = Paper(
                   id=paper_id,
                   title=sota_paper.title,
                   # Map fields
               )
               hype_session.add(new_paper)

       # Migrate references
       for ref in sota_session.query(paper_references).all():
           hype_session.execute(
               paper_references.insert().values(
                   paper_id=ref.paper_id,
                   reference_id=ref.reference_id
               )
           )
   ```

2. **Handle ID conflicts:**
   - Use `make_generated_id(title, year)` from SOTAPapers
   - If HypePaper uses UUIDs, add `sota_id` column for mapping

3. **Migrate relationships:**
   - Copy `paper_references` table
   - Validate referential integrity

4. **Backfill missing data:**
   - Run ArXiv lookup for papers missing `arxiv_id`
   - Run GitHub search for papers missing `github_url`

#### Phase 3: Validation (Week 2)
1. **Data integrity checks:**
   ```sql
   -- Check for orphaned references
   SELECT * FROM paper_references
   WHERE paper_id NOT IN (SELECT id FROM papers)
   OR reference_id NOT IN (SELECT id FROM papers);

   -- Check for duplicate ArXiv IDs
   SELECT arxiv_id, COUNT(*) FROM papers
   WHERE arxiv_id IS NOT NULL
   GROUP BY arxiv_id HAVING COUNT(*) > 1;
   ```

2. **Unit tests for converters:**
   ```python
   def test_sota_to_hype_conversion():
       sota_paper = create_sota_paper()
       hype_paper = convert_sota_to_hype(sota_paper)
       assert hype_paper.arxiv_id == sota_paper.arxiv_id
       assert len(hype_paper.references) == len(sota_paper.references)
   ```

---

## API Integration

### New Endpoints to Add

#### Paper Discovery
```python
@router.post("/api/v1/papers/discover")
async def discover_papers(
    query: PaperDiscoveryQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Discover papers via ArXiv/Semantic Scholar.

    Query params:
    - keywords: List[str] - Search keywords
    - sources: List[str] - arxiv, semantic_scholar
    - max_results: int - Limit per source
    - enrich: bool - Run LLM extraction
    """
    # Trigger Celery task
    task = discover_papers_task.delay(
        keywords=query.keywords,
        sources=query.sources,
        user_id=current_user.id
    )
    return {"task_id": task.id}
```

#### Conference Crawling
```python
@router.post("/api/v1/papers/crawl-conference")
async def crawl_conference(
    config: ConferenceCrawlConfig,
    current_user: User = Depends(get_current_user)
):
    """
    Crawl conference proceedings (CVPR, ICLR, etc.)

    Config:
    - conference: str - cvpr, iclr, etc.
    - year: int
    - keywords: List[str] - Filter papers
    - recursive_depth: int - Citation crawl depth
    """
    task = crawl_conference_task.delay(
        conference=config.conference,
        year=config.year,
        keywords=config.keywords,
        recursive_depth=config.recursive_depth
    )
    return {"task_id": task.id}
```

#### GitHub Enrichment
```python
@router.post("/api/v1/papers/{paper_id}/enrich-github")
async def enrich_github_data(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Find GitHub repo and calculate hype metrics.
    """
    paper = await paper_repo.get(paper_id)

    # Search GitHub
    repo = await github_service.search_repo(
        title=paper.title,
        arxiv_id=paper.arxiv_id
    )

    if repo:
        # Update metrics
        paper.github_url = repo.url
        paper.github_star_count = repo.stars
        paper.github_star_avg_hype = calculate_hype(
            stars=repo.stars,
            citations=paper.citations_total,
            age_days=repo.age_days
        )
        await db.commit()

    return {"github_url": repo.url if repo else None}
```

#### LLM Extraction
```python
@router.post("/api/v1/papers/{paper_id}/extract-metadata")
async def extract_metadata(
    paper_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract tasks, methods, datasets from PDF using LLM.
    """
    paper = await paper_repo.get(paper_id)

    # Download PDF if not cached
    if not pdf_cache.exists(paper_id):
        await pdf_service.download(paper.pdf_url, paper_id)

    # Queue extraction task
    background_tasks.add_task(
        llm_extraction_service.extract_all,
        paper_id=paper_id
    )

    return {"status": "queued"}
```

#### Citation Graph
```python
@router.get("/api/v1/papers/{paper_id}/graph")
async def get_citation_graph(
    paper_id: str,
    depth: int = 2,
    direction: str = "both",  # forward, backward, both
    db: AsyncSession = Depends(get_db)
):
    """
    Get citation graph for paper.

    Returns:
    {
        "nodes": [{"id": "...", "title": "...", "metrics": {...}}],
        "edges": [{"source": "id1", "target": "id2", "type": "cites"}]
    }
    """
    graph = await citation_service.build_graph(
        paper_id=paper_id,
        depth=depth,
        direction=direction
    )
    return graph
```

### Updated Endpoints

**Existing `GET /api/v1/papers/`** - Add filters:
```python
@router.get("/api/v1/papers/")
async def list_papers(
    task: Optional[str] = None,  # Filter by research task
    min_hype: Optional[int] = None,  # Min hype score
    has_github: Optional[bool] = None,  # Has GitHub repo
    conference: Optional[str] = None,  # Venue filter
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Enhanced paper listing with SOTAPapers filters."""
    query = select(Paper)

    if task:
        query = query.where(
            or_(
                Paper.primary_task == task,
                Paper.secondary_task == task,
                Paper.tertiary_task == task
            )
        )

    if min_hype:
        query = query.where(Paper.github_star_avg_hype >= min_hype)

    # ... pagination

    return {"papers": papers, "total": total, "page": page}
```

---

## Refactoring Priorities

### 1. Async Architecture (Week 3)

**Problem:** SOTAPapers uses synchronous I/O (requests, Selenium)
**Solution:** Migrate to async/await with httpx and Playwright

**Before (sync):**
```python
def search_by_title(self, title: str) -> Paper:
    response = requests.get(f"https://arxiv.org/search?q={title}")
    # Process response
```

**After (async):**
```python
async def search_by_title(self, title: str) -> Paper:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://arxiv.org/search?q={title}")
        # Process response
```

**Migration Steps:**
1. Replace `requests` → `httpx.AsyncClient`
2. Replace Selenium → Playwright (async browser automation)
3. Add async database sessions (already in HypePaper)
4. Use `asyncio.gather()` for parallel API calls

### 2. Repository Pattern (Week 3)

**Problem:** Database queries scattered across modules
**Solution:** Centralize in repository classes

**Create `app/db/repositories/paper.py`:**
```python
class PaperRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, paper_id: str) -> Optional[Paper]:
        result = await self.db.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        return result.scalar_one_or_none()

    async def get_by_arxiv_id(self, arxiv_id: str) -> Optional[Paper]:
        result = await self.db.execute(
            select(Paper).where(Paper.arxiv_id == arxiv_id)
        )
        return result.scalar_one_or_none()

    async def get_with_references(
        self,
        paper_id: str,
        depth: int = 1
    ) -> Optional[Paper]:
        # Load paper with eager loading
        result = await self.db.execute(
            select(Paper)
            .options(selectinload(Paper.references))
            .where(Paper.id == paper_id)
        )
        return result.scalar_one_or_none()

    async def create(self, paper: Paper) -> Paper:
        self.db.add(paper)
        await self.db.commit()
        await self.db.refresh(paper)
        return paper

    async def update_metrics(
        self,
        paper_id: str,
        metrics: PaperMetrics
    ) -> Paper:
        paper = await self.get(paper_id)
        paper.github_star_count = metrics.github_star_count
        paper.github_star_avg_hype = metrics.github_star_avg_hype
        # ...
        await self.db.commit()
        return paper

    async def add_reference(
        self,
        paper_id: str,
        reference_id: str
    ):
        await self.db.execute(
            paper_references.insert().values(
                paper_id=paper_id,
                reference_id=reference_id
            )
        )
        await self.db.commit()

    async def get_top_by_hype(
        self,
        limit: int = 10
    ) -> List[Paper]:
        result = await self.db.execute(
            select(Paper)
            .order_by(Paper.github_star_avg_hype.desc())
            .limit(limit)
        )
        return result.scalars().all()
```

### 3. Service Layer (Week 4)

**Create `app/services/arxiv.py`:**
```python
class ArxivService:
    def __init__(self, config: Settings):
        self.config = config
        self.max_results = config.ARXIV_MAX_RESULTS

    async def search(self, keywords: List[str]) -> List[Paper]:
        """Search ArXiv and convert to Paper schema."""
        async with httpx.AsyncClient() as client:
            results = await self._search_arxiv(keywords, client)
            papers = [self._convert_to_paper(r) for r in results]
            return papers

    async def get_by_id(self, arxiv_id: str) -> Optional[Paper]:
        # ... implementation

    def _convert_to_paper(self, arxiv_result) -> Paper:
        """Convert ArXiv API response to Paper schema."""
        return Paper(
            id=make_generated_id(arxiv_result.title, arxiv_result.year),
            arxiv_id=arxiv_result.get_short_id(),
            title=arxiv_result.title,
            # ... map all fields
        )
```

**Create `app/services/github.py`:**
```python
class GitHubService:
    def __init__(self, config: Settings, cache: Redis):
        self.token = config.GITHUB_TOKEN
        self.cache = cache

    async def search_repo(
        self,
        title: str,
        arxiv_id: Optional[str] = None
    ) -> Optional[GitHubRepo]:
        """
        Search for GitHub repo via:
        1. Papers with Code API (if arxiv_id)
        2. GitHub API search (fallback)
        """
        # Check cache first
        cache_key = f"github_repo:{arxiv_id or title}"
        cached = await self.cache.get(cache_key)
        if cached:
            return GitHubRepo.parse_raw(cached)

        repo = None

        # Try Papers with Code first
        if arxiv_id:
            repo = await self._search_papers_with_code(arxiv_id)

        # Fallback to GitHub search
        if not repo:
            repo = await self._search_github_api(title)

        # Cache result
        if repo:
            await self.cache.setex(
                cache_key,
                3600 * 24,  # 24 hours
                repo.json()
            )

        return repo

    async def get_repo_metrics(self, repo_url: str) -> RepoMetrics:
        """Scrape star count and calculate hype."""
        # Use Playwright for dynamic content
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(repo_url)

            star_count = await page.locator('a[href*="stargazers"]').text_content()
            # ... parse and calculate metrics

        return RepoMetrics(
            stars=stars,
            age_days=age,
            hype_score=self._calculate_hype(stars, age)
        )

    def _calculate_hype(
        self,
        stars: int,
        citations: int,
        age_days: int
    ) -> float:
        """Calculate hype score."""
        if age_days <= 0:
            return 0.0
        return (citations * 100 + stars) / age_days
```

**Create `app/services/pdf_analyzer.py`:**
```python
class PDFAnalyzerService:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def extract_all(self, pdf_path: Path) -> PaperContent:
        """Extract all metadata from PDF."""
        full_text = await self._extract_text(pdf_path)

        # Run extractions in parallel
        results = await asyncio.gather(
            self.extract_abstract(full_text),
            self.extract_tasks(full_text),
            self.extract_methods(full_text),
            self.extract_datasets(full_text),
            self.extract_references(pdf_path)
        )

        return PaperContent(
            abstract=results[0],
            primary_task=results[1][0] if results[1] else None,
            # ... map all fields
        )

    async def extract_references(self, pdf_path: Path) -> List[Paper]:
        """Parse references section."""
        # Use SOTAPapers logic but async
        # ...
```

### 4. Task Queue Integration (Week 4)

**Use Celery for long-running tasks:**

**Create `app/tasks/paper_crawler.py`:**
```python
from celery import shared_task

@shared_task(bind=True)
def discover_papers_task(
    self,
    keywords: List[str],
    sources: List[str],
    user_id: str
):
    """
    Background task for paper discovery.

    Updates task progress for frontend polling.
    """
    total_sources = len(sources)
    papers_found = []

    for i, source in enumerate(sources):
        self.update_state(
            state='PROGRESS',
            meta={'current': i, 'total': total_sources}
        )

        if source == 'arxiv':
            arxiv_papers = await arxiv_service.search(keywords)
            papers_found.extend(arxiv_papers)

        elif source == 'semantic_scholar':
            ss_papers = await semantic_scholar_service.search(keywords)
            papers_found.extend(ss_papers)

    # Insert to database
    async with get_async_session() as db:
        repo = PaperRepository(db)
        for paper in papers_found:
            await repo.create(paper)

    return {'papers_found': len(papers_found)}

@shared_task
def crawl_conference_task(
    conference: str,
    year: int,
    keywords: List[str],
    recursive_depth: int
):
    """Crawl conference proceedings."""
    # Adapt SOTAPapers logic but async
    # ...

@shared_task
def llm_extraction_task(paper_id: str):
    """Extract metadata from PDF using LLM."""
    async with get_async_session() as db:
        repo = PaperRepository(db)
        paper = await repo.get(paper_id)

        # Download PDF
        pdf_path = await pdf_service.download(paper.pdf_url)

        # Extract metadata
        content = await pdf_analyzer.extract_all(pdf_path)

        # Update paper
        paper.primary_task = content.primary_task
        paper.primary_method = content.primary_method
        # ...
        await db.commit()
```

### 5. Configuration Refactor (Week 5)

**Migrate from JSON to Pydantic Settings:**

**Create `app/config.py`:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Database
    DATABASE_URL: str

    # External APIs
    ARXIV_MAX_RESULTS: int = 100
    ARXIV_RETRY_DELAY: int = 3

    GITHUB_TOKEN: str
    GITHUB_API_URL: str = "https://api.github.com"

    SEMANTIC_SCHOLAR_API_KEY: Optional[str] = None
    SEMANTIC_SCHOLAR_API_URL: str = "https://api.semanticscholar.org/v1"

    OPENAI_API_KEY: Optional[str] = None

    # LLM Server
    LLAMA_CPP_SERVER_URL: str = "http://localhost:10002/v1/chat/completions"
    LLAMA_CPP_MODEL: str = "Polaris-7B-preview"
    LLAMA_CPP_MAX_TOKENS: int = 163840

    # Crawler
    PDF_DOWNLOAD_PATH: Path = Path("./data/pdfs")
    CRAWLER_RECURSIVE_DEPTH: int = 2
    CRAWLER_REQUEST_TIMEOUT: int = 300

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Migration from JSON configs:**
1. Copy values from `configs/*.json` to `.env.example`
2. Create `.env` file (gitignored)
3. Update all modules to use `settings = get_settings()`

---

## Dependencies Management

### Add to `requirements.txt` / `pyproject.toml`

**New Dependencies:**
```toml
# ArXiv
arxiv = "^2.1.0"

# Semantic Scholar
semanticscholar = "^0.8.0"

# PDF Processing
PyMuPDF = "^1.24.0"
gmft = "^0.2.0"  # Table extraction

# LLM
openai = "^1.35.0"
llama-index = "^0.10.0"

# Web Scraping (replace Selenium)
playwright = "^1.44.0"
httpx = "^0.27.0"

# Task Queue
celery = "^5.3.0"
redis = "^5.0.0"

# Utilities
python-dotenv = "^1.0.0"
loguru = "^0.7.0"
```

**Remove (if not used elsewhere):**
```toml
# Remove heavy/fragile dependencies
torch  # 50GB+ (only if not needed)
selenium
undetected-chromedriver
scholarly  # Google Scholar scraper (against ToS)
streamlit  # Frontend (HypePaper has its own)
```

### Version Pinning Strategy
```toml
[tool.poetry.dependencies]
# Pin major versions, allow minor/patch updates
arxiv = "~2.1.0"
httpx = "~0.27.0"
# ... etc
```

---

## Testing Strategy

### Unit Tests (Week 5)

**Test Converters:**
```python
# tests/unit/test_converters.py
def test_sota_paper_to_hype_paper():
    sota_paper = PaperORM(
        id="test_id",
        title="Test Paper",
        arxiv_id="1234.5678",
        # ...
    )

    hype_paper = create_paper_from_orm(sota_paper)

    assert hype_paper.id == "test_id"
    assert hype_paper.arxiv_id == "1234.5678"

def test_paper_id_generation():
    id1 = make_generated_id("Attention Is All You Need", 2017)
    id2 = make_generated_id("Attention Is All You Need", 2017)
    assert id1 == id2  # Deterministic

    id3 = make_generated_id("Different Title", 2017)
    assert id1 != id3  # Different titles
```

**Test Services:**
```python
# tests/unit/test_arxiv_service.py
@pytest.mark.asyncio
async def test_arxiv_search(mock_httpx):
    mock_httpx.get.return_value = mock_arxiv_response()

    service = ArxivService(get_settings())
    papers = await service.search(["transformers"])

    assert len(papers) > 0
    assert papers[0].arxiv_id is not None

# tests/unit/test_github_service.py
@pytest.mark.asyncio
async def test_github_search_with_cache(redis_mock):
    service = GitHubService(get_settings(), redis_mock)

    # First call - miss cache
    repo1 = await service.search_repo("Attention Is All You Need", "1706.03762")

    # Second call - hit cache
    repo2 = await service.search_repo("Attention Is All You Need", "1706.03762")

    assert repo1 == repo2
    redis_mock.get.assert_called_once()
```

### Integration Tests (Week 5)

**Test Database Operations:**
```python
# tests/integration/test_paper_repository.py
@pytest.mark.asyncio
async def test_create_paper_with_references(async_db):
    repo = PaperRepository(async_db)

    # Create main paper
    paper = Paper(
        id="paper1",
        title="Main Paper",
        # ...
    )
    await repo.create(paper)

    # Create reference
    ref_paper = Paper(
        id="ref1",
        title="Reference Paper",
        # ...
    )
    await repo.create(ref_paper)

    # Add reference relationship
    await repo.add_reference("paper1", "ref1")

    # Query with relationships
    paper_with_refs = await repo.get_with_references("paper1")

    assert len(paper_with_refs.references) == 1
    assert paper_with_refs.references[0].id == "ref1"
```

**Test API Endpoints:**
```python
# tests/integration/test_papers_api.py
@pytest.mark.asyncio
async def test_discover_papers_endpoint(async_client, celery_app):
    response = await async_client.post(
        "/api/v1/papers/discover",
        json={
            "keywords": ["transformers"],
            "sources": ["arxiv"],
            "max_results": 10
        }
    )

    assert response.status_code == 200
    assert "task_id" in response.json()

    # Wait for task completion
    task_id = response.json()["task_id"]
    result = celery_app.AsyncResult(task_id).get(timeout=30)

    assert result["papers_found"] > 0
```

### End-to-End Tests (Week 6)

**Test Full Crawl Pipeline:**
```python
# tests/e2e/test_paper_crawl.py
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_paper_crawl(async_db):
    # 1. Search ArXiv
    arxiv_service = ArxivService(get_settings())
    papers = await arxiv_service.search(["transformers"])

    assert len(papers) > 0
    paper = papers[0]

    # 2. Find GitHub repo
    github_service = GitHubService(get_settings(), redis_client)
    repo = await github_service.search_repo(paper.title, paper.arxiv_id)

    if repo:
        paper.github_url = repo.url

    # 3. Download PDF
    pdf_path = await pdf_service.download(paper.pdf_url)

    assert pdf_path.exists()

    # 4. Extract metadata
    pdf_analyzer = PDFAnalyzerService(llm_client)
    content = await pdf_analyzer.extract_all(pdf_path)

    assert content.abstract is not None

    # 5. Save to database
    repo = PaperRepository(async_db)
    saved_paper = await repo.create(paper)

    assert saved_paper.id == paper.id
```

---

## Timeline & Effort Estimation

### Phase 1: Foundation (Week 1-2) - 40 hours
- [ ] Database schema extension (Alembic migration) - 8 hours
- [ ] Update Paper model and schemas - 6 hours
- [ ] Data migration script (SOTAPapers → HypePaper) - 10 hours
- [ ] Validation and integrity checks - 6 hours
- [ ] ID generation utilities - 4 hours
- [ ] Configuration refactor (JSON → Pydantic Settings) - 6 hours

### Phase 2: Services (Week 3-4) - 50 hours
- [ ] Async ArXiv service - 8 hours
- [ ] Async GitHub service (with caching) - 12 hours
- [ ] PDF analyzer service - 14 hours
- [ ] Semantic Scholar integration - 6 hours
- [ ] Repository pattern implementation - 10 hours

### Phase 3: API & Tasks (Week 4-5) - 40 hours
- [ ] Paper discovery endpoints - 8 hours
- [ ] Conference crawl endpoints - 8 hours
- [ ] GitHub enrichment endpoints - 6 hours
- [ ] Citation graph endpoints - 8 hours
- [ ] Celery task integration - 10 hours

### Phase 4: Testing (Week 5-6) - 30 hours
- [ ] Unit tests (converters, services) - 12 hours
- [ ] Integration tests (database, API) - 10 hours
- [ ] End-to-end tests (full pipeline) - 8 hours

**Total Estimated Effort:** 160 hours (4-6 weeks for 1 developer)

### Risk Mitigation
- **Week 1:** Database migration - High risk, do first
- **Week 3:** Async refactor - Can parallelize with API work
- **Week 5:** Testing - Can be done iteratively throughout

---

## Recommended Integration Order

### Critical Path (Must Have)

1. **Database Schema (Week 1)**
   - Blocker for everything else
   - Run migrations on dev/staging first
   - Validate data integrity

2. **ArXiv Service (Week 3)**
   - Highest value, lowest risk
   - Well-documented API
   - Essential for paper discovery

3. **Repository Pattern (Week 3)**
   - Enables clean service layer
   - Required for async operations

4. **Paper Discovery API (Week 4)**
   - User-facing feature
   - Integrates ArXiv service

### High Priority (Should Have)

5. **GitHub Service (Week 3-4)**
   - High user value (hype tracking)
   - Fix security issue immediately
   - Add caching to reduce API calls

6. **PDF Analyzer (Week 4)**
   - Unique selling point (LLM extraction)
   - Complex, allocate more time

7. **Celery Tasks (Week 4-5)**
   - Enables background processing
   - Required for long-running crawls

### Medium Priority (Nice to Have)

8. **Conference Crawler (Week 5)**
   - Lower priority than ArXiv
   - Fragile web scraping
   - Consider deprioritizing if timeline tight

9. **Citation Graph API (Week 5)**
   - Cool feature but not MVP
   - Requires reference relationships working

### Low Priority (Future Enhancements)

10. **Semantic Scholar (Week 6)**
    - Can use ArXiv as primary source
    - Add later for citation counts

11. **Advanced Filters (Week 6)**
    - Task-based search, affiliations, etc.
    - Polish after core features stable

---

## Biggest Challenges

### 1. Multiprocessing → Async Migration
**Challenge:** SOTAPapers uses multiprocessing for parallel downloads
**Solution:** Use asyncio with bounded semaphore
```python
async def download_papers(papers: List[Paper], max_concurrent: int = 10):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def download_with_limit(paper):
        async with semaphore:
            return await pdf_service.download(paper.pdf_url)

    tasks = [download_with_limit(p) for p in papers]
    return await asyncio.gather(*tasks)
```

### 2. Web Scraping Reliability
**Challenge:** Conference sites and GitHub change layouts
**Solution:**
- Add retry logic with exponential backoff
- Cache results in Redis (24h TTL)
- Implement fallback strategies
- Monitor failure rates via Sentry

### 3. LLM Extraction Accuracy
**Challenge:** LLM prompts may produce inconsistent results
**Solution:**
- Validate extracted data with Pydantic
- Use structured output (JSON mode)
- Implement human review queue for low-confidence results
- Track extraction success rates

### 4. Database Performance
**Challenge:** Deep citation graphs (N+1 queries)
**Solution:**
- Use `selectinload()` for eager loading
- Add database indexes on arxiv_id, primary_task
- Implement pagination on all list endpoints
- Consider graph database (Neo4j) for citation network

### 5. Security & Secrets Management
**Challenge:** Hardcoded tokens in legacy code
**Solution:**
- Immediate: Revoke exposed GitHub token
- Add all secrets to `.env` file (gitignored)
- Use environment variables in production
- Rotate keys quarterly

---

## Success Criteria

### MVP Launch (6 weeks)
- [ ] All SOTAPapers papers migrated to HypePaper database
- [ ] ArXiv search endpoint functional
- [ ] GitHub hype tracking working for new papers
- [ ] PDF metadata extraction (tasks/methods/datasets)
- [ ] Citation graph API (depth=1)
- [ ] Background task queue operational
- [ ] 80% test coverage on core services

### Phase 2 (8 weeks)
- [ ] Conference crawler (CVPR, ICLR)
- [ ] Recursive citation discovery
- [ ] Advanced filters (task, venue, hype score)
- [ ] Semantic Scholar integration
- [ ] Real-time GitHub star tracking
- [ ] Admin dashboard for crawler monitoring

### Metrics
- **Performance:** API response time < 200ms (p95)
- **Reliability:** 99% uptime for paper discovery
- **Data Quality:** 95% accuracy on LLM extraction (human eval)
- **Coverage:** 10k+ papers in database
- **Engagement:** Users create 100+ discovery queries/week

---

## Appendix A: Security Audit

### Critical Issues (Fix Immediately)

1. **Hardcoded GitHub Token**
   - **Location:** `modules/github_repo_searcher.py:75, 110`
   - **Token:** `<REDACTED_GITHUB_TOKEN>`
   - **Action:**
     ```bash
     # Revoke token on GitHub
     # Generate new token with repo:public_repo scope only
     # Add to .env
     GITHUB_TOKEN=new_token_here
     ```

2. **No API Authentication**
   - **Location:** `backend/webserver_main.py`
   - **Issue:** All endpoints publicly accessible
   - **Action:** Add JWT middleware from HypePaper

3. **SQL Injection Risk**
   - **Location:** `modules/database_query_agent.py` (if exists)
   - **Issue:** User input in SQL queries
   - **Action:** Always use parameterized queries

### Medium Risk

4. **No Rate Limiting**
   - External APIs (ArXiv, GitHub) can be overwhelmed
   - **Action:** Add rate limiters with Redis

5. **Exposed Secrets in Logs**
   - Loguru may log API responses
   - **Action:** Redact sensitive fields

### Low Risk

6. **No Input Validation**
   - Paper titles, keywords not sanitized
   - **Action:** Use Pydantic validators

---

## Appendix B: Example Migration Script

```python
#!/usr/bin/env python3
"""
Migrate SOTAPapers data to HypePaper database.

Usage:
    python scripts/migrate_sotapapers.py --sota-db sotapapers.db --dry-run
"""

import argparse
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import AsyncSessionLocal
from app.models.paper import Paper
from app.utils.id import make_generated_id

async def migrate(sota_db_path: str, dry_run: bool = False):
    # Connect to SOTAPapers database
    sota_engine = create_engine(f'sqlite:///{sota_db_path}')
    SotaSession = sessionmaker(bind=sota_engine)
    sota_session = SotaSession()

    # Count papers
    total_papers = sota_session.execute("SELECT COUNT(*) FROM papers").scalar()
    print(f"Found {total_papers} papers in SOTAPapers DB")

    # Migrate papers
    async with AsyncSessionLocal() as hype_db:
        sota_papers = sota_session.execute("SELECT * FROM papers").fetchall()

        migrated = 0
        skipped = 0
        errors = 0

        for sota_paper in sota_papers:
            try:
                # Check if already exists
                paper_id = make_generated_id(sota_paper.title, sota_paper.year)
                existing = await hype_db.get(Paper, paper_id)

                if existing:
                    print(f"Skipping existing paper: {sota_paper.title}")
                    skipped += 1
                    continue

                # Create new paper
                new_paper = Paper(
                    id=paper_id,
                    title=sota_paper.title,
                    arxiv_id=sota_paper.arxiv_id,
                    # Map all fields...
                )

                if not dry_run:
                    hype_db.add(new_paper)
                    await hype_db.flush()

                migrated += 1
                print(f"Migrated: {sota_paper.title}")

            except Exception as e:
                print(f"Error migrating {sota_paper.title}: {e}")
                errors += 1

        if not dry_run:
            await hype_db.commit()

    print(f"\nMigration complete:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sota-db", required=True, help="Path to sotapapers.db")
    parser.add_argument("--dry-run", action="store_true", help="Don't commit changes")
    args = parser.parse_args()

    asyncio.run(migrate(args.sota_db, args.dry_run))
```

---

## Appendix C: Hype Score Algorithm

**From SOTAPapers:**
```python
def calculate_hype_score(
    stars: int,
    citations: int,
    age_days: int
) -> float:
    """
    Calculate paper hype score.

    Formula: (citations * 100 + stars) / age_days

    Rationale:
    - Citations weighted 100x (academic impact)
    - Stars indicate practical adoption
    - Normalized by age (newer papers get boost)

    Examples:
    - New paper (30 days, 10 citations, 50 stars): (1000 + 50) / 30 = 35.0
    - Old paper (1000 days, 100 citations, 1000 stars): (10000 + 1000) / 1000 = 11.0
    """
    if age_days <= 0:
        return 0.0

    weighted_score = (citations * 100) + stars
    return weighted_score / age_days
```

**Improvements for HypePaper:**
- Add time decay factor (exponential)
- Consider star velocity (weekly growth)
- Normalize by field (CV vs NLP)
- Add quality signals (venue tier, author h-index)

---

**End of Integration Plan**
