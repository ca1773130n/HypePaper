# Quickstart: Paper Enrichment Feature Testing

**Feature**: 003-add-paper-enrichment
**Date**: 2025-10-11
**Purpose**: Executable acceptance scenarios from spec.md

## Prerequisites

```bash
# Backend running
cd backend && python -m uvicorn src.main:app --reload --port 8000

# Frontend running
cd frontend && npm run dev

# Database migrations applied
cd backend && alembic upgrade head

# Test user authenticated (get JWT token)
# Use Supabase auth or create test user
```

## Scenario 1: Viewing Accurate Paper Information

**Test**: Publication date shows actual publish date, not crawl date

```bash
# Given: Paper crawled on 2025-10-10 but published on 2025-09-15
PAPER_ID="<uuid-of-test-paper>"

# Create test paper with published_date=2025-09-15, created_at=2025-10-10
curl -X POST http://localhost:8000/api/papers \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Paper for Date Display",
    "authors": ["Author One"],
    "abstract": "Test abstract",
    "published_date": "2025-09-15",
    "arxiv_id": "2509.12345"
  }'

# When: User views paper
curl http://localhost:8000/api/papers/$PAPER_ID

# Then: Response shows published_date: "2025-09-15"
# Expected: { "published_date": "2025-09-15", "created_at": "2025-10-10T..." }
```

**Frontend Test**:
1. Navigate to `/papers/{PAPER_ID}`
2. Verify date shows "Published: Sep 15, 2025" (not Oct 10, 2025)

## Scenario 2: URL Hyperlinking in Abstracts

**Test**: URLs in abstracts become clickable hyperlinks

```bash
# Given: Paper abstract contains URLs
curl -X POST http://localhost:8000/api/papers \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Paper with URLs",
    "authors": ["Author Two"],
    "abstract": "See our code at https://github.com/user/repo and project page at https://project-website.com for details.",
    "published_date": "2025-10-10",
    "arxiv_id": "2510.12346"
  }'

# When: User views abstract on paper detail page
# Then: Both URLs are clickable, GitHub URL has GitHub icon
```

**Frontend Test**:
1. Navigate to paper detail page
2. Inspect abstract rendering
3. Verify `<a href="https://github.com/user/repo">` with GitHub icon
4. Verify `<a href="https://project-website.com">` with generic link icon

## Scenario 3: Voting on Papers (Upvote)

**Test**: User can upvote a paper

```bash
# Given: Authenticated user viewing paper
TOKEN="<jwt-token>"
PAPER_ID="<uuid>"

# When: User clicks upvote button
curl -X POST http://localhost:8000/api/papers/$PAPER_ID/vote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": "upvote"}'

# Then: Vote count increases by 1, upvote button shows active state
# Expected: { "vote_type": "upvote", "vote_count": 1, ... }

# Verify vote persisted
curl http://localhost:8000/api/papers/$PAPER_ID/vote/status \
  -H "Authorization: Bearer $TOKEN"

# Expected: { "has_voted": true, "vote_type": "upvote" }
```

## Scenario 4: Voting on Papers (Remove Vote)

**Test**: User can toggle off upvote

```bash
# Given: User has already upvoted (vote_count=1)
# When: User clicks upvote button again
curl -X DELETE http://localhost:8000/api/papers/$PAPER_ID/vote \
  -H "Authorization: Bearer $TOKEN"

# Then: Vote is removed, vote_count decreases to 0
# Expected: 204 No Content

# Verify vote removed
curl http://localhost:8000/api/papers/$PAPER_ID \
  | jq '.vote_count'

# Expected: 0
```

## Scenario 5: Voting on Papers (Change Vote)

**Test**: User can change from upvote to downvote

```bash
# Given: User has upvoted (vote_count=1)
curl -X POST http://localhost:8000/api/papers/$PAPER_ID/vote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": "upvote"}'

# When: User clicks downvote button
curl -X POST http://localhost:8000/api/papers/$PAPER_ID/vote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": "downvote"}'

# Then: Vote changes, vote_count decreases by 2 (from +1 to -1)
curl http://localhost:8000/api/papers/$PAPER_ID \
  | jq '.vote_count'

# Expected: -1 (assuming no other votes)
```

