# Feature Specification: Trending Research Papers Tracker

**Feature Branch**: `001-build-a-website`
**Created**: 2025-10-01
**Status**: Clarified & Planned
**Input**: User description: "Build a website to keep track the trending research papers. users can add specific research area or topics to watch. and for each watching topic, monitor the research papers in that topic everyday to keep track the number of github stars and citation numbers. this is to score each paper a hype, not just scoring by current number of stars or citations. we need a database to keep track the metrics of papers in a daily basis to make it possible for hype(trending score) calculation. The monitoring papers will use arxiv papers and other public papers in venus like CVPR, SIGGRAPH, etc. and there should be a database to keep track the score for each paper in time series."

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-01
All ambiguities resolved during planning phase (see research.md for detailed rationale):
- Q: Topic-to-paper matching mechanism? → A: Local LLM (llama.cpp) for semantic matching with relevance scoring 0-10, threshold >= 6.0 for inclusion
- Q: Scale targets (papers per topic, concurrent users)? → A: 1,000 papers per topic maximum, 100 concurrent users (MVP)
- Q: Daily monitoring time window? → A: 4 hours maximum (triggered at 2 AM UTC)
- Q: Data retention period for metric snapshots? → A: 30 days minimum (MVP), expandable to 1 year post-MVP
- Q: Sorting criteria options for users? → A: Hype score (default), recency, absolute stars
- Q: User account requirement? → A: Optional accounts with localStorage fallback (MVP uses localStorage, no auth required)
- Q: Hype score calculation formula? → A: Weighted: 40% star growth (7d) + 30% citation growth (30d) + 20% absolute stars normalized + 10% recency bonus

## User Scenarios & Testing *(mandatory)*

### Primary User Story
A researcher wants to stay current with trending papers in their specific research areas (e.g., computer vision, machine learning) without spending hours googling. They visit HypePaper, add their topics of interest (e.g., "diffusion models", "multimodal learning"), and immediately see a ranked list of papers that are gaining traction based on both academic impact (citations) and practical adoption (GitHub stars). The system tracks these metrics daily, so the researcher can see which papers are rising in popularity this week versus stable over months.

### Acceptance Scenarios
1. **Given** a user visits HypePaper for the first time, **When** they add a research topic like "neural rendering", **Then** they see a list of trending papers in that topic ranked by hype score
2. **Given** a user has added multiple topics to watch, **When** they return to the site, **Then** they see papers grouped by their watched topics with current hype scores
3. **Given** the system has been tracking a paper for 30 days, **When** a user views that paper's details, **Then** they see a trend graph showing how GitHub stars and citations have changed over time
4. **Given** a new paper is published on arXiv with associated GitHub repository, **When** the daily monitoring runs, **Then** the paper appears in relevant topic lists within 24-48 hours
5. **Given** a paper's GitHub stars increase rapidly over 7 days, **When** the hype score is calculated, **Then** the paper rises in ranking to reflect trending status

### Edge Cases
- What happens when a paper has no GitHub repository (only citations)?
- What happens when a paper has GitHub stars but zero citations yet?
- How does system handle papers published at major conferences (CVPR, SIGGRAPH) that aren't on arXiv?
- What happens when a user adds a very broad topic (e.g., "AI") versus narrow topic (e.g., "NeRF compression")?
- How does system handle duplicate papers (same paper on arXiv and conference venue)?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST allow users to add research topics/areas they want to watch
- **FR-002**: System MUST monitor papers from arXiv and major conference venues (CVPR, SIGGRAPH, etc.)
- **FR-003**: System MUST track GitHub stars for each paper daily
- **FR-004**: System MUST track citation counts for each paper daily
- **FR-005**: System MUST store daily metrics (stars, citations) in time series for trend calculation
- **FR-006**: System MUST calculate a "hype score" based on rate of change of metrics, not just absolute numbers
- **FR-007**: System MUST display papers grouped by user's watched topics
- **FR-008**: System MUST rank papers within each topic by hype score (trending score)
- **FR-009**: System MUST update paper metrics at least once per day
- **FR-010**: System MUST display trend information (rising this week, stable, etc.) for each paper
- **FR-011**: Users MUST be able to see which papers are newly added (published within last 48 hours)
- **FR-012**: System MUST match papers to topics using local LLM semantic matching (relevance score 0-10, include if >= 6.0)
- **FR-013**: System MUST identify which papers have associated GitHub repositories
- **FR-014**: System MUST display paper metadata (title, authors, publication venue, publication date)
- **FR-015**: System MUST provide links to paper source (arXiv, conference, GitHub repo)

