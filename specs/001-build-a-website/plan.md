
# Implementation Plan: Trending Research Papers Tracker

**Branch**: `001-build-a-website` | **Date**: 2025-10-01 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-build-a-website/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Build a web application to track trending research papers using novel metrics (GitHub stars + citations). Users can watch specific research topics and see papers ranked by "hype score" calculated from daily metric changes. System monitors arXiv and conference papers, stores time-series metrics, and uses local LLM for topic-to-paper matching. MVP focuses on simple, fast trending paper discovery grouped by user interests.

## Technical Context
**Language/Version**: Python 3.11+ (backend), JavaScript/TypeScript (frontend)
**Primary Dependencies**: FastAPI (backend API), llama.cpp (local LLM for topic matching), PostgreSQL/TimescaleDB (time-series metrics)
**Storage**: PostgreSQL with TimescaleDB extension for time-series paper metrics, regular tables for papers/topics
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Linux server for backend + LLM, modern browsers for frontend
**Project Type**: web (frontend + backend separated)
**Performance Goals**: <2s page load (constitution), daily metric updates, <500ms API response for paper lists
**Constraints**: Zero-cost LLM (local only), mobile-responsive UI, topic matching must be accurate
**Scale/Scope**: MVP targets ~1000 papers per topic, 100 concurrent users, 30-day metric retention minimum

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Simple, Small, Fast ✅
- **MVP scope**: Single feature - trending papers by topic (no AI chat, notes, collaboration)
- **Fast load**: <2s target specified in technical context
- **Simple UI**: Show papers, scores, trends only

### Principle II: Novel Metrics Drive Value ✅
- **GitHub stars**: Primary hype indicator implemented
- **Citations**: Combined with stars for scoring
- **Transparent algorithm**: Hype score calculation based on rate of change
- **Recency/growth**: Time-series data enables trend detection

### Principle III: User Interest First ✅
- **User-defined topics**: Core requirement (FR-001, UI-001, UI-002)
- **Topic grouping**: Papers displayed by user's watched topics (FR-007)
- **User control**: Add/remove topics, filter by topic

### Principle IV: Real-Time, Not Stale ✅
- **Daily updates**: Metrics tracked daily (FR-003, FR-004, FR-009)
- **Time-based trends**: Show rising/stable papers (FR-010)
- **Fast surfacing**: New papers appear within 24-48 hours (acceptance scenario 4)

### Principle V: Reproducible Scoring ✅
- **Documented algorithm**: Hype score calculation transparent
- **Auditable components**: Show stars, citations, recency breakdown
- **Time-series storage**: Daily snapshots enable score verification

### Development Constraints ✅
- **Fast development**: Python/FastAPI, proven tech stack
- **Boring tech**: PostgreSQL, standard REST API
- **Minimal dependencies**: Core libs only (FastAPI, llama.cpp, TimescaleDB)

### Scope Boundaries ✅
- **IN SCOPE**: Trending papers, user topics, hype scores, filtering (all present)
- **OUT OF SCOPE**: No AI chat, notes, collaboration, recommendations (correctly excluded)

**GATE RESULT**: ✅ PASS - No constitutional violations detected

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/          # Paper, Topic, MetricSnapshot, HypeScore entities
│   ├── services/        # PaperService, MetricService, TopicMatchingService
│   ├── api/             # FastAPI routes (papers, topics, metrics)
│   ├── jobs/            # Daily metric update jobs, arXiv scraper
│   └── llm/             # llama.cpp integration for topic matching
├── tests/
│   ├── contract/        # API contract tests
│   ├── integration/     # End-to-end service tests
│   └── unit/            # Model and utility tests
└── requirements.txt

frontend/
├── src/
│   ├── components/      # PaperCard, TopicList, TrendChart, TopicManager
│   ├── pages/           # HomePage (trending papers by topic)
│   ├── services/        # API client for backend
│   └── utils/           # Hype score formatting, date utilities
├── tests/
│   ├── components/      # Component tests
│   └── integration/     # E2E tests
└── package.json

