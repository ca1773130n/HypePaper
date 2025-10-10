"""Check database connection and count papers."""
import asyncio
from src.database import AsyncSessionLocal
from sqlalchemy import text

async def check_db():
    async with AsyncSessionLocal() as db:
        # Check if papers table exists
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'papers'
            );
        """))
        table_exists = result.scalar()
        print(f"Papers table exists: {table_exists}")

        if table_exists:
            # Count papers
            result = await db.execute(text("SELECT COUNT(*) FROM papers;"))
            count = result.scalar()
            print(f"Total papers in database: {count}")

            # Show sample
            result = await db.execute(text("SELECT id, title FROM papers LIMIT 3;"))
            papers = result.fetchall()
            print("\nSample papers:")
            for paper in papers:
                print(f"  - {paper[0]}: {paper[1][:60]}...")
        else:
            print("\n❌ Papers table does NOT exist in the database!")
            print("You need to run database migrations.")

if __name__ == "__main__":
    asyncio.run(check_db())
