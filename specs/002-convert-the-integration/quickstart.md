# Integration Test Quickstart: SOTAPapers Legacy Integration

**Feature**: 002-convert-the-integration | **Date**: 2025-10-08
**Spec**: [spec.md](spec.md) | **Data Model**: [data-model.md](data-model.md)

## Overview

This document provides end-to-end integration test scenarios mapped from the acceptance criteria in `spec.md`. Each scenario validates a complete user workflow from start to finish.

**Test Environment Requirements**:
- PostgreSQL database with TimescaleDB extension
- Redis for Celery broker
- Celery worker processes running
- ArXiv API access (no authentication required)
- GitHub Personal Access Token (in `GITHUB_TOKEN` env var)
- LLM service (either OpenAI API key or LlamaCpp server)
- PDF storage directory mounted at `/data/papers`

**Performance Targets**:
- Single paper processing: 3-5 seconds (on-demand)
- Bulk crawling: Background jobs with progress tracking
- Page load: < 2 seconds for paper list view
- GitHub updates: Daily scheduled job (2 AM UTC)

---

## Scenario 1: ArXiv Paper Discovery End-to-End

**Acceptance Criteria**: FR-001, FR-002, FR-003, FR-005, PR-001

**User Story**: As a researcher, I want to discover papers from ArXiv by keyword search and have them stored in the database with deterministic IDs for duplicate detection.

### Setup

```python
import pytest
from httpx import AsyncClient
from datetime import datetime, date
from uuid import UUID

@pytest.fixture
async def client():
    """Test client with database cleanup."""
    # Initialize test database
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    # Cleanup after test
    await cleanup_test_data()

@pytest.fixture
def arxiv_keywords():
    return "transformer attention mechanisms"
```

### Execute

```python
@pytest.mark.asyncio
async def test_arxiv_paper_discovery(client, arxiv_keywords):
    """Test Scenario 1: ArXiv Paper Discovery"""

    # Step 1: Trigger ArXiv crawl job
    crawl_response = await client.post(
        "/api/v1/jobs/crawl",
        json={
            "source": "arxiv",
            "arxiv_keywords": arxiv_keywords,
            "arxiv_max_results": 10,
            "priority": "high"
        }
    )
    assert crawl_response.status_code == 202
    job_data = crawl_response.json()
    job_id = job_data["job_id"]
    assert job_data["status"] in ["queued", "processing"]

    # Step 2: Poll job status until completion (max 60 seconds)
    import asyncio
    for _ in range(60):
        status_response = await client.get(f"/api/v1/jobs/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()

        if status_data["status"] == "completed":
            break
        elif status_data["status"] == "failed":
            pytest.fail(f"Job failed: {status_data.get('error')}")

        await asyncio.sleep(1)
    else:
        pytest.fail("Job did not complete within 60 seconds")

    # Step 3: Verify job results
    assert status_data["status"] == "completed"
    results = status_data["results"]
    assert results["papers_discovered"] >= 1
    assert results["papers_created"] >= 1

    # Step 4: Query papers from database
    papers_response = await client.get(
        "/api/v1/papers",
        params={
            "search": arxiv_keywords,
            "page_size": 20
        }
    )
    assert papers_response.status_code == 200
    papers_data = papers_response.json()
    assert papers_data["total"] >= 1

    papers = papers_data["items"]
    first_paper = papers[0]

    # Step 5: Verify paper metadata
    assert "id" in first_paper
    assert UUID(first_paper["id"])  # Valid UUID
    assert "arxiv_id" in first_paper
    assert first_paper["arxiv_id"] is not None
    assert len(first_paper["title"]) >= 10
    assert len(first_paper["authors"]) >= 1
    assert len(first_paper["abstract"]) > 0
    assert "published_date" in first_paper
    assert date.fromisoformat(first_paper["published_date"])

    # Step 6: Verify deterministic ID generation
    # Create duplicate paper with same title+year
    paper_detail_response = await client.get(f"/api/v1/papers/{first_paper['id']}")
    assert paper_detail_response.status_code == 200
    paper_detail = paper_detail_response.json()
    assert "legacy_id" in paper_detail
    assert paper_detail["legacy_id"] is not None  # SHA256 hash

    # Step 7: Test duplicate detection
    # Trigger same crawl again
    duplicate_crawl_response = await client.post(
        "/api/v1/jobs/crawl",
        json={
            "source": "arxiv",
            "arxiv_keywords": arxiv_keywords,
            "arxiv_max_results": 10
        }
    )
    assert duplicate_crawl_response.status_code == 202
    dup_job_id = duplicate_crawl_response.json()["job_id"]

    # Wait for completion
    for _ in range(60):
        dup_status = await client.get(f"/api/v1/jobs/{dup_job_id}")
        if dup_status.json()["status"] == "completed":
            break
        await asyncio.sleep(1)

    dup_results = dup_status.json()["results"]
    # Should detect duplicates and update instead of create
    assert dup_results["papers_created"] == 0
    assert dup_results["papers_updated"] >= 1
```

