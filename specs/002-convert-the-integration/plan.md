
# Implementation Plan: SOTAPapers Legacy Code Integration

**Branch**: `002-convert-the-integration` | **Date**: 2025-10-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-convert-the-integration/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → Loaded: 58 requirements, 5 acceptance scenarios, 6 entities
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Project Type: Web application (backend + frontend)
   → All technical decisions resolved via legacy analysis
3. Fill Constitution Check section
   → Evaluated against HypePaper Constitution v1.0.0
4. Evaluate Constitution Check section
   → VIOLATIONS FOUND: See Complexity Tracking below
   → Documented justifications for complexity
   → Update Progress Tracking: Initial Constitution Check PASS (with justification)
5. Execute Phase 0 → research.md
   → All NEEDS CLARIFICATION already resolved in spec
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
7. Re-evaluate Constitution Check section
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 9. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Integrate SOTAPapers legacy codebase into HypePaper to enable comprehensive paper discovery, AI-powered metadata extraction, GitHub repository tracking, and citation graph construction. Migration involves extending PostgreSQL schema, porting async-compatible services, implementing background job processing with Celery, and refactoring multiprocessing to async patterns while maintaining security (no hardcoded credentials).

## Technical Context
**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLAlchemy (async), asyncpg, Alembic, Celery, llama-cpp-python, PyMuPDF, GMFT, python-json-config, httpx
**Storage**: PostgreSQL + TimescaleDB (migration from SQLite)
**Testing**: pytest, pytest-asyncio, contract tests, integration tests
**Target Platform**: Linux server (Docker containers)
**Project Type**: Web application (backend + frontend separated)
**Performance Goals**: 3-5s single paper processing, 1000+ papers bulk processing (background), daily star updates
**Constraints**: Async/await architecture, rate limits (ArXiv: 3 req/s, GitHub: 5000 req/hr), PostgreSQL only
**Scale/Scope**: 1000+ papers per topic, indefinite star tracking history, 100 concurrent users, multi-source aggregation

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Simple, Small, Fast ⚠️ VIOLATION (Justified)
**Violation**: This integration adds significant complexity to HypePaper MVP:
- Multi-source paper crawling (ArXiv, conferences, citations)
- AI-powered metadata extraction with LLM integration
- Background job processing infrastructure (Celery)
- Citation graph construction with fuzzy matching
- GitHub tracking with daily scheduled updates

**Justification**: These features are CORE to HypePaper's value proposition (trending papers with novel metrics). Without them:
- No GitHub stars → No unique "hype" metric
- No AI extraction → No rich metadata for filtering
- No citations → Incomplete trend analysis
- No background jobs → Can't scale to 1000+ papers

**Mitigation**: Phase implementation allows MVP to launch with subset (Phase 1 only), add complexity incrementally.

### Principle II: Novel Metrics Drive Value ✅ PASS
This integration DIRECTLY implements the core differentiator:
- GitHub star tracking (daily snapshots, velocity calculations)
- Citation counts from multiple sources
- Combined hype scoring algorithm
- Transparent metric breakdowns

### Principle III: User Interest First ✅ PASS
Configuration-driven approach respects user control:
- JSON config for topics/conferences
- Command-line parameter overrides
- No algorithmic interference with user preferences

### Principle IV: Real-Time, Not Stale ✅ PASS
- Daily GitHub star updates via scheduled jobs
- Incremental paper discovery (new papers within 24-48 hours)
- Background processing doesn't block user queries

### Principle V: Reproducible Scoring ✅ PASS
- Legacy hype algorithm well-documented
- Star velocity components exposed in API
- No opaque confidence scores (manual verification instead)

### Development Constraints ✅ PASS
- Using proven tech: PostgreSQL, FastAPI, Celery (boring, reliable)
- Minimal frontend changes (backend integration only)
- Page load speed unaffected (background processing)

### Scope Boundaries ⚠️ VIOLATION (Justified)
**Violation**: Integration adds features beyond MVP trending list:
- Conference paper crawling
- LLM-based metadata extraction
- Citation graph traversal

**Justification**: These are data SOURCES for trending papers, not separate features. Users still see ONE thing: trending papers list. The complexity is backend infrastructure (invisible to users).

