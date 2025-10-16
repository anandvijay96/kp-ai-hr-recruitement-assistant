# PostgreSQL Production Deployment - URGENT FIX

## 🚨 CRITICAL: Your app is using PostgreSQL, not SQLite!

The error shows missing columns in PostgreSQL. Follow these steps immediately:

---

## 🔧 QUICK FIX - Run These Commands

### Step 1: SSH to Server
```bash
ssh ubuntu@158.69.219.206
```

### Step 2: Connect to PostgreSQL
```bash
# Find PostgreSQL connection details from your app
docker exec -it <ai-hr-assistant-container> env | grep DATABASE

# OR check Dokploy environment variables
# You should see something like:
# DATABASE_URL=postgresql+asyncpg://user:pass@hr-postgres:5432/dbname
```

### Step 3: Connect to PostgreSQL Database
```bash
# Option A: From within app container
docker exec -it <ai-hr-assistant-container> bash
psql $DATABASE_URL

# Option B: Directly to postgres container
docker exec -it hr-postgres psql -U <username> -d <database>

# Option C: Using psql from host (if installed)
psql -h 158.69.219.206 -U <username> -d <database>
```

### Step 4: Run the Migration SQL
```sql
-- Copy and paste the entire postgres_phase2_migrations.sql file
-- OR run it from file:

\i /app/migrations/postgres_phase2_migrations.sql
```

### Step 5: Verify Columns Were Added
```sql
-- Check candidates table
\d candidates

-- Should show:
-- - is_deleted
-- - deleted_at
-- - deleted_by
-- - deletion_reason
-- - professional_summary
-- - linkedin_suggestions

-- Check work_experience table
\d work_experience

-- Should show:
-- - responsibilities
```

### Step 6: Restart Application
```bash
exit  # Exit psql
exit  # Exit container
docker restart <ai-hr-assistant-container>
```

---

## 📋 Alternative: Run from App Container

If you can access the app container:

```bash
# Enter app container
docker exec -it <ai-hr-assistant-container> bash

# Install psql if not available
apt-get update && apt-get install -y postgresql-client

# Run migration
psql $DATABASE_URL -f /app/migrations/postgres_phase2_migrations.sql

# Exit and restart
exit
docker restart <ai-hr-assistant-container>
```

---

## 🔍 What Columns Are Missing

Based on the error, these columns don't exist:

### candidates table:
- ✗ `is_deleted` (BOOLEAN) - **CRITICAL**
- ✗ `deleted_at` (TIMESTAMP)
- ✗ `deleted_by` (VARCHAR)
- ✗ `deletion_reason` (TEXT)
- ✗ `professional_summary` (TEXT)
- ✗ `linkedin_suggestions` (JSONB)

### work_experience table:
- ✗ `responsibilities` (JSONB)

---

## 🚀 Quick Command Reference

```bash
# 1. SSH
ssh ubuntu@158.69.219.206

# 2. Find postgres container
docker ps | grep postgres

# 3. Connect to database
docker exec -it hr-postgres psql -U postgres -d hr_recruitment

# 4. Run migration (paste the SQL from postgres_phase2_migrations.sql)

# 5. Verify
\d candidates
\d work_experience

# 6. Exit and restart app
\q
docker restart <ai-hr-assistant-container>
```

---

## ⚠️ Why This Happened

Your production uses **PostgreSQL** but the migrations were written for **SQLite**. 

The SQL syntax is different:
- SQLite: `ALTER TABLE ADD COLUMN`
- PostgreSQL: Needs `DO $$` blocks for conditional logic

---

## ✅ After Running Migration

The app should:
1. ✅ Load dashboard without errors
2. ✅ Show candidate data
3. ✅ Allow soft-delete operations
4. ✅ Display work experience with bullet points
5. ✅ Show LinkedIn suggestions

---

## 🆘 If Still Not Working

Check logs:
```bash
docker logs -f <ai-hr-assistant-container>
```

Verify database connection:
```bash
docker exec -it <ai-hr-assistant-container> python -c "from core.config import settings; print(settings.database_url)"
```

---

## 📞 Need Help?

The migration file is safe to run multiple times (idempotent).
It checks if columns exist before adding them.