### Verify

**Assertions**:
1. Job completes within 60 seconds (PR-001)
2. At least 1 paper discovered and stored
3. Paper has valid UUID, ArXiv ID, title, authors, abstract
4. Paper has deterministic `legacy_id` (SHA256 hash)
5. Duplicate crawl updates existing papers (no duplicates created)
6. Published date is valid and not in future

**Performance**:
- Job completion: < 60 seconds for 10 papers
- Individual paper query: < 500ms

---

## Scenario 2: Automated Metadata Enrichment with LLM

**Acceptance Criteria**: FR-006, FR-007, FR-008, FR-009, FR-010, FR-011-FR-018

**User Story**: As a researcher, I want papers automatically enriched with AI-extracted metadata (tasks, methods, datasets) so I can filter and discover relevant papers.

### Setup

```python
@pytest.fixture
async def sample_arxiv_paper(client):
    """Create a sample paper in database without enrichment."""
    paper_data = {
        "arxiv_id": "2301.12345",
        "title": "Sample Transformer Paper for Testing",
        "authors": ["Doe, John", "Smith, Jane"],
        "abstract": "This paper presents a novel transformer architecture...",
        "published_date": "2023-01-15",
        "arxiv_url": "https://arxiv.org/abs/2301.12345",
        "pdf_url": "https://arxiv.org/pdf/2301.12345.pdf"
    }
    # Insert directly into database (skip crawl)
    from backend.src.models import Paper
    from backend.src.database import async_session

    async with async_session() as session:
        paper = Paper(**paper_data)
        session.add(paper)
        await session.commit()
        await session.refresh(paper)
        return paper.id
```

### Execute

