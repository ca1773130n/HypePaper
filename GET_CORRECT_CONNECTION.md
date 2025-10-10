# How to Get the Correct Supabase Connection String

## The Problem

The hostname `db.zvesxmkgkldorxlbyhce.supabase.co` is not resolving, which means either:
- The project reference is incorrect
- The project is paused/not active
- You need to use a different connection format

## Solution: Get Connection String from Supabase Dashboard

### Step 1: Go to Supabase Dashboard

1. Open https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **Database**

### Step 2: Find Connection String

Scroll down to **Connection string** section. You'll see several options:

#### Option A: Connection Pooling (Recommended for serverless)
Look for the connection string that says **"Connection pooling"** or **"Transaction"** mode.

It will look like:
```
postgres://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

#### Option B: Direct Connection
Look for **"Direct connection"** or **"Session"** mode.

It will look like:
```
postgres://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

### Step 3: Copy and Modify for Alembic

**Important**: The connection string from Supabase uses `postgres://` but we need `postgresql+asyncpg://`

**For Connection Pooling (Port 6543):**
```bash
# Supabase gives you:
postgres://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Change to:
postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres?prepared_statement_cache_size=0
```

**For Direct Connection (Port 5432):**
```bash
# Supabase gives you:
postgres://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

# Change to:
postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```

### Step 4: Update Your .env File

Edit `backend/.env` and update DATABASE_URL:

```bash
# Remove the quotes!
DATABASE_URL=postgresql+asyncpg://postgres.YOUR_REF:YOUR_PASSWORD@CORRECT_HOST:PORT/postgres
```

**Important Notes:**
1. ❌ **Don't use quotes** around the URL in .env file
2. ✅ Use the **exact host** from Supabase dashboard
3. ✅ Change `postgres://` to `postgresql+asyncpg://`
4. ✅ Keep the password simple (no special characters if possible)

### Step 5: Verify Your Project Reference

In Supabase Dashboard:
1. Go to **Settings** → **General**
2. Look for **Reference ID**
3. It should match what's in your connection string

**Example:**
- If Reference ID is: `abcdefghijk`
- Your connection string should contain: `db.abcdefghijk.supabase.co` or `postgres.abcdefghijk`

## Quick Fix Script

After updating your .env, run:

```bash
cd /Users/edward.seo/dev/private/research/DeepResearch/HypePaper/backend

# Test the connection
python3 << 'EOF'
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('DATABASE_URL')

# Remove quotes if present
url = url.strip('"').strip("'")

# Replace asyncpg with postgresql for asyncpg library
url = url.replace('postgresql+asyncpg://', 'postgresql://')

print(f"Testing: {url[:50]}...")

async def test():
    try:
        conn = await asyncpg.connect(url)
        result = await conn.fetchval('SELECT current_database()')
        print(f"✅ Connected to database: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

success = asyncio.run(test())
print("")
if success:
    print("✅ Connection works! Now run:")
    print("   python -m alembic upgrade head")
else:
    print("❌ Fix the DATABASE_URL in .env file")
EOF
```

## Common Mistakes

### Mistake 1: Wrong Project Reference
❌ Using project name instead of reference ID
✅ Use the short random ID from Settings → General

### Mistake 2: Using Wrong Connection String Format
❌ `postgres://postgres:password@db.xxx.supabase.co`
✅ `postgresql+asyncpg://postgres:password@db.xxx.supabase.co`

### Mistake 3: Quotes in .env File
❌ `DATABASE_URL="postgresql+asyncpg://..."`
✅ `DATABASE_URL=postgresql+asyncpg://...`

### Mistake 4: Project Not Active
Check if your Supabase project shows "Active" status (green) in the dashboard.
If it's "Paused", click to restore it.

## Still Not Working?

Try the **Session Pooler** connection string instead:

1. In Supabase Dashboard → Settings → Database
2. Look for "Connection pooling" section
3. Mode: **Session**
4. Copy that connection string
5. Change `postgres://` to `postgresql+asyncpg://`
6. Use port **5432** not 6543

The Session pooler has better compatibility with migrations.
