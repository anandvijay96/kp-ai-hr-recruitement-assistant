# Technology Stack - AI HR Recruitment Assistant

**Version:** 1.0  
**Last Updated:** October 6, 2025  
**Status:** Approved

---

## 📋 Overview

This document defines the standardized technology stack for the AI HR Recruitment Assistant platform. All features must use these technologies unless explicitly approved otherwise.

---

## 🎯 Current Stack (Proven & Working)

### Backend Framework
- **FastAPI** (v0.104.1)
  - Modern, fast Python web framework
  - Automatic API documentation (Swagger/OpenAPI)
  - Async support for high performance
  - Type hints and validation with Pydantic

### Web Server
- **Uvicorn** (v0.24.0)
  - ASGI server for FastAPI
  - High performance
  - WebSocket support

### Database

**Primary Database: SQLite (Development) → PostgreSQL (Production)**

**Development:**
- **SQLite** (via SQLAlchemy)
  - File-based, zero configuration
  - Perfect for development and testing
  - Easy to version control (for schema)
  - Fast for < 100K records

**Production (Recommended):**
- **PostgreSQL** (v14+)
  - Production-grade RDBMS
  - ACID compliant
  - Full-text search support
  - JSON support for flexible data
  - Excellent performance at scale
  - Free and open source

**ORM:**
- **SQLAlchemy** (v2.0+)
  - Industry-standard Python ORM
  - Database-agnostic (SQLite → PostgreSQL migration easy)
  - Async support
  - Migration support via Alembic

### Caching & Session Management
- **Redis** (v5.0.1)
  - In-memory data store
  - Session management
  - Caching layer
  - Job queue (with Celery)
  - Pub/Sub for real-time features

### Background Jobs
- **Celery** (v5.3.4)
  - Distributed task queue
  - Async job processing
  - Scheduled tasks (cron-like)
  - Retry mechanisms
  - Works with Redis as broker

### Document Processing
- **PyMuPDF** (v1.24.9) - PDF processing
- **python-docx** (v1.1.0) - DOCX processing
- **pdfplumber** (v0.10.3) - PDF text extraction
- **pytesseract** (v0.3.10) - OCR for image-based PDFs
- **Pillow** (v10.1.0) - Image processing

### NLP & AI
- **spaCy** (v3.7.2) - NLP processing
- **NLTK** (v3.8.1) - Text analysis
- **scikit-learn** (v1.3.0) - ML algorithms
- **sentence-transformers** (future) - Semantic matching

### Data Processing
- **pandas** (v2.0.3) - Data manipulation
- **numpy** (v1.24.3) - Numerical operations

### Validation & Configuration
- **Pydantic** (v2.5.0) - Data validation
- **pydantic-settings** (v2.1.0) - Configuration management

### File Handling
- **aiofiles** (v23.2.1) - Async file operations
- **python-multipart** (v0.0.6) - File upload handling

### Frontend (Current)
- **Jinja2** (v3.1.2) - Template engine
- **Bootstrap 5** - CSS framework
- **Vanilla JavaScript** - Client-side logic

### Frontend (Recommended for New Features)
- **React** or **Vue.js** - Modern UI framework
- **TailwindCSS** - Utility-first CSS
- **shadcn/ui** - Component library
- **Axios** - HTTP client
- **Socket.io** - Real-time communication

### Testing
- **pytest** (v7.4.3) - Testing framework
- **pytest-asyncio** (v0.21.1) - Async testing
- **httpx** (v0.25.2) - HTTP testing

---

## 🗄️ Database Architecture

### Database Choice Rationale

**SQLite for Development:**
```python
# Simple, file-based
DATABASE_URL = "sqlite:///./hr_assistant.db"

Pros:
✅ Zero configuration
✅ Fast for development
✅ Easy to reset/recreate
✅ Version control friendly
✅ Perfect for testing

Cons:
❌ Limited concurrency
❌ No network access
❌ Size limitations
```

**PostgreSQL for Production:**
```python
# Scalable, production-ready
DATABASE_URL = "postgresql://user:pass@localhost:5432/hr_assistant"

Pros:
✅ Excellent concurrency
✅ Full-text search
✅ JSON support
✅ Scales to millions of records
✅ ACID compliant
✅ Rich ecosystem

Cons:
❌ Requires setup
❌ More complex
```

### Migration Strategy