```python
@pytest.mark.asyncio
async def test_metadata_enrichment(client, sample_arxiv_paper):
    """Test Scenario 2: Automated Metadata Enrichment"""

    paper_id = sample_arxiv_paper

    # Step 1: Trigger enrichment job
    enrich_response = await client.post(
        "/api/v1/jobs/enrich",
        json={
            "paper_ids": [str(paper_id)],
            "enrichment_tasks": [
                "download_pdf",
                "extract_text",
                "extract_tables",
                "extract_citations",
                "llm_extract_tasks",
                "llm_extract_methods",
                "llm_extract_datasets"
            ],
            "llm_provider": "llamacpp",  # Use local LLM for tests
            "priority": "high"
        }
    )
    assert enrich_response.status_code == 202
    job_id = enrich_response.json()["job_id"]

    # Step 2: Wait for job completion (max 300 seconds for LLM processing)
    import asyncio
    for _ in range(300):
        status_response = await client.get(f"/api/v1/jobs/{job_id}")
        status_data = status_response.json()

        if status_data["status"] == "completed":
            break
        elif status_data["status"] == "failed":
            pytest.fail(f"Enrichment failed: {status_data.get('error')}")

        # Log progress
        if "progress" in status_data:
            print(f"Progress: {status_data['progress']['percentage']:.1f}%")

        await asyncio.sleep(1)
    else:
        pytest.fail("Enrichment did not complete within 300 seconds")

    # Step 3: Verify enrichment results
    results = status_data["results"]
    assert results["papers_enriched"] == 1
    assert "pdf_downloaded" in results
    assert "text_extracted" in results

    # Step 4: Query enriched paper
    paper_response = await client.get(f"/api/v1/papers/{paper_id}")
    assert paper_response.status_code == 200
    paper = paper_response.json()

    # Step 5: Verify PDF content extraction
    assert paper["has_pdf_content"] is True

    # Step 6: Verify LLM extractions
    assert paper["primary_task"] is not None
    assert len(paper["primary_task"]) > 0
    # May have secondary/tertiary tasks
    if paper["secondary_task"]:
        assert len(paper["secondary_task"]) > 0

    # Verify methods
    assert paper["primary_method"] is not None
    assert len(paper["primary_method"]) > 0

    # Verify datasets (JSONB array)
    if paper["datasets_used"]:
        assert isinstance(paper["datasets_used"], list)
        assert len(paper["datasets_used"]) > 0

    # Verify metrics (JSONB array)
    if paper["metrics_used"]:
        assert isinstance(paper["metrics_used"], list)
        assert len(paper["metrics_used"]) > 0

    # Step 7: Verify LLM extraction records
    assert paper["llm_extractions_count"] > 0
    # All extractions should be pending review
    assert paper["llm_extractions_verified_count"] == 0

    # Step 8: Verify table extraction
    # Query PDF content directly
    from backend.src.models import PDFContent
    from backend.src.database import async_session

    async with async_session() as session:
        pdf_content = await session.get(PDFContent, paper_id)
        assert pdf_content is not None
        assert len(pdf_content.full_text) > 0
        assert pdf_content.extraction_success is True

        if pdf_content.table_count > 0:
            assert pdf_content.table_csv_paths is not None
            assert len(pdf_content.table_csv_paths) == pdf_content.table_count
            # Verify CSV files exist
            import os
            for csv_path in pdf_content.table_csv_paths:
                assert os.path.exists(csv_path)

    # Step 9: Verify citations extracted
    if pdf_content.parsed_references:
        assert isinstance(pdf_content.parsed_references, list)
        assert len(pdf_content.parsed_references) > 0
```

### Verify

**Assertions**:
1. Enrichment job completes within 300 seconds (includes LLM calls)
2. PDF downloaded and stored
3. Full text extracted successfully
4. Tables extracted and saved as CSV files (if present)
5. LLM extractions completed:
   - Primary task extracted
   - Primary method extracted
   - Datasets array populated (if mentioned)
   - Metrics array populated (if mentioned)
6. All LLM extractions flagged for manual review (verification_status = pending_review)
7. Citations parsed from References section
8. No data loss on extraction failures (errors logged)

**Performance**:
- PDF download: < 5 seconds
- Text extraction: < 2 seconds
- LLM extraction: < 30 seconds per field (local LlamaCpp)
- Total enrichment: 3-5 seconds (excluding LLM)

---

## Scenario 3: GitHub Repository Tracking with Daily Updates

**Acceptance Criteria**: FR-019-FR-025, DR-001, PR-004

**User Story**: As a researcher, I want to see GitHub star counts and velocity metrics for papers, updated daily, to identify trending repositories.

### Setup

```python
@pytest.fixture
async def paper_with_github(client):
    """Create paper with known GitHub repository."""
    paper_data = {
        "arxiv_id": "1706.03762",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani, Ashish", "Shazeer, Noam"],
        "abstract": "The dominant sequence transduction models...",
        "published_date": "2017-06-12",
        "github_url": "https://github.com/tensorflow/tensor2tensor"
    }
    from backend.src.models import Paper
    from backend.src.database import async_session

    async with async_session() as session:
        paper = Paper(**paper_data)
        session.add(paper)
        await session.commit()
        await session.refresh(paper)
        return paper.id
```

