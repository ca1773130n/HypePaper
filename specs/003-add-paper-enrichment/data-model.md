# Data Model: Paper Enrichment Feature

**Feature**: 003-add-paper-enrichment
**Date**: 2025-10-11
**Status**: Design Complete

## Overview

This document defines the database schema changes required for the paper enrichment feature. It extends existing models and introduces new entities to support voting, enhanced author tracking, and time-series metrics.

## Entity Relationship Diagram

```
┌─────────────┐       ┌──────────────┐       ┌─────────────────┐
│   Users     │       │    Votes     │       │     Papers      │
│ (Supabase)  │───────│              │───────│                 │
│             │ 1   * │ PK: (user,   │ *   1 │ PK: id (UUID)   │
│ - id (UUID) │       │     paper)   │       │ + vote_count    │
└─────────────┘       │ - vote_type  │       │ + quick_summary │
                      │ - created_at │       │ + key_ideas     │
                      │ - updated_at │       │ + limitations   │
                      └──────────────┘       │ + quant_perf    │
                                             │ + qual_perf     │
                                             └────────┬────────┘
                                                      │ 1
                                                      │
                                                      │ *
                                        ┌──────────────────────────┐
                                        │   PaperAuthor (junction) │
                                        │ PK: (paper_id, author_id)│
                                        │ - position               │
                                        │ - affiliation_snapshot   │
                                        └─────────────┬────────────┘
                                                      │ *
                                                      │
                                                      │ 1
                                             ┌────────┴──────────┐
                                             │     Authors       │
                                             │ PK: id (int)      │
                                             │ - name            │
                                             │ + total_citations │
                                             │ + latest_paper_id │
                                             │ + email           │
                                             │ + website_url     │
                                             └───────────────────┘

┌──────────────────┐
│ MetricSnapshots  │
│ PK: (paper_id,   │──────┐
│     date)        │      │ * Papers (1)
│ - github_stars   │      │
│ - citation_count │      │
│ + vote_count     │◄─────┘
│ + hype_score     │
└──────────────────┘
```

## Model 1: Vote (NEW)

### Purpose
Track individual user votes on papers. Supports upvote/downvote with ability to change vote.

### Schema
```python
class Vote(Base):
    __tablename__ = "votes"

    # Composite primary key
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Supabase auth user ID"
    )

    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
        comment="Paper being voted on"
    )

    # Vote type
    vote_type: Mapped[str] = mapped_column(
        Enum("upvote", "downvote", name="vote_type_enum"),
        nullable=False,
        comment="Vote direction: upvote or downvote"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        nullable=False,
        comment="When vote was first cast"
    )

    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
        nullable=False,
        comment="When vote was last changed"
    )

    # Relationships
    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="votes",
        foreign_keys=[paper_id]
    )

    # Indexes
    __table_args__ = (
        Index("idx_votes_paper", "paper_id"),
        Index("idx_votes_user", "user_id"),
    )
```

### Validation Rules
- ✅ **Primary Key Enforcement**: Composite `(user_id, paper_id)` prevents duplicate votes per user
- ✅ **Vote Type Validation**: Enum constraint ensures only 'upvote' or 'downvote' values
- ✅ **Cascade Deletion**: Votes deleted when paper or user is deleted
- ✅ **Timestamp Tracking**: `updated_at` tracks vote changes (upvote → downvote)

### State Transitions
```
No Vote → Upvote    (INSERT vote_type='upvote')
No Vote → Downvote  (INSERT vote_type='downvote')
Upvote → Downvote   (UPDATE vote_type='downvote')
Downvote → Upvote   (UPDATE vote_type='upvote')
Upvote → No Vote    (DELETE)
Downvote → No Vote  (DELETE)
```

### Related Requirements
- FR-009: System MUST allow users to upvote papers
- FR-010: System MUST allow users to downvote papers
- FR-011: System MUST allow users to remove their vote
- FR-012: System MUST allow users to change vote type
- FR-016: System MUST track individual user votes
- FR-018: System MUST require user authentication

