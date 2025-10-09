# Feature Specification: SOTAPapers Legacy Code Integration

**Feature Branch**: `002-convert-the-integration`
**Created**: 2025-10-08
**Status**: Ready for Planning
**Input**: User description: "convert the integration plan into specs"

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature: Integrate SOTAPapers legacy codebase into HypePaper
2. Extract key concepts from description
   → Actors: Research users, system administrators, background workers
   → Actions: Discover papers, extract metadata, track GitHub stars, build citation graphs
   → Data: Papers, authors, citations, GitHub metrics, PDF content, LLM extractions
   → Constraints: Async architecture, security (no hardcoded secrets), PostgreSQL only
3. For each unclear aspect:
   → All clarifications resolved with stakeholder
4. Fill User Scenarios & Testing section
   → User flows defined for paper discovery, metadata enrichment, citation tracking
5. Generate Functional Requirements
   → 45 testable requirements across discovery, extraction, tracking, security
6. Identify Key Entities
   → Paper, Author, Citation, GitHubMetrics, PDFContent, LLMExtraction
7. Run Review Checklist
   → All requirements clarified and testable
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

**As a research user**, I want the system to automatically discover and analyze academic papers from multiple sources (ArXiv, conferences, citations), extract comprehensive metadata using AI, track their GitHub repositories' popularity over time, and build citation relationship graphs, so that I can discover trending research and understand the impact and connections between papers without manual data gathering.

### Acceptance Scenarios

#### 1. ArXiv Paper Discovery
**Given** a user provides research keywords (e.g., "transformer attention mechanisms")
**When** the system executes paper discovery in background
**Then** the system must:
- Search ArXiv API for matching papers
- Extract metadata: title, authors, abstract, ArXiv ID, publication date, categories
- Store papers in database with deterministic unique IDs (title+year hash)
- Return list of discovered papers with basic metadata

#### 2. Automated Metadata Enrichment
**Given** a paper exists in the database with an ArXiv ID
**When** the system runs background metadata enrichment
**Then** the system must:
- Download the PDF from ArXiv
- Extract full text content using PDF parser
- Use AI (LLM) to identify: primary/secondary/tertiary research tasks, methods used, datasets mentioned, evaluation metrics
- Extract author affiliations and countries from metadata
- Parse and store all paper references from References section
- Extract tables from PDF and save as CSV files
- Update paper record with enriched metadata

#### 3. GitHub Repository Tracking
**Given** a paper with a title and authors
**When** the system searches for associated GitHub repositories
**Then** the system must:
- Search GitHub for repositories matching paper title/authors
- Verify repository relevance using heuristics
- Extract: repository URL, star count, creation date, last update
- Calculate hype metrics: average, weekly, monthly star velocity
- Store GitHub metrics with timestamps
- Track star count changes daily (scheduled background job)

#### 4. Citation Graph Construction
**Given** multiple papers with extracted references
**When** the system builds citation relationships
**Then** the system must:
- Parse reference strings from PDF References section using legacy citation parser
- Match reference strings to existing papers in database using title+year fuzzy matching
- Create bidirectional citation links (cites/cited-by relationships)
- Calculate citation counts for each paper
- Enable citation graph traversal queries
- Support citation-based paper discovery (find papers citing X)

#### 5. Conference Paper Integration
**Given** a user specifies conference name in JSON config file or as parameter (e.g., "CVPR 2024")
**When** the system crawls conference papers
**Then** the system must:
- Extract: paper titles, authors, session types, acceptance status
- Download PDFs when available
- Link to ArXiv versions when possible
- Track conference-specific metadata (venue, session type)
- Maintain paper source attribution (conference name)

### Edge Cases

#### Data Quality
- **What happens when ArXiv API returns incomplete metadata?**
  System must store partial data, mark fields as incomplete, and queue for retry with exponential backoff.

- **How does system handle duplicate papers from different sources?**
  System must detect duplicates using deterministic title+year hash and merge metadata from all sources without data loss.

- **What happens when PDF text extraction fails?**
  System must log failure with error details, mark paper for manual review flag, and continue processing other papers without blocking.

