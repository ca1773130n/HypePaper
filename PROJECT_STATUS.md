# HypePaper Project Status

**Last Updated**: 2025-10-01
**Branch**: `001-build-a-website`
**Current Phase**: Setup Complete → Ready for TDD

---

## 📊 Overall Progress

**Total Tasks**: 80
**Completed**: 11 (13.75%)
**Remaining**: 69 (86.25%)

```
Phase 3.1: Setup                    ████████████████████ 100% (11/11) ✅
Phase 3.2: Tests (TDD)              ░░░░░░░░░░░░░░░░░░░░   0% (0/14)
Phase 3.3: Core Backend             ░░░░░░░░░░░░░░░░░░░░   0% (0/16)
Phase 3.4: Frontend                 ░░░░░░░░░░░░░░░░░░░░   0% (0/12)
Phase 3.5: Integration & Jobs       ░░░░░░░░░░░░░░░░░░░░   0% (0/10)
Phase 3.6: Polish                   ░░░░░░░░░░░░░░░░░░░░   0% (0/17)
```

---

## ✅ Completed: Phase 3.1 - Setup

### Infrastructure
- ✅ **T001**: Backend directory structure created
  - `backend/src/{models,services,api/routes,jobs,llm}/`
  - `backend/tests/{contract,integration,unit}/`
  - `backend/alembic/versions/`
  - `backend/scripts/`

- ✅ **T002**: Frontend directory structure created
  - `frontend/src/{components,pages,services,utils}/`
  - `frontend/tests/{components,integration}/`

- ✅ **T003**: Shared schemas directory
  - `shared/schemas/`
  - `docs/`

### Backend Configuration
- ✅ **T004**: Python dependencies (`backend/requirements.txt`)
  - FastAPI 0.104.1
  - SQLAlchemy 2.0.23 (async)
  - PostgreSQL drivers (asyncpg, psycopg2-binary)
  - Alembic 1.12.1
  - llama-cpp-python 0.2.20
  - pytest, httpx, APScheduler

- ✅ **T006**: Linting & type checking (`backend/pyproject.toml`)
  - Ruff configured
  - Mypy with strict settings
  - pytest configuration

- ✅ **T009**: Alembic initialized
  - `backend/alembic.ini`
  - `backend/alembic/env.py` (async support)
  - `backend/alembic/script.py.mako`

- ✅ **T011**: LLM download script
  - `backend/scripts/download_llm_model.py`
  - Instructions for Mistral 7B Q4_K_M model

### Frontend Configuration
- ✅ **T005**: Node.js dependencies (`frontend/package.json`)
  - React 18.2.0
  - Vite 5.0.0
  - React Router 6.20.0
  - Axios, Recharts
  - TailwindCSS
  - Vitest, Testing Library

- ✅ **T007**: ESLint configuration
  - `frontend/.eslintrc.cjs`
  - TypeScript + React rules

### Database
- ✅ **T008**: PostgreSQL + TimescaleDB
  - `docker-compose.yml` with TimescaleDB image
  - `backend/init_db.sql` for extensions
  - Port 5432 exposed
  - Health checks configured

---

## 📋 Next Phase: 3.2 - Tests First (TDD)

**Critical**: All 14 tests MUST be written and MUST FAIL before proceeding to Phase 3.3

### Backend Contract Tests (T012-T016) - 5 tasks
Write API contract tests that verify OpenAPI specifications:
- [ ] **T012**: GET `/api/v1/topics` - list all topics
- [ ] **T013**: GET `/api/v1/topics/{id}` - topic details
- [ ] **T014**: GET `/api/v1/papers` - list papers with filters
- [ ] **T015**: GET `/api/v1/papers/{id}` - paper details
- [ ] **T016**: GET `/api/v1/papers/{id}/metrics` - time-series data

**Files**: `backend/tests/contract/test_*.py`

### Frontend Component Tests (T017-T020) - 4 tasks
Write component tests using React Testing Library:
- [ ] **T017**: PaperCard component
- [ ] **T018**: TopicList component
- [ ] **T019**: TrendChart component
- [ ] **T020**: TopicManager component

**Files**: `frontend/tests/components/test_*.test.tsx`

