# Tasks: Paper Enrichment Feature Improvements

**Feature**: 003-add-paper-enrichment
**Input**: Design documents from `/specs/003-add-paper-enrichment/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow

This tasks document was generated from the following design artifacts:
- **plan.md**: Tech stack (Python 3.11+/FastAPI, Vue 3/TypeScript), web app structure
- **research.md**: Vote storage, URL detection, hype score formula, author disambiguation
- **data-model.md**: Vote, Paper (extended), Author (extended), MetricSnapshot (extended)
- **contracts/**: votes-api.yaml, authors-api.yaml, papers-api-extended.yaml
- **quickstart.md**: 12 acceptance scenarios, 7 edge cases, 4 performance tests

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All file paths are absolute or relative to repository root

## Phase 3.1: Database Migrations

- [ ] **T001** [P] Create votes table migration in `backend/alembic/versions/xxx_add_votes_table.py`
  - Fields: user_id (UUID, FK to auth.users), paper_id (UUID, FK to papers), vote_type (ENUM), created_at, updated_at
  - Primary key: (user_id, paper_id)
  - Indexes: idx_votes_paper, idx_votes_user
  - Refer to: data-model.md → Vote schema

- [ ] **T002** [P] Create papers table extension migration in `backend/alembic/versions/xxx_extend_papers_table.py`
  - Add columns: vote_count (INT default 0), quick_summary (TEXT), key_ideas (TEXT), quantitative_performance (JSONB), qualitative_performance (TEXT)
  - Add index: idx_papers_vote_count
  - Refer to: data-model.md → Paper extensions

- [ ] **T003** [P] Create authors table extension migration in `backend/alembic/versions/xxx_extend_authors_table.py`
  - Drop constraint: authors_name_key (remove unique on name)
  - Add columns: total_citation_count (INT default 0), latest_paper_id (UUID FK), email (VARCHAR 200), website_url (VARCHAR 500)
  - Add indexes: idx_authors_citation_count, idx_authors_paper_count
  - Refer to: data-model.md → Author extensions

- [ ] **T004** [P] Create metric_snapshots extension migration in `backend/alembic/versions/xxx_extend_metric_snapshots.py`
  - Add columns: vote_count (INT), hype_score (FLOAT)
  - Add constraint: hype_score_non_negative CHECK
  - Refer to: data-model.md → MetricSnapshot extensions

- [ ] **T005** [P] Create vote_count trigger migration in `backend/alembic/versions/xxx_add_vote_count_trigger.py`
  - Create function: update_paper_vote_count()
  - Create trigger: vote_count_trigger on votes table (INSERT/UPDATE/DELETE)
  - Refer to: data-model.md → Migration 5

- [ ] **T006** Run database migrations and verify schema
  ```bash
  cd backend && alembic upgrade head
  ```
  - Verify all tables exist with correct columns
  - Verify constraints and indexes created
  - Rollback test: `alembic downgrade -1` then re-upgrade

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Endpoints)

- [ ] **T007** [P] Vote API contract tests in `backend/tests/contract/test_votes_api.py`
  - Test POST /api/papers/{id}/vote (upvote/downvote)
  - Test DELETE /api/papers/{id}/vote (remove vote)
  - Test GET /api/papers/{id}/vote/status (check user vote)
  - Assert response schemas match contracts/votes-api.yaml
  - Assert 401 Unauthorized without auth token
  - Refer to: contracts/votes-api.yaml

- [ ] **T008** [P] Author API contract tests in `backend/tests/contract/test_authors_api.py`
  - Test GET /api/authors/{id} (author details)
  - Test GET /api/authors/search?q=name (author search)
  - Assert response schemas match contracts/authors-api.yaml
  - Assert 404 for non-existent author
  - Refer to: contracts/authors-api.yaml

- [ ] **T009** [P] Papers API extension contract tests in `backend/tests/contract/test_papers_api_extended.py`
  - Test GET /api/papers/{id} includes vote_count, enriched fields
  - Test GET /api/papers/{id}/metrics?days=30 (time-series)
  - Assert response schemas match contracts/papers-api-extended.yaml
  - Assert published_date is actual publish date (not created_at)
  - Refer to: contracts/papers-api-extended.yaml

### Integration Tests (User Scenarios)

- [ ] **T010** [P] Voting flow integration tests in `backend/tests/integration/test_voting_flow.py`
  - Scenario 3: User upvotes paper → vote_count increases
  - Scenario 4: User removes upvote → vote_count decreases
  - Scenario 5: User changes upvote to downvote → vote_count changes by 2
  - Edge case: Unauthenticated user cannot vote (401)
  - Refer to: quickstart.md → Scenarios 3-5, EC3

- [ ] **T011** [P] Author statistics integration tests in `backend/tests/integration/test_author_stats.py`
  - Scenario 6: Clicking author name returns author details
  - Verify paper_count equals actual count in paper_authors
  - Verify total_citation_count equals sum of paper citations
  - Edge case: Author with no affiliation displays null
  - Refer to: quickstart.md → Scenario 6, EC4

- [ ] **T012** [P] Publication date accuracy tests in `backend/tests/integration/test_publication_dates.py`
  - Scenario 1: Paper shows published_date (not created_at)
  - arXiv papers with multiple versions use latest version date
  - Edge case: Paper without publish date (fallback handling)
  - Refer to: quickstart.md → Scenario 1, EC1

- [ ] **T013** [P] Hype score calculation tests in `backend/tests/integration/test_hype_score.py`
  - Test logarithmic vote component: log(1 + max(0, votes)) * 5
  - Verify 0 votes → 0 contribution, 10 votes → ~5.4, 100 votes → ~10.1
  - Test negative votes → 0 contribution (clamped)
  - Verify hype score formula: citations(35%) + stars(35%) + absolute(20%) + votes(10%)
  - Edge case: Negative vote_count (EC6, EC7)
  - Refer to: research.md → Decision 4, quickstart.md → EC6-EC7

- [ ] **T014** Run all contract and integration tests (should FAIL)
  ```bash
  cd backend && pytest tests/contract tests/integration -v
  ```
  - Expected: All tests fail (no implementation yet)
  - If any test passes: ERROR "Implementation exists before tests"

## Phase 3.3: Core Implementation (Backend Models)

**ONLY proceed after Phase 3.2 tests are written and failing**

### Database Models

- [ ] **T015** [P] Implement Vote model in `backend/src/models/vote.py`
  - Fields: user_id, paper_id, vote_type (Enum: upvote/downvote), created_at, updated_at
  - Composite primary key: (user_id, paper_id)
  - Relationships: vote.paper → Paper
  - Refer to: data-model.md → Vote model

- [ ] **T016** [P] Extend Paper model in `backend/src/models/paper.py`
  - Add fields: vote_count, quick_summary, key_ideas, quantitative_performance, qualitative_performance
  - Add relationship: paper.votes → List[Vote]
  - Add computed property: net_votes() for verification
  - Refer to: data-model.md → Paper extensions

- [ ] **T017** [P] Extend Author model in `backend/src/models/author.py`
  - Remove unique constraint on name field
  - Add fields: total_citation_count, latest_paper_id (FK), email, website_url
  - Add relationship: author.latest_paper → Paper
  - Add computed properties: primary_affiliation, avg_citations_per_paper
  - Refer to: data-model.md → Author extensions

- [ ] **T018** Extend MetricSnapshot model in `backend/src/models/metric_snapshot.py`
  - Add fields: vote_count, hype_score
  - Refer to: data-model.md → MetricSnapshot extensions

- [ ] **T019** Update model exports in `backend/src/models/__init__.py`
  - Add Vote to __all__ list
  - Import Vote in init file

## Phase 3.4: Core Implementation (Backend Services)

- [ ] **T020** Implement VoteService in `backend/src/services/vote_service.py`
  - `async def cast_vote(user_id, paper_id, vote_type, db)` - create or update vote
  - `async def remove_vote(user_id, paper_id, db)` - delete vote
  - `async def get_vote_status(user_id, paper_id, db)` - check if user voted
  - `async def get_vote_count(paper_id, db)` - calculate net votes
  - Handle upsert logic (INSERT or UPDATE on conflict)
  - Refer to: research.md → Decision 1 (vote storage)

- [ ] **T021** Implement AuthorService in `backend/src/services/author_service.py`
  - `async def get_author_by_id(author_id, db)` - fetch author with stats
  - `async def search_authors(query, limit, db)` - search by name
  - `async def get_recent_papers(author_id, limit, db)` - fetch author's recent papers
  - `async def calculate_author_stats(author_id, db)` - recompute paper_count, citation_count
  - Refer to: research.md → Decision 6 (author lookup)

- [ ] **T022** Extend PaperEnrichmentService in `backend/src/services/paper_enrichment.py`
  - `def detect_urls(abstract: str) -> list[dict]` - regex URL detection
  - `def classify_url(url: str) -> str` - return 'github' or 'project'
  - Use regex pattern: `https?://[^\s]+`
  - GitHub detection: check domain contains 'github.com' or 'github.io'
  - Refer to: research.md → Decision 2 (URL detection)