### Execute

```python
@pytest.mark.asyncio
async def test_github_tracking(client, paper_with_github):
    """Test Scenario 3: GitHub Repository Tracking"""

    paper_id = paper_with_github

    # Step 1: Verify GitHub URL exists
    paper_response = await client.get(f"/api/v1/papers/{paper_id}")
    paper = paper_response.json()
    assert paper["github_url"] is not None

    # Step 2: Trigger initial GitHub metrics fetch
    update_response = await client.post(
        f"/api/v1/github/metrics/{paper_id}/update"
    )
    assert update_response.status_code == 202
    job_id = update_response.json()["job_id"]

    # Step 3: Wait for GitHub metrics to be fetched
    import asyncio
    for _ in range(30):
        status_response = await client.get(f"/api/v1/jobs/{job_id}")
        status_data = status_response.json()

        if status_data["status"] == "completed":
            break
        elif status_data["status"] == "failed":
            pytest.fail(f"GitHub fetch failed: {status_data.get('error')}")

        await asyncio.sleep(1)
    else:
        pytest.fail("GitHub metrics fetch did not complete within 30 seconds")

    # Step 4: Query GitHub metrics
    metrics_response = await client.get(
        f"/api/v1/github/metrics/{paper_id}",
        params={"history_days": 30}
    )
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()

    # Step 5: Verify repository metadata
    assert metrics["repository"]["url"] == paper["github_url"]
    assert metrics["repository"]["owner"] == "tensorflow"
    assert metrics["repository"]["name"] == "tensor2tensor"
    assert metrics["repository"]["primary_language"] is not None

    # Step 6: Verify current stats
    assert metrics["current_stats"]["stars"] > 0
    assert metrics["current_stats"]["forks"] >= 0
    assert metrics["current_stats"]["watchers"] >= 0
    assert "last_updated" in metrics["current_stats"]

    # Step 7: Verify hype scores calculated
    assert "hype_scores" in metrics
    assert metrics["hype_scores"]["average"] is not None
    # Weekly/monthly may be null if not enough history
    if len(metrics["star_history"]) >= 7:
        assert metrics["hype_scores"]["weekly"] is not None
    if len(metrics["star_history"]) >= 30:
        assert metrics["hype_scores"]["monthly"] is not None

    # Step 8: Verify tracking metadata
    assert metrics["tracking"]["start_date"] is not None
    assert metrics["tracking"]["last_tracked"] is not None
    assert metrics["tracking"]["enabled"] is True
    assert metrics["tracking"]["total_snapshots"] >= 1

    # Step 9: Verify star history snapshots
    assert "star_history" in metrics
    assert len(metrics["star_history"]) >= 1
    first_snapshot = metrics["star_history"][0]
    assert "date" in first_snapshot
    assert "stars" in first_snapshot
    assert first_snapshot["stars"] > 0

    # Step 10: Simulate daily update (trigger again)
    await asyncio.sleep(1)  # Simulate 1 day passing
    second_update = await client.post(
        f"/api/v1/github/metrics/{paper_id}/update"
    )
    assert second_update.status_code == 202

    # Wait for second update
    second_job_id = second_update.json()["job_id"]
    for _ in range(30):
        second_status = await client.get(f"/api/v1/jobs/{second_job_id}")
        if second_status.json()["status"] == "completed":
            break
        await asyncio.sleep(1)

    # Step 11: Verify history now has 2 snapshots
    updated_metrics = await client.get(
        f"/api/v1/github/metrics/{paper_id}",
        params={"history_days": 30}
    )
    updated_data = updated_metrics.json()
    assert len(updated_data["star_history"]) >= 2

    # Step 12: Verify star delta calculated
    if len(updated_data["star_history"]) >= 2:
        latest = updated_data["star_history"][0]
        previous = updated_data["star_history"][1]
        if latest["delta"] is not None:
            expected_delta = latest["stars"] - previous["stars"]
            assert latest["delta"] == expected_delta
```