## Model 2: Paper (EXTENDED)

### Changes
Extend existing `Paper` model with new fields for votes and content enrichment.

### New Fields
```python
class Paper(Base):
    # ... existing fields ...

    # Vote tracking
    vote_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Net votes (upvotes - downvotes), denormalized for performance"
    )

    # Content enrichment fields
    quick_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Brief paper summary (1-2 sentences)"
    )

    key_ideas: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Main contributions and key ideas"
    )

    quantitative_performance: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Numerical results: {metric: value, baseline: value}"
    )

    qualitative_performance: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descriptive performance results"
    )

    # Note: limitations field already exists in current schema

    # Relationships (NEW)
    votes: Mapped[list["Vote"]] = relationship(
        "Vote",
        back_populates="paper",
        cascade="all, delete-orphan",
        doc="User votes on this paper"
    )
```

### Indexes
```python
# Add to __table_args__
Index("idx_papers_vote_count", "vote_count", postgresql_ops={"vote_count": "DESC"}),
```

### Validation Rules
- ✅ **Vote Count Range**: Can be negative (more downvotes than upvotes), zero, or positive
- ✅ **Content Fields Optional**: All enrichment fields nullable (to be filled later)
- ✅ **JSONB Structure**: `quantitative_performance` stores key-value pairs

### Computed Properties
```python
@property
def net_votes(self) -> int:
    """Calculate net votes from vote records (for verification)."""
    upvotes = sum(1 for v in self.votes if v.vote_type == "upvote")
    downvotes = sum(1 for v in self.votes if v.vote_type == "downvote")
    return upvotes - downvotes
```

### Related Requirements
- FR-013: System MUST store vote count as integer
- FR-015: System MUST display vote score in metrics block
- FR-022 to FR-028: Content enrichment fields

## Model 3: Author (EXTENDED)

### Changes
Extend existing `Author` model with statistics and contact fields. Remove unique constraint on `name` to allow disambiguation by affiliation.

### Schema Changes
```python
class Author(Base):
    # ... existing fields (name, affiliations, countries, paper_count) ...

    # NEW FIELDS

    # Statistics
    total_citation_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
        comment="Sum of citations from all author's papers"
    )

    latest_paper_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to most recent paper"
    )

    # Contact information
    email: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Author email address"
    )

    website_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Personal or lab website URL"
    )

    # REMOVED: unique=True constraint on name field
    # (To support disambiguation via affiliation)

    # Relationships (NEW)
    latest_paper: Mapped[Optional["Paper"]] = relationship(
        "Paper",
        foreign_keys=[latest_paper_id],
        uselist=False
    )
```

### Indexes
```python
# Add to __table_args__
Index("idx_authors_citation_count", "total_citation_count", postgresql_ops={"total_citation_count": "DESC"}),
Index("idx_authors_paper_count", "paper_count", postgresql_ops={"paper_count": "DESC"}),
```

### Validation Rules
- ✅ **Citation Count Non-Negative**: `total_citation_count >= 0`
- ✅ **Paper Count Non-Negative**: `paper_count >= 0`
- ✅ **Email Format**: Optional email validation at application layer
- ✅ **URL Format**: Optional URL validation at application layer
- ✅ **Name Uniqueness**: REMOVED - allow multiple authors with same name (disambiguated by affiliation)

### Computed Properties
```python
@property
def primary_affiliation(self) -> Optional[str]:
    """Get most recent affiliation."""
    return self.affiliations[0] if self.affiliations else None

@property
def avg_citations_per_paper(self) -> float:
    """Average citations per paper."""
    return self.total_citation_count / self.paper_count if self.paper_count > 0 else 0.0
```

### Related Requirements
- FR-032 to FR-038: Author fields and statistics
- FR-039: Name + affiliation disambiguation

## Model 4: MetricSnapshot (EXTENDED)

### Changes
Add `vote_count` and `hype_score` to daily metric snapshots for time-series tracking.

