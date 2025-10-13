# Feature 2: Resume Upload - Product Requirements Document

**Version:** 1.0  
**Last Updated:** 2025-10-03  
**Status:** Draft  
**Owner:** Product Team  
**Developers:** Engineering Team

---

## 1. OVERVIEW

### 1.1 Feature Description
The Resume Upload feature enables HR recruiters and administrators to upload candidate resumes to the system in multiple formats (PDF, DOCX, TXT). The feature supports both single and bulk uploads with drag-and-drop functionality, real-time progress tracking, automatic virus scanning, duplicate detection, and resume preview capabilities.

### 1.2 Problem Statement
**Current Pain Points:**
- Manual resume collection and organization is time-consuming
- No centralized repository for candidate resumes
- Risk of uploading duplicate or malicious files
- Lack of visibility into upload progress for bulk operations
- No standardized format validation or file size limits
- Difficulty in tracking which recruiter uploaded which resume

**Solution:**
A robust, user-friendly resume upload system that automates file validation, provides real-time feedback, prevents duplicates, ensures security through virus scanning, and maintains a complete audit trail of all uploads.

### 1.3 Target Users

| User Role | Primary Use Case | Access Level |
|-----------|------------------|--------------|
| **Recruiter** | Upload individual candidate resumes during screening | Upload, View Own |
| **HR Manager** | Bulk upload resumes from job fairs/events | Upload, View Team |
| **HR Admin** | Manage all resumes, delete invalid uploads | Full Access |
| **System Admin** | Configure upload settings, monitor storage | Configuration |

---

## 2. USER STORIES

### US-2.1: Single Resume Upload
**As a** Recruiter  
**I want to** upload a single candidate resume via drag-and-drop or file browser  
**So that** I can quickly add new candidates to the system without manual data entry

**Priority:** High  
**Story Points:** 5

---

### US-2.2: Bulk Resume Upload
**As an** HR Manager  
**I want to** upload multiple resumes at once (up to 50 files)  
**So that** I can efficiently process candidates from job fairs or recruitment drives

**Priority:** High  
**Story Points:** 8

---

### US-2.3: Upload Progress Tracking
**As a** Recruiter  
**I want to** see real-time progress indicators for each file being uploaded  
**So that** I know the status of my uploads and can identify any failures immediately

**Priority:** Medium  
**Story Points:** 3

---

### US-2.4: Duplicate Detection
**As an** HR Admin  
**I want the** system to automatically detect and prevent duplicate resume uploads  
**So that** we maintain data integrity and avoid processing the same candidate multiple times

**Priority:** High  
**Story Points:** 5

---

### US-2.5: Resume Preview
**As a** Recruiter  
**I want to** preview uploaded resumes before final submission  
**So that** I can verify the correct file was selected and the content is readable

**Priority:** Medium  
**Story Points:** 3

---

## 3. ACCEPTANCE CRITERIA

### AC-2.1: Single Resume Upload
- ✅ User can drag and drop a resume file onto the upload area
- ✅ User can click "Browse" to select a file from their computer
- ✅ System validates file format (PDF, DOCX, TXT only)
- ✅ System validates file size (max 10MB)
- ✅ System displays file name, size, and type before upload
- ✅ Upload completes within 5 seconds for files under 5MB
- ✅ Success message displays with resume ID after successful upload
- ✅ Error message displays if upload fails with specific reason

### AC-2.2: Bulk Resume Upload
- ✅ User can select up to 50 files at once
- ✅ System validates each file individually
- ✅ Invalid files are flagged but don't stop other uploads
- ✅ Progress bar shows overall completion percentage
- ✅ Individual file status shown (pending/uploading/success/failed)
- ✅ Summary report displays: X successful, Y failed, Z duplicates
- ✅ Failed files can be retried individually
- ✅ User can cancel bulk upload in progress

### AC-2.3: Upload Progress Tracking
- ✅ Progress bar updates in real-time (every 100ms)
- ✅ Shows percentage complete for each file
- ✅ Displays upload speed (KB/s or MB/s)
- ✅ Shows estimated time remaining
- ✅ Color-coded status: blue (uploading), green (success), red (failed)
- ✅ Detailed error messages for failed uploads

