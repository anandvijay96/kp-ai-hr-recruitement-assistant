# Feature 2: Resume Upload & Data Extraction - Technical Implementation

**Feature ID:** 02  
**Document Version:** 1.0  
**Last Updated:** 2025-10-06  
**Status:** Ready for Implementation

---

## 1. DATABASE DESIGN

### 1.1 New Tables Required

#### **candidates** (New Table)
```sql
CREATE TABLE candidates (
    id VARCHAR(36) PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    
    -- Personal Information
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    linkedin_url VARCHAR(500),
    location VARCHAR(255),
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'upload',
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36) REFERENCES users(id),
    
    -- Indexes
    INDEX idx_candidates_email (email),
    INDEX idx_candidates_phone (phone),
    INDEX idx_candidates_name (full_name),
    INDEX idx_candidates_status (status)
);
```

#### **education** (New Table)
```sql
CREATE TABLE education (
    id VARCHAR(36) PRIMARY KEY,
    candidate_id VARCHAR(36) REFERENCES candidates(id) ON DELETE CASCADE,
    
    degree VARCHAR(255),
    field VARCHAR(255),
    institution VARCHAR(255),
    location VARCHAR(255),
    start_date DATE,
    end_date DATE,
    gpa DECIMAL(3, 2),
    
    confidence_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_education_candidate (candidate_id)
);
```

#### **work_experience** (New Table)
```sql
CREATE TABLE work_experience (
    id VARCHAR(36) PRIMARY KEY,
    candidate_id VARCHAR(36) REFERENCES candidates(id) ON DELETE CASCADE,
    
    company VARCHAR(255),
    title VARCHAR(255),
    location VARCHAR(255),
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,
    duration_months INTEGER,
    description TEXT,
    
    confidence_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_experience_candidate (candidate_id)
);
```

#### **skills** (New Table)
```sql
CREATE TABLE skills (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE candidate_skills (
    candidate_id VARCHAR(36) REFERENCES candidates(id) ON DELETE CASCADE,
    skill_id VARCHAR(36) REFERENCES skills(id) ON DELETE CASCADE,
    proficiency VARCHAR(50),
    confidence_score DECIMAL(3, 2),
    PRIMARY KEY (candidate_id, skill_id)
);
```

#### **certifications** (New Table)
```sql
CREATE TABLE certifications (
    id VARCHAR(36) PRIMARY KEY,
    candidate_id VARCHAR(36) REFERENCES candidates(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    issuer VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    credential_id VARCHAR(255),
    
    confidence_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_certifications_candidate (candidate_id)
);
```

#### **duplicate_checks** (New Table)
```sql
CREATE TABLE duplicate_checks (
    id VARCHAR(36) PRIMARY KEY,
    resume_id VARCHAR(36) REFERENCES resumes(id),
    candidate_id VARCHAR(36) REFERENCES candidates(id),
    
    match_type VARCHAR(50),
    match_score DECIMAL(5, 4),
    matched_candidate_id VARCHAR(36) REFERENCES candidates(id),
    
    resolution VARCHAR(50),
    resolved_by VARCHAR(36) REFERENCES users(id),
    resolved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_duplicate_checks_resume (resume_id)
);
```

### 1.2 Modifications to Existing Tables

#### **resumes** (Existing - Add Fields)
```sql
ALTER TABLE resumes ADD COLUMN candidate_id VARCHAR(36) REFERENCES candidates(id);
ALTER TABLE resumes ADD COLUMN processing_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE resumes ADD COLUMN processing_error TEXT;
ALTER TABLE resumes ADD COLUMN processed_at TIMESTAMP;

CREATE INDEX idx_resumes_candidate ON resumes(candidate_id);
CREATE INDEX idx_resumes_processing_status ON resumes(processing_status);
```

---

## 2. API DESIGN

