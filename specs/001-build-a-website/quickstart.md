# Quickstart: Trending Research Papers Tracker

**Purpose**: End-to-end integration test scenarios that validate the complete user journey from feature specification.

**Status**: Test scenarios defined, ready for implementation

---

## Prerequisites

### Backend Setup
```bash
# Start PostgreSQL + TimescaleDB
docker-compose up -d postgres

# Run migrations
cd backend
python -m alembic upgrade head

# Seed topics
python -m scripts.seed_topics

# Start FastAPI server
uvicorn src.api.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

### LLM Setup
```bash
# Download quantized model (one-time setup)
cd backend
python -m scripts.download_llm_model  # Downloads to models/

# Verify LLM works
python -m scripts.test_llm
```

---

## Integration Test Scenarios

### Scenario 1: First-Time User Adds Topic and Sees Trending Papers
**Maps to**: Acceptance Scenario 1

**Given**:
- User visits HypePaper for the first time
- Database has been seeded with topics and sample papers
- At least one topic "neural rendering" exists with matched papers

**Steps**:
1. Open browser to `http://localhost:5173`
2. Verify homepage loads within 2 seconds
3. Verify topic list is displayed (e.g., "neural rendering", "diffusion models")
4. Click "Add" button on "neural rendering" topic
5. Verify topic is added to "My Topics" section
6. Verify papers list updates to show papers for "neural rendering"
7. Verify papers are sorted by hype score (descending)
8. Verify each paper card shows:
   - Title
   - Authors (first 3, then "et al.")
   - Published date
   - Venue (if present)
   - Hype score (0-100)
   - Trend indicator (↑ rising / → stable / ↓ declining)
   - GitHub stars (if repo exists)
   - Citation count

**Expected Outcome**:
- Topic is persisted in localStorage
- Papers list shows 10-50 papers ranked by hype score
- Page is mobile-responsive (test on 375px width)

**Success Criteria**:
- ✅ Page load < 2 seconds
- ✅ Topic persists on page refresh
- ✅ Papers are correctly ranked

---

### Scenario 2: User With Multiple Topics Returns and Sees Grouped Papers
**Maps to**: Acceptance Scenario 2

**Given**:
- User has previously added 3 topics: "neural rendering", "diffusion models", "3d reconstruction"
- Topics are stored in localStorage
- User returns to the site

**Steps**:
1. Open browser to `http://localhost:5173`
2. Verify homepage loads and shows "My Topics" section with 3 topics
3. Verify papers are displayed grouped by topic (3 sections)
4. Verify each section shows:
   - Topic name as heading
   - Top 10 papers for that topic
   - "Show more" link to expand to 50 papers
5. Verify hype scores are displayed for each paper
6. Verify overall layout is not cluttered (simple, fast principle)

**Expected Outcome**:
- User sees personalized view with their topics
- Papers are correctly grouped
- No duplicate papers across topics (same paper can appear in multiple topics)