### AC-2.4: Duplicate Detection
- ✅ System calculates SHA-256 hash for each uploaded file
- ✅ Checks hash against existing resumes in database
- ✅ Displays warning if duplicate detected
- ✅ Shows original upload date and uploader name
- ✅ User can choose to: skip, replace, or upload as new version
- ✅ Duplicate check completes within 1 second

### AC-2.5: Resume Preview
- ✅ Preview button available after file selection
- ✅ Opens modal with first page of resume
- ✅ Supports preview for PDF and DOCX formats
- ✅ Shows "Preview not available" for TXT files with option to view raw text
- ✅ Preview loads within 2 seconds
- ✅ User can close preview and continue with upload

### AC-2.6: Virus Scanning (Non-Functional)
- ✅ All files scanned before storage
- ✅ Infected files rejected immediately
- ✅ User notified of security threat
- ✅ Infected files logged for security audit
- ✅ Scan completes within 3 seconds for files under 10MB

### AC-2.7: Auto-Cleanup (Non-Functional)
- ✅ Failed uploads deleted after 24 hours
- ✅ Temporary files cleaned up after processing
- ✅ Resumes older than 2 years archived
- ✅ Deleted resumes moved to recycle bin for 30 days

---

## 4. TECHNICAL DESIGN

### 4.1 Database Schema

#### 4.1.1 Resumes Table
```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- File Information
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('pdf', 'docx', 'txt')),
    file_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 hash for duplicate detection
    
    -- Candidate Information (extracted)
    candidate_name VARCHAR(200),
    candidate_email VARCHAR(255),
    candidate_phone VARCHAR(20),
    
    -- Parsed Data
    extracted_text TEXT,
    parsed_data JSONB,  -- Structured data: skills, experience, education
    
    -- Upload Metadata
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    upload_ip VARCHAR(45),
    
    -- Processing Status
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded' 
        CHECK (status IN ('uploaded', 'parsing', 'parsed', 'failed', 'archived')),
    virus_scan_status VARCHAR(20) DEFAULT 'pending'
        CHECK (virus_scan_status IN ('pending', 'clean', 'infected', 'failed')),
    virus_scan_date TIMESTAMP WITH TIME ZONE,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_file_hash (file_hash),
    INDEX idx_uploaded_by (uploaded_by),
    INDEX idx_upload_date (upload_date),
    INDEX idx_status (status),
    INDEX idx_candidate_email (candidate_email)
);
```

#### 4.1.2 Resume Upload History Table
```sql
CREATE TABLE resume_upload_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES resumes(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,  -- uploaded, updated, deleted, scanned
    performed_by UUID REFERENCES users(id),
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_resume_id (resume_id),
    INDEX idx_timestamp (timestamp)
);
```

#### 4.1.3 Bulk Upload Sessions Table
```sql
CREATE TABLE bulk_upload_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    total_files INTEGER NOT NULL,
    successful_uploads INTEGER DEFAULT 0,
    failed_uploads INTEGER DEFAULT 0,
    duplicate_files INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'cancelled')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);
```

### 4.2 API Endpoints

#### 4.2.1 Single Resume Upload
```
POST /api/resumes/upload
Content-Type: multipart/form-data

Request Body:
{
    "file": <binary>,
    "candidate_name": "string (optional)",
    "candidate_email": "string (optional)",
    "candidate_phone": "string (optional)"
}

Response (201 Created):
{
    "success": true,
    "message": "Resume uploaded successfully",
    "data": {
        "resume_id": "uuid",
        "file_name": "string",
        "file_size": integer,
        "file_type": "string",
        "upload_date": "datetime",
        "virus_scan_status": "clean",
        "is_duplicate": false
    }
}

Response (400 Bad Request):
{
    "success": false,
    "message": "Invalid file format",
    "errors": {
        "file": ["Only PDF, DOCX, and TXT files are allowed"]
    }
}

Response (409 Conflict - Duplicate):
{
    "success": false,
    "message": "Duplicate resume detected",
    "data": {
        "existing_resume_id": "uuid",
        "uploaded_by": "string",
        "upload_date": "datetime",
        "options": ["skip", "replace", "upload_new_version"]
    }
}
```

