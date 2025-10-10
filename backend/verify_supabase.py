"""Verify Supabase connection and check if tables exist."""
import asyncio
import asyncpg
import os

async def check_supabase():
    # Connection string from .env
    conn_str = "postgresql://postgres.zvesxmkgkldorxlbyhce:dlgPwls181920@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"

    print(f"Connecting to Supabase...")
    print(f"Host: aws-1-ap-northeast-2.pooler.supabase.com")
    print(f"Database: postgres")
    print()

    try:
        conn = await asyncpg.connect(conn_str)

        # List all tables
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        print(f"✓ Connected to Supabase successfully!")
        print(f"\nTables in 'public' schema:")
        if tables:
            for table in tables:
                print(f"  - {table['table_name']}")
        else:
            print("  (no tables found)")

        # Check for papers table
        papers_count = await conn.fetchval("SELECT COUNT(*) FROM papers;") if any(t['table_name'] == 'papers' for t in tables) else 0
        print(f"\n✓ Papers count: {papers_count}")

        await conn.close()

    except Exception as e:
        print(f"✗ Error connecting to Supabase: {e}")
        print(f"\nThis means your app is NOT using Supabase - it's using a different database!")

if __name__ == "__main__":
    asyncio.run(check_supabase())