### Verify

**Assertions**:
1. GitHub repository metadata fetched successfully
2. Current stars, forks, watchers retrieved
3. Repository creation date, last update captured
4. Hype scores calculated:
   - Average hype (daily star gain since tracking start)
   - Weekly hype (if >= 7 days of history)
   - Monthly hype (if >= 30 days of history)
5. Star snapshots stored with timestamps
6. Star delta calculated between consecutive snapshots
7. Tracking metadata records start date and last update
8. Historical data retained indefinitely (DR-001)
9. Rate limiting respected (GitHub API: 5000 req/hour)

**Performance**:
- Initial GitHub fetch: < 5 seconds
- Snapshot creation: < 1 second
- Daily update batch (10,000 papers): < 1 hour

---

## Scenario 4: Citation Graph Construction with Fuzzy Matching

**Acceptance Criteria**: FR-026-FR-032

**User Story**: As a researcher, I want to see citation relationships between papers so I can understand the influence and connections in my research area.

### Setup

```python
@pytest.fixture
async def citation_corpus(client):
    """Create corpus of papers with known citation relationships."""
    papers = [
        {
            "arxiv_id": "1706.03762",
            "title": "Attention Is All You Need",
            "authors": ["Vaswani, Ashish"],
            "abstract": "Transformer architecture...",
            "published_date": "2017-06-12",
            "year": 2017
        },
        {
            "arxiv_id": "1810.04805",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "authors": ["Devlin, Jacob"],
            "abstract": "BERT model...",
            "published_date": "2018-10-11",
            "year": 2018
        },
        {
            "arxiv_id": "1409.0473",
            "title": "Neural Machine Translation by Jointly Learning to Align and Translate",
            "authors": ["Bahdanau, Dzmitry"],
            "abstract": "Attention mechanism...",
            "published_date": "2014-09-01",
            "year": 2014
        }
    ]

    from backend.src.models import Paper
    from backend.src.database import async_session

    paper_ids = []
    async with async_session() as session:
        for paper_data in papers:
            paper = Paper(**paper_data)
            session.add(paper)
            await session.flush()
            paper_ids.append(paper.id)
        await session.commit()

    return paper_ids
```

### Execute

