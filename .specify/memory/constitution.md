<!--
Sync Impact Report:
- Version change: none → 1.0.0
- Initial constitution creation for HypePaper project
- Focused on product purpose and problem-solving
- Principles established around simplicity, speed, and user value
- Templates status:
  ✅ plan-template.md - aligned with constitution check requirements
  ✅ spec-template.md - aligned with requirements structure
  ✅ tasks-template.md - aligned with test-first approach
- No follow-up TODOs
-->

# HypePaper Constitution

## Purpose & Problem

### What HypePaper Is
A real-time research paper tracking system that surfaces trending papers using
novel metrics (GitHub stars, citations) that other platforms don't combine.

### Problem Being Solved
Researchers waste hours on tedious googling and manual tracking of new papers in
their domains. Existing solutions are either too complex (full AI agentic systems)
or miss the signal (don't track GitHub hype as a quality indicator).

### Why This Matters
- **Time savings**: Eliminate repetitive paper discovery work
- **Better signal**: GitHub stars + citations reveal papers that are both
  theoretically sound AND practically useful
- **Domain focus**: Users get papers relevant to their specific interests, not
  noise

### Success Criteria
- Users can see trending papers in their domain within seconds of visiting
- Papers ranked by combined hype score (GitHub stars + other metrics)
- Simple, fast, no bloat - not an AI assistant, just a tracker

## Core Principles

### I. Simple, Small, Fast (NON-NEGOTIABLE)
HypePaper does ONE thing well: surface trending papers. MUST:
- Start with MVP: trending papers grouped by user interest
- Reject feature creep - no AI chat, no note-taking, no collaboration
- Fast load times (<2s to see trending papers)
- Simple UI - show papers, scores, trends. Nothing else.

**Rationale**: Complexity killed existing solutions. Users want speed and signal,
not another bloated research assistant.

### II. Novel Metrics Drive Value
The core differentiator is combining metrics others ignore. MUST:
- GitHub stars as primary hype indicator (papers with code = practical impact)
- Mix citation counts, recency, and growth rate
- Make the scoring algorithm transparent and adjustable
- Surface papers that are both cited AND implemented

**Rationale**: GitHub stars reveal which papers developers actually use. This is
the unique value proposition - don't dilute it.

### III. User Interest First
Features exist only if they serve user-defined interests. MUST:
- Allow users to define their domains/topics clearly
- Group and filter papers by these interests
- No algorithmic "suggestions" that ignore user preferences
- Let users control what they track

**Rationale**: Users know their domains better than any algorithm. Respect that.

### IV. Real-Time, Not Stale
Trending means current. Papers and scores MUST be:
- Updated frequently (at least daily for trending papers)
- Show time-based trends (rising this week, month, etc.)
- Surface new papers quickly (within 24-48 hours of publication)

**Rationale**: Stale data is useless for tracking trends. This is "HypePaper",
not "Archive Paper".

### V. Reproducible Scoring
Users must trust the hype scores. MUST:
- Document scoring algorithm clearly
- Make scores auditable (show components: stars, citations, recency)
- Version the scoring algorithm
- Allow users to understand why a paper ranks high

**Rationale**: Opaque ranking destroys trust. Transparency builds credibility.

## Development Constraints

### Technology Choices
- Optimize for fast development and iteration (MVP first)
- Choose boring, proven tech over bleeding-edge
- Minimize dependencies
- Prioritize page load speed and API response time

### Scope Boundaries
**IN SCOPE for MVP:**
- Trending papers list
- User interest grouping
- Hype score calculation (GitHub stars + citations)
- Basic filtering/sorting

**OUT OF SCOPE (explicitly rejected for MVP):**
- AI chat or paper summarization
- Note-taking features
- Collaboration tools
- Paper recommendations beyond trending
- User accounts (unless required for interests)

### Quality Gates
- Page load < 2 seconds
- Hype scores update at least daily
- No broken links to papers
- Mobile-responsive (users browse on phones)

## Governance

### Amendment Process
1. Propose change with rationale in constitution.md
2. Discuss impact on existing work
3. Update version following semantic versioning
4. Update dependent templates and documentation
5. Commit with clear message

### Version Policy
- **MAJOR**: Principle removal or fundamental redefinition
- **MINOR**: New principle added or expanded guidance
- **PATCH**: Clarifications, wording fixes, non-semantic updates

### Compliance
- All feature specs and plans reference current constitution version
- Constitution check in plan-template.md enforces compliance
- Regular reviews to ensure principles remain relevant

### Living Document
This constitution should evolve with the project. If a principle consistently
conflicts with productive research, it should be amended or removed rather than
ignored.

**Version**: 1.0.0 | **Ratified**: 2025-10-01 | **Last Amended**: 2025-10-01
