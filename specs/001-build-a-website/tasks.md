# Tasks: Trending Research Papers Tracker

**Input**: Design documents from `/specs/001-build-a-website/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/, quickstart.md

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/`, `backend/tests/` at repository root
- **Frontend**: `frontend/src/`, `frontend/tests/` at repository root
- **Shared**: `shared/schemas/` for TypeScript/Python type definitions

---

## Phase 3.1: Setup

- [x] T001 [P] Create backend project structure (backend/src/{models,services,api,jobs,llm}/, backend/tests/{contract,integration,unit}/)
- [x] T002 [P] Create frontend project structure (frontend/src/{components,pages,services,utils}/, frontend/tests/{components,integration}/)
- [x] T003 [P] Create shared schemas directory (shared/schemas/)
- [x] T004 Initialize Python backend with FastAPI dependencies (backend/requirements.txt: fastapi, uvicorn, sqlalchemy, asyncpg, alembic, httpx, pytest)
- [x] T005 Initialize Node.js frontend with Vite + React (frontend/package.json: react, vite, axios, recharts, tailwindcss, vitest)
- [x] T006 [P] Configure Python linting and type checking (backend/pyproject.toml: ruff, mypy)
- [x] T007 [P] Configure JavaScript linting (frontend/.eslintrc.js: ESLint with React rules)
- [x] T008 Create PostgreSQL + TimescaleDB setup script (docker-compose.yml or install instructions in docs/)
- [x] T009 Initialize Alembic for database migrations (backend/alembic/ with env.py configured for async SQLAlchemy)
- [x] T010 Download and configure llama.cpp Python bindings (backend/requirements.txt: llama-cpp-python)
- [x] T011 Create LLM model download script (backend/scripts/download_llm_model.py - downloads quantized 7B model to backend/models/)

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Backend Contract Tests
- [x] T012 [P] Contract test GET /api/v1/topics in backend/tests/contract/test_topics_get.py
- [x] T013 [P] Contract test GET /api/v1/topics/{id} in backend/tests/contract/test_topics_get_by_id.py
- [x] T014 [P] Contract test GET /api/v1/papers in backend/tests/contract/test_papers_get.py
- [x] T015 [P] Contract test GET /api/v1/papers/{id} in backend/tests/contract/test_papers_get_by_id.py
- [x] T016 [P] Contract test GET /api/v1/papers/{id}/metrics in backend/tests/contract/test_papers_metrics.py

### Frontend Component Tests
- [x] T017 [P] Component test for PaperCard in frontend/tests/components/test_paper_card.test.tsx
- [x] T018 [P] Component test for TopicList in frontend/tests/components/test_topic_list.test.tsx
- [x] T019 [P] Component test for TrendChart in frontend/tests/components/test_trend_chart.test.tsx
- [x] T020 [P] Component test for TopicManager in frontend/tests/components/test_topic_manager.test.tsx

### Integration Tests (5 Quickstart Scenarios)
- [x] T021 [P] Integration test Scenario 1 (First-time user adds topic) in backend/tests/integration/test_scenario_add_topic.py
- [x] T022 [P] Integration test Scenario 2 (Multiple topics grouped) in backend/tests/integration/test_scenario_multiple_topics.py
- [x] T023 [P] Integration test Scenario 3 (View paper trend history) in backend/tests/integration/test_scenario_paper_trends.py
- [x] T024 [P] Integration test Scenario 4 (New paper surfacing) in backend/tests/integration/test_scenario_new_paper.py
- [x] T025 [P] Integration test Scenario 5 (Rapid star growth ranking) in backend/tests/integration/test_scenario_ranking.py

---

## Phase 3.3: Core Backend Implementation ✅ COMPLETED (2025-10-02)

### Database Models
- [x] T026 [P] Create Paper model in backend/src/models/paper.py (SQLAlchemy with all fields from data-model.md)
- [x] T027 [P] Create Topic model in backend/src/models/topic.py
- [x] T028 [P] Create MetricSnapshot model in backend/src/models/metric_snapshot.py (TimescaleDB hypertable)
- [x] T029 [P] Create PaperTopicMatch model in backend/src/models/paper_topic_match.py
- [x] T030 Create Alembic migration for all models (backend/alembic/versions/001_initial_schema_with_timescaledb.py - includes TimescaleDB hypertable setup)

### Backend Services
- [x] T031 Create PaperService CRUD in backend/src/services/paper_service.py (create, get, list with filtering/sorting)
- [x] T032 Create TopicService CRUD in backend/src/services/topic_service.py (get, list)
- [x] T033 Create MetricService for time-series operations in backend/src/services/metric_service.py (create snapshot, get history, calculate growth rates)
- [x] T034 Create HypeScoreService for trend calculation in backend/src/services/hype_score_service.py (implements formula from research.md)
- [x] T035 Create TopicMatchingService with LLM integration in backend/src/services/topic_matching_service.py (llama.cpp wrapper, relevance scoring)