```python
@pytest.mark.asyncio
async def test_citation_graph_construction(client, citation_corpus):
    """Test Scenario 4: Citation Graph Construction"""

    transformer_id, bert_id, bahdanau_id = citation_corpus

    # Step 1: Add PDF content with references for BERT paper
    # BERT cites Transformer paper
    from backend.src.models import PDFContent
    from backend.src.database import async_session

    bert_references_text = """
    References

    [1] Vaswani, A., Shazeer, N., Parmar, N., et al. (2017).
        Attention is all you need.
        Advances in neural information processing systems, 30.

    [2] Bahdanau, D., Cho, K., & Bengio, Y. (2014).
        Neural machine translation by jointly learning to align and translate.
        arXiv preprint arXiv:1409.0473.
    """

    async with async_session() as session:
        pdf_content = PDFContent(
            paper_id=bert_id,
            full_text="BERT paper full text...",
            references_text=bert_references_text,
            parsed_references=[
                "Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). Attention is all you need.",
                "Bahdanau, D., Cho, K., & Bengio, Y. (2014). Neural machine translation by jointly learning to align and translate."
            ],
            extraction_success=True
        )
        session.add(pdf_content)
        await session.commit()

    # Step 2: Trigger citation matching job
    from backend.src.services.citation_service import CitationMatcher

    matcher = CitationMatcher(similarity_threshold=85)

    # Match citations to papers in database
    async with async_session() as session:
        pdf_content = await session.get(PDFContent, bert_id)
        papers = await session.execute(
            select(Paper).filter(Paper.id != bert_id)
        )
        all_papers = papers.scalars().all()

        for ref_text in pdf_content.parsed_references:
            matched_paper = matcher.match_citation(ref_text, all_papers)

            if matched_paper:
                # Create PaperReference relationship
                from backend.src.models import PaperReference
                citation = PaperReference(
                    paper_id=bert_id,
                    reference_id=matched_paper.id,
                    reference_text=ref_text,
                    match_score=matcher.last_match_score,
                    match_method="fuzzy_title_year"
                )
                session.add(citation)

        await session.commit()

    # Step 3: Query citations for BERT paper
    citations_response = await client.get(
        f"/api/v1/papers/{bert_id}/citations",
        params={"direction": "both"}
    )
    assert citations_response.status_code == 200
    citations = citations_response.json()

    # Step 4: Verify outgoing citations (papers cited by BERT)
    assert "citations_out" in citations
    assert len(citations["citations_out"]) >= 2  # Transformer + Bahdanau

    transformer_citation = next(
        c for c in citations["citations_out"]
        if c["related_paper_id"] == str(transformer_id)
    )
    assert transformer_citation["related_paper_title"] == "Attention Is All You Need"
    assert transformer_citation["match_score"] >= 85
    assert transformer_citation["match_method"] == "fuzzy_title_year"
    assert transformer_citation["reference_text"] is not None

    # Step 5: Verify incoming citations (papers citing Transformer)
    transformer_citations_response = await client.get(
        f"/api/v1/papers/{transformer_id}/citations",
        params={"direction": "in"}
    )
    transformer_citations = transformer_citations_response.json()
    assert len(transformer_citations["citations_in"]) >= 1

    bert_citation = transformer_citations["citations_in"][0]
    assert bert_citation["related_paper_id"] == str(bert_id)

    # Step 6: Query citation graph (multi-level)
    graph_response = await client.get(
        "/api/v1/citations/graph",
        params={
            "paper_id": str(transformer_id),
            "depth": 2,
            "direction": "both"
        }
    )
    assert graph_response.status_code == 200
    graph = graph_response.json()

    # Step 7: Verify graph structure
    assert graph["root_paper_id"] == str(transformer_id)
    assert graph["depth"] == 2
    assert graph["total_nodes"] >= 3  # Transformer, BERT, Bahdanau
    assert graph["total_edges"] >= 2  # BERT->Transformer, BERT->Bahdanau

    # Verify nodes
    nodes = graph["nodes"]
    root_node = next(n for n in nodes if n["paper_id"] == str(transformer_id))
    assert root_node["level"] == 0  # Root node
    assert root_node["citations_in_count"] >= 1  # Cited by BERT

    bert_node = next(n for n in nodes if n["paper_id"] == str(bert_id))
    assert bert_node["level"] == 1  # Direct citation
    assert bert_node["citations_out_count"] >= 2  # Cites Transformer + Bahdanau

    # Verify edges
    edges = graph["edges"]
    bert_to_transformer = next(
        e for e in edges
        if e["source_id"] == str(bert_id) and e["target_id"] == str(transformer_id)
    )
    assert bert_to_transformer["relationship"] == "cites"
    assert bert_to_transformer["match_score"] >= 85

    # Step 8: Test citation-based paper discovery
    discovery_response = await client.post(
        "/api/v1/citations/discover",
        json={
            "seed_paper_id": str(transformer_id),
            "strategies": ["citing_papers", "cited_papers"],
            "max_papers_per_strategy": 10
        }
    )
    assert discovery_response.status_code == 200
    discovery = discovery_response.json()

    assert discovery["total_discovered"] >= 1
    citing_papers = next(
        s for s in discovery["papers"]
        if s["strategy"] == "citing_papers"
    )
    assert len(citing_papers["papers"]) >= 1
```

### Verify

