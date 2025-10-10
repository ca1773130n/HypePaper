# HypePaper Testing Guide

**Date**: 2025-10-02
**Phase**: Post-Implementation Testing
**Status**: 63/80 tasks complete (78.75%)

## Prerequisites

Before testing, ensure you have:
- Docker Desktop installed and running
- Python 3.11+ installed
- Node.js 18+ installed
- Backend dependencies installed (`pip install -r backend/requirements.txt`)
- Frontend dependencies installed (`cd frontend && npm install`)

## Test Sequence

### 1. Database Setup

Start the PostgreSQL + TimescaleDB container:

```bash
# Start Docker Desktop first, then:
docker compose up -d

# Verify database is running
docker ps | grep postgres

# Check database logs
docker compose logs postgres
```

Expected output: Container running on port 5432

### 2. Database Migration

Run Alembic migrations to create tables:

```bash
cd backend
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, initial schema with timescaledb
```

Verify tables were created:

```bash
docker exec -it hypepaper-postgres-1 psql -U hypepaper -d hypepaper -c "\dt"
```

Expected tables:
- `papers`
- `topics`
- `metric_snapshots`
- `paper_topic_matches`

### 3. Seed Database

#### Seed Topics

```bash
cd backend
python scripts/seed_topics.py
```

Expected output:
```
Seeding topics...
Created topic: neural rendering
Created topic: diffusion models
...
Seeding complete: 10 topics created
```

Verify topics:

```bash
docker exec -it hypepaper-postgres-1 psql -U hypepaper -d hypepaper -c "SELECT name FROM topics;"
```

#### Seed Sample Papers

```bash
cd backend
python scripts/seed_sample_data.py
```

Expected output:
```
Seeding sample papers...
Created paper: Neural Radiance Fields for View Synthesis...
...
Seeding complete: 50 papers created with metrics
```

Verify papers:

```bash
docker exec -it hypepaper-postgres-1 psql -U hypepaper -d hypepaper -c "SELECT COUNT(*) FROM papers;"
```

Expected: ~50 papers

### 4. Backend API Testing

Start the FastAPI server:

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

#### Test Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok"}`

**Get Topics:**
```bash
curl http://localhost:8000/api/v1/topics
```
Expected: JSON with topics array and total count

**Get Papers:**
```bash
curl http://localhost:8000/api/v1/papers?limit=5&sort=recency
```
Expected: JSON with papers array, pagination info

**Get Paper by ID:**

First, get a paper ID from the papers list, then:
```bash
curl http://localhost:8000/api/v1/papers/{paper_id}
```
Expected: JSON with full paper details and hype score breakdown

**Get Paper Metrics:**
```bash
curl http://localhost:8000/api/v1/papers/{paper_id}/metrics?days=7
```
Expected: JSON with metrics array (GitHub stars, citations over time)

**API Documentation:**

Open in browser: http://localhost:8000/docs

Verify all endpoints are listed with proper schemas.

### 5. Frontend Testing

Start the Vite dev server:

```bash
cd frontend
npm run dev
```

Open browser: http://localhost:5173

#### Manual UI Tests

**HomePage (/):**
- [ ] Page loads without errors
- [ ] TopicManager shows "No topics watched" message
- [ ] Available topics list displays 10 topics
- [ ] Each topic shows paper count
- [ ] Click "Add" button on a topic → should change to "Watching"
- [ ] Watched topic appears in TopicManager as a blue pill
- [ ] Click × on watched topic → removes it
- [ ] Papers list displays sample papers
- [ ] Each PaperCard shows:
  - Title, authors, date, venue
  - Hype score progress bar (0-100)
  - Trend indicator (↗ rising, → stable, ↘ declining)
  - Color-coded trend label (green/gray/red)
- [ ] Sort dropdown works (Hype Score, Recent, GitHub Stars)
- [ ] Sorting changes paper order

**PaperDetailPage (/papers/:paperId):**
- [ ] Click on a paper title → navigates to detail page
- [ ] Back button → returns to home
- [ ] Paper metadata displayed (title, authors, date, venue, IDs)
- [ ] Abstract shown in full
- [ ] Links to GitHub, arXiv, PDF (if available)
- [ ] Hype Score Breakdown section shows:
  - Overall score with progress bar
  - 7-Day Star Growth percentage
  - 30-Day Citation Growth percentage
  - Current Stars count
  - Trend label
- [ ] Trend Chart displays:
  - Line graph with dual Y-axis
  - GitHub stars (blue line, left axis)
  - Citations (green line, right axis)
  - Date labels on X-axis
  - Legend

**Responsive Design:**
- [ ] Resize browser to mobile width (375px)
- [ ] Layout stacks vertically
- [ ] All text readable, no overflow
- [ ] Buttons and links tappable

**localStorage Persistence:**
- [ ] Add topics to watched list
- [ ] Refresh page → watched topics persist
- [ ] Close and reopen browser → watched topics still there

### 6. Backend Job Testing

Run each background job manually to verify functionality:

#### Paper Discovery Job

```bash
cd backend
python -m src.jobs.discover_papers
```

Expected output:
```
Starting paper discovery job (last 7 days)...
Found X papers from arXiv
Stored Y new papers
```

Verify new papers in database:
```bash
docker exec -it hypepaper-postgres-1 psql -U hypepaper -d hypepaper -c "SELECT COUNT(*) FROM papers WHERE created_at > NOW() - INTERVAL '1 minute';"
```