- [ ] **T023** Create or extend HypeScoreService in `backend/src/services/hype_score.py`
  - `def calculate_vote_component(vote_count: int) -> float` - logarithmic scaling
  - `def calculate_hype_score(citation_growth, star_growth, absolute_metrics, vote_count) -> float`
  - Formula: `log(1 + max(0, votes)) * 5` for vote component
  - Weights: citations 35%, stars 35%, absolute 20%, votes 10%
  - Refer to: research.md → Decision 4 (hype score)

## Phase 3.5: Core Implementation (Backend API Endpoints)

- [ ] **T024** Implement vote endpoints in `backend/src/api/votes.py`
  - POST /api/papers/{paper_id}/vote - cast or update vote (requires auth)
  - DELETE /api/papers/{paper_id}/vote - remove vote (requires auth)
  - GET /api/papers/{paper_id}/vote/status - get user's vote status (requires auth)
  - Extract user_id from Supabase auth context (JWT token)
  - Call VoteService methods
  - Return responses matching contracts/votes-api.yaml
  - Refer to: contracts/votes-api.yaml

- [ ] **T025** Implement author endpoints in `backend/src/api/authors.py`
  - GET /api/authors/{author_id} - author details with stats
  - GET /api/authors/search?q={query}&limit={limit} - author search
  - Call AuthorService methods
  - Return responses matching contracts/authors-api.yaml
  - Refer to: contracts/authors-api.yaml

