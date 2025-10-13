# Jobs Page 404 Error - Diagnosis & Fix
**📅 Date:** October 13, 2025 - 4:05 AM IST  
**🎯 Issue:** Jobs page shows "Failed to load jobs. Please try again."  
**🔍 Root Cause:** `/api/jobs` returns 404 - API V2 modules not loading

---

## 🐛 Problem Diagnosis

### Error Observed:
```
INFO: 127.0.0.1:60204 - "GET /api/jobs?page=1&limit=20 HTTP/1.1" 404 Not Found
```

### Browser Console:
```
Error loading jobs: Error: Failed to load jobs: 404
```

### Root Cause:
The `/api/jobs` endpoint is not registered because:
1. **API V2 modules fail to import** during app startup
2. **`API_V2_ENABLED` becomes `False`**
3. **Router never gets registered** (line 129 in main.py)
4. **All `/api/jobs/*` endpoints return 404**

### Why Import Fails:
Most likely one of these:
- Missing dependency (`aiosqlite` not installed)
- Circular import in `models.database`
- Missing `models.job_schemas` or `services.job_service`

---

## ✅ Fix Applied

### File: `main.py`

**Changes:**
1. Added detailed logging for API V2 import
2. Shows success/failure message on startup
3. Prints full traceback if import fails

**What to Look For:**
When you restart the FastAPI server, you'll see:

**Success:**
```
INFO: ✅ API V2 modules loaded successfully
INFO: Application startup complete.
```

**Failure:**
```
ERROR: ❌ API V2 modules not available: [error details]
ERROR: Jobs, Users, and other V2 features will not be available
[Full traceback printed]
```

---

## 🚀 How to Fix

### Step 1: Restart FastAPI Server
```bash
# Stop current server (Ctrl+C)
# Restart:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Check Startup Logs
Look for the API V2 status message:
- ✅ If you see "API V2 modules loaded successfully" → Jobs API should work
- ❌ If you see error → Continue to Step 3

### Step 3: Fix the Import Error

**If error is "No module named 'aiosqlite'":**
```bash
pip install aiosqlite
```

**If error is "circular import":**
The issue is in `models/database.py` or `core/database.py`. The Alembic fix we did earlier might have caused this.

**If error is "cannot import JobService":**
```bash
# Check if file exists
ls services/job_service.py

# Check if models exist
ls models/job_schemas.py
```

### Step 4: Verify Fix
1. Restart server
2. Go to `http://localhost:8000/docs`
3. Look for `/api/jobs` endpoints
4. If they're there → Fixed! ✅
5. If not → Check logs again

---

## 🔧 Alternative: Create Jobs Without API V2

If API V2 won't load, you can still create jobs directly in the database:

**File:** `scripts/create_test_job.py`
```python
import sqlite3
import uuid
from datetime import datetime

db_path = "hr_recruitment.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

job_id = str(uuid.uuid4())
cursor.execute("""
INSERT INTO jobs (
    id, title, department, location_city, location_state,
    work_type, employment_type, description, status,
    created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    job_id,
    "Senior Software Engineer",
    "Engineering",
    "San Francisco",
    "CA",
    "hybrid",
    "full_time",
    "We are looking for a senior software engineer with 5+ years experience...",
    "open",
    datetime.now().isoformat(),
    datetime.now().isoformat()
))

conn.commit()
conn.close()
print(f"✅ Job created: {job_id}")
```

Run it:
```bash
python scripts/create_test_job.py
```

---

## 📊 Current Status

**Sprint 2 (Matching):** 95% Complete
- ✅ Matching algorithm
- ✅ Matching API
- ✅ Matching UI on candidate page
- ✅ Database table created
- ⏳ Need jobs to test matching

**Jobs Feature:** Blocked
- ❌ API V2 not loading
- ❌ Jobs page shows 404
- ⏳ Need to fix import error

---

## 🎯 Next Steps

### Immediate:
1. **Restart server** and check logs
2. **Fix import error** based on traceback
3. **Verify `/api/jobs` works** in Swagger

### After Fix:
1. Create test jobs
2. Run matching for existing resumes
3. See matches on candidate detail page!

---

**📅 Status Date:** October 13, 2025 - 4:05 AM IST  
**🔍 Issue:** Jobs API not loading (404)  
**✅ Diagnostic logging added**  
**⏳ Next:** Restart server and check logs