#### 4.2.2 Bulk Resume Upload
```
POST /api/resumes/bulk-upload
Content-Type: multipart/form-data

Request Body:
{
    "files": [<binary>, <binary>, ...],  // Max 50 files
    "session_id": "uuid (optional)"
}

Response (202 Accepted):
{
    "success": true,
    "message": "Bulk upload initiated",
    "data": {
        "session_id": "uuid",
        "total_files": integer,
        "status_url": "/api/resumes/bulk-upload/{session_id}/status"
    }
}
```

#### 4.2.3 Bulk Upload Status
```
GET /api/resumes/bulk-upload/{session_id}/status

Response (200 OK):
{
    "success": true,
    "data": {
        "session_id": "uuid",
        "status": "in_progress",
        "total_files": 50,
        "processed": 35,
        "successful": 30,
        "failed": 3,
        "duplicates": 2,
        "progress_percentage": 70,
        "files": [
            {
                "file_name": "john_doe_resume.pdf",
                "status": "success",
                "resume_id": "uuid"
            },
            {
                "file_name": "jane_smith_resume.pdf",
                "status": "failed",
                "error": "File size exceeds 10MB"
            }
        ]
    }
}
```

#### 4.2.4 List Resumes (Paginated)
```
GET /api/resumes?page=1&limit=20&status=parsed&uploaded_by=uuid

Response (200 OK):
{
    "success": true,
    "data": {
        "resumes": [
            {
                "id": "uuid",
                "file_name": "string",
                "candidate_name": "string",
                "candidate_email": "string",
                "upload_date": "datetime",
                "uploaded_by": "string",
                "status": "parsed",
                "file_size": integer
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 150,
            "total_pages": 8
        }
    }
}
```

#### 4.2.5 Get Resume Details
```
GET /api/resumes/{resume_id}

Response (200 OK):
{
    "success": true,
    "data": {
        "id": "uuid",
        "file_name": "string",
        "file_path": "string",
        "file_size": integer,
        "file_type": "pdf",
        "candidate_name": "string",
        "candidate_email": "string",
        "candidate_phone": "string",
        "extracted_text": "string",
        "parsed_data": {
            "skills": ["Python", "FastAPI"],
            "experience": [...],
            "education": [...]
        },
        "uploaded_by": {
            "id": "uuid",
            "name": "string",
            "email": "string"
        },
        "upload_date": "datetime",
        "status": "parsed",
        "virus_scan_status": "clean"
    }
}
```

#### 4.2.6 Delete Resume
```
DELETE /api/resumes/{resume_id}

Response (200 OK):
{
    "success": true,
    "message": "Resume deleted successfully"
}

Response (403 Forbidden):
{
    "success": false,
    "message": "You don't have permission to delete this resume"
}
```

#### 4.2.7 Check Duplicate
```
POST /api/resumes/check-duplicate
Content-Type: application/json

Request Body:
{
    "file_hash": "string"
}

Response (200 OK):
{
    "success": true,
    "is_duplicate": true,
    "data": {
        "resume_id": "uuid",
        "file_name": "string",
        "uploaded_by": "string",
        "upload_date": "datetime"
    }
}
```

### 4.3 UI Components & User Flow

#### 4.3.1 Upload Page Components
```
┌─────────────────────────────────────────┐
│  Resume Upload                          │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   📁 Drag & Drop Files Here       │ │
│  │                                   │ │
│  │   or click to browse              │ │
│  │                                   │ │
│  │   Supported: PDF, DOCX, TXT       │ │
│  │   Max size: 10MB per file         │ │
│  │   Bulk limit: 50 files            │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Selected Files:                        │
│  ┌───────────────────────────────────┐ │
│  │ ✓ john_doe.pdf (2.3 MB)    [X]    │ │
│  │ ✓ jane_smith.docx (1.8 MB) [X]    │ │
│  │ ⚠ large_file.pdf (12 MB)   [X]    │ │
│  │   Error: File size exceeds limit  │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [Preview Selected] [Upload All]       │
└─────────────────────────────────────────┘
```