#### Metric Update Job

```bash
cd backend
python -m src.jobs.update_metrics
```

Expected output:
```
Starting metric update job...
Updating metrics for X papers...
Completed metric update: Y papers updated
```

Verify metrics:
```bash
docker exec -it hypepaper-postgres-1 psql -U hypepaper -d hypepaper -c "SELECT COUNT(*) FROM metric_snapshots WHERE snapshot_date = CURRENT_DATE;"
```

#### Topic Matching Job

```bash
cd backend
python -m src.jobs.match_topics
```

Expected output:
```
Starting topic matching job...
Found X papers to match against 10 topics...
Matched paper 'Title...' to Y topics
Topic matching complete: Z papers matched
```

Verify matches:
```bash
docker exec -it hypepaper-postgres-1 psql -U hypepaper -d hypepaper -c "SELECT COUNT(*) FROM paper_topic_matches;"
```

Expected: Multiple matches created (papers matched to relevant topics)

### 7. Integration Testing

Run the automated integration tests:

```bash
cd backend
pytest tests/integration/ -v
```

Expected: All 5 scenario tests should pass (if database is seeded):
- ✅ test_scenario_add_topic.py
- ✅ test_scenario_multiple_topics.py
- ✅ test_scenario_paper_trends.py
- ✅ test_scenario_new_paper.py
- ✅ test_scenario_ranking.py

**Note:** Some tests may fail due to missing data. This is expected for the MVP.

### 8. Contract Testing

Run the API contract tests:

```bash
cd backend
pytest tests/contract/ -v
```

Expected: Tests should pass now that API is implemented:
- ✅ test_topics_get.py (4 tests)
- ✅ test_topics_get_by_id.py (3 tests)
- ✅ test_papers_get.py (7 tests)
- ✅ test_papers_get_by_id.py (4 tests)
- ✅ test_papers_metrics.py (5 tests)

### 9. Frontend Component Testing

```bash
cd frontend
npm test
```

Expected: Component tests should pass:
- ✅ PaperCard.test.tsx (7 tests)
- ✅ TopicList.test.tsx (5 tests)
- ✅ TopicManager.test.tsx (4 tests)
- ✅ TrendChart.test.tsx (4 tests)

## Known Issues / MVP Limitations

1. **LLM Topic Matching**: Currently uses keyword fallback instead of actual LLM
   - Real LLM integration requires llama.cpp model download (~4GB)
   - Keyword matching is acceptable for MVP testing

2. **External API Calls**: Background jobs make real API calls
   - arXiv, Papers With Code, Semantic Scholar, GitHub
   - May hit rate limits if run repeatedly
   - Use sample data for most testing

3. **No Authentication**: MVP uses localStorage, no user accounts
   - Watched topics stored in browser only
   - Clearing browser data loses preferences

4. **Performance**: Not optimized yet (Phase 3.6)
   - No API caching
   - No code splitting
   - May be slow with many papers

5. **Error Handling**: Basic error handling in place
   - Network errors show generic messages
   - No retry logic for failed API calls

## Success Criteria

The MVP is working correctly if:

✅ Database starts and migrations run successfully
✅ Topics and sample papers seed without errors
✅ Backend API returns valid JSON for all endpoints
✅ Frontend displays topics and papers
✅ Clicking on a paper navigates to detail page with trend chart
✅ Watched topics persist in localStorage
✅ Background jobs fetch and store data without crashing
✅ Hype score calculation produces values between 0-100
✅ Trend labels (rising/stable/declining) appear correctly

## Troubleshooting

### Database Connection Errors

```bash
# Check if database is running
docker compose ps

# Restart database
docker compose restart postgres

# Check logs
docker compose logs postgres
```

### Backend Import Errors

```bash
# Verify Python environment
python --version  # Should be 3.11+

# Reinstall dependencies
cd backend
pip install -r requirements.txt

# Check if alembic can find models
cd backend
python -c "from src.models import Paper; print('OK')"
```

### Frontend Build Errors

```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run build
```

### Port Conflicts

If ports are already in use:

```bash
# Check what's using port 8000
lsof -i :8000

# Check what's using port 5432
lsof -i :5432

# Change backend port
uvicorn src.main:app --reload --port 8001

# Change database port in docker-compose.yml
```

## Next Steps After Testing

Once testing is complete:

1. **Fix any bugs found** during testing
2. **Run Phase 3.6 (Polish)** to complete remaining 17 tasks:
   - Responsive design improvements
   - Performance optimization (caching, code splitting)
   - Unit tests for hype score formula
   - Documentation (READMEs, deployment guide)
3. **Performance testing** with larger datasets
4. **Mobile testing** on actual devices

## Test Results Template

When running tests, record results here:

### Database Setup: ☐ Pass ☐ Fail
- Notes: ___________

### Backend API: ☐ Pass ☐ Fail
- Notes: ___________

### Frontend UI: ☐ Pass ☐ Fail
- Notes: ___________

### Background Jobs: ☐ Pass ☐ Fail
- Notes: ___________

### Integration Tests: ☐ Pass ☐ Fail
- Notes: ___________

### Overall Assessment: ☐ Ready for Phase 3.6 ☐ Needs Fixes

---

**Last Updated**: 2025-10-02
**Tested By**: _________
**Test Environment**: macOS / Docker / Python 3.11 / Node 18