- [ ] **T026** Extend paper endpoints in `backend/src/api/papers.py`
  - Update GET /api/papers/{paper_id} response to include vote_count, enriched fields
  - Include author affiliations in author list
  - Use published_date field (not created_at)
  - Refer to: contracts/papers-api-extended.yaml

- [ ] **T027** Create metrics endpoint in `backend/src/api/metrics.py`
  - GET /api/papers/{paper_id}/metrics?days={days} - time-series snapshots
  - Query metric_snapshots table with date filter
  - Order by snapshot_date ASC
  - Return array of snapshots with date, citation_count, github_stars, vote_count, hype_score
  - Refer to: contracts/papers-api-extended.yaml → MetricSnapshot schema

- [ ] **T028** Register new API routes in `backend/src/main.py`
  - Include votes router: `app.include_router(votes.router, prefix="/api", tags=["votes"])`
  - Include authors router: `app.include_router(authors.router, prefix="/api", tags=["authors"])`
  - Include metrics router: `app.include_router(metrics.router, prefix="/api", tags=["metrics"])`

## Phase 3.6: Data Population Scripts

- [ ] **T029** [P] Create author population script in `backend/scripts/populate_author_statistics.py`
  - Iterate over all authors
  - Calculate paper_count from paper_authors table
  - Calculate total_citation_count from sum of paper citations
  - Find latest_paper_id (most recent by published_date)
  - Update author records
  - Refer to: data-model.md → Data Population Scripts

- [ ] **T030** Run author population script
  ```bash
  cd backend && python scripts/populate_author_statistics.py
  ```
  - Verify author statistics are accurate
  - Check logs for any errors

- [ ] **T031** [P] Create vote_count sync script in `backend/scripts/sync_vote_counts.py`
  - Iterate over all papers
  - Calculate vote_count from votes table (COUNT upvotes - COUNT downvotes)
  - Update papers.vote_count field
  - Refer to: data-model.md → Script 2