**Phase 1: Development (SQLite)**
- Use SQLAlchemy ORM
- Design schema for PostgreSQL compatibility
- Avoid SQLite-specific features

**Phase 2: Production (PostgreSQL)**
- One-line change in DATABASE_URL
- Run Alembic migrations
- Test thoroughly
- Deploy

**Code Example:**
```python
# core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Works with both SQLite and PostgreSQL
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True  # PostgreSQL health check
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
```

---

## 📦 Additional Dependencies for New Features

### Feature 2: Resume Upload & Data Extraction
```python
# Already have most dependencies
# Additional:
python-magic==0.4.27  # File type detection (already included)
```

### Feature 3: Advanced Resume Filtering
```python
# Option 1: PostgreSQL Full-Text Search (Recommended)
# No additional dependencies - built into PostgreSQL

# Option 2: Elasticsearch (If needed for very large scale)
elasticsearch==8.11.0
```

### Feature 4: Candidate Tracking System
```python
# Calendar Integration
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-api-python-client==2.108.0

# Microsoft Graph (Outlook)
msal==1.25.0
msgraph-core==1.0.0

# Email
sendgrid==6.11.0
# OR
boto3==1.29.7  # For AWS SES

# WebSocket (Real-time)
python-socketio==5.10.0
```

### Feature 5: Manual Resume Rating
```python
# No additional dependencies needed
# Uses existing database and API
```

### Feature 6: Job Creation & Management
```python
# Rich text editor support
bleach==6.1.0  # HTML sanitization
markdown==3.5.1  # Markdown support (optional)
```

### Feature 7: AI-Powered Resume Matching
```python
# Semantic similarity
sentence-transformers==2.2.2
torch==2.1.0  # Required by sentence-transformers

# OR lightweight alternative
gensim==4.3.2  # Word2Vec, Doc2Vec
```

### Feature 8: Jobs Dashboard & Management
```python
# External job board APIs
requests==2.31.0  # HTTP client
requests-oauthlib==1.3.1  # OAuth for APIs
```

### Feature 9: Resume Match Rating & Ranking
```python
# No additional dependencies
# Uses existing ML libraries
```

### Feature 10: Advanced User Management
```python
# Password hashing (already have bcrypt via passlib)
passlib[bcrypt]==1.7.4

# JWT tokens
python-jose[cryptography]==3.3.0

# RBAC
casbin==1.31.0  # Policy-based access control (optional)
```

---

## 🏗️ Architecture Patterns

### Project Structure
```
ai-hr-assistant/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
│
├── core/                   # Core functionality
│   ├── config.py          # Configuration
│   ├── database.py        # Database connection
│   ├── cache.py           # Redis cache
│   └── security.py        # Auth & security
│
├── models/                 # Data models
│   ├── schemas.py         # Pydantic schemas (API)
│   ├── database.py        # SQLAlchemy models (DB)
│   └── enums.py           # Enumerations
│
├── services/               # Business logic
│   ├── document_processor.py
│   ├── resume_analyzer.py
│   ├── candidate_service.py
│   ├── job_service.py
│   └── matching_service.py
│
├── api/                    # API routes
│   ├── auth.py
│   ├── resumes.py
│   ├── candidates.py
│   ├── jobs.py
│   └── users.py
│
├── tasks/                  # Celery tasks
│   ├── resume_tasks.py
│   ├── matching_tasks.py
│   └── notification_tasks.py
│
├── templates/              # Jinja2 templates
├── static/                 # Static files
├── tests/                  # Test files
├── migrations/             # Alembic migrations
└── docs/                   # Documentation
```

### Design Patterns

**1. Repository Pattern**
```python
# Separate data access from business logic
class CandidateRepository:
    def get_by_id(self, id: int) -> Candidate
    def get_all(self, filters: dict) -> List[Candidate]
    def create(self, candidate: CandidateCreate) -> Candidate
    def update(self, id: int, data: dict) -> Candidate
```

**2. Service Layer**
```python
# Business logic separated from API routes
class CandidateService:
    def __init__(self, repo: CandidateRepository):
        self.repo = repo
    
    def create_candidate(self, data: CandidateCreate):
        # Validation, business rules
        return self.repo.create(data)
```

**3. Dependency Injection**
```python
# FastAPI's built-in DI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/candidates")
def get_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).all()
```

---

## 🔒 Security Standards

### Authentication
- JWT tokens for API authentication
- Session-based for web interface
- Secure password hashing (bcrypt)
- Password policies enforced

