# Bug Fixes - Migration & Celery Errors
**📅 Date:** October 13, 2025 - 3:35 AM IST  
**🎯 Goal:** Fix Alembic migration and Celery task errors

---

## ✅ Fixes Applied

### Fix 1: Alembic Migration Error ✅
**Error:**
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; 
can't call await_only() here.
```

**Root Cause:**
- Alembic was trying to use async SQLAlchemy engine
- Alembic requires synchronous database operations
- Database URL was `sqlite+aiosqlite://` (async)

**Solution:**
**File:** `alembic/env.py`

**Changes:**
1. Convert async database URL to sync:
   ```python
   sync_db_url = settings.database_url.replace('sqlite+aiosqlite://', 'sqlite:///')
   config.set_main_option("sqlalchemy.url", sync_db_url)
   ```

2. Import Base with all models registered:
   ```python
   import models.database
   from core.database import Base as AppBase
   Base = AppBase
   ```

**Result:** Migration will now use sync SQLite driver

---

### Fix 2: Celery Task Error ✅
**Error:**
```
AttributeError: 'Resume' object has no attribute 'raw_text'
```

**Root Cause:**
- Celery task was using `resume.raw_text`
- Resume model uses `resume.extracted_text` (not `raw_text`)

**Solution:**
**File:** `tasks/resume_tasks.py`

**Changes:**
```python
# BEFORE (Line 59)
if resume.raw_text and len(resume.raw_text.strip()) >= 50:
    text = resume.raw_text

# AFTER
if resume.extracted_text and len(resume.extracted_text.strip()) >= 50:
    text = resume.extracted_text
```

```python
# BEFORE (Line 66)
resume.raw_text = text

# AFTER
resume.extracted_text = text
```

**Result:** Celery tasks will now work correctly

---

## 🧪 Testing Instructions

### Test 1: Run Migration
```bash
# From WSL terminal
cd /mnt/d/Projects/BMAD/ai-hr-assistant
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade add_fulltext_search_support -> 002_resume_job_matches, add resume job matches table
```

**Success Indicators:**
- No errors
- Migration completes
- Table `resume_job_matches` created

### Test 2: Verify Table Created
```bash
# Check if table exists
sqlite3 ai_hr_assistant.db "SELECT name FROM sqlite_master WHERE type='table' AND name='resume_job_matches';"
```

**Expected Output:**
```
resume_job_matches
```

### Test 3: Test Celery Task
1. **Restart Celery worker:**
   ```bash
   # Stop current worker (Ctrl+C)
   # Start new worker
   celery -A tasks.celery_app worker --loglevel=info
   ```

2. **Upload a resume** through the UI
3. **Check Celery logs** - should see:
   ```
   INFO: Processing resume [id]: [filename]
   INFO: Using pre-extracted text (XXXX chars)
   ```

**Success Indicators:**
- No `AttributeError` about `raw_text`
- Resume processes successfully
- Status updates to 'processed'

---

## 📋 Files Modified

### 1. `alembic/env.py`
**Changes:**
- Convert async DB URL to sync
- Import Base with all models
- Better error handling

**Lines Changed:** 8-24, 30-32

### 2. `tasks/resume_tasks.py`
**Changes:**
- Replace `raw_text` with `extracted_text` (2 occurrences)

**Lines Changed:** 59, 66

---

## 🔍 Root Cause Analysis

### Why Migration Failed
1. **Async vs Sync:** FastAPI uses async SQLAlchemy (`aiosqlite`)
2. **Alembic Limitation:** Alembic only supports sync operations
3. **URL Mismatch:** `sqlite+aiosqlite://` is async, Alembic needs `sqlite:///`

### Why Celery Failed
1. **Model Change:** Resume model was refactored
2. **Old Code:** Celery task still used old attribute name
3. **No Tests:** No automated tests caught the attribute error

---

## 🚀 Next Steps

### Immediate (Now)
1. **Run the migration:**
   ```bash
   alembic upgrade head
   ```

2. **Restart Celery worker:**
   ```bash
   celery -A tasks.celery_app worker --loglevel=info
   ```

3. **Test resume upload** to verify Celery works

### After Migration Success
1. **Test matching API endpoints**
2. **Verify resume_job_matches table has correct schema**
3. **Continue with Sprint 2 implementation**

---

## ✅ Verification Checklist

- [ ] Alembic migration runs without errors
- [ ] Table `resume_job_matches` exists in database
- [ ] Table has correct columns and indexes
- [ ] Celery worker starts without errors
- [ ] Resume upload works without AttributeError
- [ ] Resume processing completes successfully

---

## 🐛 If Migration Still Fails

### Error: "No module named 'models.database'"
**Solution:** Make sure you're in the correct directory
```bash
cd /mnt/d/Projects/BMAD/ai-hr-assistant
python -c "import models.database; print('OK')"
```

### Error: "Table already exists"
**Solution:** Table might already exist from previous attempt
```bash
# Check if table exists
sqlite3 ai_hr_assistant.db ".tables" | grep resume_job_matches

# If exists, either:
# Option 1: Skip migration (table already there)
# Option 2: Drop and recreate
sqlite3 ai_hr_assistant.db "DROP TABLE IF EXISTS resume_job_matches;"
alembic upgrade head
```

### Error: "Cannot import Base"
**Solution:** Check Python path
```bash
export PYTHONPATH=/mnt/d/Projects/BMAD/ai-hr-assistant:$PYTHONPATH
alembic upgrade head
```

---

**📅 Status Date:** October 13, 2025 - 3:35 AM IST  
**✅ Fixes Applied:** 2/2  
**⏳ Next:** Run migration and test  
**🎯 Goal:** Complete Sprint 2 database setup
