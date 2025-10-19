# Implementation Plan: Paper Enrichment Feature Improvements

**Branch**: `003-add-paper-enrichment` | **Date**: 2025-10-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-add-paper-enrichment/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ Project Type: Web application (frontend + backend)
   → ✅ All technical details resolved from codebase inspection
3. Fill the Constitution Check section
   → ✅ Evaluated against HypePaper Constitution v1.0.0
4. Evaluate Constitution Check section
   → ✅ PASS - Feature aligns with all principles
   → ✅ Progress Tracking: Initial Constitution Check PASS
5. Execute Phase 0 → research.md
   → ✅ Complete (research.md generated)
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ Complete (all artifacts generated)
7. Re-evaluate Constitution Check section
   → ✅ PASS - No violations, design aligns with constitution
8. Plan Phase 2 → Describe task generation approach
   → ✅ Complete (see Phase 2 section below)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Add comprehensive paper enrichment improvements to HypePaper, including:
1. **Publication Date Fix**: Display actual paper publication dates (from arXiv/source) instead of database crawl dates
2. **URL Hyperlinking**: Auto-detect and hyperlink URLs in abstracts (GitHub repos vs project pages)
3. **Voting System**: Allow authenticated users to upvote/downvote papers with persistent vote tracking
4. **Enhanced Hype Score**: Incorporate vote values using logarithmic scaling to maintain balanced scoring
5. **Rich Paper Details**: Add affiliation info, quick summary, key ideas, performance metrics, and limitations sections
6. **Author Management**: Populate authors table with individual records (name, affiliation, citations, paper count, contact info)
7. **Author Interaction**: Make author names clickable to display detailed author information
8. **Citation Network Quick Action**: Add "Start Crawling from This Paper" button for easy citation network exploration
9. **Time-Series Metrics**: Display daily tracking graphs for citations, stars, votes, and hype score

**Technical Approach**: Extend existing FastAPI backend with new database models (Vote, enhanced Author), add voting API endpoints with authentication, enhance paper enrichment service for URL detection, update Vue.js frontend with voting UI components, author modals, and Chart.js time-series graphs.

## Technical Context

**Language/Version**:
- Backend: Python 3.11+
- Frontend: Vue 3 with TypeScript 5.2+

**Primary Dependencies**:
- Backend: FastAPI 0.104+, SQLAlchemy 2.0 (async), Supabase 2.3+ (auth), asyncpg 0.29
- Frontend: Vue 3.4, Vue Router 4.2, Pinia 3.0, Chart.js 4.5, Axios 1.6, Supabase JS 2.74

**Storage**:
- PostgreSQL with Supabase (currently deployed)
- Existing tables: papers, authors, paper_authors, metric_snapshots, citation_snapshots, paper_references
- New tables needed: votes

**Testing**:
- Backend: pytest 7.4+ with pytest-asyncio for async tests
- Frontend: Vitest 1.0+ with Vue Test Utils 2.4

**Target Platform**:
- Server: Linux/macOS (Supabase cloud PostgreSQL)
- Frontend: Modern browsers (Chrome/Firefox/Safari latest 2 versions), mobile-responsive

**Project Type**: Web application (frontend + backend)

**Performance Goals**:
- Page load < 2 seconds (constitutional requirement)
- Vote API response < 200ms
- Time-series graph render < 500ms for 30 days of data
- Author lookup modal < 300ms

**Constraints**:
- Must use Supabase authentication (already integrated)
- Maintain existing hype score calculation stability (vote impact max 10-15%)
- No breaking changes to existing API contracts
- Time-series data retention: all historical data (no auto-deletion)

**Scale/Scope**:
- Expected users: 100 concurrent users (constitutional requirement)
- Papers in database: ~1000 papers/topic
- Authors: ~5000 individual author records (estimated)
- Votes per paper: 0-500 (estimated)
- Metric snapshots: 30 days per paper minimum

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle I: Simple, Small, Fast (NON-NEGOTIABLE)
**Status**: PASS

