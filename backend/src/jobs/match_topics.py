"""Topic matching job.

Matches papers to topics using LLM-based relevance scoring.
Creates PaperTopicMatch records for papers with relevance >= 6.0.
"""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import Paper, PaperTopicMatch, Topic
from ..services import TopicMatchingService


class TopicMatchingJob:
    """Job for matching papers to topics using LLM."""

    def __init__(self):
        """Initialize topic matching job."""
        pass

    async def match_unmatched_papers(self):
        """Match papers that don't have topic assignments yet."""
        print("Starting topic matching job...")

        async with AsyncSessionLocal() as session:
            matching_service = TopicMatchingService(session)

            # Get all topics
            topic_query = select(Topic)
            topic_result = await session.execute(topic_query)
            topics = list(topic_result.scalars().all())

            if not topics:
                print("No topics found in database. Run seed_topics.py first.")
                return

            # Get papers without topic matches
            # Query for papers that don't have any topic matches yet
            subquery = select(PaperTopicMatch.paper_id).distinct()
            paper_query = select(Paper).where(Paper.id.notin_(subquery))

            result = await session.execute(paper_query)
            unmatched_papers = list(result.scalars().all())

            print(f"Found {len(unmatched_papers)} papers to match against {len(topics)} topics...")

            matched_count = 0

            for paper in unmatched_papers:
                try:
                    # Match paper to all topics
                    matches = await matching_service.match_paper_to_topics(
                        paper_id=paper.id,
                        threshold=6.0,
                    )

                    if matches:
                        matched_count += 1
                        print(f"Matched paper '{paper.title[:50]}...' to {len(matches)} topics")

                    if matched_count % 10 == 0:
                        print(f"Processed {matched_count}/{len(unmatched_papers)} papers...")

                except Exception as e:
                    print(f"Error matching paper {paper.id}: {e}")
                    continue

            await session.commit()
            print(f"Topic matching complete: {matched_count} papers matched")

    async def rematch_all_papers(self):
        """Re-match all papers to topics (use sparingly).

        This is useful if topic definitions change or LLM model improves.
        """
        print("Re-matching ALL papers to topics...")

        async with AsyncSessionLocal() as session:
            # Delete existing matches
            await session.execute(
                "DELETE FROM paper_topic_matches"
            )
            await session.commit()

        # Now match all papers
        await self.match_unmatched_papers()

    async def run(self, rematch_all: bool = False):
        """Run the topic matching job.

        Args:
            rematch_all: If True, delete existing matches and re-match all papers
        """
        if rematch_all:
            await self.rematch_all_papers()
        else:
            await self.match_unmatched_papers()


async def run_topic_matching_job(rematch_all: bool = False):
    """Entry point for running the topic matching job.

    Args:
        rematch_all: If True, re-match all papers (default False)
    """
    job = TopicMatchingJob()
    await job.run(rematch_all=rematch_all)


if __name__ == "__main__":
    import sys

    rematch = "--rematch-all" in sys.argv
    asyncio.run(run_topic_matching_job(rematch_all=rematch))