#### 4.3.2 Upload Progress Modal
```
┌─────────────────────────────────────────┐
│  Uploading Resumes...            [X]    │
├─────────────────────────────────────────┤
│                                         │
│  Overall Progress: 60% (3/5 files)      │
│  ████████████░░░░░░░░                   │
│                                         │
│  ✓ john_doe.pdf - Uploaded              │
│  ✓ jane_smith.docx - Uploaded           │
│  ⟳ mike_jones.pdf - Uploading (45%)     │
│  ⏳ sarah_williams.pdf - Pending        │
│  ✗ invalid_file.txt - Failed            │
│    Error: Invalid format                │
│                                         │
│  [Cancel Upload]                        │
└─────────────────────────────────────────┘
```

#### 4.3.3 User Flow Diagram
```
Start
  │
  ├─> Select Upload Method
  │     ├─> Single File
  │     │     ├─> Drag & Drop / Browse
  │     │     ├─> Validate File
  │     │     │     ├─> Valid → Preview (optional)
  │     │     │     └─> Invalid → Show Error
  │     │     ├─> Check Duplicate
  │     │     │     ├─> Duplicate → Show Options
  │     │     │     └─> Unique → Continue
  │     │     ├─> Virus Scan
  │     │     │     ├─> Clean → Upload
  │     │     │     └─> Infected → Reject
  │     │     └─> Success → Show Resume ID
  │     │
  │     └─> Bulk Upload
  │           ├─> Select Multiple Files (max 50)
  │           ├─> Validate Each File
  │           ├─> Create Upload Session
  │           ├─> Process Files Asynchronously
  │           │     ├─> Show Real-time Progress
  │           │     └─> Update Status per File
  │           └─> Show Summary Report
  │
  └─> End
```

### 4.4 Integration Points

#### 4.4.1 Authentication System
- **Dependency:** User must be authenticated
- **Integration:** Use existing JWT token validation
- **User Context:** Extract user_id from token for `uploaded_by` field

#### 4.4.2 File Storage Service
- **Local Storage:** Development environment
- **Cloud Storage:** Production (S3/Azure Blob)
- **Path Structure:** `/{year}/{month}/{user_id}/{resume_id}.{ext}`

#### 4.4.3 Virus Scanning Service
- **Library:** ClamAV (open-source) or VirusTotal API
- **Integration:** Async scanning after upload
- **Fallback:** If scanner unavailable, mark as "scan_pending"

#### 4.4.4 Document Processing Pipeline
- **Trigger:** After successful upload and virus scan
- **Process:** Extract text → Parse data → Update resume record
- **Queue:** Use Celery for async processing

#### 4.4.5 Notification System
- **Events:** Upload success, bulk upload complete, duplicate detected
- **Channels:** In-app notifications, email (optional)

---

## 5. DEPENDENCIES

### 5.1 External Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| `python-multipart` | >=0.0.6 | Handle multipart form data |
| `aiofiles` | >=23.2.1 | Async file operations |
| `python-magic` | >=0.4.27 | File type detection |
| `hashlib` | Built-in | SHA-256 hash calculation |
| `clamd` | >=1.0.2 | ClamAV virus scanning |
| `PyPDF2` | >=3.0.0 | PDF preview generation |
| `python-docx` | >=1.1.0 | DOCX preview generation |

### 5.2 Internal Modules

| Module | Modification Required | Purpose |
|--------|----------------------|---------|
| `core/config.py` | Yes | Add upload settings (max size, allowed formats) |
| `core/storage.py` | Create New | File storage abstraction layer |
| `services/virus_scanner.py` | Create New | Virus scanning service |
| `services/file_processor.py` | Create New | File validation and processing |
| `models/database.py` | Yes | Add Resume, UploadHistory, BulkSession models |
| `api/resumes.py` | Create New | Resume upload endpoints |