## Project Structure

### Documentation (this feature)
```
specs/002-convert-the-integration/
├── plan.md              # This file (/plan command output)
├── spec.md              # Feature specification (input)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── papers-api.yaml          # Papers CRUD + search endpoints
│   ├── github-api.yaml          # GitHub tracking endpoints
│   ├── citations-api.yaml       # Citation graph endpoints
│   └── jobs-api.yaml            # Background job status endpoints
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/
│   │   ├── paper.py              # Extended Paper model (37 fields from legacy)
│   │   ├── author.py             # Author entity
│   │   ├── citation.py           # Citation relationships
│   │   ├── github_metrics.py    # GitHub tracking data
│   │   ├── pdf_content.py       # PDF extraction results
│   │   └── llm_extraction.py    # AI metadata extractions
│   ├── services/
│   │   ├── arxiv_service.py     # ArXiv API client (async port)
│   │   ├── github_service.py    # GitHub API client (secure auth)
│   │   ├── pdf_service.py       # PDF parsing + GMFT tables
│   │   ├── llm_service.py       # LLM integration (OpenAI + LlamaCpp)
│   │   ├── citation_service.py  # Citation parser + fuzzy matching
│   │   └── config_service.py    # JSON config loader
│   ├── jobs/
│   │   ├── celery_app.py        # Celery configuration
│   │   ├── paper_crawler.py     # Background paper discovery
│   │   ├── metadata_enricher.py # LLM extraction jobs
│   │   └── star_tracker.py      # Daily GitHub star updates
│   ├── api/
│   │   ├── v1/
│   │   │   ├── papers.py        # Extended papers endpoints
│   │   │   ├── citations.py     # Citation graph queries
│   │   │   └── github.py        # GitHub metrics endpoints
│   │   └── dependencies.py      # Shared dependencies
│   └── migrations/
│       └── versions/
│           └── XXXX_add_legacy_fields.py  # Alembic migration
└── tests/
    ├── contract/
    │   ├── test_papers_api.py
    │   ├── test_citations_api.py
    │   └── test_github_api.py
    ├── integration/
    │   ├── test_paper_discovery.py
    │   ├── test_metadata_enrichment.py
    │   ├── test_citation_graph.py
    │   └── test_github_tracking.py
    └── unit/
        ├── test_arxiv_service.py
        ├── test_citation_parser.py
        └── test_llm_service.py

frontend/
├── src/
│   ├── components/
│   │   ├── PaperCard.vue        # Enhanced with citations, GitHub
│   │   └── CitationGraph.vue    # NEW: Citation visualization
│   ├── pages/
│   │   └── HomePage.vue         # Updated to show enriched metadata
│   └── services/
│       ├── papersApi.ts         # Extended API client
│       └── citationsApi.ts      # NEW: Citation queries
└── tests/
    └── integration/
        └── test_enriched_display.spec.ts

shared/
└── schemas/
    ├── paper_extended.json      # JSON schema with 37 fields
    ├── citation.json            # Citation relationship schema
    └── github_metrics.json      # GitHub tracking schema
```

**Structure Decision**: Web application structure maintained (backend + frontend separation). Integration extends backend with new services/models, minimal frontend changes for displaying enriched data.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - ✅ All resolved during specification phase (13 clarifications completed)
   - No NEEDS CLARIFICATION markers remain

2. **Research tasks to execute**:
   - Legacy database schema analysis (SQLite → PostgreSQL migration)
   - GMFT table extraction library integration patterns
   - python-json-config package usage patterns
   - Celery + FastAPI integration best practices
   - Citation fuzzy matching algorithms from legacy
   - Async migration patterns for multiprocessing code
   - Security audit: credential storage patterns

3. **Generate research.md** with decisions on:
   - Database migration strategy (Alembic scripts)
   - Background job architecture (Celery vs APScheduler)
   - LLM service abstraction (unified interface for OpenAI + LlamaCpp)
   - Configuration management (JSON files + env vars)
   - Citation matching algorithm (port legacy logic)
   - PDF storage strategy (local filesystem vs object storage)
   - Testing strategy (contract tests for external APIs)