shared/
└── schemas/             # Shared TypeScript/Python types for API contracts
```

**Structure Decision**: Web application structure selected (Option 2 adapted). Backend and frontend are fully separated for independent deployment. Backend handles all data processing, LLM operations, and daily jobs. Frontend is a thin client focused on fast rendering of paper lists and trends. Shared schemas ensure type safety across the boundary.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract endpoint → contract test task [P]
- Each entity (Paper, Topic, MetricSnapshot, PaperTopicMatch) → model task [P]
- Each service (PaperService, MetricService, TopicMatchingService) → implementation task
- Each quickstart scenario → integration test task
- Frontend components (PaperCard, TopicList, TrendChart) → component tasks [P]

**Ordering Strategy**:
- **Phase 3.1**: Setup (project init, dependencies, DB setup, LLM model download)
- **Phase 3.2**: Tests First (TDD - MUST FAIL before implementation)
  - Backend contract tests for 2 API endpoints [P]
  - Frontend component tests [P]
  - Integration tests for 5 quickstart scenarios
- **Phase 3.3**: Core Implementation (backend models, services, API routes)
  - Database models [P] → Services → API routes
  - LLM integration for topic matching
  - Hype score calculation service
- **Phase 3.4**: Frontend Implementation
  - API client service
  - React components [P]
  - Pages and routing
- **Phase 3.5**: Integration & Jobs
  - Daily update job (arXiv scraper, metric updates)
  - Background worker setup
  - API integrations (arXiv, Papers With Code, Semantic Scholar, GitHub)
- **Phase 3.6**: Polish
  - Mobile responsive styling
  - Performance optimization (<2s page load)
  - Error handling and logging
  - Documentation

**Dependency Graph**:
```
Setup → Tests → Models → Services → API Routes → Frontend → Jobs → Polish
         ↓        ↓        ↓          ↓           ↓          ↓       ↓
      [Must fail] [P]     [P]      [Sequential] [P]      [Cron]  [Final]
```

**Estimated Output**: 40-50 numbered, ordered tasks in tasks.md

**Key Parallelization Opportunities**:
- 4 database models can be created in parallel (different files)
- 2 API contract tests in parallel (different endpoints)
- 5+ frontend components in parallel (independent)
- Contract tests + component tests in parallel (backend vs frontend)

**Critical Path**:
1. Database setup → Models → MetricSnapshot (blocks Services)
2. PaperService + TopicMatchingService → API routes
3. API routes → Frontend API client
4. All core features → Daily job (depends on full stack)

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
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - ✅ research.md generated
- [x] Phase 1: Design complete (/plan command) - ✅ data-model.md, contracts/, quickstart.md, CLAUDE.md generated
- [x] Phase 2: Task planning complete (/plan command - describe approach only) - ✅ Detailed strategy documented
- [ ] Phase 3: Tasks generated (/tasks command) - Ready to execute
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (no violations detected)
- [x] Post-Design Constitution Check: PASS (design aligns with all 5 principles)
- [x] All NEEDS CLARIFICATION resolved (via user input + research decisions)
- [x] Complexity deviations documented (none - MVP scope well-bounded)

**Artifacts Generated**:
- ✅ `/specs/001-build-a-website/plan.md` (this file)
- ✅ `/specs/001-build-a-website/research.md` (10 research decisions)
- ✅ `/specs/001-build-a-website/data-model.md` (5 entities, SQL schema)
- ✅ `/specs/001-build-a-website/contracts/api-topics.yaml` (Topics API contract)
- ✅ `/specs/001-build-a-website/contracts/api-papers.yaml` (Papers API contract)
- ✅ `/specs/001-build-a-website/quickstart.md` (5 scenarios + 5 edge cases)
- ✅ `/CLAUDE.md` (agent context file updated)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