### 5.3 Infrastructure Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Storage** | 100GB initial | Scalable cloud storage |
| **ClamAV** | Installed & Running | For virus scanning |
| **Celery Workers** | 2-4 workers | For async processing |
| **Redis** | Running | Task queue backend |
| **Database** | PostgreSQL 12+ | JSONB support required |

### 5.4 Prerequisites

- ✅ Feature 1 (Authentication) must be completed
- ✅ User roles and permissions configured
- ✅ File storage directory created with proper permissions
- ✅ ClamAV installed and virus definitions updated
- ✅ Celery and Redis configured

---

## 6. TESTING PLAN

### 6.1 Unit Tests

#### 6.1.1 File Validation Tests
```python
# tests/test_file_validator.py

def test_validate_file_format_pdf():
    """Test PDF file validation"""
    assert validate_file_format("resume.pdf") == True

def test_validate_file_format_invalid():
    """Test invalid file format rejection"""
    assert validate_file_format("resume.exe") == False

def test_validate_file_size_within_limit():
    """Test file size within 10MB limit"""
    assert validate_file_size(5 * 1024 * 1024) == True

def test_validate_file_size_exceeds_limit():
    """Test file size exceeding 10MB limit"""
    assert validate_file_size(15 * 1024 * 1024) == False

def test_calculate_file_hash():
    """Test SHA-256 hash calculation"""
    hash1 = calculate_file_hash(file_content)
    hash2 = calculate_file_hash(file_content)
    assert hash1 == hash2  # Same content = same hash
```

#### 6.1.2 Duplicate Detection Tests
```python
# tests/test_duplicate_detection.py

async def test_detect_duplicate_resume():
    """Test duplicate resume detection"""
    # Upload first resume
    resume1 = await upload_resume(file_content)
    
    # Try uploading same file
    result = await check_duplicate(file_hash)
    assert result["is_duplicate"] == True
    assert result["existing_resume_id"] == resume1.id

async def test_no_duplicate_for_unique_file():
    """Test unique file is not flagged as duplicate"""
    result = await check_duplicate(unique_file_hash)
    assert result["is_duplicate"] == False
```

#### 6.1.3 Virus Scanning Tests
```python
# tests/test_virus_scanner.py

async def test_scan_clean_file():
    """Test scanning clean file"""
    result = await scan_file(clean_file_path)
    assert result["status"] == "clean"

async def test_scan_infected_file():
    """Test scanning infected file (EICAR test file)"""
    result = await scan_file(eicar_test_file)
    assert result["status"] == "infected"

async def test_scan_timeout():
    """Test scanner timeout handling"""
    result = await scan_file(large_file, timeout=1)
    assert result["status"] == "failed"
```

### 6.2 Integration Tests

#### 6.2.1 Single Upload Flow
```python
# tests/integration/test_upload_flow.py

async def test_complete_upload_flow():
    """Test complete single resume upload flow"""
    # 1. Authenticate user
    token = await login_user("recruiter@test.com", "password")
    
    # 2. Upload resume
    response = await client.post(
        "/api/resumes/upload",
        files={"file": ("resume.pdf", pdf_content, "application/pdf")},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] == True
    assert "resume_id" in data["data"]
    
    # 3. Verify resume in database
    resume = await get_resume(data["data"]["resume_id"])
    assert resume.file_name == "resume.pdf"
    assert resume.virus_scan_status == "clean"
    assert resume.status == "uploaded"
```

#### 6.2.2 Bulk Upload Flow
```python
async def test_bulk_upload_flow():
    """Test bulk upload with multiple files"""
    files = [
        ("file", ("resume1.pdf", pdf1, "application/pdf")),
        ("file", ("resume2.pdf", pdf2, "application/pdf")),
        ("file", ("resume3.docx", docx1, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
    ]
    
    response = await client.post(
        "/api/resumes/bulk-upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 202
    session_id = response.json()["data"]["session_id"]
    
    # Poll status until complete
    status = await poll_upload_status(session_id)
    assert status["successful"] == 3
    assert status["failed"] == 0
```

