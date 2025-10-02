"""Daily metric update job.

Fetches GitHub stars and citation counts for all tracked papers,
creates MetricSnapshot records.
"""
import asyncio
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..models import Paper
from ..services import MetricService
from .github_client import GitHubClient
from .semanticscholar_client import SemanticScholarClient


class MetricUpdateJob:
    """Job for updating paper metrics daily."""

    def __init__(self):
        """Initialize metric update job."""
        self.github_client = GitHubClient()
        self.scholar_client = SemanticScholarClient()

    async def update_metrics_for_papers(self):
        """Update metrics for all papers in the database."""
        print("Starting metric update job...")

        async with AsyncSessionLocal() as session:
            metric_service = MetricService(session)

            # Get all papers
            query = select(Paper)
            result = await session.execute(query)
            papers = list(result.scalars().all())

            print(f"Updating metrics for {len(papers)} papers...")

            snapshot_date = date.today()
            updated_count = 0

            for paper in papers:
                try:
                    # Check if snapshot already exists for today
                    existing = await metric_service.get_metric_at_date(
                        paper.id, snapshot_date
                    )
                    if existing:
                        continue  # Skip if already updated today

                    # Fetch GitHub stars
                    github_stars = None
                    if paper.github_url:
                        github_stars = await self.github_client.get_star_count(
                            paper.github_url
                        )

                    # Fetch citation count
                    citation_count = await self.scholar_client.get_citation_count(
                        arxiv_id=paper.arxiv_id,
                        doi=paper.doi,
                    )

                    # Create metric snapshot
                    await metric_service.create_metric_snapshot(
                        paper_id=paper.id,
                        snapshot_date=snapshot_date,
                        github_stars=github_stars,
                        citation_count=citation_count,
                    )

                    updated_count += 1

                    if updated_count % 10 == 0:
                        print(f"Updated {updated_count}/{len(papers)} papers...")

                except Exception as e:
                    print(f"Error updating metrics for paper {paper.id}: {e}")
                    continue

            await session.commit()
            print(f"Completed metric update: {updated_count} papers updated")

    async def run(self):
        """Run the metric update job."""
        try:
            await self.update_metrics_for_papers()
        finally:
            await self.github_client.close()
            await self.scholar_client.close()


async def run_metric_update_job():
    """Entry point for running the metric update job."""
    job = MetricUpdateJob()
    await job.run()


if __name__ == "__main__":
    asyncio.run(run_metric_update_job())
