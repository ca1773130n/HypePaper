#!/bin/bash

# Script to migrate database schema to Supabase
# This ensures migrations run against Supabase, not local database

echo "🚀 HypePaper - Supabase Database Migration"
echo "==========================================="
echo ""

# Check if DATABASE_URL is provided
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    echo ""
    echo "Please provide your Supabase DATABASE_URL:"
    echo ""
    echo "Format:"
    echo "  postgresql+asyncpg://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres"
    echo ""
    echo "If your password has special characters (!@#$%), encode them first:"
    echo "  python3 -c \"import urllib.parse; print(urllib.parse.quote_plus('YOUR_PASSWORD'))\""
    echo ""
    echo "Then run:"
    echo "  export DATABASE_URL='postgresql+asyncpg://postgres:ENCODED_PASSWORD@db.xxx.supabase.co:5432/postgres'"
    echo "  ./migrate_to_supabase.sh"
    echo ""
    exit 1
fi

echo "📋 Configuration:"
echo "  DATABASE_URL: ${DATABASE_URL:0:50}..."
echo ""

# Test connection first
echo "🔍 Testing Supabase connection..."
python3 << EOF
import asyncio
import asyncpg
import sys

async def test_connection():
    try:
        # Extract connection params from DATABASE_URL
        url = "$DATABASE_URL"
        # Remove postgresql+asyncpg:// prefix
        url = url.replace("postgresql+asyncpg://", "postgresql://")

        conn = await asyncpg.connect(url)
        version = await conn.fetchval('SELECT version()')
        print(f"✅ Connected to Supabase!")
        print(f"   PostgreSQL version: {version[:50]}...")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("")
        print("Common issues:")
        print("  1. Password not URL-encoded (use: python3 -c \"import urllib.parse; print(urllib.parse.quote_plus('PASSWORD'))\")")
        print("  2. Wrong project reference (check Supabase dashboard)")
        print("  3. Database not ready (wait a minute and try again)")
        return False

success = asyncio.run(test_connection())
sys.exit(0 if success else 1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Cannot proceed with migration - connection test failed"
    exit 1
fi

echo ""
echo "🔄 Running Alembic migrations..."
python -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration complete!"
    echo ""
    echo "🔍 Verifying tables in Supabase..."

    python3 << EOF
import asyncio
import asyncpg

async def check_tables():
    url = "$DATABASE_URL".replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)

    tables = await conn.fetch("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    print("")
    print("Tables created in Supabase:")
    for table in tables:
        print(f"  ✓ {table['table_name']}")

    await conn.close()

asyncio.run(check_tables())
EOF

    echo ""
    echo "✅ All done! Check your Supabase SQL Editor to see the tables."
    echo ""
else
    echo ""
    echo "❌ Migration failed. Check the error messages above."
    exit 1
fi
