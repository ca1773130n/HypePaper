# Feature Specification: Paper Enrichment Feature Improvements

**Feature Branch**: `003-add-paper-enrichment`
**Created**: 2025-10-10
**Status**: Clarified - Ready for Planning
**Input**: User description: "add paper enrichment feature improvement.
- fix the problem of incorrect paper published date issue. it's still showing the crawling date instead of actual publish date of the paper.
- detect the website url in abstract and add hyperlink when showing abstract. also, remember you should recognize project url or github url by its address and the sentence.
- add vote feature for the papers. prepare integer value in the paper metric as well as in the database. add up/down vote button in paper details page. show hype score and vote score in metric block in paper detail page. so there would be four metric to be shown.
- add vote value when calculating hype score. vote value could be zero or even minus. but usually it would be zero or positive integer.
- paper detail page is too boring. add affiliation info. add quick summary, key idea and quantitive and qualifitive performance, limitations block. add attributes for these blocks in papers database. we will implement how to fill these blocks later.
- there is authors table in supabase which is not used. i want to have rows for each author. an author row would have columns like name, affiliation, total citation number, latest paper reference id to the apper row in papers table, total number of paper as author for papers in our database, email address and personal website url.
- show the author information when clicked in paper details page or even in main page's paper list where there is also author list.
- the quick actions in the paper details page is too simple. add start crawling from this paper button where user will be at new crawler page with citation network type, auto filled the paper id. then user can configure other options and can launch the crawler.
- add graphs for tracked metrics. for each metric, add graph in time-series. (daily basis)"

