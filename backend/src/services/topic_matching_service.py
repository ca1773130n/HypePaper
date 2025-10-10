"""TopicMatchingService for LLM-based paper-topic matching.

Uses local LLM (llama.cpp) to calculate relevance scores between papers and topics.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Paper, PaperTopicMatch, Topic


class TopicMatchingService:
    """Service for matching papers to topics using LLM.

    For MVP, this is a stub implementation.
    Real implementation will use llama.cpp with a quantized 7B model.
    """

    def __init__(self, session: AsyncSession, llm_model_path: Optional[str] = None):
        """Initialize service with database session and LLM model.

        Args:
            session: Database session
            llm_model_path: Path to llama.cpp model file (optional for MVP)
        """
        self.session = session
        self.llm_model_path = llm_model_path
        self.llm = None  # Will be initialized when needed

    def _load_llm_model(self):
        """Load LLM model using llama.cpp.

        Deferred for MVP - will be implemented in Phase 3.5.
        """
        # TODO: Implement llama.cpp model loading
        # from llama_cpp import Llama
        # self.llm = Llama(model_path=self.llm_model_path, n_ctx=2048)
        pass

    async def calculate_relevance(
        self,
        paper: Paper,
        topic: Topic,
    ) -> float:
        """Calculate relevance score between paper and topic.

        Uses LLM to analyze paper abstract and title against topic.

        Args:
            paper: Paper entity
            topic: Topic entity

        Returns:
            Relevance score (0.0-10.0)
        """
        # MVP stub: Return fixed score for testing
        # Real implementation will use LLM prompt:
        # "Rate the relevance of this paper to the topic on a scale of 0-10.
        #  Paper: {title}\n{abstract}
        #  Topic: {topic.name} - {topic.description}
        #  Score:"

        # For MVP, use simple keyword matching as placeholder
        score = self._keyword_matching_fallback(paper, topic)
        return score

    def _keyword_matching_fallback(
        self,
        paper: Paper,
        topic: Topic,
    ) -> float:
        """Simple keyword matching fallback for MVP.

        Args:
            paper: Paper entity
            topic: Topic entity

        Returns:
            Relevance score (0.0-10.0)
        """
        # Convert to lowercase for matching
        paper_text = (
            f"{paper.title.lower()} {paper.abstract.lower()}"
        )
        topic_name = topic.name.lower()

        # Check if topic name appears in paper
        if topic_name in paper_text:
            return 8.0  # High relevance if exact match

        # Check keywords if available
        if topic.keywords:
            matches = sum(
                1 for keyword in topic.keywords
                if keyword.lower() in paper_text
            )
            if matches > 0:
                # Score based on keyword matches (max 10.0)
                return min(10.0, 6.0 + (matches * 0.5))

        return 5.0  # Neutral score as fallback

    async def match_paper_to_topics(
        self,
        paper_id: UUID,
        topic_ids: Optional[list[UUID]] = None,
        threshold: float = 6.0,
    ) -> list[PaperTopicMatch]:
        """Match a paper to topics and create matches.

        Args:
            paper_id: Paper UUID
            topic_ids: List of topic UUIDs to match against (None = all topics)
            threshold: Minimum relevance score for match (default 6.0)

        Returns:
            List of created PaperTopicMatch entities
        """
        from .paper_service import PaperService
        from .topic_service import TopicService

        paper_service = PaperService(self.session)
        topic_service = TopicService(self.session)

        # Get paper
        paper = await paper_service.get_paper_by_id(paper_id)
        if not paper:
            return []

        # Get topics to match
        if topic_ids:
            topics = [
                await topic_service.get_topic_by_id(tid)
                for tid in topic_ids
            ]
            topics = [t for t in topics if t is not None]
        else:
            # Match against all topics
            topics_data = await topic_service.get_all_topics()
            topics = [
                await topic_service.get_topic_by_id(UUID(t["id"]))
                for t in topics_data
            ]
            topics = [t for t in topics if t is not None]

        # Calculate relevance and create matches
        matches = []
        for topic in topics:
            relevance_score = await self.calculate_relevance(paper, topic)

            if relevance_score >= threshold:
                match = PaperTopicMatch(
                    paper_id=paper_id,
                    topic_id=topic.id,
                    relevance_score=relevance_score,
                    matched_by="llm",
                )
                self.session.add(match)
                matches.append(match)

        await self.session.flush()
        return matches
