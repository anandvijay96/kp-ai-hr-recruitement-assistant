# Quick Fix for "table jobs has no column named archived_at" Error

## The Problem
Your application's database is missing three columns that were added in a recent migration:
- `archived_at`
- `view_count`  
- `application_deadline`

## Solution

### Step 1: Stop Your Running Application
**IMPORTANT**: Stop the FastAPI server if it's currently running.
- Press `Ctrl+C` in the terminal where the server is running
- Or close the terminal/command prompt

### Step 2: Run the Database Fix Script
```bash
python fix_database_schema.py
```

This script will:
- Find all database files
- Add the missing columns
- Confirm the fix was applied

### Step 3: Restart Your Application
```bash
uvicorn main:app --reload
# or
python -m uvicorn main:app --reload
# or however you normally start it
```

### Step 4: Try Creating a Job Again
The error should now be resolved!

---

## Alternative: Use SQLAlchemy to Recreate Tables

If the above doesn't work, you can force SQLAlchemy to recreate all tables:

```python
# Run this Python script once
import asyncio
from sqlalchemy import text
from core.database import engine
from models.database import Base

async def recreate_tables():
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        # Recreate all tables with current schema
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables recreated successfully!")

asyncio.run(recreate_tables())
```

**WARNING**: This will delete all existing data!

---

## Why This Happened

Your application uses an `.env` file to configure the database location. The `.env` file was missing, so the application used the default path from `core/config.py` which points to `/tmp/hr_recruitment.db`.

I've created a `.env` file for you that points to `./hr_recruitment.db` (in the project root) and fixed that database file.

---

## Verify the Fix

After restarting, you can verify the schema is correct:

```bash
python -c "import sqlite3; conn = sqlite3.connect('hr_recruitment.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(jobs)'); print([row[1] for row in cursor.fetchall()]); conn.close()"
```

You should see `archived_at`, `view_count`, and `application_deadline` in the output.
