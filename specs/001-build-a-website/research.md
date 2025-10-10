# Research: Trending Research Papers Tracker

**Phase**: 0 - Technology Research & Decisions
**Date**: 2025-10-01

## Research Questions

### Q1: Topic-to-Paper Matching Mechanism
**Decision**: Use local small language model (SLM) via llama.cpp for semantic matching

**Rationale**:
- User specified zero-cost requirement → local LLM mandatory
- Topic matching is critical for accuracy → keyword matching insufficient
- llama.cpp provides efficient CPU/CUDA inference on Linux servers
- Small models (7B params) can run on modest hardware
- Better semantic understanding than keyword/regex matching

**Alternatives Considered**:
- Keyword matching: Too simplistic, misses semantic relationships (e.g., "neural rendering" vs "NeRF")
- Cloud LLM APIs: Violates zero-cost constraint
- Sentence transformers + cosine similarity: Viable alternative, but LLM provides better context understanding

**Implementation Approach**:
- Use llama.cpp Python bindings
- Load quantized model (Q4_K_M format) for balance of size/quality
- Prompt: Given paper title/abstract and topic, score relevance 0-10
- Cache results to avoid re-processing same paper-topic pairs

### Q2: Time-Series Data Storage
**Decision**: PostgreSQL with TimescaleDB extension

**Rationale**:
- Native time-series optimization (hypertables, compression)
- SQL familiarity reduces complexity vs specialized TSDB
- Excellent performance for daily snapshots (low write volume)
- Supports complex queries for trend calculation
- Easy backup/restore with standard PostgreSQL tools

**Alternatives Considered**:
- InfluxDB: Overkill for daily snapshots, adds operational complexity
- Raw PostgreSQL: Works but TimescaleDB provides significant query optimization
- SQLite: Insufficient for concurrent users, no time-series optimization

### Q3: Paper Source Integration
**Decision**: arXiv API + Papers With Code API

**Rationale**:
- arXiv API: Official, reliable, provides daily updates
- Papers With Code: Links papers to GitHub repos, tracks stars
- Both have free APIs with reasonable rate limits
- Conference papers (CVPR, SIGGRAPH) often indexed in Papers With Code

**Alternatives Considered**:
- Semantic Scholar API: Good for citations but rate limits restrictive
- Google Scholar scraping: Fragile, violates ToS
- Direct conference site scraping: High maintenance, inconsistent formats

**Implementation Approach**:
- Daily job fetches arXiv papers by category (cs.CV, cs.LG, etc.)
- Cross-reference with Papers With Code for GitHub links
- Store paper metadata, track metrics daily
- Use arXiv ID as canonical identifier, handle duplicates via DOI/title matching

### Q4: Citation Count Source
**Decision**: Semantic Scholar API for citation counts

**Rationale**:
- Free API with citation data
- Covers arXiv and major conferences
- Returns citation count without requiring paper details
- Rate limit (100 req/s) sufficient for daily batch updates

**Alternatives Considered**:
- Google Scholar: No official API, scraping fragile
- CrossRef: Good for DOIs but incomplete arXiv coverage
- OpenAlex: Viable alternative, less mature than Semantic Scholar

### Q5: Hype Score Calculation Algorithm
**Decision**: Weighted combination of growth rates with recency bias

**Formula**:
```
hype_score = (
    0.4 * star_growth_rate_7d +
    0.3 * citation_growth_rate_30d +
    0.2 * absolute_stars_normalized +
    0.1 * recency_bonus
)
```

**Rationale**:
- Growth rates capture "trending" better than absolute values
- 7-day window for stars (faster signal) vs 30-day for citations (slower)
- Absolute stars prevent new papers from dominating entirely
- Recency bonus surfaces new papers (decay after 60 days)
- Transparent, versioned algorithm (constitution principle V)

**Normalization**:
- star_growth_rate_7d: (stars_today - stars_7d_ago) / max(stars_7d_ago, 1)
- citation_growth_rate_30d: (citations_today - citations_30d_ago) / max(citations_30d_ago, 1)
- absolute_stars_normalized: log10(stars + 1) / log10(max_stars_in_topic + 1)
- recency_bonus: 1.0 if < 30 days old, linear decay to 0.0 at 60 days

### Q6: Frontend Framework
**Decision**: React with Vite

**Rationale**:
- Fast build times (Vite) support <2s page load goal
- React ecosystem mature, component reusability
- Easy to optimize with code splitting, lazy loading
- Familiar to most developers (boring tech principle)

**Alternatives Considered**:
- Vue: Similar benefits, less ecosystem
- Svelte: Faster runtime but less familiar, smaller ecosystem
- Plain JS: More control but slower development

### Q7: User Account Requirements
**Decision**: Optional accounts with localStorage fallback (MVP)

**Rationale**:
- MVP: localStorage for topic preferences (no backend)
- Simple, fast, no auth complexity
- Future: Add accounts for cross-device sync if demanded

