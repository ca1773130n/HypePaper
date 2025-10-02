"""Daily paper discovery job.

Fetches papers from arXiv, cross-references with Papers With Code,
and stores them in the database.
"""
import asyncio
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal
from ..services import PaperService
from .arxiv_client import ArxivClient
from .paperwithcode_client import PapersWithCodeClient


class PaperDiscoveryJob:
    """Job for discovering new research papers."""

    # arXiv categories to monitor
    CATEGORIES = [
        "cs.CV",  # Computer Vision
        "cs.LG",  # Machine Learning
        "cs.AI",  # Artificial Intelligence
        "cs.GR",  # Graphics
        "cs.RO",  # Robotics
    ]

    def __init__(self):
        """Initialize discovery job."""
        self.arxiv_client = ArxivClient()
        self.pwc_client = PapersWithCodeClient()

    async def discover_papers(self, days: int = 7, max_per_category: int = 50):
        """Discover papers from the last N days.

        Args:
            days: Number of days to look back (default 7)
            max_per_category: Max papers per category (default 50)
        """
        print(f"Starting paper discovery job (last {days} days)...")

        # Fetch papers from arXiv
        arxiv_papers = await self.arxiv_client.get_recent_papers(
            categories=self.CATEGORIES,
            days=days,
            max_per_category=max_per_category,
        )

        print(f"Found {len(arxiv_papers)} papers from arXiv")

        # Cross-reference with Papers With Code for GitHub links
        arxiv_ids = [p["arxiv_id"] for p in arxiv_papers]
        github_urls = await self.pwc_client.batch_get_github_urls(arxiv_ids)

        # Add GitHub URLs to papers
        for paper in arxiv_papers:
            arxiv_id = paper["arxiv_id"]
            if arxiv_id in github_urls:
                paper["github_url"] = github_urls[arxiv_id]

        # Store papers in database
        async with AsyncSessionLocal() as session:
            paper_service = PaperService(session)
            stored_count = 0

            for paper_data in arxiv_papers:
                try:
                    # Check if paper already exists
                    existing = await paper_service.get_paper_by_arxiv_id(
                        paper_data["arxiv_id"]
                    )

                    if existing:
                        continue  # Skip if already in database

                    # Create paper
                    await paper_service.create_paper(
                        {
                            "arxiv_id": paper_data["arxiv_id"],
                            "doi": paper_data.get("doi"),
                            "title": paper_data["title"],
                            "authors": paper_data["authors"],
                            "abstract": paper_data["abstract"],
                            "published_date": paper_data["published_date"],
                            "venue": paper_data.get("category"),
                            "github_url": paper_data.get("github_url"),
                            "arxiv_url": paper_data.get("arxiv_url"),
                            "pdf_url": paper_data.get("pdf_url"),
                        }
                    )
                    stored_count += 1

                except Exception as e:
                    print(f"Error storing paper {paper_data['arxiv_id']}: {e}")
                    continue

            await session.commit()
            print(f"Stored {stored_count} new papers")

    async def run(self):
        """Run the paper discovery job."""
        try:
            await self.discover_papers()
        finally:
            await self.arxiv_client.close()
            await self.pwc_client.close()


async def run_discovery_job():
    """Entry point for running the paper discovery job."""
    job = PaperDiscoveryJob()
    await job.run()


if __name__ == "__main__":
    asyncio.run(run_discovery_job())
