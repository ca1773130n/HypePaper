"""Vote model for user votes on papers.

Represents individual user votes (upvote/downvote) on papers.
"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .paper import Paper


class Vote(Base):
    """User vote on a paper (upvote or downvote).

    Composite primary key (user_id, paper_id) ensures one vote per user per paper.
    Users can change their vote type (upvote ↔ downvote) by updating the record.
    """

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

    def __repr__(self) -> str:
        """String representation."""
        return f"<Vote(user={self.user_id}, paper={self.paper_id}, type={self.vote_type})>"
