"""Update venue field for existing papers from arXiv."""
import asyncio
from sqlalchemy import select
from src.database import AsyncSessionLocal
from src.models import Paper
from src.services.arxiv_service import AsyncArxivService


async def update_paper_venues():
    """Update venue field for papers that don't have one."""
    arxiv_service = AsyncArxivService()
    
    async with AsyncSessionLocal() as db:
        # Get papers without venue
        result = await db.execute(
            select(Paper).where(Paper.venue.is_(None), Paper.arxiv_id.isnot(None))
        )
        papers = result.scalars().all()
        
        print(f"Found {len(papers)} papers without venue")
        
        for i, paper in enumerate(papers, 1):
            try:
                # Search by arxiv ID
                papers_data = await arxiv_service.search_by_arxiv_id(paper.arxiv_id)
                
                if papers_data:
                    paper_data = papers_data[0]
                    
                    # Extract venue
                    venue = paper_data.get("journal_ref")
                    if not venue and paper_data.get("primary_category"):
                        venue = paper_data.get("primary_category")
                    
                    if venue:
                        paper.venue = venue
                        print(f"[{i}/{len(papers)}] Updated {paper.title[:50]} -> {venue}")
                
                # Rate limiting
                if i % 10 == 0:
                    await db.commit()
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"Error updating {paper.arxiv_id}: {e}")
                continue
        
        await db.commit()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(update_paper_venues())
