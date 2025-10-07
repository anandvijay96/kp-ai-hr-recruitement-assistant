# 🚀 Phase 1: Database Foundation - Quick Start

**Status:** ✅ COMPLETE - Ready to Test  
**Time to Setup:** ~10 minutes

---

## ⚡ Fastest Path to Testing

### Step 1: Install Dependencies (2 minutes)

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 2: Initialize Database (30 seconds)

```bash
python init_db.py
```

### Step 3: Start Redis (30 seconds)

**Option A - Docker (Recommended):**
```bash
docker run -d -p 6379:6379 redis:latest
```

**Option B - Native:**
```bash
redis-server
```

### Step 4: Start Celery Worker (in new terminal)

```bash
# Linux/Mac
celery -A core.celery_app worker --loglevel=info

# Windows
celery -A core.celery_app worker --loglevel=info --pool=solo
```

### Step 5: Start API (in new terminal)

```bash
uvicorn main:app --reload
```

---

## 🧪 Quick Test

### Upload a Resume

```bash
# Create a test resume (or use any PDF/DOCX)
curl -X POST "http://localhost:8000/api/v1/resumes/upload" \
  -F "file=@path/to/resume.pdf"
```

**Expected Response:**
```json
{
  "job_id": "1",
  "file_name": "resume.pdf",
  "status": "processing"
}
```

### Check Status (wait 5-10 seconds)

```bash
curl "http://localhost:8000/api/v1/resumes/jobs/1"
```

**Expected Response:**
```json
{
  "job_id": "1",
  "status": "completed",
  "candidate_id": 1,
  "authenticity_score": 85,
  "extracted_data": {
    "email": "candidate@example.com",
    "phone": "+1-555-123-4567",
    "name": "John Doe",
    "skills": ["Python", "Java"],
    "education": [...],
    "work_experience": [...]
  }
}
```

### View Candidate

```bash
curl "http://localhost:8000/api/v1/candidates/1"
```

---

## 📊 What to Verify

✅ **Database Created**: Check `hr_assistant.db` exists  
✅ **Resume Uploaded**: File in `uploads/` directory  
✅ **Data Extracted**: Email, phone, skills found  
✅ **Candidate Created**: Candidate record in database  
✅ **Authenticity Score**: Score between 0-100  
✅ **Background Processing**: Celery processed the task  

---

## 🧪 Run Tests

```bash
# Run all tests
pytest tests/ -v

# Should see:
# test_database_models.py ............ PASSED
# test_data_extractor.py ............. PASSED
# All tests passing!
```

---

## 🐛 Troubleshooting

### "Cannot connect to Redis"
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not, start Redis
redis-server
```

### "No module named 'models.db'"
```bash
# Make sure you're in the project root directory
cd /path/to/ai-hr-assistant
python init_db.py
```

### "Database locked" (SQLite)
```bash
# Close any other processes using the database
# Or just restart everything
```

### Celery tasks not processing
```bash
# Check Celery worker logs for errors
# Ensure Redis is running
# Restart Celery worker
```

---

## 📁 File Structure After Setup

```
ai-hr-assistant/
├── hr_assistant.db         # ✅ SQLite database (created)
├── uploads/                # ✅ Uploaded resumes (created)
│   └── 20251007_143000_resume.pdf
├── core/
│   ├── database.py         # ✅ Database connection
│   ├── celery_app.py       # ✅ Celery config
├── models/db/              # ✅ 6 database models
├── services/
│   ├── resume_service.py           # ✅ Updated
│   ├── candidate_service.py        # ✅ Updated
│   └── resume_data_extractor.py    # ✅ New
├── tasks/
│   └── resume_tasks.py     # ✅ Celery tasks
└── tests/                  # ✅ Comprehensive tests
```

---

## 🎯 Success Checklist

- [ ] Dependencies installed
- [ ] Database initialized (hr_assistant.db exists)
- [ ] Redis running (redis-cli ping works)
- [ ] Celery worker running (no errors in logs)
- [ ] API running (http://localhost:8000 accessible)
- [ ] Resume uploaded successfully
- [ ] Data extracted (email, phone found)
- [ ] Candidate created in database
- [ ] All tests passing

---

## 📚 Next Steps

Once everything is working:

1. **Read Full Documentation**: `docs/PHASE1_SETUP_GUIDE.md`
2. **Explore API**: http://localhost:8000/docs (FastAPI Swagger UI)
3. **Run More Tests**: Upload different resume formats
4. **Check Database**: Use DB browser to inspect data
5. **Review Code**: Understand the architecture

---

## 🎉 Phase 1 Complete!

**What You Have Now:**
- ✅ Production-ready database architecture
- ✅ Intelligent resume data extraction
- ✅ Background processing with Celery
- ✅ Duplicate detection
- ✅ RESTful API with database persistence
- ✅ Comprehensive test suite

**Ready for Phase 2:**
- Feature 2: Complete Resume Upload & Processing
- Feature 3: Advanced Resume Filtering
- Feature 7: Enhanced AI Matching

---

**Questions?** Check `docs/PHASE1_SETUP_GUIDE.md` for detailed documentation.

**Issues?** Review logs:
- FastAPI: Terminal output
- Celery: Worker terminal output
- Database: `hr_assistant.db` (use DB Browser for SQLite)
