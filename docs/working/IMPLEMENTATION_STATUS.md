# HypePaper Enhancement Implementation Status

## ✅ Completed Tasks

### 1. Database-Backed Crawler Job Tracking
- **Status**: COMPLETE
- **Files Created**:
  - `backend/src/models/crawler_job.py` - CrawlerJob model
  - `backend/create_crawler_jobs_table.sql` - SQL migration
- **Database Changes**:
  - `crawler_jobs` table created in Supabase with JSONB logs
  - Jobs now persist across server restarts
- **Files Modified**:
  - `backend/src/jobs/reference_crawler.py` - Completely rewritten to use database tracking
  - `backend/src/models/__init__.py` - Added CrawlerJob import

### 2. URL Extraction Service
- **Status**: COMPLETE
- **Files Created**:
  - `backend/src/services/url_extractor.py` - Extracts and classifies URLs from abstracts
- **Capabilities**:
  - Detects GitHub repository URLs
  - Detects project website URLs (github.io, academic sites, etc.)
  - Detects YouTube video URLs
  - Normalizes URLs to standard formats
  - Distinguishes between GitHub repos and GitHub Pages

### 3. GitHub Repository Search
- **Status**: COMPLETE
- **Files Created**:
  - `backend/src/services/github_search.py` - Searches GitHub API for paper implementations
- **Features**:
  - Searches by paper title
  - Searches by arXiv ID
  - Uses GitHub token if available (GITHUB_TOKEN env var)
  - Sorts results by stars for best match

### 4. Citation Counter Service
- **Status**: COMPLETE
- **Files Created**:
  - `backend/src/services/citation_counter.py` - Google Scholar citation extraction
- **Features**:
  - Async citation count retrieval
  - Title matching with tolerance
  - Handles scholarly library gracefully if not installed

### 5. Database Schema Extensions
- **Status**: COMPLETE
- **Files Created**:
  - `backend/add_citation_tracking.sql` - Citation tracking migration
- **Database Changes**:
  - `citation_count` column added to `papers` table
  - `citation_snapshots` table for historical tracking
  - `project_page_url` column added to `papers` table
  - `youtube_url` column added to `papers` table

## 🔄 In Progress / Needs Completion

### 6. Paper Enrichment Service
- **Status**: NOT STARTED
- **Required**:
  - Create `backend/src/services/paper_enrichment.py`
  - Combine all extractors (URLs, GitHub, citations)
  - Integrate with crawler to enrich papers automatically

### 7. Update Crawler to Use Enrichment
- **Status**: NOT STARTED
- **Required**:
  - Modify `backend/src/jobs/reference_crawler.py`
  - Call enrichment service for each new paper
  - Store extracted GitHub URLs, project URLs, YouTube links, citation counts

### 8. Citation Snapshot Model
- **Status**: SCHEMA COMPLETE, MODEL NOT CREATED
- **Required**:
  - Create `backend/src/models/citation_snapshot.py`
  - Add to `backend/src/models/__init__.py`

### 9. Paper Model Updates
- **Status**: SCHEMA COMPLETE, MODEL MAPPING NOT UPDATED
- **Required**:
  - Update `backend/src/models/paper.py` to include:
    - `citation_count: Mapped[int]`
    - `project_page_url: Mapped[Optional[str]]`
    - `youtube_url: Mapped[Optional[str]]` (already exists)

### 10. Frontend: Paper Detail Page Redesign
- **Status**: NOT STARTED
- **Required Files**:
  - `frontend/src/pages/PaperDetailPage.vue` - Complete redesign
- **Features Needed**:
  - Icon-based links (PDF, GitHub, Project Site, YouTube, DOI, BibTeX)
  - Compact metrics display
  - GitHub star tracking graph
  - Citation count tracking graph
  - Better visual hierarchy

### 11. Frontend: Tracking Graphs Component
- **Status**: NOT STARTED
- **Required**:
  - Create `frontend/src/components/CitationGraph.vue`
  - Create `frontend/src/components/GitHubStarsGraph.vue`
  - Use Chart.js or similar library
  - Fetch historical data from API

### 12. API Endpoints for Graphs
- **Status**: NOT STARTED
- **Required**:
  - Add endpoint: `GET /api/v1/papers/{id}/citation-history`
  - Already exists: `GET /api/v1/papers/{id}/star-history`
  - Return time-series data for charts

## 📋 Implementation Plan (Next Steps)

### Step 1: Complete Paper Enrichment Service
```python
# backend/src/services/paper_enrichment.py
class PaperEnrichmentService:
    def __init__(self):
        self.url_extractor = URLExtractor()
        self.github_search = GitHubSearchService()
        self.citation_counter = CitationCounter()

    async def enrich_paper(self, paper: Paper):
        # Extract URLs from abstract
        # Search GitHub if no URL found
        # Get citation count
        # Update paper object
        pass
```

### Step 2: Update Crawler Integration
Add enrichment call after creating each paper in `reference_crawler.py`

### Step 3: Create Citation Snapshot Model
Standard SQLAlchemy model matching the schema

### Step 4: Update Paper Model
Add the three new mapped columns

### Step 5: Frontend Paper Detail Page
Complete redesign with all required elements

### Step 6: Create Graph Components
Two separate Vue components for citation and star tracking

### Step 7: API Endpoint for Citation History
Query `citation_snapshots` table and return time-series data

## 🎯 Priority Order

1. **HIGH**: Paper Enrichment Service (blocks everything else)
2. **HIGH**: Update Crawler Integration (makes enrichment useful)
3. **HIGH**: Citation Snapshot Model + Paper Model updates
4. **MEDIUM**: Frontend Paper Detail Page redesign
5. **MEDIUM**: Tracking graphs and API endpoints
6. **LOW**: Polish and optimization

## 📝 Notes

- All database migrations completed successfully
- Services are async-ready
- GitHub token should be set as GITHUB_TOKEN environment variable
- scholarly library needs to be added to requirements.txt if not present
- Consider rate limiting for GitHub API (5000 req/hour with token)
- Consider caching for citation counts (they don't change frequently)

## 🔧 Dependencies to Add

```txt
scholarly  # For Google Scholar citation counting
```

## 🚀 Testing Checklist

- [ ] Crawler jobs persist across backend restart
- [ ] URL extraction works for various abstract formats
- [ ] GitHub search finds correct repositories
- [ ] Citation counter handles errors gracefully
- [ ] Frontend displays all new paper metadata
- [ ] Graphs render correctly with historical data
- [ ] Icons are clickable and link to correct URLs
