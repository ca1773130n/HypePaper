"""PaperTopicMatch model for paper-topic relationships.

Junction table linking papers to topics with relevance scores.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PaperTopicMatch(Base):
    """Paper-to-topic match with relevance score.

    Many-to-many junction table linking papers and topics.

    Fields:
    - id: Internal UUID identifier
    - paper_id: Reference to paper
    - topic_id: Reference to topic
    - relevance_score: LLM-generated relevance (0.0-10.0)
    - matched_at: Match creation timestamp
    - matched_by: "llm" or "manual" (future manual curation)

    Constraints:
    - Unique (paper_id, topic_id) - one match per pair
    - relevance_score between 0.0 and 10.0
    - Only include matches with relevance_score >= 6.0

    Indexes:
    - Composite (topic_id, relevance_score DESC) for fast topic filtering
    """

    __tablename__ = "paper_topic_matches"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default="gen_random_uuid()",
    )

    # Foreign keys
    paper_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Match metadata
    relevance_score: Mapped[float] = mapped_column(nullable=False)
    matched_at: Mapped[datetime] = mapped_column(
        server_default="NOW()", nullable=False
    )
    matched_by: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="'llm'"
    )

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="topic_matches")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="paper_matches")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("paper_id", "topic_id", name="unique_paper_topic_pair"),
        CheckConstraint(
            "relevance_score >= 0.0 AND relevance_score <= 10.0",
            name="relevance_score_range",
        ),
        CheckConstraint(
            "relevance_score >= 6.0",
            name="relevance_score_threshold",
        ),
        CheckConstraint(
            "matched_by IN ('llm', 'manual')",
            name="matched_by_valid_values",
        ),
        # Composite index for fast topic filtering sorted by relevance
        Index(
            "idx_paper_topic_matches_topic",
            "topic_id",
            "relevance_score",
            postgresql_ops={"relevance_score": "DESC"},
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<PaperTopicMatch(paper_id={self.paper_id}, "
            f"topic_id={self.topic_id}, score={self.relevance_score:.1f})>"
        )
