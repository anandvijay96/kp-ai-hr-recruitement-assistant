# PRD: Resume Upload & Data Extraction

**Feature ID:** 02  
**Feature Name:** Resume Upload & Data Extraction  
**Priority:** P0 (Critical)  
**Complexity:** High  
**Estimated Effort:** 3-4 weeks  
**Phase:** 1 (Foundation)  
**Status:** Draft

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Goals & Success Metrics](#goals--success-metrics)
3. [User Stories](#user-stories)
4. [Functional Requirements](#functional-requirements)
5. [Technical Requirements](#technical-requirements)
6. [Database Schema](#database-schema)
7. [API Specifications](#api-specifications)
8. [UI/UX Specifications](#uiux-specifications)
9. [Testing Strategy](#testing-strategy)
10. [Implementation Plan](#implementation-plan)
11. [Dependencies & Risks](#dependencies--risks)

---

## 1. Overview

### 1.1 Feature Description
Enhanced resume upload system that allows recruiters to upload single or multiple resumes, automatically extract structured data, and detect duplicates to maintain data quality.

### 1.2 Business Value
- **Efficiency:** Reduce manual data entry by 90%
- **Accuracy:** 95%+ data extraction accuracy
- **Scale:** Process 100+ resumes in < 5 minutes
- **Quality:** Prevent duplicate candidate entries

### 1.3 Target Users
- **Primary:** Recruiters uploading candidate resumes
- **Secondary:** Hiring Managers reviewing candidates
- **Tertiary:** Admins managing system data

---

## 2. Goals & Success Metrics

### 2.1 Goals
1. Enable bulk resume upload (up to 50 files simultaneously)
2. Extract structured data with 95%+ accuracy
3. Detect 99%+ of duplicate resumes
4. Provide real-time progress feedback
5. Handle errors gracefully with clear messaging

### 2.2 Success Metrics

**Functional Metrics:**
- Data extraction accuracy: > 95%
- Duplicate detection rate: > 99%
- Processing speed: 100 resumes in < 5 minutes
- Error rate: < 1%

**User Experience Metrics:**
- Upload success rate: > 98%
- User satisfaction: > 4/5 stars
- Time to upload 10 resumes: < 2 minutes

**Technical Metrics:**
- API response time: < 500ms
- Background job completion: > 99%
- System uptime: 99.9%

---

## 3. User Stories

### 3.1 Epic: Resume Upload

**US-2.1: Single Resume Upload**
```
As a recruiter
I want to upload a single resume
So that I can quickly add a new candidate to the system

Acceptance Criteria:
- [ ] Support PDF, DOC, DOCX formats
- [ ] File size limit: 10MB
- [ ] Show upload progress
- [ ] Display success/error message
- [ ] Extract data automatically
- [ ] Show extracted data for review
- [ ] Allow manual corrections
- [ ] Save candidate to database
```

**US-2.2: Bulk Resume Upload**
```
As a recruiter
I want to upload multiple resumes at once
So that I can process candidates efficiently

Acceptance Criteria:
- [ ] Support up to 50 files simultaneously
- [ ] Drag-and-drop interface
- [ ] Show progress for each file
- [ ] Process files in background
- [ ] Show summary of successes/failures
- [ ] Allow retry for failed uploads
- [ ] Export results as CSV
```

**US-2.3: Data Extraction**
```
As a recruiter
I want candidate data automatically extracted from resumes
So that I don't have to manually enter information

Acceptance Criteria:
- [ ] Extract: Name, Email, Phone, LinkedIn
- [ ] Extract: Education (degree, institution, year)
- [ ] Extract: Work Experience (company, role, duration)
- [ ] Extract: Skills and certifications
- [ ] Handle multiple formats and layouts
- [ ] Confidence score for each field
- [ ] Allow manual override of extracted data
```

**US-2.4: Duplicate Detection**
```
As a recruiter
I want to be notified if a resume is a duplicate
So that I don't create duplicate candidate records

Acceptance Criteria:
- [ ] Check by email address (exact match)
- [ ] Check by phone number (normalized)
- [ ] Check by name similarity (fuzzy match)
- [ ] Check by content similarity (> 90%)
- [ ] Show existing candidate details
- [ ] Options: Skip, Merge, or Force Create
- [ ] Log duplicate detection events
```

**US-2.5: Error Handling**
```
As a recruiter
I want clear error messages when uploads fail
So that I can fix issues and retry

Acceptance Criteria:
- [ ] Validate file format before upload
- [ ] Validate file size before upload
- [ ] Handle corrupted files gracefully
- [ ] Handle password-protected files
- [ ] Show specific error messages
- [ ] Provide troubleshooting tips
- [ ] Allow retry without re-uploading
```

---

## 4. Functional Requirements

### 4.1 Upload Functionality

**FR-2.1.1: File Format Support**
- Support: PDF, DOC, DOCX
- Reject: Other formats with clear message
- Validate: File type by content (not just extension)

**FR-2.1.2: File Size Limits**
- Single file: Max 10MB
- Batch upload: Max 50 files or 200MB total
- Show size validation before upload

**FR-2.1.3: Upload Interface**
- File picker button
- Drag-and-drop zone
- Multiple file selection
- Preview selected files
- Remove files before upload

**FR-2.1.4: Progress Tracking**
- Individual file progress (0-100%)
- Overall batch progress
- Estimated time remaining
- Cancel upload option

### 4.2 Data Extraction

**FR-2.2.1: Personal Information**
```python
{
    "name": str,              # Full name
    "email": str,             # Primary email
    "phone": str,             # Primary phone (normalized)
    "linkedin_url": str,      # LinkedIn profile URL
    "location": str,          # Current location
    "confidence": {           # Confidence scores
        "name": float,        # 0.0 - 1.0
        "email": float,
        "phone": float
    }
}
```

**FR-2.2.2: Education**
```python
{
    "education": [
        {
            "degree": str,           # e.g., "Bachelor of Science"
            "field": str,            # e.g., "Computer Science"
            "institution": str,      # University name
            "location": str,         # City, Country
            "start_date": str,       # YYYY-MM or YYYY
            "end_date": str,         # YYYY-MM or YYYY or "Present"
            "gpa": float,            # Optional
            "confidence": float      # 0.0 - 1.0
        }
    ]
}
```

**FR-2.2.3: Work Experience**
```python
{
    "experience": [
        {
            "company": str,          # Company name
            "title": str,            # Job title
            "location": str,         # City, Country
            "start_date": str,       # YYYY-MM
            "end_date": str,         # YYYY-MM or "Present"
            "duration_months": int,  # Calculated
            "description": str,      # Job description
            "achievements": [str],   # Bullet points
            "confidence": float      # 0.0 - 1.0
        }
    ],
    "total_experience_months": int  # Sum of all experience
}
```

**FR-2.2.4: Skills & Certifications**
```python
{
    "skills": [
        {
            "name": str,             # Skill name
            "category": str,         # Technical, Soft, Language
            "proficiency": str,      # Beginner, Intermediate, Expert
            "confidence": float      # 0.0 - 1.0
        }
    ],
    "certifications": [
        {
            "name": str,             # Certification name
            "issuer": str,           # Issuing organization
            "date": str,             # YYYY-MM
            "expiry_date": str,      # YYYY-MM or null
            "credential_id": str,    # Optional
            "confidence": float      # 0.0 - 1.0
        }
    ]
}
```

### 4.3 Duplicate Detection

**FR-2.3.1: Detection Methods**

1. **Email Match (Exact)**
   - Normalize email (lowercase, trim)
   - Exact match in database
   - Highest confidence

2. **Phone Match (Normalized)**
   - Remove formatting: +1 (555) 123-4567 → 15551234567
   - Match last 10 digits
   - High confidence

3. **Name Similarity (Fuzzy)**
   - Levenshtein distance
   - Threshold: > 85% similarity
   - Medium confidence

4. **Content Similarity (Semantic)**
   - Compare resume text
   - TF-IDF or embeddings
   - Threshold: > 90% similarity
   - Lower confidence

**FR-2.3.2: Duplicate Resolution**
- Show existing candidate details
- Show similarity score
- Options:
  - **Skip:** Don't upload duplicate
  - **Merge:** Update existing record
  - **Force Create:** Create new record anyway
- Log decision for audit

### 4.4 Background Processing

**FR-2.4.1: Job Queue**
- Use Celery + Redis
- Process uploads asynchronously
- Retry failed jobs (max 3 attempts)
- Job timeout: 5 minutes per resume

**FR-2.4.2: Status Updates**
- Real-time progress via WebSocket
- Fallback to polling (every 2 seconds)
- Job states: PENDING, PROCESSING, SUCCESS, FAILED

---

## 5. Technical Requirements

### 5.1 Technology Stack

**Backend:**
- FastAPI (existing)
- SQLAlchemy ORM
- Celery for background jobs
- Redis for job queue
- spaCy for NLP

**Data Extraction:**
- PyMuPDF (PDF)
- python-docx (DOCX)
- spaCy (entity extraction)
- Regular expressions (patterns)

**Duplicate Detection:**
- FuzzyWuzzy (string similarity)
- scikit-learn (TF-IDF, cosine similarity)

### 5.2 Architecture

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTP POST /api/upload
       ▼
┌─────────────┐
│   FastAPI   │
│  API Server │
└──────┬──────┘
       │ Save files
       │ Create Celery task
       ▼
┌─────────────┐
│    Redis    │
│  Job Queue  │
└──────┬──────┘
       │ Task: process_resume
       ▼
┌─────────────┐
│   Celery    │
│   Worker    │
└──────┬──────┘
       │ 1. Extract text
       │ 2. Parse data
       │ 3. Check duplicates
       │ 4. Save to DB
       ▼
┌─────────────┐
│  PostgreSQL │
│  Database   │
└─────────────┘
```

### 5.3 Performance Requirements

- Upload API response: < 500ms
- File processing: < 30 seconds per resume
- Batch processing: 100 resumes in < 5 minutes
- Duplicate check: < 2 seconds
- Concurrent uploads: Support 10 users simultaneously

---

## 6. Database Schema

### 6.1 Tables

**candidates**
```sql
CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Personal Info
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    linkedin_url VARCHAR(500),
    location VARCHAR(255),
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'upload',  -- upload, referral, job_board
    status VARCHAR(50) DEFAULT 'new',     -- new, screened, interviewed, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    
    -- Search
    search_vector TSVECTOR,  -- Full-text search
    
    -- Indexes
    INDEX idx_candidates_email (email),
    INDEX idx_candidates_phone (phone),
    INDEX idx_candidates_name (full_name),
    INDEX idx_candidates_status (status),
    INDEX idx_candidates_search (search_vector) USING GIN
);
```

**resumes**
```sql
CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    
    -- File Info
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,  -- pdf, docx
    file_hash VARCHAR(64) NOT NULL,  -- SHA-256 for duplicate detection
    
    -- Processing
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    processed_at TIMESTAMP,
    processing_error TEXT,
    
    -- Content
    raw_text TEXT,
    extracted_data JSONB,  -- All extracted data
    
    -- Metadata
    uploaded_at TIMESTAMP DEFAULT NOW(),
    uploaded_by INTEGER REFERENCES users(id),
    
    -- Indexes
    INDEX idx_resumes_candidate (candidate_id),
    INDEX idx_resumes_hash (file_hash),
    INDEX idx_resumes_status (status)
);
```

**education**
```sql
CREATE TABLE education (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    
    degree VARCHAR(255),
    field VARCHAR(255),
    institution VARCHAR(255),
    location VARCHAR(255),
    start_date DATE,
    end_date DATE,
    gpa DECIMAL(3, 2),
    
    confidence_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_education_candidate (candidate_id),
    INDEX idx_education_degree (degree),
    INDEX idx_education_institution (institution)
);
```

**work_experience**
```sql
CREATE TABLE work_experience (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    
    company VARCHAR(255),
    title VARCHAR(255),
    location VARCHAR(255),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    duration_months INTEGER,
    description TEXT,
    achievements TEXT[],
    
    confidence_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_experience_candidate (candidate_id),
    INDEX idx_experience_company (company),
    INDEX idx_experience_title (title)
);
```

**skills**
```sql
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),  -- technical, soft, language
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE candidate_skills (
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
    proficiency VARCHAR(50),  -- beginner, intermediate, expert
    confidence_score DECIMAL(3, 2),
    PRIMARY KEY (candidate_id, skill_id),
    
    INDEX idx_candidate_skills_candidate (candidate_id),
    INDEX idx_candidate_skills_skill (skill_id)
);
```

**certifications**
```sql
CREATE TABLE certifications (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    issuer VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    credential_id VARCHAR(255),
    credential_url VARCHAR(500),
    
    confidence_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_certifications_candidate (candidate_id),
    INDEX idx_certifications_name (name)
);
```

**duplicate_checks**
```sql
CREATE TABLE duplicate_checks (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id),
    candidate_id INTEGER REFERENCES candidates(id),
    
    match_type VARCHAR(50),  -- email, phone, name, content
    match_score DECIMAL(5, 4),
    matched_candidate_id INTEGER REFERENCES candidates(id),
    
    resolution VARCHAR(50),  -- skip, merge, force_create
    resolved_by INTEGER REFERENCES users(id),
    resolved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_duplicate_checks_resume (resume_id),
    INDEX idx_duplicate_checks_candidate (candidate_id)
);
```

---

## 7. API Specifications

### 7.1 Upload Resume (Single)

**Endpoint:** `POST /api/resumes/upload`

**Request:**
```http
POST /api/resumes/upload
Content-Type: multipart/form-data

file: <resume.pdf>
check_duplicates: true
```

**Response (Success):**
```json
{
    "status": "success",
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Resume uploaded successfully. Processing in background.",
    "resume": {
        "id": 123,
        "filename": "john_doe_resume.pdf",
        "status": "processing"
    }
}
```

**Response (Duplicate Found):**
```json
{
    "status": "duplicate_found",
    "resume": {
        "id": 123,
        "filename": "john_doe_resume.pdf"
    },
    "duplicates": [
        {
            "candidate_id": 456,
            "name": "John Doe",
            "email": "john@example.com",
            "match_type": "email",
            "match_score": 1.0,
            "uploaded_at": "2025-09-15T10:30:00Z"
        }
    ],
    "options": ["skip", "merge", "force_create"]
}
```

### 7.2 Upload Resumes (Bulk)

**Endpoint:** `POST /api/resumes/upload/batch`

**Request:**
```http
POST /api/resumes/upload/batch
Content-Type: multipart/form-data

files: [<resume1.pdf>, <resume2.pdf>, ...]
check_duplicates: true
```

**Response:**
```json
{
    "status": "success",
    "batch_id": "batch_550e8400",
    "total_files": 10,
    "message": "Batch upload started. Processing in background.",
    "job_ids": [
        "job_1",
        "job_2",
        ...
    ]
}
```

### 7.3 Get Upload Status

**Endpoint:** `GET /api/resumes/upload/status/{job_id}`

**Response:**
```json
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",  // pending, processing, completed, failed
    "progress": 65,  // 0-100
    "message": "Extracting work experience...",
    "result": null  // Available when status = completed
}
```

### 7.4 Get Batch Status

**Endpoint:** `GET /api/resumes/upload/batch/{batch_id}`

**Response:**
```json
{
    "batch_id": "batch_550e8400",
    "status": "processing",
    "total": 10,
    "completed": 7,
    "failed": 1,
    "pending": 2,
    "results": [
        {
            "job_id": "job_1",
            "filename": "resume1.pdf",
            "status": "completed",
            "candidate_id": 123
        },
        {
            "job_id": "job_2",
            "filename": "resume2.pdf",
            "status": "failed",
            "error": "Corrupted file"
        }
    ]
}
```

### 7.5 Resolve Duplicate

**Endpoint:** `POST /api/resumes/{resume_id}/resolve-duplicate`

**Request:**
```json
{
    "action": "merge",  // skip, merge, force_create
    "matched_candidate_id": 456
}
```

**Response:**
```json
{
    "status": "success",
    "action": "merge",
    "candidate_id": 456,
    "message": "Resume merged with existing candidate"
}
```

---

## 8. UI/UX Specifications

### 8.1 Upload Page

**Layout:**
```
┌────────────────────────────────────────────────┐
│  📤 Upload Resumes                             │
├────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │                                           │ │
│  │     Drag & Drop files here               │ │
│  │     or                                    │ │
│  │     [Choose Files]                        │ │
│  │                                           │ │
│  │     Supported: PDF, DOC, DOCX            │ │
│  │     Max size: 10MB per file              │ │
│  │     Max files: 50                         │ │
│  │                                           │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  Selected Files (3):                           │
│  ┌──────────────────────────────────────────┐ │
│  │ ✓ john_doe.pdf (2.3 MB)          [×]    │ │
│  │ ✓ jane_smith.docx (1.8 MB)       [×]    │ │
│  │ ✓ bob_jones.pdf (3.1 MB)         [×]    │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  ☑ Check for duplicates                        │
│                                                 │
│  [Upload All]  [Clear All]                     │
│                                                 │
└────────────────────────────────────────────────┘
```

### 8.2 Progress View

```
┌────────────────────────────────────────────────┐
│  📊 Upload Progress                            │
├────────────────────────────────────────────────┤
│                                                 │
│  Overall: 7/10 completed (70%)                 │
│  ████████████████░░░░░░░░░░                   │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │ ✓ john_doe.pdf                           │ │
│  │   Status: Completed                       │ │
│  │   Candidate: John Doe                     │ │
│  │   [View Details]                          │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │ ⚠ jane_smith.docx                        │ │
│  │   Status: Duplicate Found                 │ │
│  │   Match: Jane Smith (jane@example.com)   │ │
│  │   [Skip] [Merge] [Force Create]          │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │ ⏳ bob_jones.pdf                          │ │
│  │   Status: Processing (65%)                │ │
│  │   ████████████████░░░░░░                 │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  ┌──────────────────────────────────────────┐ │
│  │ ✗ corrupted.pdf                           │ │
│  │   Status: Failed                          │ │
│  │   Error: Unable to read file              │ │
│  │   [Retry]                                 │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
└────────────────────────────────────────────────┘
```

### 8.3 Candidate Details (After Upload)

```
┌────────────────────────────────────────────────┐
│  👤 Candidate Details                          │
├────────────────────────────────────────────────┤
│                                                 │
│  Personal Information                          │
│  ┌──────────────────────────────────────────┐ │
│  │ Name:     John Doe                ✏️     │ │
│  │ Email:    john@example.com        ✏️     │ │
│  │ Phone:    +1 (555) 123-4567       ✏️     │ │
│  │ LinkedIn: linkedin.com/in/johndoe ✏️     │ │
│  │ Location: San Francisco, CA       ✏️     │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  Education                                     │
│  ┌──────────────────────────────────────────┐ │
│  │ • BS Computer Science                     │ │
│  │   Stanford University (2015-2019)         │ │
│  │   GPA: 3.8                        ✏️     │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  Work Experience (5 years)                     │
│  ┌──────────────────────────────────────────┐ │
│  │ • Senior Software Engineer                │ │
│  │   Google (2021-Present)                   │ │
│  │   - Led team of 5 engineers               │ │
│  │   - Improved performance by 40%   ✏️     │ │
│  └──────────────────────────────────────────┘ │
│                                                 │
│  Skills (12)                                   │
│  [Python] [Java] [React] [AWS] ...    ✏️     │
│                                                 │
│  Certifications (2)                            │
│  • AWS Certified Solutions Architect          │
│  • PMP Certification                   ✏️     │
│                                                 │
│  [Save] [Cancel]                               │
│                                                 │
└────────────────────────────────────────────────┘
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Test Coverage:**
- Data extraction functions
- Duplicate detection algorithms
- File validation
- Database operations

**Example Tests:**
```python
def test_extract_email():
    text = "Contact: john@example.com"
    email = extract_email(text)
    assert email == "john@example.com"

def test_detect_duplicate_by_email():
    candidate = create_candidate(email="john@example.com")
    is_duplicate = check_duplicate(email="john@example.com")
    assert is_duplicate == True

def test_normalize_phone():
    phone = "+1 (555) 123-4567"
    normalized = normalize_phone(phone)
    assert normalized == "15551234567"
```

### 9.2 Integration Tests

**Test Scenarios:**
- Upload single resume (PDF)
- Upload single resume (DOCX)
- Upload batch of resumes
- Duplicate detection workflow
- Error handling (corrupted file)
- Background job processing

**Example Test:**
```python
async def test_upload_resume():
    # Upload file
    response = await client.post(
        "/api/resumes/upload",
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )
    assert response.status_code == 200
    
    # Check job created
    job_id = response.json()["job_id"]
    assert job_id is not None
    
    # Wait for processing
    await wait_for_job(job_id)
    
    # Verify candidate created
    candidate = await get_candidate_by_job(job_id)
    assert candidate.name == "John Doe"
```

### 9.3 End-to-End Tests

**Test Flows:**
1. Complete upload flow (upload → process → review → save)
2. Duplicate resolution flow (upload → duplicate found → merge)
3. Batch upload flow (upload multiple → track progress → review all)
4. Error recovery flow (upload → fail → retry → success)

---

## 10. Implementation Plan

### 10.1 Week 1: Foundation

**Day 1-2: Database Setup**
- [ ] Create database schema
- [ ] Write Alembic migrations
- [ ] Create SQLAlchemy models
- [ ] Write repository classes

**Day 3-4: File Upload API**
- [ ] Create upload endpoint
- [ ] Implement file validation
- [ ] Set up file storage
- [ ] Add progress tracking

**Day 5: Testing**
- [ ] Write unit tests for models
- [ ] Write integration tests for upload API
- [ ] Test file validation

### 10.2 Week 2: Data Extraction

**Day 1-2: Text Extraction**
- [ ] Implement PDF text extraction
- [ ] Implement DOCX text extraction
- [ ] Handle OCR for image-based PDFs
- [ ] Write tests

**Day 3-4: Entity Extraction**
- [ ] Extract personal information
- [ ] Extract education
- [ ] Extract work experience
- [ ] Extract skills
- [ ] Write tests

**Day 5: Refinement**
- [ ] Improve extraction accuracy
- [ ] Add confidence scores
- [ ] Handle edge cases
- [ ] Write tests

### 10.3 Week 3: Duplicate Detection & Background Jobs

**Day 1-2: Duplicate Detection**
- [ ] Implement email matching
- [ ] Implement phone matching
- [ ] Implement name similarity
- [ ] Implement content similarity
- [ ] Write tests

**Day 3-4: Background Jobs**
- [ ] Set up Celery
- [ ] Create resume processing task
- [ ] Implement job status tracking
- [ ] Add retry logic
- [ ] Write tests

**Day 5: Integration**
- [ ] Connect upload API to Celery
- [ ] Test end-to-end flow
- [ ] Performance testing

### 10.4 Week 4: UI & Polish

**Day 1-2: Upload UI**
- [ ] Create upload page
- [ ] Implement drag-and-drop
- [ ] Add file preview
- [ ] Show validation errors

**Day 3-4: Progress & Results UI**
- [ ] Create progress view
- [ ] Implement real-time updates
- [ ] Create candidate details view
- [ ] Add edit functionality

**Day 5: Testing & Deployment**
- [ ] End-to-end testing
- [ ] User acceptance testing
- [ ] Performance testing
- [ ] Deploy to staging
- [ ] Documentation

---

## 11. Dependencies & Risks

### 11.1 Dependencies

**Internal:**
- ✅ Database schema design
- ✅ User authentication (Feature 1)
- ⏳ File storage setup
- ⏳ Celery/Redis configuration

**External:**
- PyMuPDF library
- python-docx library
- spaCy models
- Redis server

### 11.2 Risks

**Risk 1: Data Extraction Accuracy**
- **Impact:** High
- **Probability:** Medium
- **Mitigation:**
  - Use multiple extraction methods
  - Add manual review step
  - Continuous improvement with feedback
  - Confidence scores for each field

**Risk 2: Performance at Scale**
- **Impact:** High
- **Probability:** Medium
- **Mitigation:**
  - Background job processing
  - Horizontal scaling of Celery workers
  - Database indexing
  - Caching

**Risk 3: Duplicate Detection False Positives**
- **Impact:** Medium
- **Probability:** Medium
- **Mitigation:**
  - Multiple detection methods
  - Confidence scores
  - Manual review option
  - Logging for analysis

**Risk 4: File Format Variations**
- **Impact:** Medium
- **Probability:** High
- **Mitigation:**
  - Support multiple extraction libraries
  - Fallback to OCR
  - Handle errors gracefully
  - User feedback mechanism

---

## 12. Appendices

### 12.1 Sample Data Extraction

**Input:** Resume PDF

**Output:**
```json
{
    "personal_info": {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "linkedin": "linkedin.com/in/johndoe",
        "location": "San Francisco, CA",
        "confidence": {
            "name": 0.98,
            "email": 1.0,
            "phone": 0.95,
            "linkedin": 1.0
        }
    },
    "education": [
        {
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "institution": "Stanford University",
            "location": "Stanford, CA",
            "start_date": "2015-09",
            "end_date": "2019-06",
            "gpa": 3.8,
            "confidence": 0.92
        }
    ],
    "experience": [
        {
            "company": "Google",
            "title": "Senior Software Engineer",
            "location": "Mountain View, CA",
            "start_date": "2021-03",
            "end_date": "Present",
            "duration_months": 42,
            "description": "Led development of...",
            "achievements": [
                "Improved system performance by 40%",
                "Mentored 5 junior engineers"
            ],
            "confidence": 0.95
        }
    ],
    "skills": [
        {"name": "Python", "category": "technical", "proficiency": "expert", "confidence": 0.98},
        {"name": "Java", "category": "technical", "proficiency": "expert", "confidence": 0.95},
        {"name": "AWS", "category": "technical", "proficiency": "intermediate", "confidence": 0.90}
    ],
    "certifications": [
        {
            "name": "AWS Certified Solutions Architect",
            "issuer": "Amazon Web Services",
            "date": "2022-06",
            "expiry_date": "2025-06",
            "credential_id": "AWS-SA-12345",
            "confidence": 0.98
        }
    ],
    "total_experience_months": 60
}
```

---

**Status:** Ready for Implementation  
**Next:** Begin Week 1 implementation