### Integration Tests (T021-T025) - 5 tasks
Write end-to-end scenario tests from `quickstart.md`:
- [ ] **T021**: Scenario 1 - First-time user adds topic
- [ ] **T022**: Scenario 2 - Multiple topics grouped
- [ ] **T023**: Scenario 3 - View paper trend history
- [ ] **T024**: Scenario 4 - New paper surfacing
- [ ] **T025**: Scenario 5 - Rapid star growth ranking

**Files**: `backend/tests/integration/test_scenario_*.py`

### Why TDD Matters
These tests define the contracts before implementation. They will:
1. Guide implementation (tests tell you what to build)
2. Prevent scope creep (only build what tests require)
3. Enable refactoring (tests ensure nothing breaks)
4. Document behavior (tests show how system should work)

---

## 🔜 Upcoming Phases

### Phase 3.3: Core Backend (T026-T041) - 16 tasks
**Database Models** (4 tasks, can run in parallel):
- Paper, Topic, MetricSnapshot (TimescaleDB hypertable), PaperTopicMatch
- Alembic migration with TimescaleDB configuration

**Services** (5 tasks, sequential):
- PaperService, TopicService, MetricService
- HypeScoreService (implements formula from research.md)
- TopicMatchingService (llama.cpp integration)

**API Routes** (6 tasks):
- Topics endpoints (GET /topics, GET /topics/{id})
- Papers endpoints (GET /papers, GET /papers/{id}, GET /papers/{id}/metrics)
- FastAPI app configuration (CORS, error handlers, docs)

### Phase 3.4: Frontend (T042-T053) - 12 tasks
**API Client** (2 tasks):
- Axios wrapper
- TypeScript types from OpenAPI

**Components** (5 tasks, can run in parallel):
- PaperCard, TopicList, TrendChart, TopicManager, PaperList

**Pages** (3 tasks):
- HomePage, PaperDetailPage, React Router setup

**Utilities** (2 tasks):
- localStorage wrapper
- Formatting utilities (scores, dates)

### Phase 3.5: Integration & Jobs (T054-T063) - 10 tasks
**External API Clients** (4 tasks, can run in parallel):
- arXiv, Papers With Code, Semantic Scholar, GitHub

**Background Jobs** (4 tasks):
- Daily paper discovery
- Metric updates
- Topic matching with LLM
- APScheduler configuration (2 AM UTC cron)

**Database Seeding** (2 tasks):
- Predefined topics
- Sample papers for testing

### Phase 3.6: Polish (T064-T080) - 17 tasks
**Styling** (4 tasks):
- TailwindCSS mobile-first
- Responsive layouts (375px, 768px, 1024px)
- Loading states
- Error boundaries

**Performance** (4 tasks):
- API caching (1-hour hype scores)
- Code splitting
- Database query optimization
- Performance testing (<2s page load)

**Testing** (3 tasks):
- Unit tests (hype score formula, topic matching accuracy)
- Full integration suite
- Mobile responsiveness validation

**Documentation** (6 tasks):
- Backend README
- Frontend README
- Hype score algorithm documentation
- Deployment guide
- Quickstart execution script

---

## 🏗️ Project Architecture

### Technology Stack
**Backend**:
- Python 3.11+ with FastAPI
- PostgreSQL 15 + TimescaleDB 2.11
- SQLAlchemy 2.0 (async)
- llama.cpp for local LLM inference

**Frontend**:
- React 18 with TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- Recharts (trend visualization)

**Data**:
- 5 entities: Paper, Topic, MetricSnapshot, PaperTopicMatch, HypeScore
- Time-series optimized with TimescaleDB hypertables
- 30-day metric retention (MVP)

### Key Features
1. **Topic Matching**: Local LLM (zero-cost) scores paper-topic relevance
2. **Hype Score**: Weighted formula (40% star growth + 30% citation growth + 20% absolute + 10% recency)
3. **Real-Time Updates**: Daily monitoring of arXiv + conference papers
4. **User Persistence**: localStorage (no accounts for MVP)
5. **Mobile-First**: Responsive design <2s page load

---

## 📂 Project Structure