### 2.1 Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/resumes/upload` | Upload single resume |
| POST | `/api/resumes/upload/batch` | Upload multiple resumes |
| GET | `/api/resumes/upload/status/{job_id}` | Get processing status |
| GET | `/api/resumes/upload/batch/{batch_id}` | Get batch status |
| POST | `/api/resumes/{resume_id}/resolve-duplicate` | Resolve duplicate |
| POST | `/api/resumes/{resume_id}/parse` | Trigger parsing |
| GET | `/api/candidates` | List candidates |
| GET | `/api/candidates/{candidate_id}` | Get candidate details |
| PUT | `/api/candidates/{candidate_id}` | Update candidate |

### 2.2 Request/Response Schemas

#### **Upload Single Resume**
```python
# Request (multipart/form-data)
class SingleUploadRequest(BaseModel):
    file: UploadFile
    check_duplicates: bool = True
    auto_parse: bool = True

# Response
class UploadResponse(BaseModel):
    status: str  # "success", "duplicate_found"
    job_id: str
    message: str
    resume: ResumeInfo
    duplicates: Optional[List[DuplicateMatch]] = None
```

#### **Batch Upload**
```python
class BatchUploadResponse(BaseModel):
    status: str
    batch_id: str
    total_files: int
    message: str
    job_ids: List[str]
```

#### **Parsed Data Schema**
```python
class ParsedResumeData(BaseModel):
    personal_info: PersonalInfo
    education: List[Education]
    experience: List[WorkExperience]
    skills: List[Skill]
    certifications: List[Certification]
    total_experience_months: Optional[int]
    
class PersonalInfo(BaseModel):
    name: str
    email: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    location: Optional[str]
    confidence: Dict[str, float]

class Education(BaseModel):
    degree: str
    field: Optional[str]
    institution: str
    location: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    gpa: Optional[float]
    confidence: float

class WorkExperience(BaseModel):
    company: str
    title: str
    location: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    duration_months: Optional[int]
    description: Optional[str]
    achievements: List[str]
    confidence: float

class Skill(BaseModel):
    name: str
    category: str
    proficiency: Optional[str]
    confidence: float

class Certification(BaseModel):
    name: str
    issuer: Optional[str]
    date: Optional[str]
    expiry_date: Optional[str]
    credential_id: Optional[str]
    confidence: float
```

---

## 3. SERVICE LAYER

### 3.1 New Services

#### **CandidateService**
```python
class CandidateService:
    """Manages candidate records"""
    
    async def create_candidate(self, parsed_data: ParsedResumeData) -> Candidate
    async def get_candidate_by_id(self, candidate_id: str) -> Candidate
    async def update_candidate(self, candidate_id: str, data: dict) -> Candidate
    async def search_candidates(self, filters: dict) -> List[Candidate]
    async def merge_candidates(self, source_id: str, target_id: str) -> Candidate
```

#### **ResumeParsingService** (Enhanced)
```python
class ResumeParsingService:
    """Enhanced resume parsing with structured data extraction"""
    
    async def parse_resume_full(self, file_content: bytes, file_type: str) -> ParsedResumeData
    async def extract_personal_info(self, text: str) -> PersonalInfo
    async def extract_education(self, text: str) -> List[Education]
    async def extract_experience(self, text: str) -> List[WorkExperience]
    async def extract_skills(self, text: str) -> List[Skill]
    async def extract_certifications(self, text: str) -> List[Certification]
    async def calculate_confidence_scores(self, data: dict) -> dict
```

#### **DuplicateDetectionService**
```python
class DuplicateDetectionService:
    """Detects duplicate candidates"""
    
    async def check_duplicates(self, parsed_data: ParsedResumeData) -> List[DuplicateMatch]
    async def check_email_match(self, email: str) -> Optional[Candidate]
    async def check_phone_match(self, phone: str) -> Optional[Candidate]
    async def check_name_similarity(self, name: str, threshold: float = 0.85) -> List[Candidate]
    async def check_content_similarity(self, text: str, threshold: float = 0.90) -> List[Candidate]
    async def log_duplicate_check(self, resume_id: str, matches: List[DuplicateMatch])
```