**Alternatives Considered**:
- Required accounts: Adds friction, violates "simple, fast" principle for MVP
- No persistence: Poor UX, users lose topics on refresh

### Q8: API Design Pattern
**Decision**: REST API with JSON

**Rationale**:
- Simple, well-understood, cacheable
- No over-fetching concerns with limited data model
- Easy to document with OpenAPI
- Frontend can poll or use Server-Sent Events for updates

**Alternatives Considered**:
- GraphQL: Overkill for simple data model, adds complexity
- gRPC: Wrong tool for browser clients

### Q9: Daily Metric Update Strategy
**Decision**: Cron job + background worker queue

**Rationale**:
- Cron triggers daily at low-traffic time (2 AM UTC)
- Worker queue (Celery/RQ) handles parallel paper updates
- Graceful handling of API rate limits
- Metrics update window: 2-4 hours acceptable

**Alternatives Considered**:
- Real-time updates: Too expensive (API costs, rate limits)
- Manual refresh: Violates "real-time, not stale" principle

### Q10: Scale & Performance Targets (MVP Clarification)
**Decision**: MVP targets defined

**Targets**:
- 1,000 papers per topic maximum
- 100 concurrent users
- 30-day metric retention (expandable to 1 year post-MVP)
- Daily monitoring completes within 4 hours
- Sorting options: hype score (default), recency, absolute stars
- Topics stored in localStorage (no accounts for MVP)

**Rationale**:
- Conservative targets for MVP validation
- Can scale up after user feedback
- 30-day retention sufficient for trending analysis
- localStorage sufficient for single-user experience

## Technology Stack Summary

### Backend
- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **Database**: PostgreSQL 15+ with TimescaleDB 2.11+
- **LLM**: llama.cpp with quantized 7B model (e.g., Mistral, Llama 2)
- **Background Jobs**: APScheduler (simpler than Celery for MVP)
- **HTTP Client**: httpx for async API calls
- **ORM**: SQLAlchemy 2.0 with asyncpg

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **State Management**: React Context + hooks (no Redux for MVP)
- **HTTP Client**: Axios
- **Charting**: Recharts (trend graphs)
- **Styling**: TailwindCSS (fast development, mobile-first)

### Infrastructure
- **Server**: Linux server (Ubuntu 22.04 recommended)
- **Database**: PostgreSQL + TimescaleDB (Docker or native)
- **LLM Runtime**: llama.cpp (CPU or CUDA)
- **Reverse Proxy**: nginx (serve frontend, proxy API)

### Development Tools
- **Testing**: pytest (backend), vitest (frontend)
- **Linting**: ruff (Python), ESLint (JS/TS)
- **Type Checking**: mypy (Python), TypeScript
- **API Docs**: FastAPI auto-generates OpenAPI/Swagger

## Key Integration Points

1. **arXiv → Backend**: Daily fetch via arXiv API
2. **Papers With Code → Backend**: Link papers to GitHub repos
3. **Semantic Scholar → Backend**: Fetch citation counts
4. **GitHub API → Backend**: Fetch star counts (unauthenticated, 60 req/hr limit)
5. **llama.cpp → Backend**: Topic-paper matching
6. **Backend API → Frontend**: REST endpoints for papers, topics, metrics
7. **PostgreSQL ← TimescaleDB**: Hypertables for metric snapshots

## Risk Mitigation

### Risk 1: GitHub API Rate Limits
**Mitigation**:
- Cache star counts for 24 hours
- Use authenticated API (5000 req/hr) if needed
- Gracefully handle rate limit errors, retry with exponential backoff

### Risk 2: LLM Inference Speed
**Mitigation**:
- Batch topic matching during daily job (not request time)
- Cache match results indefinitely (paper-topic pairs stable)
- Quantized models (Q4) for faster inference

### Risk 3: Topic Matching Accuracy
**Mitigation**:
- Manual review of top 100 papers during development
- Adjust prompts based on false positives/negatives
- Future: Allow users to flag mismatched papers

### Risk 4: Data Retention Growth
**Mitigation**:
- TimescaleDB automatic compression (30+ days old)
- Archive old snapshots to cold storage (post-MVP)
- 30-day retention sufficient for MVP trending analysis

## Phase 0 Completion Checklist
- [x] Topic-to-paper matching mechanism decided
- [x] Time-series storage solution selected
- [x] Paper source APIs identified
- [x] Citation count source determined
- [x] Hype score algorithm defined
- [x] Frontend framework chosen
- [x] User account strategy decided
- [x] API design pattern selected
- [x] Daily update strategy planned
- [x] MVP scale targets clarified
- [x] Technology stack finalized
- [x] Integration points documented
- [x] Key risks identified with mitigations

**Status**: ✅ Research complete, ready for Phase 1 (Design & Contracts)