## Execution Flow (main)
```
1. Parse user description from Input
   → Extracted 9 distinct improvement areas
2. Extract key concepts from description
   → Identified: papers, authors, votes, metrics, tracking, UI enhancements
3. For each unclear aspect:
   → Marked with [NEEDS CLARIFICATION] tags
4. Fill User Scenarios & Testing section
   → Created scenarios for each major feature area
5. Generate Functional Requirements
   → 45 testable requirements defined
6. Identify Key Entities (if data involved)
   → Papers, Authors, Votes, Metric Snapshots entities
7. Run Review Checklist
   → Spec has 4 clarification items for user input
8. Return: SUCCESS (spec ready for clarification)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing

### Primary User Story
As a researcher browsing papers in HypePaper, I want to see accurate publication dates, rich author information, and be able to vote on papers to help the community identify valuable research. I also want to easily understand paper contributions through quick summaries and track how papers gain popularity over time.

### Acceptance Scenarios

#### Scenario 1: Viewing Accurate Paper Information
1. **Given** a paper was crawled on 2025-10-10 but published on 2025-09-15
   **When** user views the paper in the list or detail page
   **Then** the displayed date should be 2025-09-15 (actual publication date)

2. **Given** a paper abstract contains URLs like "https://project-website.com" and "https://github.com/user/repo"
   **When** user views the paper abstract
   **Then** URLs should be clickable hyperlinks, visually distinguished from plain text

#### Scenario 2: Voting on Papers
3. **Given** a user viewing a paper detail page
   **When** user clicks the upvote button
   **Then** vote count increases by 1 and upvote button shows active state

4. **Given** a user has already upvoted a paper
   **When** user clicks the upvote button again
   **Then** upvote is removed and vote count decreases by 1

5. **Given** a user has upvoted a paper
   **When** user clicks the downvote button
   **Then** upvote is removed, downvote is applied, vote count changes by -2

#### Scenario 3: Viewing Author Information
6. **Given** a paper with multiple authors
   **When** user clicks on an author name in the paper list
   **Then** author detail modal/popup shows with affiliation, citation count, paper count, and contact info

7. **Given** viewing a paper detail page
   **When** page loads
   **Then** author cards display with affiliation information for each author

#### Scenario 4: Understanding Paper Content
8. **Given** a paper detail page loads
   **When** user scrolls down
   **Then** user sees Quick Summary, Key Ideas, Performance Metrics, and Limitations sections

9. **Given** a paper's performance section is populated
   **When** user views the section
   **Then** both quantitative metrics (numbers) and qualitative results (text) are clearly separated

#### Scenario 5: Tracking Paper Metrics
10. **Given** a paper has been tracked for 30 days
    **When** user views the paper detail page
    **Then** time-series graphs show daily trends for citations, GitHub stars, votes, and hype score

11. **Given** viewing a metric graph
    **When** user hovers over a data point
    **Then** tooltip shows exact date and value

#### Scenario 6: Starting Citation Network Crawl
12. **Given** user is on a paper detail page
    **When** user clicks "Start Crawling from This Paper" button
    **Then** user is navigated to crawler page with citation network mode pre-selected and paper ID pre-filled

### Edge Cases

#### Publication Date Issues
- What happens when arXiv paper has multiple version dates?
  → **CLARIFIED**: Use the latest version date
- How to handle papers with no publication date in source data?
  → Display crawl date with clear label "Added to database: [date]"

#### URL Detection in Abstracts
- What if abstract contains malformed or partial URLs?
  → Only hyperlink valid, complete URLs (http:// or https://)
- How to handle very long URLs that break layout?
  → **CLARIFIED**: URLs are not expected to be excessively long, no truncation needed

#### Voting System
- Can users vote without authentication?
  → **CLARIFIED**: Users must be logged in to vote
- What prevents vote manipulation (one user voting many times)?
  → **CLARIFIED**: Authentication-based - one vote per logged-in user account
- Can users change their vote from upvote to downvote?
  → Yes, as per Scenario 5 above
- What is the initial vote count for newly added papers?
  → Starts at 0

#### Author Information
- What if author has no affiliation data?
  → Display "Affiliation not available"
- How to handle duplicate author names?
  → **CLARIFIED**: Use name + affiliation combination to distinguish authors with identical names
- What if email/website not available?
  → Display only available fields, hide missing ones

#### Metric Tracking
- When does daily metric snapshot get recorded?
  → System should record one snapshot per day per metric per paper
- What if paper has no GitHub repo for star tracking?
  → Graph shows only citation and vote metrics
- How long to retain historical metric data?
  → Retain all historical data (no automatic deletion)

#### Hype Score Calculation
- If vote is negative, can hype score go negative?
  → Hype score minimum should be 0
- What weight should votes have relative to citations and stars?
  → **CLARIFIED**: Formula design with minimal vote impact:
    - Votes are unbounded and non-normalized
    - Use logarithmic scaling to dampen vote impact: vote_component = log(1 + max(0, votes)) * 5
    - This gives: 0 votes → 0 points, 10 votes → ~5.4 points, 100 votes → ~10.1 points
    - Hype Score = (citation_growth * 0.35) + (star_growth * 0.35) + (absolute_metrics * 0.20) + (vote_component * 0.10)
    - Maximum contribution from votes is ~10-15% even with very high vote counts

---

## Requirements

### Functional Requirements

#### Publication Date (FR-001 to FR-004)
- **FR-001**: System MUST display the actual publication date from the paper source (arXiv, conference, journal), not the crawl date
- **FR-002**: System MUST store both publication date and crawl date separately in the database
- **FR-003**: System MUST extract publication date from arXiv metadata when crawling papers
- **FR-004**: For arXiv papers with multiple versions, system MUST use the latest version date as the publication date

#### URL Detection and Hyperlinking (FR-005 to FR-008)
- **FR-005**: System MUST automatically detect valid URLs (http://, https://) in paper abstracts
- **FR-006**: System MUST convert detected URLs into clickable hyperlinks when displaying abstracts
- **FR-007**: System MUST distinguish between GitHub repository URLs and project website URLs based on domain name
- **FR-008**: System MUST visually style hyperlinks to be distinguishable from regular text (color, underline, or icon)

#### Voting System (FR-009 to FR-018)
- **FR-009**: System MUST allow users to upvote papers
- **FR-010**: System MUST allow users to downvote papers
- **FR-011**: System MUST allow users to remove their vote (toggle off)
- **FR-012**: System MUST allow users to change vote from upvote to downvote and vice versa
- **FR-013**: System MUST store vote count as an integer (can be negative, zero, or positive)
- **FR-014**: System MUST display upvote and downvote buttons on paper detail page
- **FR-015**: System MUST display total vote score in the metrics block on paper detail page
- **FR-016**: System MUST track individual user votes to prevent duplicate voting from same user
- **FR-017**: System MUST visually indicate active vote state (which button user has pressed)
- **FR-018**: System MUST require user authentication (login) to cast votes

#### Hype Score Enhancement (FR-019 to FR-021)
- **FR-019**: System MUST incorporate vote count into hype score calculation using logarithmic scaling
- **FR-020**: System MUST ensure hype score never goes below zero even if votes are negative
- **FR-021**: System MUST use formula: Hype Score = (citation_growth * 0.35) + (star_growth * 0.35) + (absolute_metrics * 0.20) + (vote_component * 0.10), where vote_component = log(1 + max(0, votes)) * 5

#### Paper Detail Page Content (FR-022 to FR-030)
- **FR-022**: System MUST display author affiliation information for each author on paper detail page
- **FR-023**: System MUST provide a "Quick Summary" section on paper detail page
- **FR-024**: System MUST provide a "Key Ideas" section on paper detail page
- **FR-025**: System MUST provide a "Quantitative Performance" section showing numerical results
- **FR-026**: System MUST provide a "Qualitative Performance" section showing descriptive results
- **FR-027**: System MUST provide a "Limitations" section on paper detail page
- **FR-028**: System MUST store Quick Summary, Key Ideas, Performance, and Limitations data in the database
- **FR-029**: Paper detail page MUST display four metric cards: Citations, GitHub Stars, Hype Score, and Vote Score
- **FR-030**: System MUST allow these content sections to be empty/unpopulated initially (to be filled later)

#### Author Management (FR-031 to FR-039)
- **FR-031**: System MUST create individual author records in the authors table
- **FR-032**: System MUST store author name for each author
- **FR-033**: System MUST store author affiliation for each author
- **FR-034**: System MUST track total citation count per author (sum of citations from all their papers)
- **FR-035**: System MUST store reference to the author's latest paper
- **FR-036**: System MUST track total number of papers per author in the database
- **FR-037**: System MUST store author email address (when available)
- **FR-038**: System MUST store author personal website URL (when available)
- **FR-039**: System MUST use name + affiliation combination to uniquely identify authors with identical names

#### Author Display and Interaction (FR-040 to FR-042)
- **FR-040**: System MUST allow users to click on author names in paper lists to view author information
- **FR-041**: System MUST allow users to click on author names in paper detail page to view author information
- **FR-042**: Author information display MUST show: name, affiliation, total citations, paper count, email (if available), and website (if available)

#### Quick Actions Enhancement (FR-043 to FR-045)
- **FR-043**: Paper detail page MUST provide a "Start Crawling from This Paper" button in the Quick Actions section
- **FR-044**: When clicked, system MUST navigate user to the crawler page
- **FR-045**: Crawler page MUST pre-fill with: citation network crawl type selected, and current paper ID populated

#### Metric Tracking Graphs (FR-046 to FR-049)
- **FR-046**: System MUST display time-series graphs for each tracked metric (citations, GitHub stars, votes, hype score)
- **FR-047**: Graphs MUST show daily snapshots (one data point per day)
- **FR-048**: System MUST record daily snapshots of all metrics for each paper
- **FR-049**: Graphs MUST be interactive with tooltips showing exact date and value on hover

### Key Entities

#### Paper (Extended)
- Existing paper entity with new attributes:
  - **vote_count**: Integer representing net votes (upvotes minus downvotes)
  - **quick_summary**: Text field for brief paper summary
  - **key_ideas**: Text field for main contributions
  - **quantitative_performance**: Structured data for numerical results
  - **qualitative_performance**: Text field for descriptive results
  - **limitations**: Text field for paper limitations

#### Author
- Represents individual researchers:
  - **name**: Author's full name
  - **affiliation**: Current institutional affiliation
  - **total_citation_count**: Sum of citations from all their papers in database
  - **latest_paper_id**: Reference to their most recent paper
  - **paper_count**: Number of papers they've authored in the database
  - **email**: Contact email (optional)
  - **website_url**: Personal or lab website (optional)

#### Vote
- Represents user votes on papers:
  - **paper_id**: Reference to the voted paper
  - **user_identifier**: Unique identifier for the voting user
  - **vote_type**: Upvote (+1) or downvote (-1)
  - **timestamp**: When vote was cast

#### MetricSnapshot (Extended)
- Daily tracking of paper metrics:
  - **paper_id**: Reference to paper
  - **snapshot_date**: Date of snapshot
  - **citation_count**: Citations on that date
  - **github_stars**: Stars on that date (if repo exists)
  - **vote_count**: Net votes on that date
  - **hype_score**: Calculated hype score on that date

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain (all 5 items clarified)
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

### Clarifications Provided (All Resolved)
1. **Publication date versions**: ✅ Use latest version date for papers with multiple arXiv versions
2. **URL length handling**: ✅ URLs not expected to be excessively long, no truncation needed
3. **Authentication for voting**: ✅ Users must be logged in to vote (authentication required)
4. **Author disambiguation**: ✅ Use name + affiliation combination to distinguish authors
5. **Hype score formula**: ✅ Use logarithmic scaling with vote_component = log(1 + max(0, votes)) * 5, weighted at 10% in overall score

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (5 clarification items)
- [x] User scenarios defined (12 acceptance scenarios)
- [x] Requirements generated (49 functional requirements)
- [x] Entities identified (4 key entities)
- [x] Clarifications received and incorporated
- [x] Review checklist passed

---

## Next Steps

1. ✅ **All clarifications provided** - Spec is now complete and unambiguous
2. **Ready for `/plan` phase** - Proceed with implementation design
3. Implementation will include:
   - Database schema updates for new fields (vote_count, quick_summary, key_ideas, etc.)
   - Author table population and management
   - Voting system with authentication
   - Enhanced hype score calculation with logarithmic vote scaling
   - URL hyperlinking in abstracts
   - Time-series metric graphs
   - Enhanced paper detail page UI
4. **Future phase**: Implement AI/LLM-based content generation for Quick Summary, Key Ideas, Performance, and Limitations sections (will be separate feature)
