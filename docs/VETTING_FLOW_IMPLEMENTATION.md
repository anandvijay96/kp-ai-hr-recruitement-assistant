# Resume Vetting Flow Implementation Plan

## Overview
Separate authenticity vetting from database upload to align with PRD requirements.

## Two-Phase Architecture

### Phase 1: Resume Vetting (No DB Save)
**Route:** `/vet-resumes`  
**Purpose:** Scan and review resumes for authenticity before approval

**Features:**
- Upload multiple resumes for scanning
- Real-time authenticity analysis
- Review interface with approve/reject actions
- Temporary storage (session-based)
- Bulk actions (approve all, reject all, approve score > X%)
- Export approved list

### Phase 2: Resume Upload (Save to DB)
**Route:** `/upload`  
**Purpose:** Save approved or trusted resumes to database

**Features:**
- Accept pre-approved resumes from vetting
- Direct upload option (skip vetting for trusted sources)
- Batch processing with progress tracking
- Candidate creation and duplicate detection
- Database storage

## Implementation Steps

### Step 1: Create Vetting Page (`/vet-resumes`)

**Frontend (vet_resumes.html):**
```html
- Upload interface for batch scanning
- Scanning progress indicator
- Results table with columns:
  - Filename
  - Authenticity Score (with color coding)
  - Key Flags
  - Status (Pending/Approved/Rejected)
  - Actions (Approve/Reject buttons)
- Bulk action toolbar
- "Upload Approved" button → redirects to /upload with approved files
```

**JavaScript Functions:**
```javascript
- scanResumes() - Upload and analyze without DB save
- approveResume(id) - Mark as approved
- rejectResume(id) - Mark as rejected
- approveAll() - Bulk approve
- rejectAll() - Bulk reject
- approveByScore(threshold) - Approve resumes >= threshold
- uploadApproved() - Send approved resumes to upload page
```

### Step 2: Update Backend APIs

**Vetting API (No DB Save):**
```python
POST /api/vet-resume
- Accept file upload
- Run authenticity analysis
- Store results in session/temp storage
- Return analysis results
- DO NOT save to database

GET /api/vetting-session
- Retrieve current vetting session results
- Return list of scanned resumes with statuses
```

**Upload API (With DB Save):**
```python
POST /api/v1/resumes/upload
- Accept approved files or direct uploads
- Option: skip_vetting flag for trusted sources
- Create candidate records
- Run duplicate detection
- Save to database
```

### Step 3: Temporary Storage

**Session-Based Storage:**
```python
# services/vetting_session.py
class VettingSession:
    - store_scan_result(file_hash, result)
    - get_scan_result(file_hash)
    - mark_approved(file_hash)
    - mark_rejected(file_hash)
    - get_approved_files()
    - clear_session()
```

**Using Redis or File-Based:**
```python
# Option A: Redis (recommended for production)
redis_client.setex(f"vetting:{session_id}:{file_hash}", ttl=3600, json.dumps(result))

# Option B: File-based (for development)
temp_dir = "temp/vetting_sessions/{session_id}/"
```

### Step 4: Modify Upload Page

**Changes to upload.html:**
```html
- Add "Source" selector:
  - "Pre-Approved Resumes" (from vetting)
  - "Direct Upload" (trusted sources, skip vetting)

- If pre-approved selected:
  - Show list of approved files from vetting session
  - Disable file selection
  - Show "Upload to Database" button

- If direct upload:
  - Show normal file upload
  - Add checkbox: "Skip authenticity vetting"
  - Proceed with current batch upload flow
```

### Step 5: Data Passing Between Pages

**Method A: Session Storage (Recommended)**
```javascript
// In vet_resumes.html
sessionStorage.setItem('approved_resumes', JSON.stringify(approvedList));
window.location.href = '/upload?source=vetting';

// In upload.html
const source = new URLSearchParams(window.location.search).get('source');
if (source === 'vetting') {
    const approvedResumes = JSON.parse(sessionStorage.getItem('approved_resumes'));
    // Load and display approved resumes
}
```

**Method B: API-Based**
```javascript
// Store in backend session
POST /api/vetting-session/approve-selected
{ file_hashes: [...] }

// Retrieve in upload page
GET /api/vetting-session/approved-files
Returns: list of approved file references
```

## File Structure

```
New Files:
- templates/vet_resumes.html (vetting interface)
- services/vetting_session.py (temporary storage)
- api/v1/vetting.py (vetting endpoints)

Modified Files:
- templates/upload.html (add pre-approved source option)
- main.py (add /vet-resumes route)
- api/v1/resumes.py (update upload to handle pre-approved)
```

## Database Changes

**No new tables needed** - vetting uses temporary storage only

**Optional:** Add audit trail
```sql
CREATE TABLE vetting_audit (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR,
    file_name VARCHAR,
    file_hash VARCHAR,
    authenticity_score FLOAT,
    status VARCHAR,  -- 'approved', 'rejected'
    vetted_at TIMESTAMP,
    uploaded_at TIMESTAMP
);
```

## User Flows

### Flow A: Vetting → Upload
```
1. HR visits /vet-resumes
2. Uploads 10 resumes for scanning
3. System analyzes all (no DB save)
4. HR reviews results table
5. Approves 7 resumes (3 rejected - low scores)
6. Clicks "Upload Approved"
7. Redirected to /upload with 7 pre-approved files
8. Confirms upload → files saved to DB
9. Candidates created, duplicates detected
```

### Flow B: Direct Upload (Trusted)
```
1. HR visits /upload directly
2. Selects "Direct Upload" mode
3. Uploads resumes
4. Checks "Skip vetting" checkbox
5. Uploads → files saved to DB directly
6. Candidates created, duplicates detected
```

## Implementation Timeline

| Task | Effort | Priority |
|------|--------|----------|
| Create vetting page UI | 2 hours | High |
| Build vetting API endpoints | 2 hours | High |
| Implement temporary storage | 1 hour | High |
| Modify upload page | 1 hour | Medium |
| Connect flows with data passing | 2 hours | High |
| Testing and bug fixes | 2 hours | High |

**Total:** ~10 hours (1.5 days)

## Next Steps

1. Create `vet_resumes.html` template
2. Create `api/v1/vetting.py` endpoints
3. Create `services/vetting_session.py`
4. Modify `upload.html` for pre-approved source
5. Update `main.py` routes
6. Test complete flows
7. Update documentation

## Success Criteria

✅ HR can scan resumes without saving to DB  
✅ HR can approve/reject individual resumes  
✅ HR can bulk approve/reject  
✅ Only approved resumes get uploaded to DB  
✅ Direct upload still works for trusted sources  
✅ Progress tracking works for both flows  
✅ Duplicate detection works correctly  
