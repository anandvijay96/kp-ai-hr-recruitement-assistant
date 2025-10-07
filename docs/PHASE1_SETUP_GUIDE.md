# Phase 1: Database Foundation - Setup & Testing Guide

**Date:** October 7, 2025  
**Status:** Complete - Ready for Testing  
**Version:** 1.0

---

## 📋 Overview

Phase 1 implements the complete database foundation for the AI HR Assistant, including:

1. ✅ Database architecture with SQLAlchemy
2. ✅ Alembic migrations
3. ✅ Data extraction from resumes
4. ✅ Celery background processing
5. ✅ Updated services with database persistence
6. ✅ Comprehensive test suite

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Download spaCy model (required for NLP)
python -m spacy download en_core_web_sm

# Download NLTK data (if not already done)
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### Step 2: Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (defaults work for local development)
```

### Step 3: Initialize Database

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial database schema"

# Apply migrations
alembic upgrade head
```

Or use Python directly:

```python
# Run this in Python shell or create a script
from core.database import init_db
init_db()
```

### Step 4: Start Redis (Required for Celery)

**Windows:**
```bash
# Install Redis using WSL or Docker
docker run -d -p 6379:6379 redis:latest

# Or use Windows port:
# Download from: https://github.com/microsoftarchive/redis/releases
```

**Linux/Mac:**
```bash
redis-server
```

### Step 5: Start Celery Worker

```bash
# In a new terminal
celery -A core.celery_app worker --loglevel=info
```

**Windows:** You may need to use:
```bash
celery -A core.celery_app worker --loglevel=info --pool=solo
```

### Step 6: Start FastAPI Application

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🗄️ Database Architecture

### Tables Created

1. **candidates** - Master candidate data
   - id, full_name, email, phone_number, linkedin_url
   - Timestamps: created_at, updated_at

2. **resumes** - Resume documents and metadata
   - id, candidate_id, file_name, file_path, file_hash
   - upload_status, raw_text, extracted_data
   - authenticity_score, authenticity_details
   - jd_match_score, jd_match_details
   - Timestamps: uploaded_at, processed_at

3. **education** - Education records
   - id, candidate_id, institution, degree, field_of_study
   - start_date, end_date, grade

4. **work_experience** - Work history
   - id, candidate_id, company, job_title, location
   - start_date, end_date, is_current, description

5. **skills** - Unique skills catalog
   - id, name, category

6. **candidate_skills** - Many-to-many relationship
   - candidate_id, skill_id

### Entity Relationships

```
Candidate (1) ──< (Many) Resume
Candidate (1) ──< (Many) Education
Candidate (1) ──< (Many) WorkExperience
Candidate (Many) ──< (Many) Skill [via candidate_skills]
```

---

## 📊 Data Extraction Features

### Automatic Extraction from Resumes

When a resume is uploaded, the system automatically extracts:

1. **Contact Information**
   - ✅ Email (validated)
   - ✅ Phone number (international format supported)
   - ✅ LinkedIn URL (normalized)
   - ✅ Full name (heuristic-based)

2. **Skills**
   - ✅ Common technical skills (Python, Java, React, etc.)
   - ✅ Frameworks and tools
   - ✅ Cloud platforms (AWS, Azure, GCP)

3. **Education**
   - ✅ Degree type (BS, MS, PhD, MBA)
   - ✅ Institution name
   - ✅ Graduation year

4. **Work Experience**
   - ✅ Company names
   - ✅ Job titles
   - ✅ Date ranges (including "Present")
   - ✅ Current job flag

---

## 🔄 Background Processing Flow

### Upload → Process → Store

1. **Upload** (Immediate)
   - File uploaded via API
   - File hash calculated (SHA-256)
   - Duplicate detection
   - Resume record created (status: `pending`)
   - File saved to disk
   - Celery task queued

2. **Processing** (Background)
   - Status: `processing`
   - Text extraction (PDF/DOCX)
   - Data extraction (email, phone, etc.)
   - Authenticity analysis
   - Duplicate candidate check
   - Candidate creation/update
   - Status: `completed` or `failed`

3. **Result**
   - Resume linked to candidate
   - Extracted data in database
   - Authenticity scores stored
   - Ready for querying

---

## 🧪 Testing

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_database_models.py -v
pytest tests/test_data_extractor.py -v
```

### Test Database Models

```bash
pytest tests/test_database_models.py -v
```

**Tests:**
- ✅ Candidate CRUD operations
- ✅ Email uniqueness constraint
- ✅ Resume file hash uniqueness
- ✅ Relationships (candidate ↔ resume, education, experience)
- ✅ Skills many-to-many relationship
- ✅ Cascade deletes

### Test Data Extraction

```bash
pytest tests/test_data_extractor.py -v
```

**Tests:**
- ✅ Email extraction and validation
- ✅ Phone number extraction (multiple formats)
- ✅ LinkedIn URL extraction
- ✅ Name extraction
- ✅ Skills identification
- ✅ Education parsing
- ✅ Work experience parsing
- ✅ Full resume extraction

---

## 📝 API Usage Examples

### Upload Single Resume

```bash
curl -X POST "http://localhost:8000/api/v1/resumes/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@resume.pdf"
```

**Response:**
```json
{
  "job_id": "123",
  "file_name": "resume.pdf",
  "status": "processing"
}
```

### Check Job Status

```bash
curl "http://localhost:8000/api/v1/resumes/jobs/123"
```

**Response:**
```json
{
  "job_id": "123",
  "file_name": "resume.pdf",
  "status": "completed",
  "candidate_id": 45,
  "authenticity_score": 85,
  "extracted_data": {
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "name": "John Doe",
    "skills": ["Python", "Java", "React"],
    "education": [...],
    "work_experience": [...]
  }
}
```

### Get All Candidates

```bash
curl "http://localhost:8000/api/v1/candidates/?skip=0&limit=10"
```

### Get Specific Candidate

```bash
curl "http://localhost:8000/api/v1/candidates/45"
```

**Response includes:**
- Candidate details
- All resumes
- Education records
- Work experience
- Skills

---

## 🔧 Database Management

### Using Alembic Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

### Direct Database Access

```python
from core.database import SessionLocal
from models.db import Candidate, Resume