### Authorization
- Role-Based Access Control (RBAC)
- Permission checks at API level
- Resource-level permissions

### Data Security
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (template escaping)
- CSRF protection
- HTTPS/TLS in production
- Sensitive data encryption

### API Security
- Rate limiting
- CORS configuration
- API key authentication (for external integrations)
- Request size limits

---

## 📊 Performance Guidelines

### Database
- Use indexes on frequently queried fields
- Implement pagination (limit/offset)
- Use database-level filtering
- Connection pooling
- Query optimization

### Caching Strategy
```python
# Cache expensive operations
@cache.memoize(timeout=300)  # 5 minutes
def get_candidate_matches(candidate_id: int):
    # Expensive AI matching
    return matches

# Cache search results
@cache.memoize(timeout=60)  # 1 minute
def search_candidates(filters: dict):
    return results
```

### Background Jobs
- Use Celery for:
  - Bulk resume processing
  - AI matching calculations
  - Email sending
  - Report generation
  - Data exports

### API Response Times
- Target: < 500ms for most endpoints
- Use async/await for I/O operations
- Implement pagination
- Use database indexes
- Cache frequently accessed data

---

## 🧪 Testing Standards

### Test Coverage
- Minimum 80% code coverage
- Unit tests for all services
- Integration tests for APIs
- End-to-end tests for critical flows

### Test Structure
```python
tests/
├── unit/
│   ├── test_services/
│   ├── test_models/
│   └── test_utils/
├── integration/
│   ├── test_api/
│   └── test_database/
└── e2e/
    └── test_workflows/
```

---

## 🚀 Deployment

### Development
```bash
# SQLite database
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
# PostgreSQL database
# Gunicorn + Uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📝 Configuration Management

### Environment Variables
```python
# .env file
DATABASE_URL=sqlite:///./hr_assistant.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
DEBUG=True

# Production
DATABASE_URL=postgresql://user:pass@localhost:5432/hr_assistant
REDIS_URL=redis://redis:6379/0
SECRET_KEY=strong-random-key
DEBUG=False
```

### Settings Class
```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AI HR Assistant"
    database_url: str
    redis_url: str
    secret_key: str
    debug: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## ✅ Technology Decision Matrix

| Feature | Technology | Rationale |
|---------|------------|-----------|
| Web Framework | FastAPI | Modern, fast, async, auto-docs |
| Database (Dev) | SQLite | Simple, fast, zero-config |
| Database (Prod) | PostgreSQL | Scalable, reliable, feature-rich |
| ORM | SQLAlchemy | Standard, database-agnostic |
| Caching | Redis | Fast, versatile, proven |
| Background Jobs | Celery | Distributed, reliable, scalable |
| Search | PostgreSQL FTS | Built-in, good enough for most cases |
| AI/ML | spaCy + scikit-learn | Proven, lightweight, effective |
| Frontend | React/Vue + Tailwind | Modern, component-based, fast |
| Testing | pytest | Standard, powerful, async support |

---

## 🔄 Migration Path

### SQLite → PostgreSQL

**Step 1: Design for PostgreSQL**
```python
# Use SQLAlchemy types that work in both
from sqlalchemy import String, Integer, DateTime, Text, JSON

# Avoid SQLite-specific features
# Use standard SQL
```

**Step 2: Test with PostgreSQL Early**
```bash
# Run tests against PostgreSQL
DATABASE_URL=postgresql://localhost/test_db pytest
```

**Step 3: Migration Script**
```python
# migrations/migrate_sqlite_to_postgres.py
import sqlite3
import psycopg2

def migrate():
    # Export from SQLite
    # Import to PostgreSQL
    # Verify data integrity
```

---

## 📚 Learning Resources

### FastAPI
- Official Docs: https://fastapi.tiangolo.com/
- Tutorial: https://fastapi.tiangolo.com/tutorial/

### SQLAlchemy
- Official Docs: https://docs.sqlalchemy.org/
- Tutorial: https://docs.sqlalchemy.org/en/20/tutorial/

### PostgreSQL
- Official Docs: https://www.postgresql.org/docs/
- Tutorial: https://www.postgresqltutorial.com/

### Redis
- Official Docs: https://redis.io/documentation
- Python Client: https://redis-py.readthedocs.io/

---

**Status: ✅ APPROVED**  
**Next: Use this stack for all PRD implementations**