**Success Criteria**:
- ✅ Topics loaded from localStorage
- ✅ Papers grouped correctly
- ✅ Hype scores are current (from today's metrics)

---

### Scenario 3: User Views Paper Details With Historical Trend
**Maps to**: Acceptance Scenario 3

**Given**:
- Database has been tracking a paper "Neural Radiance Fields" for 30 days
- Paper has daily metric snapshots (stars and citations)
- User is viewing papers list

**Steps**:
1. Click on paper "Neural Radiance Fields" from the list
2. Verify paper detail page loads
3. Verify page displays:
   - Full title, authors, abstract
   - Links to arXiv, PDF, GitHub (if present)
   - Current metrics (stars, citations)
   - Hype score with breakdown (stars growth, citation growth, recency)
4. Scroll to "Trend Analysis" section
5. Verify chart displays:
   - X-axis: Last 30 days
   - Y-axis (left): GitHub stars
   - Y-axis (right): Citation count
   - Two lines showing historical data
6. Verify trend direction matches trend label (rising/stable/declining)

**Expected Outcome**:
- User can see why a paper is trending
- Historical data validates hype score
- Chart is readable on mobile

**Success Criteria**:
- ✅ All metadata displayed correctly
- ✅ Chart renders with 30 days of data
- ✅ Hype score breakdown explains calculation

---

### Scenario 4: New Paper Appears After Daily Monitoring
**Maps to**: Acceptance Scenario 4

**Given**:
- A new paper "Instant Neural Graphics" is published on arXiv today
- Paper has an associated GitHub repository
- Daily monitoring job has not yet run

**Steps**:
1. Manually trigger daily job: `python -m src.jobs.daily_update`
2. Verify job logs show:
   - Fetched new papers from arXiv
   - Found "Instant Neural Graphics"
   - Linked to GitHub repo via Papers With Code API
   - LLM matched paper to "neural rendering" topic (relevance >= 6.0)
   - Created initial MetricSnapshot
3. Refresh frontend homepage
4. Verify "Instant Neural Graphics" appears in "neural rendering" topic
5. Verify paper has "NEW" badge (published within 48 hours)
6. Verify hype score reflects recency bonus (paper < 30 days old)

**Expected Outcome**:
- New paper is discoverable within 24-48 hours of publication
- Topic matching is accurate
- Metrics are tracked from day one

**Success Criteria**:
- ✅ Daily job completes within 4 hours
- ✅ New paper appears in correct topic
- ✅ Recency bonus applied to hype score

---

### Scenario 5: Paper With Rapid Star Growth Rises in Ranking
**Maps to**: Acceptance Scenario 5

**Given**:
- Paper "3D Gaussian Splatting" has been tracked for 14 days
- Days 1-7: 50 stars, 10 citations
- Days 8-14: 500 stars (+900% growth), 12 citations (+20% growth)
- Another paper "Old NeRF Method" has 1000 stars but flat growth (0%)

**Steps**:
1. Query papers API for "neural rendering" topic: `GET /api/v1/papers?topic_id={id}&sort=hype_score`
2. Verify "3D Gaussian Splatting" ranks higher than "Old NeRF Method"
3. Verify hype score calculation:
   - "3D Gaussian Splatting": High star growth (0.4 weight) + recency bonus → ~85/100
   - "Old NeRF Method": Low growth, no recency → ~30/100
4. Verify trend label:
   - "3D Gaussian Splatting": "rising" (↑)
   - "Old NeRF Method": "stable" (→)
5. On frontend, verify papers are displayed in correct order

**Expected Outcome**:
- Growth rate matters more than absolute values
- Trending papers surface at top
- Algorithm aligns with constitution principle II (novel metrics)

**Success Criteria**:
- ✅ Hype score reflects growth, not just absolute metrics
- ✅ UI clearly shows trending vs stable papers
- ✅ Ranking is intuitive to users

---

## Edge Case Tests

### Edge Case 1: Paper Without GitHub Repository
**Given**: Paper "Pure Theory Paper" has no GitHub repo, only citations

**Expected**:
- Paper appears in topic list (citations alone are valid)
- GitHub stars displayed as "N/A" or hidden
- Hype score calculated without star component (reweight formula)
- No broken links to GitHub

### Edge Case 2: Paper Without Citations (Brand New)
**Given**: Paper published yesterday, not yet cited

**Expected**:
- Paper appears with 0 citations
- Hype score relies on recency bonus and star growth (if repo exists)
- "NEW" badge displayed prominently

### Edge Case 3: Conference Paper Not on arXiv
**Given**: Paper "SIGGRAPH 2024 Best Paper" published at conference, not on arXiv

**Expected**:
- Paper discovered via Papers With Code API (conference track)
- doi used as canonical identifier (arxiv_id null)
- Venue displayed as "SIGGRAPH 2024"
- Link to conference proceedings instead of arXiv

### Edge Case 4: Duplicate Paper Across Sources
**Given**: Same paper exists on arXiv and in CVPR proceedings

**Expected**:
- Database constraint prevents duplicate (unique doi)
- If arXiv version found first, doi linked when conference version discovered
- Only one entry in database
- Both URLs (arXiv and conference) stored

### Edge Case 5: Very Broad Topic ("AI")
**Given**: User watches topic "artificial intelligence" (extremely broad)

**Expected**:
- LLM matches papers with relevance >= 6.0 (high threshold)
- Papers list is capped at 1000 (from research.md scale target)
- Hype score ranking still works (top 100 papers are well-ranked)
- UI suggests narrower topics if >1000 matches

---

## Performance Validation

### Load Time Test
```bash
# Measure homepage load time
curl -w "Total time: %{time_total}s\n" -o /dev/null -s http://localhost:5173

# Target: < 2 seconds (constitution principle I)
```

### API Response Time Test
```bash
# Measure papers API response
curl -w "API time: %{time_total}s\n" -o /dev/null -s "http://localhost:8000/api/v1/papers?topic_id={uuid}&limit=50"

# Target: < 500ms
```

### Daily Job Completion Test
```bash
# Run daily update job and measure duration
time python -m src.jobs.daily_update

# Target: < 4 hours (from research.md)
```

---

## Mobile Responsiveness Test

### Test on Device Widths
- 375px (iPhone SE)
- 768px (iPad)
- 1024px (Desktop)

**Verify**:
- Topic list is scrollable/collapsible on mobile
- Paper cards stack vertically on narrow screens
- Trend chart resizes gracefully
- Touch targets are >= 44px (accessibility)
- No horizontal scrolling

---

## Data Validation Tests

### Hype Score Calculation Validation
```python
# Test hype score formula matches research.md specification
def test_hype_score_calculation():
    paper = get_test_paper()  # Known metrics
    metrics = get_metrics_for_paper(paper.id, days=30)

    calculated_score = calculate_hype_score(paper, metrics)

    # Manual calculation
    star_growth_7d = (100 - 50) / 50  # 1.0
    citation_growth_30d = (20 - 10) / 10  # 1.0
    absolute_stars_norm = log10(100 + 1) / log10(1000 + 1)  # ~0.67
    recency_bonus = 1.0  # Paper < 30 days old

    expected_score = (0.4 * 1.0 + 0.3 * 1.0 + 0.2 * 0.67 + 0.1 * 1.0) * 100
    # = (0.4 + 0.3 + 0.134 + 0.1) * 100 = 83.4

    assert abs(calculated_score - expected_score) < 0.1
```

### Topic Matching Accuracy Test
```python
# Verify LLM correctly matches papers to topics
def test_topic_matching_accuracy():
    test_cases = [
        ("Neural Radiance Fields for View Synthesis", "neural rendering", expected_score >= 8.0),
        ("Bitcoin Price Prediction Using LSTM", "neural rendering", expected_score < 6.0),
        ("Diffusion Models Beat GANs", "diffusion models", expected_score >= 8.0),
    ]

    for title, topic_name, expected in test_cases:
        score = match_paper_to_topic(title, topic_name)
        assert expected(score), f"Failed for: {title} -> {topic_name}"
```

---

## Status Summary

**✅ Scenarios Defined**: 5 acceptance scenarios + 5 edge cases
**✅ Performance Targets**: Load time, API response, daily job duration
**✅ Validation Tests**: Hype score calculation, topic matching accuracy
**✅ Mobile Tests**: Responsive design across device widths

**Ready for**: Task generation via `/tasks` command

---

**Notes**:
- All test scenarios are executable once implementation is complete
- Tests validate constitution principles (simple, fast, accurate)
- Edge cases ensure robustness for MVP
- Performance tests enforce <2s page load requirement