### API Routes
- [x] T036 Create GET /api/v1/topics endpoint in backend/src/api/topics.py (list all topics)
- [x] T037 Create GET /api/v1/topics/{id} endpoint in backend/src/api/topics.py (topic details)
- [x] T038 Create GET /api/v1/papers endpoint in backend/src/api/papers.py (list papers with filtering by topic, sorting by hype/recency/stars)
- [x] T039 Create GET /api/v1/papers/{id} endpoint in backend/src/api/papers.py (paper details with topics)
- [x] T040 Create GET /api/v1/papers/{id}/metrics endpoint in backend/src/api/papers.py (time-series metrics history)
- [x] T041 Configure FastAPI app with CORS, error handlers, API docs in backend/src/main.py

---

## Phase 3.4: Frontend Implementation ✅ COMPLETED (2025-10-02)

### API Client
- [x] T042 Create API client services in frontend/src/services/{papersService,topicsService}.ts (Axios wrappers for all backend endpoints)
- [x] T043 Create TypeScript types inline in service files (Paper, Topic, MetricSnapshot interfaces)

### React Components
- [x] T044 [P] Create PaperCard component in frontend/src/components/PaperCard.tsx (displays paper with hype score, trend indicator, links)
- [x] T045 [P] Create TopicList component in frontend/src/components/TopicList.tsx (displays available topics with add/remove buttons)
- [x] T046 [P] Create TrendChart component in frontend/src/components/TrendChart.tsx (Recharts line chart for stars/citations over time)
- [x] T047 [P] Create TopicManager component in frontend/src/components/TopicManager.tsx (manages localStorage for watched topics)
- [x] T048 [MERGED] PaperList functionality integrated into HomePage.tsx (papers displayed with sorting/filtering)

### Pages and Routing
- [x] T049 Create HomePage in frontend/src/pages/HomePage.tsx (main view: topic list + papers with sorting)
- [x] T050 Create PaperDetailPage in frontend/src/pages/PaperDetailPage.tsx (paper details + trend chart)
- [x] T051 Configure React Router in frontend/src/App.tsx (routes: / → HomePage, /papers/:paperId → PaperDetailPage)

### Utilities
- [x] T052 [INLINE] localStorage utility implemented inline in TopicManager.tsx (save/load watched topics)
- [x] T053 [INLINE] Formatting utilities implemented inline in components (date, score, trend formatting)

---

## Phase 3.5: Integration & Background Jobs ✅ COMPLETED (2025-10-02)

### API Integrations
- [x] T054 [P] Create arXiv API client in backend/src/jobs/arxiv_client.py (fetch papers by category, parse metadata)
- [x] T055 [P] Create Papers With Code API client in backend/src/jobs/paperwithcode_client.py (link papers to GitHub repos)
- [x] T056 [P] Create Semantic Scholar API client in backend/src/jobs/semanticscholar_client.py (fetch citation counts)
- [x] T057 [P] Create GitHub API client in backend/src/jobs/github_client.py (fetch star counts with rate limiting)

### Background Jobs
- [x] T058 Create daily paper discovery job in backend/src/jobs/discover_papers.py (fetch from arXiv, cross-reference Papers With Code, store in DB)
- [x] T059 Create daily metric update job in backend/src/jobs/update_metrics.py (fetch stars/citations for all tracked papers, create MetricSnapshots)
- [x] T060 Create topic matching job in backend/src/jobs/match_topics.py (run LLM on new papers, create PaperTopicMatches with relevance >= 6.0)
- [x] T061 Configure APScheduler in backend/src/jobs/scheduler.py (cron: 2 AM UTC daily for all jobs)

### Database Seeding
- [x] T062 Create topic seed script in backend/scripts/seed_topics.py (insert predefined topics: neural rendering, diffusion models, 3d reconstruction, etc.)
- [x] T063 Create sample data seed script in backend/scripts/seed_sample_data.py (add ~50 sample papers for testing)

---

## Phase 3.6: Polish

### Styling & Responsiveness
- [ ] T064 [P] Configure TailwindCSS for mobile-first design in frontend/tailwind.config.js
- [ ] T065 [P] Implement responsive layouts for all components (breakpoints: 375px mobile, 768px tablet, 1024px desktop)
- [ ] T066 [P] Add loading states to all components (skeleton screens or spinners)
- [ ] T067 [P] Add error boundaries and error messages in frontend/src/components/ErrorBoundary.tsx

### Performance Optimization
- [ ] T068 Implement API response caching in backend (cache hype scores for 1 hour)
- [ ] T069 Add code splitting and lazy loading in frontend/src/App.tsx (lazy load PaperDetailPage)
- [ ] T070 Optimize database queries (add missing indexes, verify TimescaleDB compression working)
- [ ] T071 Run performance tests (page load < 2s, API response < 500ms) and fix bottlenecks