## Scenario 6: Viewing Author Information (Click)

**Test**: Clicking author name shows author details in modal

```bash
# Given: Paper with author "John Smith"
AUTHOR_ID="<author-id>"

# When: User clicks author name
curl http://localhost:8000/api/authors/$AUTHOR_ID

# Then: Author modal shows affiliation, citation count, paper count, contact info
# Expected: {
#   "id": 123,
#   "name": "John Smith",
#   "primary_affiliation": "MIT",
#   "paper_count": 15,
#   "total_citation_count": 450,
#   "email": "jsmith@mit.edu",
#   "recent_papers": [...]
# }
```

**Frontend Test**:
1. Click author name in paper detail page
2. Verify modal opens with author information
3. Verify recent papers list (up to 5 papers)
4. Click "View all papers" → filters papers by author

## Scenario 7: Author Cards in Paper Detail

**Test**: Paper detail page shows author affiliation cards

**Frontend Test**:
1. Navigate to `/papers/{PAPER_ID}`
2. Scroll to authors section
3. Verify each author has card with:
   - Author name
   - Affiliation (at time of paper)
   - Clickable to open author modal

## Scenario 8: Paper Content Enrichment

**Test**: Quick Summary, Key Ideas, Performance, Limitations sections display

```bash
# Given: Paper with enriched content
curl -X PATCH http://localhost:8000/api/papers/$PAPER_ID \
  -H "Content-Type: application/json" \
  -d '{
    "quick_summary": "Novel approach to image classification using transformers",
    "key_ideas": "- Self-attention mechanism\n- Pre-training on large datasets",
    "quantitative_performance": {"accuracy": "95.2%", "baseline": "90.1%"},
    "qualitative_performance": "Outperforms previous SOTA on ImageNet",
    "limitations": "High computational cost, requires large GPU memory"
  }'

# When: User views paper detail page
# Then: All sections display with proper formatting
```

**Frontend Test**:
1. Navigate to paper detail page
2. Verify sections appear:
   - **Quick Summary**: 1-2 sentences
   - **Key Ideas**: Bulleted list
   - **Performance**: Table with quantitative metrics
   - **Qualitative**: Paragraph text
   - **Limitations**: Paragraph text

## Scenario 9: Performance Metrics Separation

**Test**: Quantitative and qualitative performance clearly separated

**Frontend Test**:
1. Paper detail page shows "Performance" section with two tabs:
   - **Metrics** tab: Table of numerical results (accuracy, F1, etc.)
   - **Analysis** tab: Qualitative description
2. Verify quantitative data renders as table
3. Verify qualitative data renders as text

## Scenario 10: Time-Series Metrics Graphs

**Test**: Daily metric graphs display for citations, stars, votes, hype score

```bash
# Given: Paper has 30 days of metric snapshots
curl http://localhost:8000/api/papers/$PAPER_ID/metrics?days=30

# Expected: [
#   {"date": "2025-09-11", "citation_count": 10, "github_stars": 50, "vote_count": 5, "hype_score": 23.4},
#   {"date": "2025-09-12", "citation_count": 12, "github_stars": 55, "vote_count": 7, "hype_score": 25.1},
#   ...
# ]
```

**Frontend Test**:
1. Navigate to paper detail page
2. Scroll to "Metrics Trends" section
3. Verify 4 line charts display:
   - Citations over time
   - GitHub stars over time
   - Votes over time
   - Hype score over time
4. Hover over data point → tooltip shows exact date and value
5. Verify graphs load in < 500ms

## Scenario 11: Graph Tooltip Interaction

**Test**: Hovering over metric graph shows tooltip