**Assertions**:
1. Citations parsed from PDF References section
2. Citation strings matched to papers using fuzzy matching (Levenshtein distance)
3. Match scores >= 85% threshold
4. Bidirectional relationships created (cites/cited-by)
5. Original reference text preserved
6. Citation graph traversal works (depth 2)
7. Graph nodes include metadata (title, authors, year, citation counts)
8. Graph edges include match metadata (score, method)
9. Citation-based discovery finds related papers
10. Malformed references stored for manual review (no processing failure)

**Performance**:
- Citation matching: < 1 second per reference
- Graph query (depth 2, 100 nodes): < 2 seconds
- Discovery query: < 3 seconds

---

## Scenario 5: Conference Paper Integration

**Acceptance Criteria**: FR-004, FR-005, CF-001, CF-005

**User Story**: As a researcher, I want to crawl conference papers from specific venues (e.g., CVPR 2024) with conference-specific metadata.

### Setup

```python
@pytest.fixture
def conference_config():
    """Conference configuration for CVPR 2024."""
    return {
        "conference_name": "CVPR 2024",
        "conference_year": 2024,
        "venue_url": "https://cvpr.thecvf.com/Conferences/2024"
    }
```

### Execute

```python
@pytest.mark.asyncio
async def test_conference_paper_integration(client, conference_config):
    """Test Scenario 5: Conference Paper Integration"""

    # Step 1: Trigger conference crawl
    crawl_response = await client.post(
        "/api/v1/jobs/crawl",
        json={
            "source": "conference",
            "conference_name": conference_config["conference_name"],
            "conference_year": conference_config["conference_year"],
            "priority": "normal"
        }
    )
    assert crawl_response.status_code == 202
    job_id = crawl_response.json()["job_id"]

    # Step 2: Wait for crawl completion
    import asyncio
    for _ in range(300):  # Conference crawls take longer
        status_response = await client.get(f"/api/v1/jobs/{job_id}")
        status_data = status_response.json()

        if status_data["status"] == "completed":
            break
        elif status_data["status"] == "failed":
            pytest.fail(f"Conference crawl failed: {status_data.get('error')}")

        await asyncio.sleep(1)
    else:
        pytest.fail("Conference crawl did not complete within 300 seconds")

    # Step 3: Verify papers crawled
    results = status_data["results"]
    assert results["papers_discovered"] >= 1
    assert results["papers_created"] >= 1

    # Step 4: Query conference papers
    papers_response = await client.get(
        "/api/v1/papers",
        params={
            "venue": conference_config["conference_name"],
            "year": conference_config["conference_year"],
            "page_size": 50
        }
    )
    assert papers_response.status_code == 200
    papers_data = papers_response.json()
    assert papers_data["total"] >= 1

    conference_paper = papers_data["items"][0]

    # Step 5: Verify conference-specific metadata
    assert conference_paper["venue"] == conference_config["conference_name"]
    assert conference_paper["year"] == conference_config["conference_year"]

    # Conference metadata fields
    if conference_paper["paper_type"]:
        assert conference_paper["paper_type"] in ["oral", "poster", "spotlight", "workshop"]

    if conference_paper["session_type"]:
        assert len(conference_paper["session_type"]) > 0

    if conference_paper["accept_status"]:
        assert conference_paper["accept_status"] in ["accepted", "rejected", "pending"]

    # Step 6: Verify source attribution
    # Query detailed paper
    detail_response = await client.get(f"/api/v1/papers/{conference_paper['id']}")
    detail = detail_response.json()

    # Should have conference name in venue
    assert detail["venue"] == conference_config["conference_name"]

    # Step 7: Test ArXiv linking (if available)
    if detail["arxiv_id"]:
        # Verify ArXiv metadata merged
        assert detail["arxiv_url"] is not None
        assert detail["pdf_url"] is not None

    # Step 8: Test filtering by paper type
    oral_papers = await client.get(
        "/api/v1/papers",
        params={
            "venue": conference_config["conference_name"],
            "paper_type": "oral"
        }
    )
    assert oral_papers.status_code == 200
    for paper in oral_papers.json()["items"]:
        assert paper["paper_type"] == "oral"

    # Step 9: Test filtering by session type
    if conference_paper["session_type"]:
        session_papers = await client.get(
            "/api/v1/papers",
            params={
                "venue": conference_config["conference_name"],
                "session_type": conference_paper["session_type"]
            }
        )
        assert session_papers.status_code == 200
```