### 6.3 Manual Testing Scenarios

#### Scenario 1: Single Resume Upload
1. Login as recruiter
2. Navigate to Resume Upload page
3. Drag and drop a PDF resume
4. Verify file appears in selected files list
5. Click "Preview" and verify resume displays
6. Click "Upload"
7. Verify success message with resume ID
8. Navigate to resumes list and verify new resume appears

#### Scenario 2: Bulk Upload with Mixed Results
1. Login as HR manager
2. Select 10 files: 7 valid PDFs, 2 oversized files, 1 invalid format
3. Click "Upload All"
4. Verify progress modal shows real-time updates
5. Verify 7 successful uploads
6. Verify 2 files rejected for size
7. Verify 1 file rejected for format
8. Verify summary report shows correct counts

#### Scenario 3: Duplicate Detection
1. Upload a resume successfully
2. Try uploading the same file again
3. Verify duplicate warning appears
4. Verify original upload details shown
5. Select "Skip" option
6. Verify file not uploaded again
7. Try again and select "Upload as new version"
8. Verify new version uploaded with different ID

#### Scenario 4: Virus Detection
1. Upload EICAR test file (standard virus test file)
2. Verify file rejected immediately
3. Verify error message indicates security threat
4. Verify file not saved to storage
5. Verify incident logged in security audit

### 6.4 Edge Cases

| Edge Case | Expected Behavior |
|-----------|-------------------|
| Upload 0-byte file | Reject with "File is empty" error |
| Upload file with no extension | Detect type by content, reject if invalid |
| Upload file with fake extension (exe renamed to pdf) | Detect by magic bytes, reject |
| Upload during network interruption | Show retry option, resume upload |
| Upload same file simultaneously | First completes, second flagged as duplicate |
| Upload 51 files in bulk | Reject with "Max 50 files allowed" |
| Upload while session expires | Redirect to login, preserve selected files |
| Upload with special characters in filename | Sanitize filename, preserve original in metadata |
| Upload file with Unicode filename | Support UTF-8, store correctly |
| Virus scanner unavailable | Mark as "scan_pending", process later |

---

## 7. IMPLEMENTATION PLAN

### Phase 1: Core Upload Functionality (Week 1-2)
**Effort:** 40 hours

#### Tasks:
1. **Database Setup** (4 hours)
   - Create resumes table migration
   - Create upload_history table migration
   - Create bulk_upload_sessions table migration
   - Add indexes and constraints

2. **File Storage Service** (8 hours)
   - Create storage abstraction layer
   - Implement local storage for development
   - Implement cloud storage (S3/Azure) for production
   - Add file path generation logic
   - Add cleanup utilities

3. **File Validation Service** (6 hours)
   - Implement file format validation
   - Implement file size validation
   - Implement magic byte detection
   - Add hash calculation (SHA-256)
   - Create validation error messages

4. **Single Upload API** (10 hours)
   - Create `/api/resumes/upload` endpoint
   - Implement file upload handling
   - Add duplicate detection logic
   - Integrate with storage service
   - Add response formatting
   - Write unit tests

5. **Upload UI - Basic** (12 hours)
   - Create upload page component
   - Implement drag-and-drop zone
   - Add file browser integration
   - Display selected files list
   - Show validation errors
   - Add upload button and progress

**Deliverables:**
- ✅ Single file upload working end-to-end
- ✅ File validation and duplicate detection
- ✅ Basic UI with drag-and-drop
- ✅ Unit tests for core services

**Risks & Mitigation:**
- **Risk:** File storage configuration issues
  - *Mitigation:* Start with local storage, add cloud later
- **Risk:** Large file upload timeouts
  - *Mitigation:* Implement chunked uploads if needed

---

### Phase 2: Bulk Upload & Advanced Features (Week 3-4)
**Effort:** 50 hours

#### Tasks:
1. **Virus Scanning Integration** (10 hours)
   - Install and configure ClamAV
   - Create virus scanner service
   - Implement async scanning with Celery
   - Add scan result handling
   - Create fallback for scanner unavailable
   - Write tests with EICAR file