### New Fields
```python
class MetricSnapshot(Base):
    # ... existing fields (paper_id, snapshot_date, github_stars, citation_count) ...

    # NEW FIELDS

    vote_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Net vote count at time of snapshot"
    )

    hype_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Calculated hype score at time of snapshot"
    )
```

### Validation Rules
- ✅ **Vote Count Range**: Can be negative, zero, or positive
- ✅ **Hype Score Non-Negative**: Ensured at application layer (clamped to >= 0)
- ✅ **Unique Constraint**: Existing `(paper_id, snapshot_date)` remains

### Constraints
```python
# Add to __table_args__
CheckConstraint(
    "hype_score IS NULL OR hype_score >= 0",
    name="hype_score_non_negative"
),
```

### Related Requirements
- FR-046 to FR-049: Time-series metric tracking
- FR-019 to FR-021: Hype score calculation with votes

## Migration Strategy

### Migration 1: Create votes table
```sql
CREATE TYPE vote_type_enum AS ENUM ('upvote', 'downvote');

CREATE TABLE votes (
    user_id UUID NOT NULL,
    paper_id UUID NOT NULL,
    vote_type vote_type_enum NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, paper_id),
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

CREATE INDEX idx_votes_paper ON votes(paper_id);
CREATE INDEX idx_votes_user ON votes(user_id);
```

### Migration 2: Extend papers table
```sql
ALTER TABLE papers
ADD COLUMN vote_count INTEGER NOT NULL DEFAULT 0,
ADD COLUMN quick_summary TEXT NULL,
ADD COLUMN key_ideas TEXT NULL,
ADD COLUMN quantitative_performance JSONB NULL,
ADD COLUMN qualitative_performance TEXT NULL;

CREATE INDEX idx_papers_vote_count ON papers(vote_count DESC);
```

### Migration 3: Extend authors table
```sql
ALTER TABLE authors
DROP CONSTRAINT IF EXISTS authors_name_key,  -- Remove unique constraint on name
ADD COLUMN total_citation_count INTEGER NOT NULL DEFAULT 0,
ADD COLUMN latest_paper_id UUID NULL,
ADD COLUMN email VARCHAR(200) NULL,
ADD COLUMN website_url VARCHAR(500) NULL,
ADD CONSTRAINT fk_authors_latest_paper FOREIGN KEY (latest_paper_id) REFERENCES papers(id) ON DELETE SET NULL;

CREATE INDEX idx_authors_citation_count ON authors(total_citation_count DESC);
CREATE INDEX idx_authors_paper_count ON authors(paper_count DESC);
```

### Migration 4: Extend metric_snapshots table
```sql
ALTER TABLE metric_snapshots
ADD COLUMN vote_count INTEGER NULL,
ADD COLUMN hype_score FLOAT NULL,
ADD CONSTRAINT hype_score_non_negative CHECK (hype_score IS NULL OR hype_score >= 0);
```

### Migration 5: Trigger for vote_count update
```sql
-- Function to update paper vote_count
CREATE OR REPLACE FUNCTION update_paper_vote_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE papers
    SET vote_count = (
        SELECT COALESCE(SUM(CASE WHEN vote_type = 'upvote' THEN 1 ELSE -1 END), 0)
        FROM votes
        WHERE paper_id = COALESCE(NEW.paper_id, OLD.paper_id)
    )
    WHERE id = COALESCE(NEW.paper_id, OLD.paper_id);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger on INSERT, UPDATE, DELETE
CREATE TRIGGER vote_count_trigger
AFTER INSERT OR UPDATE OR DELETE ON votes
FOR EACH ROW EXECUTE FUNCTION update_paper_vote_count();
```

## Data Population Scripts