- ✅ **MVP Focus**: All features directly support core trending papers functionality
  - Publication dates improve data accuracy
  - Voting adds community signal (aligns with "better signal" goal)
  - Author info enhances researcher context
  - Time-series graphs show trending over time
- ✅ **No Feature Creep**: All improvements enhance existing paper discovery, no AI chat/notes/collaboration
- ✅ **Fast Load Times**: Vote API cached in frontend state, graphs lazy-loaded, no performance regression
- ✅ **Simple UI**: Incremental additions to existing paper detail page, no new complex workflows

**Justification**: Voting system adds complexity but provides essential community signal (similar to GitHub stars). Logarithmic scaling ensures votes don't dominate hype score, maintaining simplicity.

### ✅ Principle II: Novel Metrics Drive Value
**Status**: PASS

- ✅ **Voting as Metric**: Complements GitHub stars with direct user feedback on paper quality
- ✅ **Transparent Scoring**: Vote component uses documented logarithmic formula `log(1 + max(0, votes)) * 5`
- ✅ **Maintained Differentiation**: Vote weight is 10% (stars 35%, citations 35%, absolute 20%), preserving GitHub stars as primary signal
- ✅ **Time-Series Tracking**: Graphs show citation/star growth over time, reinforcing trend visibility

### ✅ Principle III: User Interest First
**Status**: PASS

- ✅ **User Control**: Users directly vote on papers they find valuable
- ✅ **No Algorithmic Manipulation**: Votes are transparent, user-driven signal
- ✅ **Author Context**: Clicking authors shows their work, helping users discover relevant researchers

### ✅ Principle IV: Real-Time, Not Stale
**Status**: PASS

- ✅ **Daily Snapshots**: Metric tracking updated daily (existing infrastructure)
- ✅ **Publication Dates**: Showing actual publish dates (not crawl dates) improves temporal accuracy
- ✅ **Vote Tracking**: Votes update instantly, daily snapshots capture vote trends

### ✅ Principle V: Reproducible Scoring
**Status**: PASS

- ✅ **Documented Formula**: Vote component formula explicitly defined in spec (FR-021)
- ✅ **Auditable Components**: Vote score displayed separately in metrics block
- ✅ **Versioned Algorithm**: Hype score update documented, formula preserved in code comments

### Summary
**PASS** - All features align with HypePaper constitution. Voting system adds complexity but provides community signal consistent with GitHub stars principle. All performance constraints met, no scope creep.

## Project Structure

### Documentation (this feature)
```
specs/003-add-paper-enrichment/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── votes-api.yaml
│   ├── authors-api.yaml
│   └── papers-api-extended.yaml
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/
│   │   ├── paper.py                # Extend with vote_count, quick_summary, key_ideas, etc.
│   │   ├── author.py               # Extend with total_citation_count, latest_paper_id, email, website_url
│   │   ├── vote.py                 # NEW: User votes on papers
│   │   ├── metric_snapshot.py      # Extend to include vote_count in daily snapshots
│   │   └── __init__.py
│   ├── services/
│   │   ├── vote_service.py         # NEW: Vote management logic
│   │   ├── author_service.py       # NEW: Author lookup and statistics
│   │   ├── paper_enrichment.py     # Extend: URL detection in abstracts
│   │   └── hype_score.py           # Extend: Add vote component to calculation
│   ├── api/
│   │   ├── votes.py                # NEW: Vote endpoints (POST /papers/{id}/vote, DELETE)
│   │   ├── authors.py              # NEW: Author endpoints (GET /authors/{id})
│   │   ├── papers.py               # Extend: Include vote_count, author_affiliations in responses
│   │   └── metrics.py              # Extend: Time-series endpoint with vote data
│   └── tests/
│       ├── contract/
│       │   ├── test_votes_api.py   # NEW: Vote API contract tests
│       │   └── test_authors_api.py # NEW: Author API contract tests
│       ├── integration/
│       │   ├── test_voting_flow.py # NEW: End-to-end voting scenarios
│       │   └── test_author_stats.py # NEW: Author statistics accuracy
│       └── unit/
│           ├── test_vote_service.py
│           └── test_hype_score.py

frontend/
├── src/
│   ├── components/
│   │   ├── VoteButtons.vue         # NEW: Upvote/downvote UI
│   │   ├── AuthorModal.vue         # NEW: Author detail popup
│   │   ├── MetricGraph.vue         # NEW: Time-series chart component
│   │   └── AbstractWithLinks.vue   # NEW: Render abstract with hyperlinked URLs
│   ├── pages/
│   │   └── PaperDetailPage.vue     # Extend: Add voting UI, author cards, graphs, quick actions
│   ├── services/
│   │   ├── voteService.ts          # NEW: Vote API calls
│   │   └── authorService.ts        # NEW: Author API calls
│   ├── composables/
│   │   └── useVoting.ts            # NEW: Voting state management
│   └── tests/
│       ├── unit/
│       │   ├── VoteButtons.spec.ts
│       │   └── AuthorModal.spec.ts
│       └── integration/
│           └── PaperDetailPage.spec.ts
```

