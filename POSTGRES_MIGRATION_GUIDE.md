# 🐘 PostgreSQL Production Migration Guide

**CRITICAL**: Production is using PostgreSQL, not SQLite!

---

## ⚠️ ERROR IN PRODUCTION

```
column candidates.github_url does not exist
```

**Root Cause**: Database schema not updated with new columns

---

## 🔧 MIGRATION OPTIONS

Choose ONE of the following methods:

---

### **OPTION 1: Direct SQL (Recommended - Fastest)**

Run this SQL directly in your PostgreSQL database:

```sql
-- Add github_url column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='candidates' AND column_name='github_url'
    ) THEN
        ALTER TABLE candidates ADD COLUMN github_url VARCHAR(500);
        RAISE NOTICE 'Added column: candidates.github_url';
    END IF;
END $$;

-- Add linkedin_suggestions column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='candidates' AND column_name='linkedin_suggestions'
    ) THEN
        ALTER TABLE candidates ADD COLUMN linkedin_suggestions JSONB;
        RAISE NOTICE 'Added column: candidates.linkedin_suggestions';
    END IF;
END $$;
```

**Methods to run**:

#### A. Using psql (CLI):
```bash
# Connect to database
psql -h <host> -U <user> -d <database>

# Run the SQL
\i migrations/add_github_url_postgres.sql

# Verify
\d candidates
```

#### B. Using pgAdmin (GUI):
1. Connect to your database
2. Open Query Tool (Tools → Query Tool)
3. Copy-paste the SQL above
4. Click Execute (F5)
5. Verify: Right-click `candidates` table → View/Edit Data

#### C. Using Docker exec:
```bash
# If PostgreSQL is in Docker
docker exec -i <postgres-container> psql -U <user> -d <database> < migrations/add_github_url_postgres.sql
```

---

### **OPTION 2: Python Migration Script**

If you prefer automated script:

```bash
# 1. Set environment variable
export DATABASE_URL='postgresql+asyncpg://user:password@host:port/database'

# 2. Install asyncpg if not installed
pip install asyncpg

# 3. Run migration
python fix_postgres_migrations.py
```

**Expected Output**:
```
============================================================
🔧 PostgreSQL Migration Script
============================================================

📋 Checking candidates table...
✅ Added column: candidates.github_url
✅ Added column: candidates.linkedin_suggestions

📋 Checking clients table...
✅ Created table: clients

============================================================
✅ Migration completed!
============================================================
```

---

## 🚀 COMPLETE DEPLOYMENT STEPS

### Step 1: Pull Latest Code
```bash
cd /app
git pull origin mvp-1
```

### Step 2: Run Migration (Choose one method above)

**Quick Command** (if using Docker + psql):
```bash
docker exec -i <postgres-container> psql -U <user> -d <database> << EOF
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS github_url VARCHAR(500);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS linkedin_suggestions JSONB;
EOF
```

### Step 3: Verify Migration
```bash
# Check columns exist
docker exec -i <postgres-container> psql -U <user> -d <database> -c "\d candidates" | grep -E "github_url|linkedin_suggestions"
```

**Expected Output**:
```
 github_url              | character varying(500) |
 linkedin_suggestions    | jsonb                  |
```

### Step 4: Restart Application
```bash
docker-compose restart app
# OR
docker restart <app-container>
```

### Step 5: Verify Application
```bash
# Check logs
docker logs -f <app-container>

# Should NOT see:
# ❌ column candidates.github_url does not exist

# Should see:
# ✅ Database tables created successfully
# ✅ Application startup complete
```

---

## 🧪 POST-MIGRATION TESTING

### 1. Test Candidates Page
```bash
curl -X GET "https://hrms.kloudportal.com/candidates"
```
**Expected**: Page loads without errors ✅

### 2. Test Dashboard
```bash
curl -X GET "https://hrms.kloudportal.com/api/dashboard/stats"
```
**Expected**: Returns stats successfully ✅

### 3. Test Candidate Search
```bash
curl -X POST "https://hrms.kloudportal.com/api/v1/candidates/search"
```
**Expected**: Returns search results ✅

### 4. Test GitHub URL (via UI)
1. Go to candidate detail page
2. Edit candidate
3. Add GitHub URL
4. Save
5. Verify link works

---

## 🔍 VERIFICATION QUERIES

Run these to verify the migration:

```sql
-- Check if columns exist
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'candidates'
AND column_name IN ('github_url', 'linkedin_suggestions')
ORDER BY column_name;

-- Count candidates with GitHub URLs
SELECT COUNT(*) as candidates_with_github
FROM candidates
WHERE github_url IS NOT NULL;

-- Sample data
SELECT id, full_name, github_url, linkedin_suggestions
FROM candidates
LIMIT 5;
```

---

## 🐛 TROUBLESHOOTING

### Problem: "permission denied for table candidates"
**Solution**:
```sql
-- Grant permissions to your app user
GRANT ALL PRIVILEGES ON TABLE candidates TO <app_user>;
```

### Problem: Migration script can't connect to database
**Solution**:
```bash
# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql+asyncpg://user:pass@host:port/db

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Problem: Column still doesn't exist after migration
**Solution**:
```sql
-- Verify migration ran
SELECT column_name 
FROM information_schema.columns 
WHERE table_name='candidates' AND column_name='github_url';

-- If empty, run again:
ALTER TABLE candidates ADD COLUMN github_url VARCHAR(500);
```

### Problem: Application still shows error after migration
**Solution**:
```bash
# 1. Clear application cache
docker exec <app-container> rm -rf __pycache__

# 2. Restart container (IMPORTANT!)
docker-compose restart app

# 3. Check logs
docker logs -f <app-container>
```

---

## 📋 MIGRATION CHECKLIST

- [ ] Pull latest code from `mvp-1` branch
- [ ] Connect to PostgreSQL database
- [ ] Run SQL migration (Option 1) OR Python script (Option 2)
- [ ] Verify columns added: `\d candidates`
- [ ] Restart application container
- [ ] Check application logs (no errors)
- [ ] Test candidates page loads
- [ ] Test dashboard loads
- [ ] Test candidate search
- [ ] Verify GitHub URL functionality

---

## 🔄 ROLLBACK (If Needed)

If migration causes issues:

```sql
-- Remove columns (ONLY if needed)
ALTER TABLE candidates DROP COLUMN IF EXISTS github_url;
ALTER TABLE candidates DROP COLUMN IF EXISTS linkedin_suggestions;

-- Then restart app
```

---

## 📊 DATABASE COMPARISON

### SQLite (Local Development)
- Uses `fix_clients_table.py`
- File-based database
- No concurrent writes

### PostgreSQL (Production)
- Uses SQL migration or `fix_postgres_migrations.py`
- Server-based database
- Concurrent access
- Better performance

---

## 🎯 SUMMARY

**Issue**: Missing columns in PostgreSQL production database  
**Columns to Add**: `github_url`, `linkedin_suggestions`  
**Fastest Fix**: Run SQL directly (Option 1)  
**Time Required**: 2-3 minutes  
**Downtime**: None (if using Option 1)

**After migration, application should work perfectly!**

---

**Created**: Oct 27, 2025 - 5:15 PM  
**Database**: PostgreSQL  
**Priority**: 🔥 CRITICAL - Fixes production errors