### Testing & Validation
- [ ] T072 [P] Write unit tests for hype score calculation in backend/tests/unit/test_hype_score.py (validate formula matches research.md)
- [ ] T073 [P] Write unit tests for topic matching accuracy in backend/tests/unit/test_topic_matching.py (validate relevance scoring)
- [ ] T074 Run full integration test suite (all 5 quickstart scenarios) and verify passing
- [ ] T075 Run mobile responsiveness tests (375px, 768px, 1024px widths)

### Documentation & Deployment
- [ ] T076 [P] Create backend README in backend/README.md (setup instructions, API docs link, architecture overview)
- [ ] T077 [P] Create frontend README in frontend/README.md (setup instructions, component structure, development guide)
- [ ] T078 [P] Document hype score algorithm in docs/hype-score.md (formula, examples, versioning)
- [ ] T079 Create deployment guide in docs/deployment.md (docker-compose setup, nginx config, environment variables)
- [ ] T080 Create quickstart execution script in scripts/run_quickstart.sh (automate all 5 scenarios for validation)

---

## Dependencies

```
Setup (T001-T011)
  ↓
Tests (T012-T025) [Must fail before implementation]
  ↓
Models (T026-T030) [P] → Services (T031-T035) → API Routes (T036-T041)
  ↓
Frontend Components (T044-T048) [P] → Pages (T049-T051)
  ↓
Jobs (T054-T061) → Seeding (T062-T063)
  ↓
Polish (T064-T080)
```

### Critical Path
1. **T001-T011**: Setup infrastructure (parallel where possible)
2. **T012-T025**: Write all tests (TDD - must fail)
3. **T026-T030**: Database models (blocks services)
4. **T031-T035**: Services (blocks API routes and jobs)
5. **T036-T041**: API routes (blocks frontend)
6. **T042-T051**: Frontend (depends on API)
7. **T054-T063**: Jobs and seeding (depends on full stack)
8. **T064-T080**: Polish (depends on everything)

---

## Parallel Execution Examples

### Example 1: Backend Setup (T001, T002, T003 together)
```bash
# Run in parallel since they create different directories
mkdir -p backend/src/{models,services,api,jobs,llm} backend/tests/{contract,integration,unit}
mkdir -p frontend/src/{components,pages,services,utils} frontend/tests/{components,integration}
mkdir -p shared/schemas
```

### Example 2: Database Models (T026-T029 together)
All model files are independent, can be created in parallel:
- backend/src/models/paper.py
- backend/src/models/topic.py
- backend/src/models/metric_snapshot.py
- backend/src/models/paper_topic_match.py

### Example 3: Contract Tests (T012-T016 together)
All contract tests can be written in parallel since they test different endpoints:
- backend/tests/contract/test_topics_get.py
- backend/tests/contract/test_topics_get_by_id.py
- backend/tests/contract/test_papers_get.py
- backend/tests/contract/test_papers_get_by_id.py
- backend/tests/contract/test_papers_metrics.py

### Example 4: Frontend Components (T044-T048 together)
All component files are independent:
- frontend/src/components/PaperCard.tsx
- frontend/src/components/TopicList.tsx
- frontend/src/components/TrendChart.tsx
- frontend/src/components/TopicManager.tsx
- frontend/src/components/PaperList.tsx

### Example 5: API Clients (T054-T057 together)
All external API clients can be implemented in parallel:
- backend/src/jobs/arxiv_client.py
- backend/src/jobs/paperwithcode_client.py
- backend/src/jobs/semanticscholar_client.py
- backend/src/jobs/github_client.py

---

## Notes

### TDD Enforcement
- **Phase 3.2** tests MUST fail before moving to Phase 3.3
- Verify tests are actually failing by running:
  - Backend: `cd backend && pytest`
  - Frontend: `cd frontend && npm test`
- Do not proceed until you see expected failures

### File Path Specificity
Each task specifies exact file paths to avoid ambiguity:
- ✅ "Create Paper model in backend/src/models/paper.py"
- ❌ "Create Paper model"

### Constitution Alignment
- T068-T071: Performance tasks enforce <2s page load (Principle I)
- T034, T072: Hype score transparency (Principle V)
- T035, T073: Topic matching accuracy (Principle II)
- T062: Predefined topics seed (Principle III)
- T058-T061: Daily updates (Principle IV)

### MVP Scope Boundaries
Tasks excluded from MVP (deferred to post-MVP):
- User authentication/accounts (using localStorage)
- User-created topics (predefined only)
- Paper recommendations beyond trending
- AI chat or summarization features
- Note-taking or collaboration features

---

**Total Tasks**: 80
**Parallel Opportunities**: ~25 tasks marked [P]
**Estimated Completion**: 40-50 hours for MVP (with parallelization)

**Status**: ✅ Ready for execution via `/implement` or manual task processing