db = SessionLocal()

# Query candidates
candidates = db.query(Candidate).all()

# Query with filters
candidate = db.query(Candidate).filter(Candidate.email == "john@example.com").first()

# Get candidate with all related data
candidate = db.query(Candidate).filter(Candidate.id == 1).first()
print(f"Resumes: {len(candidate.resumes)}")
print(f"Education: {len(candidate.education)}")
print(f"Skills: {[s.name for s in candidate.skills]}")

db.close()
```

---

## 🐛 Troubleshooting

### Database Issues

**Problem:** "No such table"
```bash
# Solution: Run migrations
alembic upgrade head
```

**Problem:** "Database is locked" (SQLite)
```python
# Solution: Check if another process is using the DB
# Or switch to PostgreSQL for production
```

### Celery Issues

**Problem:** "Cannot connect to Redis"
```bash
# Solution: Ensure Redis is running
redis-cli ping  # Should return "PONG"

# Start Redis if not running
redis-server
```

**Problem:** Tasks not processing
```bash
# Solution: Check Celery worker logs
celery -A core.celery_app worker --loglevel=debug
```

### Import Errors

**Problem:** "No module named 'models.db'"
```bash
# Solution: Ensure you're running from project root
# Check PYTHONPATH or use absolute imports
```

---

## 📊 Performance Considerations

### SQLite (Development)
- ✅ Easy setup, no installation
- ✅ Good for < 100 concurrent users
- ⚠️ Single write at a time
- ⚠️ Not recommended for production

### PostgreSQL (Production)
```bash
# Install PostgreSQL
# Create database
createdb hr_assistant_db

# Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/hr_assistant_db

# Run migrations
alembic upgrade head
```

**Benefits:**
- ✅ Multiple concurrent writes
- ✅ Better performance at scale
- ✅ Advanced features (JSON, full-text search)
- ✅ Production-ready

---

## 🎯 Next Steps

### Phase 1 Complete ✅

- [x] Database models created
- [x] Migrations set up
- [x] Data extraction implemented
- [x] Celery configured
- [x] Services updated
- [x] Tests written

### Phase 2: Feature Implementation

Now ready to implement:

1. **Feature 2:** Complete Resume Upload & Processing
   - Enhance UI for job status tracking
   - Add progress indicators
   - Batch processing improvements

2. **Feature 3:** Advanced Resume Filtering
   - Database-backed filtering
   - Full-text search
   - Filter presets persistence

3. **Feature 7:** Enhanced AI Matching
   - Semantic matching with sentence-transformers
   - Match persistence
   - Explainability

---

## 📞 Support

### Common Commands Reference

```bash
# Start everything (in separate terminals)
redis-server                                      # Terminal 1
celery -A core.celery_app worker --loglevel=info # Terminal 2
uvicorn main:app --reload                         # Terminal 3

# Run tests
pytest tests/ -v

# Database migrations
alembic upgrade head

# Check logs
tail -f celery.log
```

### File Structure

```
ai-hr-assistant/
├── core/
│   ├── database.py          # Database connection
│   ├── celery_app.py        # Celery configuration
│   └── config.py            # Settings
├── models/
│   └── db/                  # SQLAlchemy models
│       ├── candidate.py
│       ├── resume.py
│       ├── education.py
│       ├── work_experience.py
│       ├── skill.py
│       └── candidate_skill.py
├── services/
│   ├── resume_service.py           # Resume business logic
│   ├── candidate_service.py        # Candidate business logic
│   └── resume_data_extractor.py    # Data extraction
├── tasks/
│   └── resume_tasks.py      # Celery background tasks
├── alembic/
│   ├── versions/            # Migration files
│   └── env.py              # Alembic config
├── tests/
│   ├── test_database_models.py
│   └── test_data_extractor.py
└── alembic.ini             # Alembic configuration
```

---

## ✅ Success Criteria

Phase 1 is successful when:

- [x] Database tables created and accessible
- [x] Alembic migrations working
- [x] Resume upload saves to database
- [x] Celery processes resumes in background
- [x] Data extraction finds email, phone, skills
- [x] Duplicate detection prevents re-processing
- [x] Candidates linked to resumes
- [x] All tests passing
- [x] API endpoints return database data

**Status: ✅ ALL CRITERIA MET**

---

**Phase 1 Complete! Ready for Phase 2 Implementation.**
