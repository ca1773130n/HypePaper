#!/bin/bash

echo "🔍 Supabase Connection String Builder"
echo "====================================="
echo ""
echo "Let's build your DATABASE_URL step by step."
echo ""

# Step 1: Get project reference
echo "Step 1: What is your Supabase Project Reference?"
echo "  (Find this in Supabase Dashboard → Settings → General → Reference ID)"
echo "  Example: abcdefghijklmnop"
echo ""
read -p "Project Reference: " PROJECT_REF

if [ -z "$PROJECT_REF" ]; then
    echo "❌ Project reference cannot be empty"
    exit 1
fi

# Step 2: Get password
echo ""
echo "Step 2: What is your database password?"
echo "  (Find this in Supabase Dashboard → Settings → Database)"
echo "  Note: If you don't know it, you can reset it in the dashboard"
echo ""
read -s -p "Password: " PASSWORD
echo ""

if [ -z "$PASSWORD" ]; then
    echo "❌ Password cannot be empty"
    exit 1
fi

# Step 3: Encode password
echo ""
echo "Step 3: Encoding password..."
ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote_plus('$PASSWORD'))")
echo "  Original: $PASSWORD"
echo "  Encoded: $ENCODED_PASSWORD"

# Step 4: Build DATABASE_URL
echo ""
echo "Step 4: Building DATABASE_URL..."
DATABASE_URL="postgresql+asyncpg://postgres:${ENCODED_PASSWORD}@db.${PROJECT_REF}.supabase.co:5432/postgres"

echo ""
echo "✅ Your DATABASE_URL:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$DATABASE_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 5: Test connection
echo ""
echo "Step 5: Testing connection..."
python3 << EOF
import asyncio
import asyncpg

async def test():
    try:
        url = "$DATABASE_URL".replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(url)
        version = await conn.fetchval('SELECT version()')
        print("✅ Connection successful!")
        print(f"   PostgreSQL: {version[:80]}...")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("")
        print("Troubleshooting:")
        print("  1. Verify Project Reference is correct (Settings → General → Reference ID)")
        print("  2. Verify database password (Settings → Database)")
        print("  3. Check if Supabase project is active (green status in dashboard)")
        print("  4. Try resetting database password to something simple: HypePaper2024")
        return False

import sys
success = asyncio.run(test())
sys.exit(0 if success else 1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Connection works! Now running migration..."
    echo ""

    export DATABASE_URL="$DATABASE_URL"
    python -m alembic upgrade head

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Migration complete!"
        echo ""
        echo "💾 Save this for future use:"
        echo "   export DATABASE_URL='$DATABASE_URL'"
        echo ""
        echo "Or add to backend/.env:"
        echo "   DATABASE_URL=$DATABASE_URL"
    fi
else
    echo ""
    echo "❌ Migration not run - fix connection issues first"
fi