```
HypePaper/
├── backend/
│   ├── src/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic
│   │   ├── api/routes/      # FastAPI endpoints
│   │   ├── jobs/            # Background tasks + external APIs
│   │   └── llm/             # LLM integration
│   ├── tests/
│   │   ├── contract/        # API contract tests
│   │   ├── integration/     # End-to-end scenarios
│   │   └── unit/            # Unit tests
│   ├── alembic/             # Database migrations
│   ├── scripts/             # Utility scripts
│   ├── requirements.txt     ✅
│   ├── pyproject.toml       ✅
│   └── alembic.ini          ✅
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API client
│   │   └── utils/           # Helpers
│   ├── tests/
│   │   ├── components/      # Component tests
│   │   └── integration/     # E2E tests
│   ├── package.json         ✅
│   └── .eslintrc.cjs        ✅
├── shared/schemas/          # Shared types
├── docs/                    # Documentation
├── specs/001-build-a-website/
│   ├── spec.md              # Feature specification
│   ├── research.md          # Technology decisions
│   ├── plan.md              # Implementation plan
│   ├── data-model.md        # Database design
│   ├── quickstart.md        # Integration tests
│   ├── tasks.md             # This task list
│   └── contracts/           # OpenAPI specs
├── docker-compose.yml       ✅
└── .specify/                # Project templates & scripts
```

---

## 🚀 Quick Start for Developers

### 1. Install Dependencies

**Backend**:
```bash
cd backend
pip install -r requirements.txt
```

**Frontend**:
```bash
cd frontend
npm install
```

### 2. Start Database
```bash
docker-compose up -d
```

### 3. Run Migrations
```bash
cd backend
alembic upgrade head
```

### 4. Download LLM Model (optional)
```bash
cd backend
python scripts/download_llm_model.py
```

### 5. Start Development Servers

**Backend**:
```bash
cd backend
uvicorn src.api.main:app --reload --port 8000
```

**Frontend**:
```bash
cd frontend
npm run dev
```

---

## 📖 Key Documentation

- **Constitution**: [.specify/memory/constitution.md](.specify/memory/constitution.md) - v1.0.0
- **Feature Spec**: [specs/001-build-a-website/spec.md](specs/001-build-a-website/spec.md)
- **Research Decisions**: [specs/001-build-a-website/research.md](specs/001-build-a-website/research.md)
- **Data Model**: [specs/001-build-a-website/data-model.md](specs/001-build-a-website/data-model.md)
- **API Contracts**: [specs/001-build-a-website/contracts/](specs/001-build-a-website/contracts/)
- **Integration Tests**: [specs/001-build-a-website/quickstart.md](specs/001-build-a-website/quickstart.md)
- **Task List**: [specs/001-build-a-website/tasks.md](specs/001-build-a-website/tasks.md)

---

## 🎯 MVP Success Criteria

From the constitution and feature spec:

1. **Performance**: Page load < 2 seconds
2. **Scale**: 1,000 papers per topic, 100 concurrent users
3. **Updates**: Daily metric monitoring within 4 hours
4. **Accuracy**: Topic matching relevance score >= 6.0
5. **Retention**: 30-day metric history
6. **Mobile**: Responsive at 375px, 768px, 1024px
7. **Transparency**: Hype score algorithm documented and auditable

---

## 💡 Next Steps

### Immediate (You can do this now):
1. **Install dependencies**: Run `pip install -r backend/requirements.txt` and `npm install` in frontend
2. **Start database**: Run `docker-compose up -d`
3. **Review planning docs**: Read through spec.md, research.md, plan.md to understand the system

### Phase 3.2 (Next development phase):
1. **Write failing tests** (T012-T025): Start with contract tests for API endpoints
2. **Verify tests fail**: Run `pytest` in backend and `npm test` in frontend
3. **Document test scenarios**: Use quickstart.md as reference

### Phase 3.3 (After tests):
1. **Implement database models** (T026-T029): Can be done in parallel
2. **Run migration**: `alembic upgrade head`
3. **Implement services**: Sequential (depends on models)
4. **Create API endpoints**: Make the tests pass!

---

## 📝 Git Commits

- ✅ `595f8a2` - Complete planning (constitution, spec, research, data model, contracts, tasks)
- ✅ `df826c2` - Phase 3.1 setup complete (project structure, dependencies, configurations)

**Branch**: `001-build-a-website` (ready to push to remote)

---

## 🤖 Development Notes

- **TDD Enforced**: Phase 3.2 tests must exist and fail before Phase 3.3 implementation
- **Parallel Tasks**: 25 tasks marked [P] can run concurrently
- **Constitution Compliance**: All 5 principles validated in planning phase
- **Estimated Effort**: 40-50 hours for full MVP implementation

**Status**: Foundation complete, ready for test-driven development.