- [ ] **T032** Verify backend integration tests pass
  ```bash
  cd backend && pytest tests/integration -v
  ```
  - Expected: All integration tests pass
  - If failures: Debug and fix implementation

## Phase 3.7: Frontend Components (Tests First)

- [ ] **T033** [P] VoteButtons component tests in `frontend/tests/unit/VoteButtons.spec.ts`
  - Test upvote button click → emits 'vote' event with 'upvote'
  - Test downvote button click → emits 'vote' event with 'downvote'
  - Test active state when user has voted (upvote button highlighted)
  - Test disabled state when not authenticated
  - Test vote count display updates

- [ ] **T034** [P] AuthorModal component tests in `frontend/tests/unit/AuthorModal.spec.ts`
  - Test modal opens on author name click
  - Test displays author name, affiliation, stats
  - Test recent papers list renders (up to 5 papers)
  - Test "View all papers" button navigation
  - Test modal closes on backdrop click

- [ ] **T035** [P] MetricGraph component tests in `frontend/tests/unit/MetricGraph.spec.ts`
  - Test Chart.js line chart renders with time-series data
  - Test tooltip shows on hover (date + value)
  - Test handles null values (e.g., github_stars=null)
  - Test loading state while fetching data
  - Test error state on API failure

- [ ] **T036** [P] AbstractWithLinks component tests in `frontend/tests/unit/AbstractWithLinks.spec.ts`
  - Test URLs in abstract are hyperlinked
  - Test GitHub URLs have GitHub icon
  - Test non-GitHub URLs have generic link icon
  - Test `rel="noopener noreferrer"` on links
  - Test plain text without URLs renders unchanged

- [ ] **T037** Run frontend component tests (should FAIL)
  ```bash
  cd frontend && npm run test
  ```
  - Expected: All tests fail (components not implemented yet)

## Phase 3.8: Frontend Components (Implementation)

- [ ] **T038** Implement VoteButtons component in `frontend/src/components/VoteButtons.vue`
  - Upvote and downvote buttons with icons
  - Display current vote_count
  - Emit 'vote' event with vote_type ('upvote' | 'downvote')
  - Emit 'removeVote' event when clicking active button
  - Show active state (highlighted button) when user has voted
  - Disable buttons when not authenticated

- [ ] **T039** Implement AuthorModal component in `frontend/src/components/AuthorModal.vue`
  - Modal dialog with author information
  - Display: name, primary_affiliation, paper_count, total_citation_count, email, website_url
  - Recent papers list (up to 5 papers with titles and dates)
  - "View all papers" button → navigates to filtered papers page
  - Close button and backdrop click to close modal
  - Refer to: research.md → Decision 6 (author modal)