### Script 1: Populate author statistics
```python
async def populate_author_statistics(db: AsyncSession):
    """Calculate and update author statistics from existing papers."""
    authors = await db.execute(select(Author))

    for author in authors.scalars():
        # Get all papers by this author
        papers = await db.execute(
            select(Paper)
            .join(PaperAuthor)
            .where(PaperAuthor.author_id == author.id)
        )
        papers_list = papers.scalars().all()

        # Calculate statistics
        author.paper_count = len(papers_list)
        author.total_citation_count = sum(p.citation_count for p in papers_list)

        # Find latest paper
        if papers_list:
            latest = max(papers_list, key=lambda p: p.published_date)
            author.latest_paper_id = latest.id

    await db.commit()
```

### Script 2: Initialize vote_count from existing votes (if any)
```python
async def sync_vote_counts(db: AsyncSession):
    """Sync paper vote_count with votes table."""
    papers = await db.execute(select(Paper))

    for paper in papers.scalars():
        votes = await db.execute(
            select(Vote).where(Vote.paper_id == paper.id)
        )
        vote_list = votes.scalars().all()

        upvotes = sum(1 for v in vote_list if v.vote_type == "upvote")
        downvotes = sum(1 for v in vote_list if v.vote_type == "downvote")
        paper.vote_count = upvotes - downvotes

    await db.commit()
```

## Performance Considerations

### Denormalization
- **vote_count on papers**: Avoid `COUNT(*)` on votes table for every paper query
- **total_citation_count on authors**: Avoid `SUM(citation_count)` aggregation on JOIN
- **paper_count on authors**: Avoid `COUNT(*)` on paper_authors table

### Index Strategy
- **votes(paper_id)**: Fast lookup of all votes for a paper
- **votes(user_id)**: Check if user has voted (for vote button state)
- **papers(vote_count DESC)**: Sort papers by vote count
- **authors(total_citation_count DESC)**: Sort authors by citations
- **metric_snapshots(paper_id, snapshot_date)**: Fast time-series queries

### Query Patterns
```sql
-- Get paper with vote count (denormalized)
SELECT * FROM papers WHERE id = $1;

-- Get user's vote on paper
SELECT vote_type FROM votes WHERE user_id = $1 AND paper_id = $2;

-- Get top voted papers
SELECT * FROM papers ORDER BY vote_count DESC LIMIT 20;

-- Get author statistics
SELECT * FROM authors WHERE id = $1;  -- All stats precomputed

-- Get metric time-series
SELECT * FROM metric_snapshots
WHERE paper_id = $1 AND snapshot_date >= $2
ORDER BY snapshot_date ASC;
```

## Data Integrity

### Consistency Checks
1. **Vote count accuracy**: `papers.vote_count` should equal sum of votes
2. **Author paper count**: `authors.paper_count` should equal count in paper_authors
3. **Author citation count**: `authors.total_citation_count` should equal sum of paper citations
4. **Latest paper reference**: `authors.latest_paper_id` should point to valid paper

### Validation Queries
```sql
-- Check vote_count consistency
SELECT p.id, p.vote_count,
       COALESCE(SUM(CASE WHEN v.vote_type = 'upvote' THEN 1 ELSE -1 END), 0) AS actual_votes
FROM papers p
LEFT JOIN votes v ON p.id = v.paper_id
GROUP BY p.id, p.vote_count
HAVING p.vote_count != COALESCE(SUM(CASE WHEN v.vote_type = 'upvote' THEN 1 ELSE -1 END), 0);

-- Check author paper_count consistency
SELECT a.id, a.paper_count, COUNT(pa.paper_id) AS actual_count
FROM authors a
LEFT JOIN paper_authors pa ON a.id = pa.author_id
GROUP BY a.id, a.paper_count
HAVING a.paper_count != COUNT(pa.paper_id);
```

## Approval & Sign-off

**Data Model Complete**: ✅ All entities and relationships defined
**Migration Strategy**: ✅ 5 migrations planned with rollback support
**Performance Optimized**: ✅ Denormalization and indexes in place
**Validation Rules**: ✅ All constraints and checks defined

---
*Data model designed: 2025-10-11*
*Next phase: API Contract Design (contracts/*.yaml)*