**Frontend Test**:
1. Open paper detail page with graphs
2. Hover over citation graph data point
3. Verify tooltip appears: "Oct 5, 2025: 42 citations"
4. Move to different point → tooltip updates
5. Verify no flickering or lag

## Scenario 12: Citation Network Quick Action

**Test**: "Start Crawling from This Paper" button pre-fills crawler form

```bash
# Given: User on paper detail page with PAPER_ID="abc-123"
# When: User clicks "Start Crawling from This Paper" button
# Then: Navigates to /crawler?type=citation_network&paper_id=abc-123
```

**Frontend Test**:
1. Navigate to paper detail page
2. Find "Quick Actions" section
3. Click "Start Crawling from This Paper" button
4. Verify redirect to crawler page
5. Verify form pre-filled:
   - Crawl type: "Citation Network"
   - Paper ID: `<current-paper-id>`
6. User can configure depth, max papers, etc.
7. Click "Start Crawling" → job begins

## Edge Case Tests

### EC1: Publication Date Fallback

```bash
# Given: Paper has no publication date in source
curl -X POST http://localhost:8000/api/papers \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Paper Without Publish Date",
    "authors": ["Author"],
    "abstract": "Abstract",
    "published_date": null
  }'

# Expected: API returns error (published_date required)
# OR: Falls back to created_at with label "Added to database: Oct 10, 2025"
```

### EC2: Malformed URLs in Abstract

```bash
# Given: Abstract with partial URL "github.com/user/repo" (no https://)
# Expected: Not hyperlinked (regex requires https?://)
```

### EC3: Voting Without Authentication

```bash
# Given: Unauthenticated user (no token)
curl -X POST http://localhost:8000/api/papers/$PAPER_ID/vote \
  -H "Content-Type: application/json" \
  -d '{"vote_type": "upvote"}'

# Expected: 401 Unauthorized
```

### EC4: Author with No Affiliation

```bash
# Given: Author record with affiliations=null
curl http://localhost:8000/api/authors/$AUTHOR_ID

# Expected: { "primary_affiliation": null, ... }
# Frontend: Display "Affiliation not available"
```

### EC5: Paper with No GitHub Repo

```bash
# Given: Paper with github_url=null
curl http://localhost:8000/api/papers/$PAPER_ID/metrics?days=30

# Expected: Snapshots have github_stars=null
# Frontend: Graph shows only citations and votes (stars line hidden)
```

### EC6: Negative Vote Count

```bash
# Given: Paper with 2 upvotes, 5 downvotes
# Expected: vote_count=-3
# Frontend: Display "-3 votes" with downvote icon color
```

### EC7: Hype Score with Negative Votes

```bash
# Given: Paper with vote_count=-10
# Calculate: vote_component = log(1 + max(0, -10)) * 5 = log(1) * 5 = 0
# Expected: Negative votes contribute 0 to hype score (clamped)
```

## Performance Validation

### P1: Vote API Response Time

```bash
time curl -X POST http://localhost:8000/api/papers/$PAPER_ID/vote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote_type": "upvote"}'

# Expected: < 200ms
```

### P2: Author Lookup Response Time

```bash
time curl http://localhost:8000/api/authors/$AUTHOR_ID

# Expected: < 300ms
```

### P3: Metric Graph Render Time

**Frontend Test**:
1. Open DevTools Network tab
2. Navigate to paper detail page
3. Measure time from metrics API response to graph render complete
4. Expected: < 500ms

### P4: Page Load Time

**Frontend Test**:
1. Open DevTools Performance tab
2. Navigate to paper detail page (full load)
3. Measure time to interactive
4. Expected: < 2 seconds (constitutional requirement)

## Acceptance Criteria

All scenarios must pass for feature to be considered complete:

- [x] Scenario 1-12: All functional scenarios pass
- [x] EC1-7: All edge cases handled correctly
- [x] P1-4: All performance validations meet targets

**Sign-off**: Feature ready for production when all checkboxes above are checked.

---
*Quickstart scenarios generated: 2025-10-11*
*Based on spec.md acceptance scenarios*
