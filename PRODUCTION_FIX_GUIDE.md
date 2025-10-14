# Production Database Fix Guide

## Issue
Production database is missing the `professional_summary` column in the `candidates` table, causing vetting uploads to fail.

**Error:**
```
column candidates.professional_summary does not exist
```

---

## Solution

### Option 1: Run Migration Script (Recommended)

**Steps:**

1. **SSH into Dokploy server:**
```bash
ssh your-server
```

2. **Navigate to application directory:**
```bash
cd /path/to/ai-hr-assistant
```

3. **Run the migration script:**
```bash
python scripts/add_professional_summary_column.py
```

**Expected Output:**
```
INFO:__main__:Adding 'professional_summary' column to candidates table...
INFO:__main__:✅ Successfully added 'professional_summary' column to candidates table
INFO:__main__:✅ Migration completed successfully!
```

4. **Restart the application:**
```bash
# In Dokploy dashboard, restart the service
# OR
docker-compose restart
```

---

### Option 2: Manual SQL (If script fails)

**Connect to PostgreSQL:**
```bash
# Find your database container
docker ps | grep postgres

# Connect to database
docker exec -it <postgres-container-id> psql -U <username> -d <database>
```

**Run SQL:**
```sql
-- Check if column exists
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'candidates' 
AND column_name = 'professional_summary';

-- If not exists, add it
ALTER TABLE candidates 
ADD COLUMN professional_summary TEXT;

-- Verify
\d candidates
```

**Exit and restart:**
```bash
\q
# Restart application
```

---

### Option 3: Use Alembic (Full Migration System)

**If you want to use Alembic for all future migrations:**

1. **Initialize Alembic (if not done):**
```bash
alembic upgrade head
```

2. **This will run all pending migrations including:**
   - `add_resume_job_matches_table.py`
   - `add_professional_summary_to_candidates.py`
   - `add_fulltext_search_support.py`

---

## Verification

**After running the fix, test:**

1. **Upload a resume through vetting:**
   - Go to `/vet-resumes`
   - Upload a test resume
   - Click "Approve"
   - Click "Upload to Database"

2. **Check logs:**
   - Should see: `Created new candidate: [Name] (ID: [UUID])`
   - Should NOT see: `professional_summary does not exist`

3. **Verify in database:**
```sql
SELECT id, full_name, email, professional_summary 
FROM candidates 
ORDER BY created_at DESC 
LIMIT 5;
```

---

## Code Changes Made

### 1. Backward-Compatible Vetting Code
**File:** `api/v1/vetting.py`

**Changes:**
- Added try-catch around candidate queries
- Falls back to querying without `professional_summary` if column doesn't exist
- Creates candidates without the field if DB doesn't support it
- Logs warnings when schema mismatch is detected

**Result:** Application won't crash even if column is missing, but will log warnings.

### 2. Migration Script
**File:** `scripts/add_professional_summary_column.py`

**Features:**
- Checks if column exists before adding (safe to run multiple times)
- Uses raw SQL for maximum compatibility
- Async-compatible with your database setup

---

## Why This Happened

**Root Cause:**
- Local development uses SQLite with auto-created schema
- Production uses PostgreSQL with manual migrations
- The `professional_summary` column was added to the model but migration wasn't run on production

**Prevention:**
- Always run migrations on production after model changes
- Use Alembic for version-controlled migrations
- Test on staging environment first

---

## Quick Fix Commands (Copy-Paste)

**For Dokploy:**
```bash
# 1. SSH to server
ssh your-dokploy-server

# 2. Find your app container
docker ps | grep ai-hr-assistant

# 3. Run migration inside container
docker exec -it <container-id> python scripts/add_professional_summary_column.py

# 4. Restart container
docker restart <container-id>
```

**For Direct Server:**
```bash
# 1. SSH to server
ssh your-server

# 2. Navigate to app
cd /path/to/ai-hr-assistant

# 3. Activate venv (if using)
source venv/bin/activate

# 4. Run migration
python scripts/add_professional_summary_column.py

# 5. Restart service
systemctl restart ai-hr-assistant
# OR
pm2 restart ai-hr-assistant
```

---

## Rollback (If Needed)

**If something goes wrong:**

```sql
-- Remove the column
ALTER TABLE candidates DROP COLUMN professional_summary;
```

**Then revert code changes:**
```bash
git checkout HEAD~1 api/v1/vetting.py
git push origin mvp-1 --force
```

---

## Status

✅ **Code Fixed:** Backward-compatible vetting code deployed  
✅ **Migration Script:** Created and ready to run  
✅ **Local:** Works with or without column  
⏳ **Production:** Needs migration script to be run  

---

## Next Steps

1. Run the migration script on production
2. Test vetting upload
3. Verify no errors in logs
4. Mark as resolved

---

**Need Help?**
- Check logs: `docker logs <container-id> -f`
- Database access: Use Dokploy's database management UI
- Rollback: Use the rollback commands above