- [ ] **T040** Implement MetricGraph component in `frontend/src/components/MetricGraph.vue`
  - Use Chart.js Line chart
  - Props: paperId, metricType ('citations' | 'stars' | 'votes' | 'hype_score')
  - Fetch data from /api/papers/{paperId}/metrics?days=30
  - X-axis: dates, Y-axis: metric values
  - Tooltip on hover showing date and value
  - Handle null values (don't break chart)
  - Refer to: research.md → Decision 5 (Chart.js graphs)

- [ ] **T041** Implement AbstractWithLinks component in `frontend/src/components/AbstractWithLinks.vue`
  - Props: abstract (string)
  - Detect URLs using regex: `https?://[^\s]+`
  - Replace URLs with `<a>` tags
  - Add GitHub icon for github.com/github.io URLs
  - Add generic link icon for other URLs
  - Add `rel="noopener noreferrer" target="_blank"` to links
  - Refer to: research.md → Decision 2 (URL detection)

## Phase 3.9: Frontend Services & State Management

- [ ] **T042** Implement vote service in `frontend/src/services/voteService.ts`
  - `castVote(paperId, voteType)` - POST /api/papers/{id}/vote
  - `removeVote(paperId)` - DELETE /api/papers/{id}/vote
  - `getVoteStatus(paperId)` - GET /api/papers/{id}/vote/status
  - Include auth token in headers
  - Handle 401 Unauthorized errors

- [ ] **T043** Implement author service in `frontend/src/services/authorService.ts`
  - `getAuthor(authorId)` - GET /api/authors/{id}
  - `searchAuthors(query, limit)` - GET /api/authors/search
  - Handle 404 Not Found errors

- [ ] **T044** Implement useVoting composable in `frontend/src/composables/useVoting.ts`
  - State: currentVote (upvote | downvote | null), voteCount, isLoading
  - Methods: upvote(), downvote(), removeVote()
  - Fetch vote status on mount
  - Update local state after vote actions
  - Emit events for vote count changes

## Phase 3.10: Frontend Integration

- [ ] **T045** Update PaperDetailPage in `frontend/src/pages/PaperDetailPage.vue`
  - Add VoteButtons component above abstract
  - Replace plain author names with clickable author cards
  - Add AuthorModal component (opens on author name click)
  - Replace plain abstract text with AbstractWithLinks component
  - Add "Quick Summary", "Key Ideas", "Performance", "Limitations" sections (if data exists)
  - Add "Metrics Trends" section with 4 MetricGraph components (citations, stars, votes, hype_score)
  - Add "Start Crawling from This Paper" button in Quick Actions
  - Refer to: quickstart.md → Scenarios 7-12

- [ ] **T046** Add Quick Actions section to PaperDetailPage
  - "Start Crawling from This Paper" button
  - Navigate to `/crawler?type=citation_network&paper_id={paperId}` on click
  - Refer to: quickstart.md → Scenario 12

- [ ] **T047** Update paper list components to display vote_count
  - Show vote count badge next to paper title
  - Update sort options to include "Most Voted"

## Phase 3.11: Performance & Polish

- [ ] **T048** [P] Backend unit tests for vote logic in `backend/tests/unit/test_vote_service.py`
  - Test vote upsert logic (INSERT vs UPDATE)
  - Test vote_count calculation (upvotes - downvotes)
  - Test edge cases: negative votes, zero votes

- [ ] **T049** [P] Backend unit tests for hype score in `backend/tests/unit/test_hype_score.py`
  - Test logarithmic vote component calculation
  - Test edge cases: 0 votes, negative votes, 1000 votes
  - Verify formula weights (35%/35%/20%/10%)

- [ ] **T050** [P] Frontend integration tests in `frontend/tests/integration/PaperDetailPage.spec.ts`
  - Test voting flow: upvote → vote count increases
  - Test author modal opens on click
  - Test time-series graphs render
  - Test URL hyperlinking in abstract

- [ ] **T051** Performance validation: Vote API response time
  ```bash
  # Measure vote endpoint latency
  time curl -X POST http://localhost:8000/api/papers/{id}/vote \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"vote_type": "upvote"}'
  ```
  - Target: < 200ms
  - If slower: Optimize database query or add caching
  - Refer to: quickstart.md → P1

- [ ] **T052** Performance validation: Author lookup response time
  ```bash
  time curl http://localhost:8000/api/authors/{id}
  ```
  - Target: < 300ms
  - If slower: Add database indexes or caching
  - Refer to: quickstart.md → P2

- [ ] **T053** Performance validation: Metric graph render time
  - Open DevTools Performance tab
  - Navigate to paper detail page
  - Measure time from metrics API response to graph render
  - Target: < 500ms
  - If slower: Reduce data points or optimize Chart.js config
  - Refer to: quickstart.md → P3

- [ ] **T054** Performance validation: Page load time
  - Open DevTools Performance tab
  - Hard refresh paper detail page
  - Measure time to interactive
  - Target: < 2 seconds (constitutional requirement)
  - Refer to: quickstart.md → P4, constitution.md

## Phase 3.12: Quickstart Validation

- [ ] **T055** Execute all quickstart scenarios in `specs/003-add-paper-enrichment/quickstart.md`
  - Scenarios 1-12: All functional scenarios
  - Edge cases EC1-EC7: All edge cases handled
  - Performance P1-P4: All performance targets met
  - Document any failures and fix before proceeding

- [ ] **T056** Verify data integrity with validation queries
  ```sql
  -- Check vote_count consistency
  SELECT p.id, p.vote_count,
         COALESCE(SUM(CASE WHEN v.vote_type = 'upvote' THEN 1 ELSE -1 END), 0) AS actual_votes
  FROM papers p
  LEFT JOIN votes v ON p.id = v.paper_id
  GROUP BY p.id, p.vote_count
  HAVING p.vote_count != COALESCE(SUM(CASE WHEN v.vote_type = 'upvote' THEN 1 ELSE -1 END), 0);
  ```
  - Refer to: data-model.md → Data Integrity section
  - Expected: No rows returned (perfect consistency)

- [ ] **T057** Final constitution check
  - Page load < 2s? ✅
  - Vote feature adds community signal? ✅
  - GitHub stars remain primary metric (35% weight)? ✅
  - No feature creep (no AI chat, notes, collaboration)? ✅
  - Refer to: constitution.md, plan.md → Constitution Check

## Dependencies

### Phase Order
- Phase 3.1 (Migrations) → Phase 3.2 (Tests)
- Phase 3.2 (Tests) → Phase 3.3-3.5 (Backend Implementation)
- Phase 3.3 (Models) → Phase 3.4 (Services) → Phase 3.5 (Endpoints)
- Phase 3.5 (Backend APIs) → Phase 3.7 (Frontend Tests) → Phase 3.8-3.10 (Frontend Implementation)
- Phase 3.1-3.10 → Phase 3.11 (Performance & Polish) → Phase 3.12 (Validation)

### Critical Blockers
- T001-T006 (migrations) block all backend implementation
- T007-T014 (tests) must FAIL before T015-T028 (implementation)
- T015-T019 (models) block T020-T023 (services)
- T020-T023 (services) block T024-T028 (endpoints)
- T024-T028 (endpoints) block T042-T044 (frontend services)

### Parallel Opportunities
- T001-T005: All migrations can be created in parallel
- T007-T013: All test files can be written in parallel
- T015-T017: Model extensions can be done in parallel
- T020-T023: Service implementations can be done in parallel (different files)
- T033-T036: Frontend component tests can be written in parallel
- T038-T041: Frontend components can be implemented in parallel (different files)

## Parallel Execution Examples

### Execute all migration tasks together:
```bash
# Task: Create votes table migration
alembic revision -m "add_votes_table"
# Edit the generated file with Vote schema

# Task: Extend papers table migration
alembic revision -m "extend_papers_table"
# Edit with Paper extensions

# Task: Extend authors table migration
alembic revision -m "extend_authors_table"
# Edit with Author extensions

# Task: Extend metric_snapshots migration
alembic revision -m "extend_metric_snapshots"
# Edit with MetricSnapshot extensions

# Task: Add vote_count trigger
alembic revision -m "add_vote_count_trigger"
# Edit with trigger function
```

### Execute all contract test tasks together:
```bash
# Launch 3 agents in parallel to write test files
pytest tests/contract/test_votes_api.py -v  # Should fail
pytest tests/contract/test_authors_api.py -v  # Should fail
pytest tests/contract/test_papers_api_extended.py -v  # Should fail
```

### Execute all frontend component implementations together:
```bash
# These tasks modify different files, can run in parallel
# Task: VoteButtons.vue
# Task: AuthorModal.vue
# Task: MetricGraph.vue
# Task: AbstractWithLinks.vue
```

## Validation Checklist

*GATE: All must be checked before feature is complete*

- [x] All contracts have corresponding tests (T007-T009)
- [x] All entities have model tasks (T015-T018)
- [x] All tests come before implementation (Phase 3.2 before 3.3)
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD workflow enforced (tests → implementation)
- [x] Performance targets specified (<200ms, <300ms, <500ms, <2s)
- [x] Constitution compliance verified (T057)

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **TDD enforcement**: Tests in Phase 3.2 MUST fail before implementing Phase 3.3-3.5
- **Commit strategy**: Commit after each task completion
- **Database backups**: Backup database before running migrations
- **Auth requirement**: All vote endpoints require Supabase JWT authentication
- **Avoid**: Vague tasks, same file conflicts, skipping tests

---
**Task Count**: 57 tasks
**Estimated Time**: 30-40 hours for full implementation
**Ready for Execution**: ✅ All tasks are specific and executable
**Next Command**: Start with T001 (migrations) or execute T001-T005 in parallel