### Performance & Scale Requirements
- **PR-001**: Page load time MUST be under 2 seconds (per constitution principle I)
- **PR-002**: System MUST handle at least 1,000 papers per topic (MVP target)
- **PR-003**: System MUST support at least 100 concurrent users (MVP target)
- **PR-004**: Daily monitoring MUST complete within 4 hours maximum (triggered at 2 AM UTC)

### Data Requirements
- **DR-001**: System MUST retain daily metric snapshots for at least 30 days (MVP minimum, expandable to 1 year post-MVP)
- **DR-002**: System MUST handle papers that have GitHub repos and those that don't
- **DR-003**: System MUST handle papers that have citations and those that don't (new papers)
- **DR-004**: System MUST prevent duplicate entries for the same paper from different sources
- **DR-005**: System MUST calculate hype score using weighted formula: 40% star growth (7d) + 30% citation growth (30d) + 20% absolute stars (normalized) + 10% recency bonus

### User Interaction Requirements
- **UI-001**: Users MUST be able to add topics to their watch list
- **UI-002**: Users MUST be able to remove topics from their watch list
- **UI-003**: Users MUST be able to view papers filtered by specific topic
- **UI-004**: Users MUST be able to sort papers by hype score (default), recency, or absolute stars
- **UI-005**: Users MUST be able to see historical trend data for a paper
- **UI-006**: Interface MUST be mobile-responsive (per constitution quality gate)
- **UI-007**: System MUST persist user's watched topics in browser localStorage (no user accounts required for MVP)

### Key Entities *(include if feature involves data)*
- **Paper**: Represents a research paper with title, authors, abstract, publication date, venue (arXiv, CVPR, etc.), links to source and GitHub repository (if exists)
- **Topic**: Represents a research area or domain (e.g., "diffusion models", "neural rendering") that users can watch
- **Metric Snapshot**: Daily capture of a paper's GitHub stars and citation count, timestamped for trend analysis
- **Hype Score**: Calculated score based on rate of change of metrics over time (not just current absolute values)
- **Watch List**: Collection of topics a user is monitoring (relationship between user and topics)

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed
- [x] All clarifications resolved (Session 2025-10-01)
- [x] Planning phase completed (research.md, data-model.md, contracts/, quickstart.md)

---

## Notes

**Implementation Decisions (from research.md)**:
- Topic matching: Local LLM (llama.cpp) with semantic scoring
- Database: PostgreSQL with TimescaleDB for time-series optimization
- Paper sources: arXiv API + Papers With Code + Semantic Scholar
- Frontend: React with Vite for fast builds
- User persistence: localStorage (MVP), optional accounts (future)
- Scale: 1,000 papers/topic, 100 concurrent users, 30-day retention (MVP)

**Alignment with Constitution:**
- Supports Principle I (Simple, Small, Fast): MVP focused on one feature - trending papers by topic
- Supports Principle II (Novel Metrics): GitHub stars as unique differentiator combined with citations
- Supports Principle III (User Interest First): Users define topics they want to watch
- Supports Principle IV (Real-Time, Not Stale): Daily updates with time-series tracking
- Supports Principle V (Reproducible Scoring): Requirement for transparent hype score calculation