#### **BackgroundJobService**
```python
class BackgroundJobService:
    """Manages background processing jobs"""
    
    async def create_parsing_job(self, resume_id: str) -> str
    async def get_job_status(self, job_id: str) -> JobStatus
    async def update_job_progress(self, job_id: str, progress: int, message: str)
    async def complete_job(self, job_id: str, result: dict)
    async def fail_job(self, job_id: str, error: str)
```

### 3.2 Service Integration Flow

```
Upload Request
    ↓
FileValidatorService (validate file)
    ↓
FileStorageService (save file)
    ↓
ResumeService (create resume record)
    ↓
BackgroundJobService (create job)
    ↓
[Background Processing]
    ↓
ResumeParsingService (extract data)
    ↓
DuplicateDetectionService (check duplicates)
    ↓
CandidateService (create/update candidate)
    ↓
Complete Job
```

---

## 4. UI/UX DESIGN

### 4.1 New Templates

#### **templates/resumes/upload_enhanced.html**
- Drag-and-drop zone
- Multi-file selection
- File preview list
- Progress indicators
- Duplicate handling UI

#### **templates/resumes/processing_status.html**
- Real-time progress tracking
- Individual file status
- Error display
- Retry options

#### **templates/candidates/list.html**
- Candidate listing with search/filter
- Pagination
- Quick actions (view, edit, delete)

#### **templates/candidates/detail.html**
- Complete candidate profile
- Editable fields
- Resume history
- Activity timeline

### 4.2 Key UI Components

**Upload Interface:**
```html
<div class="upload-zone">
    <input type="file" multiple accept=".pdf,.docx,.txt" />
    <div class="drag-drop-area">
        <i class="upload-icon"></i>
        <p>Drag & Drop files or Click to Browse</p>
        <span>Supported: PDF, DOCX, TXT (Max 10MB, 50 files)</span>
    </div>
    <div class="file-list">
        <!-- Selected files with remove option -->
    </div>
    <label>
        <input type="checkbox" checked /> Check for duplicates
    </label>
    <button class="btn-primary">Upload All</button>
</div>
```

**Progress Tracking:**
```html
<div class="progress-container">
    <div class="overall-progress">
        <span>7/10 completed (70%)</span>
        <div class="progress-bar">
            <div class="progress-fill" style="width: 70%"></div>
        </div>
    </div>
    <div class="file-status-list">
        <!-- Individual file progress cards -->
    </div>
</div>
```

---

## 5. INTEGRATION POINTS

### 5.1 Existing Module Integration

**Authentication Integration:**
- Use existing `get_current_user` dependency
- Leverage `UserActivityLog` for tracking
- Apply role-based access control

**File Storage Integration:**
- Use existing `FileStorageService`
- Leverage `FileValidatorService`
- Maintain existing file structure

**Database Integration:**
- Use existing `AsyncSession` pattern
- Leverage existing `Base` model
- Follow existing migration strategy

### 5.2 New Dependencies

**Python Packages:**
```toml
# Add to pyproject.toml
spacy = "^3.7.0"
fuzzywuzzy = "^0.18.0"
python-Levenshtein = "^0.21.0"
scikit-learn = "^1.3.0"
celery = "^5.3.0"
redis = "^5.0.0"
```

**External Services:**
- Redis for job queue
- Celery for background processing

---

## 6. FILE STRUCTURE

### 6.1 New Files to Create