2. **Bulk Upload API** (12 hours)
   - Create `/api/resumes/bulk-upload` endpoint
   - Implement session management
   - Add async file processing with Celery
   - Create status tracking endpoint
   - Implement progress calculation
   - Add cancellation support
   - Write integration tests

3. **Upload Progress Tracking** (8 hours)
   - Implement WebSocket for real-time updates
   - Create progress calculation logic
   - Add per-file status tracking
   - Implement upload speed calculation
   - Add estimated time remaining

4. **Resume Preview** (10 hours)
   - Create preview generation service
   - Implement PDF preview (first page)
   - Implement DOCX preview
   - Add preview modal component
   - Optimize preview loading speed

5. **Enhanced UI** (10 hours)
   - Add bulk upload interface
   - Create progress modal
   - Implement duplicate warning dialog
   - Add preview functionality
   - Create summary report view
   - Add retry failed uploads

**Deliverables:**
- ✅ Bulk upload with progress tracking
- ✅ Virus scanning integrated
- ✅ Resume preview working
- ✅ Complete UI with all features
- ✅ Integration tests passing

**Risks & Mitigation:**
- **Risk:** ClamAV installation issues
  - *Mitigation:* Provide Docker container with ClamAV pre-installed
- **Risk:** WebSocket connection issues
  - *Mitigation:* Fallback to polling if WebSocket fails
- **Risk:** Preview generation slow for large files
  - *Mitigation:* Cache previews, show loading state

---

### Phase 3: Polish & Production Readiness (Week 5)
**Effort:** 30 hours

#### Tasks:
1. **Performance Optimization** (8 hours)
   - Add database query optimization
   - Implement file upload chunking for large files
   - Add caching for duplicate checks
   - Optimize preview generation
   - Load testing and tuning

2. **Error Handling & Logging** (6 hours)
   - Add comprehensive error handling
   - Implement detailed logging
   - Create error recovery mechanisms
   - Add user-friendly error messages

3. **Security Hardening** (6 hours)
   - Add rate limiting on upload endpoints
   - Implement file type verification (magic bytes)
   - Add CSRF protection
   - Sanitize filenames
   - Add upload audit logging

4. **Auto-Cleanup Jobs** (4 hours)
   - Create Celery task for failed upload cleanup
   - Implement 2-year archive job
   - Add temporary file cleanup
   - Create recycle bin for deleted resumes

5. **Documentation & Deployment** (6 hours)
   - Write API documentation
   - Create user guide
   - Update deployment scripts
   - Create monitoring dashboards
   - Write runbook for operations

**Deliverables:**
- ✅ Production-ready upload system
- ✅ Complete documentation
- ✅ Monitoring and alerts configured
- ✅ All tests passing (unit + integration)
- ✅ Security audit completed

**Risks & Mitigation:**
- **Risk:** Performance issues under load
  - *Mitigation:* Load test early, scale infrastructure
- **Risk:** Storage costs exceeding budget
  - *Mitigation:* Implement compression, archive old files

---

### Total Effort Estimate
- **Phase 1:** 40 hours (2 weeks)
- **Phase 2:** 50 hours (2 weeks)
- **Phase 3:** 30 hours (1 week)
- **Total:** 120 hours (5 weeks)
- **Buffer:** +20% = 144 hours (6 weeks)

---

## 8. SUCCESS METRICS

### 8.1 Key Performance Indicators (KPIs)

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Upload Success Rate** | > 98% | (Successful uploads / Total uploads) × 100 |
| **Average Upload Time** | < 5 seconds | Time from upload start to completion (files < 5MB) |
| **Bulk Upload Completion Rate** | > 95% | (Completed sessions / Total sessions) × 100 |
| **Duplicate Detection Accuracy** | 100% | (Correctly identified duplicates / Total duplicates) × 100 |
| **Virus Detection Rate** | 100% | (Infected files blocked / Total infected files) × 100 |
| **User Satisfaction** | > 4.5/5 | Post-upload survey rating |