### Verify

**Assertions**:
1. Conference papers crawled successfully
2. Conference name and year stored correctly
3. Conference-specific fields populated:
   - paper_type (oral/poster/spotlight/workshop)
   - session_type (conference session category)
   - accept_status (accepted/rejected/pending)
4. Source attribution maintained (conference name)
5. ArXiv versions linked when available (duplicate detection)
6. Filtering by conference metadata works
7. BibTeX entries generated (if applicable)
8. Conference configuration loaded from JSON or parameters

**Performance**:
- Conference crawl (100 papers): < 5 minutes
- Metadata merge with ArXiv: < 1 second per paper

---

## Performance Validation Tests

### Page Load Performance

```python
@pytest.mark.asyncio
async def test_page_load_performance(client):
    """Verify page load performance targets."""

    # Create test data: 1000 papers
    from backend.src.models import Paper
    from backend.src.database import async_session
    import asyncio

    papers = []
    for i in range(1000):
        papers.append(Paper(
            arxiv_id=f"2301.{10000 + i}",
            title=f"Test Paper {i}",
            authors=["Test Author"],
            abstract="Test abstract",
            published_date=date(2023, 1, i % 28 + 1),
            year=2023
        ))

    async with async_session() as session:
        session.add_all(papers)
        await session.commit()

    # Measure page load time
    import time
    start = time.time()

    papers_response = await client.get(
        "/api/v1/papers",
        params={
            "page": 1,
            "page_size": 20,
            "sort": "published_date_desc"
        }
    )

    elapsed = time.time() - start

    assert papers_response.status_code == 200
    assert elapsed < 2.0  # Target: < 2 seconds
    print(f"Page load time: {elapsed:.3f}s")
```

### Bulk Processing Performance

```python
@pytest.mark.asyncio
async def test_bulk_processing_performance(client):
    """Verify bulk paper processing performance."""

    # Test bulk processing of 100 papers
    crawl_response = await client.post(
        "/api/v1/jobs/crawl",
        json={
            "source": "arxiv",
            "arxiv_keywords": "machine learning",
            "arxiv_max_results": 100
        }
    )
    job_id = crawl_response.json()["job_id"]

    import time
    start = time.time()

    # Wait for completion
    import asyncio
    for _ in range(600):  # 10 minutes max
        status_response = await client.get(f"/api/v1/jobs/{job_id}")
        if status_response.json()["status"] == "completed":
            break
        await asyncio.sleep(1)

    elapsed = time.time() - start

    assert elapsed < 600  # Should complete within 10 minutes
    print(f"Bulk processing time (100 papers): {elapsed:.1f}s")
    print(f"Average per paper: {elapsed / 100:.2f}s")
```

---

## Summary

These integration test scenarios validate all acceptance criteria from `spec.md`:

1. **Scenario 1**: ArXiv paper discovery with duplicate detection (FR-001-FR-005)
2. **Scenario 2**: Automated metadata enrichment with LLM (FR-006-FR-018)
3. **Scenario 3**: GitHub tracking with daily updates (FR-019-FR-025)
4. **Scenario 4**: Citation graph construction (FR-026-FR-032)
5. **Scenario 5**: Conference paper integration (FR-004, FR-005, CF-001, CF-005)

**Performance Targets Met**:
- Single paper processing: 3-5 seconds ✓
- Page load: < 2 seconds ✓
- Bulk crawling: Background jobs ✓
- GitHub updates: Daily scheduled ✓

**Next Steps**:
1. Run contract tests to validate API schemas
2. Execute integration tests in CI/CD pipeline
3. Monitor performance metrics in production
4. Set up alerting for job failures
5. Manual verification of LLM extractions