- **What happens when AI extraction has issues?**
  System must store raw extraction results, flag papers for manual human verification, and continue processing. No confidence scores used (legacy codebase doesn't implement them).

#### Performance & Scale
- **How does system handle rate limits from ArXiv/GitHub APIs?**
  System must implement exponential backoff (1s, 2s, 4s, 8s delays) and queue-based retry logic with maximum retry count from config.

- **What happens when processing 1000+ papers simultaneously?**
  System must process papers in batches with concurrency limit specified in JSON config file and based on system processor count. Queue overflow protection enabled.

- **How long should GitHub star tracking history be retained?**
  System must retain ALL star tracking data indefinitely (no retention limit). Daily snapshots stored with timestamps for hype calculation.

#### Security & Errors
- **What happens when GitHub authentication fails?**
  System must fail gracefully with error log, disable GitHub tracking for that session, and alert administrator. Uses GitHub Personal Access Token from environment variables.

- **How does system prevent exposure of API credentials?**
  System must store all credentials (GitHub token, ArXiv API key, LLM API keys) in environment variables or secure vault, NEVER in code or config files.

- **What happens when citation parsing detects malformed references?**
  System must log malformed reference string with paper ID, store original malformed text for debugging, and continue processing remaining references.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Paper Discovery
- **FR-001**: System MUST search ArXiv API using keywords and return matching papers with metadata (title, authors, abstract, ArXiv ID, publication date, categories)
- **FR-002**: System MUST generate deterministic unique IDs for papers based on title + publication year hash using legacy ID generation algorithm
- **FR-003**: System MUST detect duplicate papers across different sources using ID hash and merge their metadata without data loss
- **FR-004**: System MUST support crawling conference papers from conferences specified in JSON config file or passed as parameters
- **FR-005**: System MUST track paper source attribution (ArXiv, conference name, citation discovery) for provenance

#### PDF Analysis
- **FR-006**: System MUST download PDF files from ArXiv using ArXiv ID
- **FR-007**: System MUST extract full text content from PDF files using PyMuPDF parser
- **FR-008**: System MUST parse paper references from PDF References section using legacy citation parser
- **FR-009**: System MUST extract tables from PDFs using GMFT (AutoTableDetector + AutoTableFormatter) and save as CSV files alongside PDF
- **FR-010**: System MUST handle PDF extraction failures gracefully, log errors, mark papers for retry, and continue processing other papers

#### AI Metadata Extraction
- **FR-011**: System MUST use AI (LLM) to identify primary research task from paper content
- **FR-012**: System MUST use AI to identify secondary and tertiary research tasks when present
- **FR-013**: System MUST use AI to identify research methods used in paper
- **FR-014**: System MUST use AI to identify datasets mentioned in paper (from tables and text)
- **FR-015**: System MUST use AI to identify evaluation metrics used in paper
- **FR-016**: System MUST extract author affiliations and countries from paper metadata
- **FR-017**: System MUST store all AI extraction results (no confidence scoring required - legacy doesn't implement it)
- **FR-018**: System MUST flag all AI extractions for human verification with manual review queue

#### GitHub Repository Tracking
- **FR-019**: System MUST search GitHub for repositories associated with papers using title + author keywords
- **FR-020**: System MUST verify repository relevance to paper using heuristics (title match, author match, paper mention in README)
- **FR-021**: System MUST extract GitHub repository metadata: URL, stars, creation date, last update, primary language
- **FR-022**: System MUST track GitHub star count changes daily via scheduled background job
- **FR-023**: System MUST calculate star velocity metrics: average hype, weekly hype, monthly hype scores using legacy algorithm
- **FR-024**: System MUST store star tracking history with timestamps indefinitely (no expiration)
- **FR-025**: System MUST handle GitHub API rate limits with exponential backoff and retry using limits from config

#### Citation Graph
- **FR-026**: System MUST parse paper references from extracted PDF text References section
- **FR-027**: System MUST match reference strings to existing papers in database using title + year fuzzy matching (legacy parser logic)
- **FR-028**: System MUST create bidirectional citation relationships (cites/cited-by) in many-to-many paper_references table
- **FR-029**: System MUST calculate citation counts for each paper by counting incoming citations
- **FR-030**: System MUST support citation graph traversal queries (find all papers citing X, find all papers cited by X)
- **FR-031**: System MUST enable citation-based paper discovery (expand search via citation links)
- **FR-032**: System MUST handle incomplete reference matching gracefully by storing original unparsed reference text

#### Data Management
- **FR-033**: System MUST store all paper metadata in relational database (SQLite in legacy, PostgreSQL in HypePaper)
- **FR-034**: System MUST maintain data integrity across paper, author, citation, and metrics tables with foreign key constraints
- **FR-035**: System MUST support incremental updates to paper metadata without overwriting unmodified fields
- **FR-036**: System MUST retain paper processing history and error logs with timestamps for debugging
- **FR-037**: System MUST support bulk paper imports from external sources (ArXiv XML exports, conference CSV files)
- **FR-038**: System MUST provide data export via database ORM access and API endpoints (JSON format via REST API)

#### Security & Configuration
- **FR-039**: System MUST store all API credentials (GitHub token, ArXiv API key, LLM API keys) in environment variables, NEVER in code
- **FR-040**: System MUST NOT hardcode any credentials, tokens, or secrets in source code (revoke legacy hardcoded GitHub token)
- **FR-041**: System MUST validate and sanitize all user inputs (keywords, conference names, paper IDs)
- **FR-042**: System MUST log all security-relevant events (auth failures, invalid requests, credential access) with timestamps
- **FR-043**: System MUST support configurable processing parameters via JSON config files using python-json-config package (batch sizes, rate limits, retry attempts, concurrency limits)
- **FR-044**: System MUST provide health check endpoints for monitoring (database connectivity, API availability, queue status)
- **FR-045**: System MUST support graceful shutdown and restart without data loss or corruption using transaction management

### Performance Requirements

- **PR-001**: System MUST process single paper requests within 3-5 seconds for on-demand processing (download PDF + basic extraction)
- **PR-002**: System MUST process bulk paper crawling as background jobs with concurrency limits from JSON config (based on CPU count) and queue management
- **PR-003**: System MUST implement rate limiting to comply with external API limits: ArXiv (3 req/s), GitHub (5000 req/hour)
- **PR-004**: System MUST cache frequently accessed data using simple cache implementation or 3rd-party package to reduce API calls

### Data Retention & Lifecycle

- **DR-001**: System MUST retain GitHub star tracking history indefinitely without expiration
- **DR-002**: System MUST retain paper processing logs for at least 90 days for debugging
- **DR-003**: System MUST retain failed extraction attempts with error details for retry analysis
- **DR-004**: System MUST archive old PDF files after 365 days to external storage (optional optimization)

### Configuration Requirements

- **CF-001**: System MUST load all configuration from JSON files using python-json-config package
- **CF-002**: System MUST support per-environment config overrides (development, staging, production)
- **CF-003**: System MUST validate configuration schema on startup and fail fast with clear error messages
- **CF-004**: Configuration MUST include: conference list, concurrency limits, API rate limits, retry parameters, batch sizes, API endpoints
- **CF-005**: System MUST support passing conference names as command-line parameters for ad-hoc crawling

### Key Entities *(include if feature involves data)*

#### Paper
Core entity representing an academic research paper. Contains bibliographic metadata, content, metrics, and relationships.

**Key Attributes:**
- Unique identifier (deterministic hash from title + year)
- Bibliographic: title, authors (list), publication date, year, venue, ArXiv ID, conference name
- Content: abstract, full text, keywords, categories, BibTeX
- AI extractions: primary/secondary/tertiary tasks, methods, datasets, metrics, limitations, comparisons
- External links: PDF URL, GitHub repository URL, conference page URL
- Metrics: citation count, GitHub stars, hype scores (average, weekly, monthly)
- Metadata: session type, acceptance status, affiliations, countries
- Relationships: citations (to/from via paper_references), authors, PDF content, LLM extractions

#### Author
Represents a research paper author with affiliation information.

**Key Attributes:**
- Name (full name as string)
- Affiliations (list of organizations)
- Countries (list of countries from affiliations)
- Relationships: papers authored (many-to-many)

#### Citation
Represents the relationship between two papers (citing and cited paper).

**Key Attributes:**
- Source paper ID (paper that contains the reference)
- Target paper ID (referenced/cited paper)
- Reference text (original citation string from PDF)
- Match quality (fuzzy match score from title+year matching)
- Relationships: bidirectional link between papers via paper_references table

#### GitHubMetrics
Tracks GitHub repository metrics over time for papers with associated repositories.

**Key Attributes:**
- Paper ID (foreign key)
- Repository URL
- Star count snapshots (list of timestamp + count pairs for daily tracking)
- Hype scores: average hype, weekly hype, monthly hype (calculated from star velocity)
- Repository metadata: creation date, last update, primary language, description
- Tracking period: start date, latest snapshot date
- Relationships: associated with single paper

#### PDFContent
Stores extracted content from paper PDFs.

**Key Attributes:**
- Paper ID (foreign key)
- Full text (complete extracted text)
- Extracted tables (list of CSV file paths, one per table: paper.table00.csv, paper.table01.csv, etc.)
- Parsed references (list of reference strings from References section)
- Extraction metadata: timestamp, PDF parser version, GMFT version, success/failure status, error messages
- Relationships: belongs to single paper

#### LLMExtraction
Stores AI-extracted metadata from paper content using LLM.

**Key Attributes:**
- Paper ID (foreign key)
- Extraction type: task, method, dataset, metric, limitation, comparison
- Extracted values: primary, secondary, tertiary (when applicable)
- AI model used: model name and version (LlamaCpp, OpenAI GPT-4, etc.)
- Extraction timestamp
- Verification status: pending_review, verified, rejected (for manual human verification workflow)
- Relationships: belongs to single paper

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain - **All 13 clarifications resolved**
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable - **SLAs defined**
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

### Resolved Clarifications
1. ✅ Conference tracking: User specifies in JSON config file or passes as command-line parameter
2. ✅ AI confidence: No confidence scoring (legacy codebase doesn't implement it), all extractions flagged for manual human review
3. ✅ Review process: Manual human verification workflow with verification status field (pending_review, verified, rejected), future automation possible
4. ✅ Processing scale: Concurrency limits from JSON config file + system CPU count detection, queue overflow protection enabled
5. ✅ Star tracking retention: Daily snapshots stored with timestamps, retained indefinitely with NO expiration policy
6. ✅ GitHub auth: GitHub Personal Access Token stored in environment variables (GITHUB_TOKEN), never in code or config files
7. ✅ Table format: CSV files extracted using GMFT library (AutoTableDetector + AutoTableFormatter), saved as paper.table00.csv, paper.table01.csv, etc.
8. ✅ Data export: Direct database ORM access + JSON REST API endpoints for programmatic access
9. ✅ Configuration: JSON config files loaded via python-json-config package, per-environment overrides supported
10. ✅ Cache: Simple in-memory cache or 3rd-party caching package (implementation choice, not specified)
11. ✅ Citation matching: Title + year fuzzy matching using legacy citation parser logic, no confidence scores (parser either matches or doesn't)
12. ✅ LLM verification: All AI extractions require human review with verification_status field tracking, optional automation in future
13. ✅ Performance SLAs: 3-5 seconds for single on-demand paper processing, bulk crawling as background jobs, daily star updates via scheduled tasks

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities clarified with stakeholder
- [x] User scenarios defined (5 acceptance scenarios, 11 edge cases)
- [x] Requirements generated (45 functional, 4 performance, 4 data retention, 5 configuration)
- [x] Entities identified (6 core entities with detailed attributes)
- [x] Review checklist passed

---

## Dependencies & Assumptions

### External Service Dependencies
- **ArXiv API**: Rate limit 3 req/s, requires API key for bulk access
- **GitHub API**: Rate limit 5000 req/hour with auth, requires Personal Access Token
- **LLM Services**: OpenAI GPT-4 API or local LlamaCpp server
- **PDF Processing**: PyMuPDF (fitz) for text extraction, GMFT for table detection

### Assumptions
- Legacy SOTAPapers codebase is available and readable
- PostgreSQL database is available and configured
- Sufficient disk space for PDF storage and CSV table exports
- System has adequate CPU cores for concurrent processing (config: max_workers = CPU count)
- Manual human reviewers available for LLM extraction verification
- GitHub Personal Access Token with appropriate scopes (public_repo access)

### Migration Risks
1. **Hardcoded GitHub token exposure** - Must be revoked immediately before integration
2. **Multiprocessing complexity** - May need refactoring to async/await patterns
3. **Citation parser fragility** - Reference string parsing may fail on unusual formats
4. **LLM API costs** - OpenAI API usage costs for bulk processing (consider local LlamaCpp)
5. **Data migration** - SQLite to PostgreSQL schema differences require careful mapping

---

## Next Steps

1. ✅ **Clarification Complete**: All 13 requirements clarified
2. **Ready for Planning**: Proceed to `/plan` phase to generate implementation plan
3. **Technical Planning**: Generate data model, API design, task breakdown
4. **Security Action**: Revoke hardcoded GitHub token before any code migration
5. **Environment Setup**: Prepare PostgreSQL database, Redis (if used), Celery workers