### 8.2 Business Metrics

| Metric | Target | Impact |
|--------|--------|--------|
| **Daily Upload Volume** | 500+ resumes/day | Measure adoption |
| **Time Saved per Upload** | 2 minutes | vs manual entry |
| **Storage Efficiency** | < 5GB/1000 resumes | Cost optimization |
| **Duplicate Prevention** | 10% reduction | Data quality |
| **Failed Upload Rate** | < 2% | System reliability |

### 8.3 Technical Metrics

| Metric | Target | Monitoring Tool |
|--------|--------|-----------------|
| **API Response Time (p95)** | < 200ms | Application monitoring |
| **File Processing Time** | < 10 seconds | Celery task monitoring |
| **Storage Usage Growth** | < 10GB/week | Cloud storage metrics |
| **Error Rate** | < 1% | Error tracking system |
| **Uptime** | > 99.9% | Infrastructure monitoring |

### 8.4 Success Criteria

**Feature is considered successful if:**
1. ✅ Upload success rate > 98% for 2 consecutive weeks
2. ✅ No critical bugs reported for 1 week post-launch
3. ✅ User satisfaction score > 4.5/5
4. ✅ Daily upload volume reaches 500+ resumes
5. ✅ Zero security incidents related to file uploads
6. ✅ All automated tests passing with > 90% code coverage

### 8.5 Monitoring & Alerts

**Dashboard Metrics:**
- Real-time upload success/failure rate
- Average upload time (hourly)
- Storage usage trend
- Top error types
- User activity heatmap

**Alerts:**
- Upload success rate drops below 95%
- Average upload time exceeds 10 seconds
- Virus detected (immediate alert)
- Storage usage exceeds 80% capacity
- Error rate exceeds 5% in 5 minutes

---

## 9. APPENDIX

### 9.1 File Format Specifications

| Format | MIME Type | Max Size | Preview Support |
|--------|-----------|----------|-----------------|
| PDF | application/pdf | 10MB | Yes (first page) |
| DOCX | application/vnd.openxmlformats-officedocument.wordprocessingml.document | 10MB | Yes (converted) |
| TXT | text/plain | 10MB | Yes (raw text) |

### 9.2 Error Codes

| Code | Message | HTTP Status |
|------|---------|-------------|
| UPLOAD_001 | Invalid file format | 400 |
| UPLOAD_002 | File size exceeds limit | 400 |
| UPLOAD_003 | Duplicate file detected | 409 |
| UPLOAD_004 | Virus detected | 400 |
| UPLOAD_005 | Upload failed | 500 |
| UPLOAD_006 | Bulk upload limit exceeded | 400 |
| UPLOAD_007 | Storage quota exceeded | 507 |

### 9.3 Configuration Settings

```python
# config/upload_settings.py

UPLOAD_SETTINGS = {
    "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
    "ALLOWED_FORMATS": ["pdf", "docx", "txt"],
    "BULK_UPLOAD_LIMIT": 50,
    "VIRUS_SCAN_TIMEOUT": 30,  # seconds
    "UPLOAD_TIMEOUT": 300,  # 5 minutes
    "CHUNK_SIZE": 1024 * 1024,  # 1MB chunks
    "PREVIEW_CACHE_TTL": 3600,  # 1 hour
    "FAILED_UPLOAD_RETENTION": 24,  # hours
    "RESUME_RETENTION_YEARS": 2,
    "RECYCLE_BIN_RETENTION_DAYS": 30
}
```

---

## 10. SIGN-OFF

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Product Manager** | | | |
| **Engineering Lead** | | | |
| **QA Lead** | | | |
| **Security Lead** | | | |
| **DevOps Lead** | | | |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-03 | Product Team | Initial PRD creation |

---

**Next Steps:**
1. Review and approve PRD
2. Create technical implementation document (similar to Feature 1)
3. Set up development environment
4. Begin Phase 1 implementation
5. Schedule daily standups during development

---

*This PRD is a living document and will be updated as requirements evolve.*