```
models/
├── candidate_schemas.py          # Pydantic schemas for candidates
├── parsing_schemas.py            # Schemas for parsed data

services/
├── candidate_service.py          # Candidate management
├── duplicate_detection_service.py # Duplicate detection
├── background_job_service.py     # Job management
└── enhanced_parser_service.py    # Enhanced parsing

api/
├── candidates.py                 # Candidate endpoints

templates/
├── resumes/
│   ├── upload_enhanced.html
│   └── processing_status.html
├── candidates/
│   ├── list.html
│   ├── detail.html
│   └── edit.html

static/
├── js/
│   ├── resume_upload.js
│   └── candidate_management.js
├── css/
│   └── candidates.css

migrations/
└── versions/
    └── 002_add_candidate_tables.py

tests/
├── test_candidate_service.py
├── test_duplicate_detection.py
└── test_resume_parsing_enhanced.py
```

### 6.2 Files to Modify

```
main.py                           # Add candidate routes
services/resume_parser_service.py # Enhance parsing logic
services/resume_service.py        # Add candidate linking
models/database.py                # Add new models
core/config.py                    # Add new settings
```

---

## 7. TESTING STRATEGY

### 7.1 Unit Tests

```python
# test_candidate_service.py
async def test_create_candidate():
    """Test candidate creation from parsed data"""
    
async def test_update_candidate():
    """Test candidate update"""

# test_duplicate_detection.py
async def test_email_duplicate_detection():
    """Test exact email match"""
    
async def test_name_fuzzy_matching():
    """Test fuzzy name matching with threshold"""
    
async def test_content_similarity():
    """Test content-based duplicate detection"""

# test_resume_parsing_enhanced.py
async def test_parse_education_section():
    """Test education extraction with confidence scores"""
    
async def test_parse_experience_section():
    """Test work experience extraction"""
```

### 7.2 Integration Tests

```python
async def test_upload_and_parse_workflow():
    """Test complete upload → parse → candidate creation"""
    
async def test_duplicate_detection_workflow():
    """Test upload → duplicate found → resolution"""
    
async def test_batch_upload_workflow():
    """Test batch upload with mixed results"""
```

### 7.3 Manual Testing Checklist

- [ ] Upload single PDF resume
- [ ] Upload single DOCX resume
- [ ] Upload batch of 10 resumes
- [ ] Duplicate detection (email match)
- [ ] Duplicate detection (name similarity)
- [ ] Manual data correction after parsing
- [ ] Candidate profile view/edit
- [ ] Search and filter candidates
- [ ] Error handling (corrupted file)
- [ ] Error handling (oversized file)

---

## 8. DEPLOYMENT CONSIDERATIONS

### 8.1 Environment Variables

```bash
# Add to .env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
ENABLE_BACKGROUND_JOBS=true
DUPLICATE_DETECTION_THRESHOLD=0.85
MAX_BATCH_SIZE=50
```

### 8.2 Database Migration

```python
# migrations/versions/002_add_candidate_tables.py
"""Add candidate and related tables

Revision ID: 002
Revises: 001
Create Date: 2025-10-06
"""

def upgrade():
    # Create candidates table
    op.create_table('candidates', ...)
    # Create education table
    op.create_table('education', ...)
    # Create work_experience table
    op.create_table('work_experience', ...)
    # Create skills table
    op.create_table('skills', ...)
    # Create candidate_skills table
    op.create_table('candidate_skills', ...)
    # Create certifications table
    op.create_table('certifications', ...)
    # Create duplicate_checks table
    op.create_table('duplicate_checks', ...)
    # Alter resumes table
    op.add_column('resumes', sa.Column('candidate_id', ...))

def downgrade():
    # Reverse all changes
```

### 8.3 Deployment Steps

1. **Install Dependencies:**
   ```bash
   uv pip install spacy fuzzywuzzy python-Levenshtein scikit-learn celery redis
   python -m spacy download en_core_web_sm
   ```

2. **Setup Redis:**
   ```bash
   # Install Redis (if not already)
   # Start Redis server
   redis-server
   ```

3. **Run Migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Start Celery Worker:**
   ```bash
   celery -A services.background_job_service worker --loglevel=info
   ```

5. **Deploy Application:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

### 8.4 Performance Optimization

