# 🔧 Service Instantiation Issue - FIXED!

**Issue:** `CandidateService.__init__() missing 1 required positional argument: 'db_session'`  
**Status:** ✅ RESOLVED  
**Commit:** `69dbc14`

---

## 🎯 What Was Wrong

Services from the **job-creation branch** use **dependency injection** pattern - they require a database session to be passed during initialization:

```python
class CandidateService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
```

But in several API files, these services were being **instantiated globally** without any session:

```python
# ❌ WRONG - instantiated at module level without session
candidate_service = CandidateService()  # TypeError!
resume_service = ResumeService()        # TypeError!
auth_service = AuthService()            # TypeError!
```

---

## ✅ The Fix

Removed global instantiation for services that require database sessions. These services should be instantiated **inside endpoint functions** where they can access the database session via dependency injection.

### Files Fixed

#### 1. `api/v1/resumes.py`
```python
# Before (WRONG):
candidate_service = CandidateService()
resume_service = ResumeService()

# After (CORRECT):
# Services that don't need database session can be instantiated globally
duplicate_detector = DuplicateDetector()

# Services that need database session (CandidateService, ResumeService) 
# will be instantiated in endpoint functions via dependency injection
```

#### 2. `api/v1/candidates.py`
```python
# Before (WRONG):
filter_service = FilterService()
preset_service = PresetService()
candidate_service = CandidateService()  # ❌ Needs session!
export_service = ExportService()

# After (CORRECT):
# Services that don't need database session can be instantiated globally
filter_service = FilterService()
preset_service = PresetService()
export_service = ExportService()

# CandidateService needs database session - instantiate in endpoints
```

#### 3. `api/v1/auth.py`
```python
# Before (WRONG):
from models.database import get_db  # ❌ Wrong import
auth_service = AuthService()        # ❌ Needs session!

# After (CORRECT):
from core.database import get_db    # ✅ Correct import
from services.password_service import PasswordService

# AuthService needs database session and password service
# Instantiate in endpoints via dependency injection
```

---

## 🎁 Services Classification

### ✅ Can Be Global (No Session Needed)
These services don't need database sessions in `__init__`:
- `DuplicateDetector()`
- `FilterService()`
- `PresetService()`
- `ExportService()`
- `FileStorageService()`
- `FileValidatorService()`
- `ResumeParserService()`

### ❌ Must Be Local (Session Required)
These services need `db_session: AsyncSession` in `__init__`:
- `CandidateService(db_session)`
- `ResumeService(db_session, ...)`
- `AuthService(db_session, password_service)`
- `JobService(db_session)`
- `UserManagementService(db_session)`
- `PermissionService(db_session)`
- `AuditService(db_session)`
- `BulkOperationsService(db_session)`

---

## 📝 Correct Usage Pattern

### For Endpoints Using These Services

**Pattern 1: Instantiate in endpoint**
```python
@router.post("/some-endpoint")
async def my_endpoint(db: AsyncSession = Depends(get_db)):
    # Instantiate service with database session
    candidate_service = CandidateService(db)
    resume_service = ResumeService(db)
    
    # Use the services
    result = await candidate_service.some_method()
    return result
```

**Pattern 2: Create dependency function**
```python
async def get_candidate_service(db: AsyncSession = Depends(get_db)):
    return CandidateService(db)

@router.post("/some-endpoint")
async def my_endpoint(
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    result = await candidate_service.some_method()
    return result
```

---

## 🚀 Test It Now

Run this command on your WSL/Linux terminal:

```bash
python test_import.py
```

**Expected output:**
```
Testing imports...
1. Testing core.config...
   ✅ Database URL: sqlite+aiosqlite:///./hr_recruitment.db

2. Testing aiosqlite module...
   ✅ aiosqlite version: 0.19.0

3. Testing core.database...
   ✅ Database module imported

4. Testing main.py...
   ✅ main.py imported successfully!

==================================================
🎉 ALL IMPORTS SUCCESSFUL!
==================================================
```

---

## 📊 Why This Pattern?

### Problem with Global Instantiation
```python
# At module load time:
candidate_service = CandidateService()  # ❌
# - No database session available yet
# - Services are created before FastAPI starts
# - Database connection not established
# - Leads to TypeError
```

### Solution: Dependency Injection
```python
# At request time:
@router.post("/endpoint")
async def endpoint(db: AsyncSession = Depends(get_db)):
    candidate_service = CandidateService(db)  # ✅
    # - Database session available from FastAPI
    # - Fresh session per request
    # - Proper connection pooling
    # - Clean transaction management
```

---

## 🔍 Technical Details

### Why Some Services Don't Need Sessions

Services like `DuplicateDetector`, `FilterService`, etc. either:
1. **Receive db as method parameter:**
   ```python
   class FilterService:
       def full_text_search(self, query: str, db: Session, ...):
           # db passed per method call
   ```

2. **Are stateless utilities:**
   ```python
   class FileValidatorService:
       def calculate_file_hash(self, content: bytes) -> str:
           # No database needed
   ```

### Why Some Services Need Sessions

Services like `CandidateService`, `ResumeService`, etc.:
1. **Store db as instance variable:**
   ```python
   class CandidateService:
       def __init__(self, db_session: AsyncSession):
           self.db = db_session  # Used across methods
   ```

2. **Perform complex database operations:**
   - Multiple queries per method
   - Transaction management
   - Relationship loading

---

## 🎯 Next Steps

### Step 1: Test Imports
```bash
python test_import.py
```

### Step 2: Start Server
```bash
uvicorn main:app --reload --port 8000
```

### Step 3: Verify Dashboard
Open: **http://localhost:8000**

---

## 📚 Related Fixes

This is the **3rd issue** resolved during MVP-1 merge:
1. ✅ **Database Driver** - Fixed `.env` to use `sqlite+aiosqlite://`
2. ✅ **Model Conflicts** - Consolidated duplicate table definitions
3. ✅ **Service Instantiation** - Fixed global service initialization ⬅ YOU ARE HERE

---

**Status:** ✅ READY TO TEST

**Test Command:**
```bash
python test_import.py && uvicorn main:app --reload --port 8000
```