**Structure Decision**: Web application structure (Option 2 from template). Backend uses existing FastAPI structure with SQLAlchemy models in `backend/src/models/`, service layer in `backend/src/services/`, and API routes in `backend/src/api/`. Frontend uses Vue 3 composition API with component-based architecture in `frontend/src/components/` and page views in `frontend/src/pages/`. Tests follow pytest conventions (backend) and Vitest conventions (frontend).

## Phase 0: Outline & Research

### Research Tasks
All technical context is resolved from existing codebase inspection. No unknowns remain.

**Key Research Areas**:
1. ✅ **Authentication Integration**: Supabase auth already integrated (confirmed from frontend/src/stores/auth.ts and backend dependencies)
2. ✅ **Database Schema**: PostgreSQL via Supabase, SQLAlchemy async ORM (confirmed from backend/src/models/)
3. ✅ **Time-Series Storage**: metric_snapshots table exists with snapshot_date field (confirmed from backend/src/models/metric_snapshot.py)
4. ✅ **Frontend State Management**: Pinia stores for auth and API services (confirmed from frontend structure)
5. ✅ **Charting Library**: Chart.js 4.5 already in dependencies (confirmed from frontend/package.json)

### Decisions to Document in research.md

1. **Vote Storage Strategy**
   - Decision: Create separate `votes` table with (user_id, paper_id, vote_type) composite primary key
   - Rationale: Enable per-user vote tracking, support vote changes (upvote → downvote)
   - Alternatives: Store votes in JSONB array on papers table (rejected: can't enforce user uniqueness)

2. **URL Detection in Abstracts**
   - Decision: Regex-based URL detection (`https?://[^\s]+`) with domain-based classification
   - Rationale: Simple, fast, sufficient for MVP (abstracts are structured text)
   - Alternatives: NLP-based link extraction (rejected: overkill for well-formed URLs)

3. **Author Disambiguation**
   - Decision: Use (name, primary_affiliation) composite for uniqueness, store affiliation history in JSONB
   - Rationale: Handles name collisions, tracks affiliation changes over time
   - Alternatives: Author ID from external services (rejected: adds external dependency)

4. **Hype Score Calculation Update**
   - Decision: Add vote component as separate function, cache in daily metric snapshots
   - Rationale: Maintains transparency, allows rollback if vote weights need adjustment
   - Alternatives: Inline vote calculation (rejected: harder to audit and version)

5. **Time-Series Graph Implementation**
   - Decision: Chart.js line charts, fetch 30-day snapshots via `/papers/{id}/metrics?days=30`
   - Rationale: Chart.js already in dependencies, line charts optimal for time-series
   - Alternatives: Custom D3.js graphs (rejected: adds dependency, overkill for simple line charts)

6. **Author Quick Lookup**
   - Decision: Modal overlay (not new page), lazy-load author stats on click
   - Rationale: Maintains context (user stays on paper page), reduces navigation friction
   - Alternatives: Dedicated author profile pages (rejected: scope creep, adds routing complexity)

**Output**: Generating research.md now...

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

Will generate:
1. **data-model.md**: Extended Paper model, new Vote model, extended Author model, extended MetricSnapshot
2. **contracts/votes-api.yaml**: POST/DELETE /papers/{id}/vote, GET /papers/{id}/vote/status
3. **contracts/authors-api.yaml**: GET /authors/{id}, GET /authors/search
4. **contracts/papers-api-extended.yaml**: Extended paper responses with vote_count, affiliations
5. **quickstart.md**: Acceptance scenarios from spec.md as executable test steps
6. **CLAUDE.md**: Updated with Vote/Author models, new API endpoints

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. **Database Migration Tasks** (Phase 1):
   - T001: Create votes table migration [P]
   - T002: Extend papers table (vote_count, quick_summary, key_ideas, etc.) [P]
   - T003: Extend authors table (total_citation_count, latest_paper_id, email, website_url) [P]
   - T004: Extend metric_snapshots table (add vote_count field) [P]
   - T005: Run migrations and verify schema

2. **Contract Test Tasks** (Phase 2 - TDD):
   - T006: Write vote API contract tests (test_votes_api.py) [P]
   - T007: Write author API contract tests (test_authors_api.py) [P]
   - T008: Write extended paper API contract tests [P]
   - T009: Run contract tests (should FAIL - no implementation yet)

3. **Backend Model Tasks** (Phase 3):
   - T010: Implement Vote model (backend/src/models/vote.py) [P]
   - T011: Update Paper model with new fields [P]
   - T012: Update Author model with new fields [P]
   - T013: Update MetricSnapshot model with vote_count

4. **Backend Service Tasks** (Phase 4):
   - T014: Implement VoteService (vote management logic)
   - T015: Implement AuthorService (author lookup and stats calculation)
   - T016: Extend PaperEnrichmentService (URL detection in abstracts)
   - T017: Extend HypeScoreService (add vote component with logarithmic scaling)

5. **Backend API Tasks** (Phase 5):
   - T018: Implement vote endpoints (POST/DELETE /papers/{id}/vote)
   - T019: Implement author endpoints (GET /authors/{id})
   - T020: Extend paper endpoints (include vote_count, affiliations)
   - T021: Implement metrics time-series endpoint

6. **Integration Test Tasks** (Phase 6):
   - T022: Test voting flow (upvote → downvote → remove vote)
   - T023: Test author statistics accuracy
   - T024: Test hype score calculation with votes
   - T025: Test publication date display (arXiv latest version)

7. **Frontend Component Tasks** (Phase 7 - TDD):
   - T026: Write VoteButtons component tests [P]
   - T027: Write AuthorModal component tests [P]
   - T028: Write MetricGraph component tests [P]
   - T029: Implement VoteButtons component
   - T030: Implement AuthorModal component
   - T031: Implement MetricGraph component (Chart.js)
   - T032: Implement AbstractWithLinks component (URL detection)

8. **Frontend Integration Tasks** (Phase 8):
   - T033: Implement useVoting composable (state management)
   - T034: Implement voteService.ts (API calls)
   - T035: Implement authorService.ts (API calls)
   - T036: Update PaperDetailPage (add voting UI, author cards, graphs)
   - T037: Add "Start Crawling" button in quick actions

9. **Data Population Tasks** (Phase 9):
   - T038: Write script to populate author records from existing papers
   - T039: Run author population script
   - T040: Verify author statistics (paper_count, citation_count)

10. **Quickstart Validation** (Phase 10):
    - T041: Execute quickstart.md acceptance scenarios
    - T042: Fix any failing acceptance scenarios
    - T043: Performance validation (vote API < 200ms, graphs < 500ms)

**Ordering Strategy**:
- TDD order: Contract tests → models → services → API implementation → integration tests
- Dependency order: Database migrations → backend models → services → API → frontend
- [P] marks parallelizable tasks (independent files/modules)

**Estimated Output**: ~43 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

**No violations** - All features align with HypePaper constitution. Complexity tracking not required.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command) - 57 tasks ready for execution
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (none in spec)
- [x] Complexity deviations documented (none)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