- **Database Indexing:** All foreign keys and search fields indexed
- **Caching:** Redis cache for duplicate checks
- **Background Jobs:** Celery for async processing
- **Connection Pooling:** SQLAlchemy async pool
- **File Storage:** Efficient file system organization

---

## 9. IMPLEMENTATION EXAMPLES

### 9.1 Candidate Service Implementation

```python
# services/candidate_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import Candidate, Education, WorkExperience
from models.candidate_schemas import ParsedResumeData
import uuid

class CandidateService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_candidate(self, parsed_data: ParsedResumeData, created_by: str) -> str:
        """Create candidate from parsed resume data"""
        # Create candidate
        candidate = Candidate(
            id=str(uuid.uuid4()),
            uuid=str(uuid.uuid4()),
            full_name=parsed_data.personal_info.name,
            email=parsed_data.personal_info.email,
            phone=parsed_data.personal_info.phone,
            linkedin_url=parsed_data.personal_info.linkedin_url,
            location=parsed_data.personal_info.location,
            created_by=created_by
        )
        self.db.add(candidate)
        
        # Add education
        for edu in parsed_data.education:
            education = Education(
                id=str(uuid.uuid4()),
                candidate_id=candidate.id,
                degree=edu.degree,
                field=edu.field,
                institution=edu.institution,
                confidence_score=edu.confidence
            )
            self.db.add(education)
        
        # Add work experience
        for exp in parsed_data.experience:
            experience = WorkExperience(
                id=str(uuid.uuid4()),
                candidate_id=candidate.id,
                company=exp.company,
                title=exp.title,
                duration_months=exp.duration_months,
                confidence_score=exp.confidence
            )
            self.db.add(experience)
        
        await self.db.commit()
        return candidate.id
```

### 9.2 Duplicate Detection Implementation

```python
# services/duplicate_detection_service.py
from fuzzywuzzy import fuzz
from sqlalchemy import select
from models.database import Candidate

class DuplicateDetectionService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def check_email_match(self, email: str) -> Optional[dict]:
        """Check for exact email match"""
        if not email:
            return None
        
        result = await self.db.execute(
            select(Candidate).where(Candidate.email == email.lower())
        )
        candidate = result.scalar_one_or_none()
        
        if candidate:
            return {
                "candidate_id": candidate.id,
                "name": candidate.full_name,
                "email": candidate.email,
                "match_type": "email",
                "match_score": 1.0
            }
        return None
    
    async def check_name_similarity(self, name: str, threshold: float = 0.85) -> List[dict]:
        """Check for fuzzy name match"""
        result = await self.db.execute(select(Candidate))
        candidates = result.scalars().all()
        
        matches = []
        for candidate in candidates:
            similarity = fuzz.ratio(name.lower(), candidate.full_name.lower()) / 100.0
            if similarity >= threshold:
                matches.append({
                    "candidate_id": candidate.id,
                    "name": candidate.full_name,
                    "match_type": "name",
                    "match_score": similarity
                })
        
        return matches
```

### 9.3 API Endpoint Implementation

```python
# api/candidates.py
from fastapi import APIRouter, Depends
from services.candidate_service import CandidateService

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])

@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    current_user: dict = Depends(get_current_user),
    candidate_service: CandidateService = Depends(get_candidate_service)
):
    """Get candidate details with all related data"""
    candidate = await candidate_service.get_candidate_full(candidate_id)
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {
        "success": True,
        "data": candidate
    }
```

---

## 10. SUCCESS METRICS

### 10.1 Technical Metrics
- API response time < 500ms
- Background job completion rate > 99%
- Data extraction accuracy > 95%
- Duplicate detection rate > 99%

### 10.2 Business Metrics
- Time to process 100 resumes < 5 minutes
- User satisfaction > 4/5
- Manual data entry reduction > 90%

---

**Status:** Ready for Implementation  
**Next Steps:** Begin database schema creation and migration