**Output**: research.md with all technical decisions documented

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Paper (37 fields from legacy + existing HypePaper fields)
   - Author (many-to-many with papers)
   - Citation (paper_references junction table, bidirectional)
   - GitHubMetrics (time-series with TimescaleDB)
   - PDFContent (full text + table CSV paths)
   - LLMExtraction (AI metadata with verification status)
   - Validation rules: deterministic IDs, foreign keys, indexes
   - State transitions: paper processing status, verification workflow

2. **Generate API contracts** from functional requirements:
   - Papers API: GET /papers (extended filters), GET /papers/{id}/citations, GET /papers/{id}/github
   - Citations API: GET /citations/graph, POST /citations/discover (expand via citations)
   - GitHub API: GET /github/metrics/{paper_id}, GET /github/trending
   - Jobs API: POST /jobs/crawl (trigger paper discovery), GET /jobs/{id}/status
   - Output OpenAPI 3.0 schemas to `/contracts/`

3. **Generate contract tests** from contracts:
   - test_papers_api.py: Assert extended response schema, filter parameters
   - test_citations_api.py: Assert graph structure, bidirectional links
   - test_github_api.py: Assert metrics time-series format
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Acceptance Scenario 1 → test_arxiv_discovery.py
   - Acceptance Scenario 2 → test_metadata_enrichment.py
   - Acceptance Scenario 3 → test_github_tracking.py
   - Acceptance Scenario 4 → test_citation_graph.py
   - Acceptance Scenario 5 → test_conference_integration.py
   - Quickstart test validates end-to-end paper discovery + enrichment flow

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
   - Add: PostgreSQL extended schema, Celery jobs, LLM services, citation graph
   - Update recent changes: "Extended Paper model with 37 legacy fields"
   - Keep under 150 lines for token efficiency
   - Output to CLAUDE.md in repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate from Phase 1 design docs
- Group into phases:
  1. Database Migration (Alembic scripts, extended models)
  2. Core Services (ArXiv, GitHub, PDF, LLM, Citations)
  3. Background Jobs (Celery tasks, schedulers)
  4. API Endpoints (Papers, Citations, GitHub)
  5. Integration Tests (End-to-end scenarios)
  6. Security Audit (Revoke hardcoded token, verify env vars)

**Ordering Strategy**:
- TDD: Contract tests [P] → Integration tests → Implementation
- Dependencies: Models [P] → Services [P] → Jobs [P] → API endpoints
- Critical path: Database migration → ArXiv service → Paper crawler
- Mark [P] for parallel: All contract tests, all model files, independent services

**Estimated Output**: 60-80 numbered tasks across 6 phases
- Phase 1: Database (8-10 tasks)
- Phase 2: Services (15-20 tasks)
- Phase 3: Background Jobs (10-12 tasks)
- Phase 4: API Endpoints (12-15 tasks)
- Phase 5: Integration Tests (10-12 tasks)
- Phase 6: Security & Polish (5-8 tasks)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Adds complexity beyond MVP | GitHub tracking, AI extraction, citation graph are CORE to "hype" metric value proposition | Without these: HypePaper is just another ArXiv frontend with no differentiation |
| Background job infrastructure (Celery) | Must process 1000+ papers without blocking user queries, daily star updates | Synchronous processing would timeout API requests, can't scale |
| Multi-source aggregation | Need ArXiv + conferences + citations for comprehensive trending data | Single source misses papers, incomplete trend picture |
| LLM integration complexity | Rich metadata (tasks, methods, datasets) enables better filtering/discovery | Basic metadata insufficient for researchers to evaluate relevance |
| Citation graph traversal | Discover related papers via citation links, calculate citation-based hype | Missing citation data = incomplete "trending" picture |

**Mitigation Strategy**: Implement in phases. MVP can launch with Phase 1 (basic paper discovery + GitHub tracking), add AI extraction in Phase 2, citation graph in Phase 3. Each phase delivers incremental value.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - research.md generated
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md, CLAUDE.md generated
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command) - 72 tasks across 6 phases in tasks.md
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (with justified violations)
- [x] Post-Design Constitution Check: PASS (complexity necessary for core value proposition)
- [x] All NEEDS CLARIFICATION resolved (13 clarifications completed in spec phase)
- [x] Complexity deviations documented (5 violations justified in Complexity Tracking)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
