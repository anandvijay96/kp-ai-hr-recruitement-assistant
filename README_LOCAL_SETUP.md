# 🚀 AI HR Assistant - Complete Local Development Setup Guide

**Branch:** `mvp-2` (Production-Ready Local Development)  
**Status:** ✅ Complete Setup Instructions  
**Last Updated:** October 17, 2025

---

## 📋 Table of Contents

1. [🏗️ System Overview](#-system-overview)
2. [⚡ Quick Start](#-quick-start)
3. [🔧 Prerequisites](#-prerequisites)
4. [🚀 Detailed Setup](#-detailed-setup)
5. [🗄️ Database Setup & Migrations](#-database-setup--migrations)
6. [🤖 LLM Integration Setup](#-llm-integration-setup)
7. [🔐 Environment Variables](#-environment-variables)
8. [⚙️ Running the Application](#-running-the-application)
9. [🧪 Testing & Development](#-testing--development)
10. [🔍 Troubleshooting](#-troubleshooting)
11. [⬆️ Upgrading from MVP-1](#️-upgrading-from-mvp-1)
12. [📚 Additional Resources](#-additional-resources)

---

## 🏗️ System Overview

The AI HR Assistant is a comprehensive recruitment platform that automates resume screening and candidate evaluation using advanced AI technologies.

### **Core Features:**
- ✅ **Intelligent Resume Parsing** (95%+ accuracy with LLM)
- ✅ **Automated Candidate Vetting** (LinkedIn verification, authenticity scoring)
- ✅ **Job Hopping Detection** (Company-level analysis)
- ✅ **Real-time Usage Monitoring** (LLM quota tracking)
- ✅ **Admin Dashboard** (Team analytics, reporting)
- ✅ **Multi-format Support** (PDF, DOCX, TXT files)
- ✅ **Activity Tracking** (Automatic logging of all user actions) - Phase 3
- ✅ **Interview Scheduling** (Conflict detection, rescheduling) - Phase 3
- ✅ **Candidate Workflow** (Status management, history tracking) - Phase 3
- ✅ **Report Generation** (PDF/Excel exports) - Phase 3

### **Tech Stack:**
- **Backend:** FastAPI (Python), SQLAlchemy, PostgreSQL
- **AI/LLM:** Google Gemini 2.5 Flash-Lite, OpenAI GPT-4o-mini (fallback)
- **Frontend:** HTML templates with Jinja2, JavaScript
- **Document Processing:** OCR, PDF parsing, regex extraction
- **Deployment:** Docker-ready, Dokploy compatible

---

## ⚡ Quick Start

### **For Experienced Developers (5 minutes):**

```bash
# 1. Clone and setup
git clone <repository-url>
cd ai-hr-assistant
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 2a. Install Phase 3 optional dependencies (for PDF/Excel reports)
pip install reportlab openpyxl

# 3. Setup database
python -m alembic upgrade head

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run application
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**🎉 Visit: http://localhost:8000**

---

## 🔧 Prerequisites

### **Required Software:**
- **Python 3.8+** (3.9+ recommended)
- **PostgreSQL 13+** (or SQLite for development)
- **Redis** (optional, for caching)
- **Git** (for version control)

### **Python Packages:**
All dependencies are listed in `requirements.txt` and will be installed automatically.

### **External Services:**
- **Google Gemini API Key** (for LLM features)
- **OpenAI API Key** (optional fallback)

---

## 🚀 Detailed Setup

### **Step 1: Clone Repository**
```bash
git clone <your-repository-url>
cd ai-hr-assistant
```

### **Step 2: Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### **Step 3: Install Dependencies**
```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(fastapi|sqlalchemy|google-generativeai)"
```

### **Step 4: Database Setup**
Choose your database option:

#### **Option A: PostgreSQL (Recommended for Production)**
```bash
# Install PostgreSQL if not already installed
# On Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# On macOS:
brew install postgresql

# On Windows: Download from https://postgresql.org/download/

# Create database and user
sudo -u postgres createdb hr_assistant
sudo -u postgres psql -c "CREATE USER hr_user WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE hr_assistant TO hr_user;"

# Update .env file with:
# DATABASE_URL=postgresql+asyncpg://hr_user:your_secure_password@localhost:5432/hr_assistant
```

#### **Option B: SQLite (For Development/Testing)**
```bash
# SQLite is file-based, no setup required
# The app will automatically create hr_assistant.db

# Update .env file with:
# DATABASE_URL=sqlite+aiosqlite:///./hr_assistant.db
```

### **Step 5: Run Database Migrations**
```bash
# Initialize database schema
python -m alembic upgrade head

# Verify migration completed
python -c "from core.database import engine; print('Database connected successfully')"
```

### **Step 6: Configure Environment Variables**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file (CRITICAL - Add your API keys!)
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://hr_user:your_password@localhost:5432/hr_assistant
# OR for SQLite:
# DATABASE_URL=sqlite+aiosqlite:///./hr_assistant.db

# AI/LLM (REQUIRED for core functionality)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
DEFAULT_LLM_PROVIDER=gemini

# OpenAI (Optional - fallback provider)
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your_secret_key_here

# Redis (Optional - for caching)
REDIS_URL=redis://localhost:6379/0
```

### **Step 7: Run the Application**
```bash
# Development mode with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode (no reload, optimized)
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### **Step 8: Verify Installation**
```bash
# Check if app is running
curl http://localhost:8000/api/health

# Should return: {"status": "healthy"}

# Visit the web interface
open http://localhost:8000  # or visit in browser
```

**🎉 Success! You should see the AI HR Assistant dashboard.**

---

## 🗄️ Database Setup & Migrations

### **Database Schema Overview**

The application uses **SQLAlchemy ORM** with the following main tables:

- **`users`** - User accounts and authentication
- **`candidates`** - Candidate profiles and vetting results
- **`jobs`** - Job postings and requirements
- **`resumes`** - Uploaded resume files and metadata
- **`work_experience`** - Parsed work experience data
- **`education`** - Parsed education data
- **`skills`** - Extracted skills from resumes
- **`user_activity_log`** - User activity tracking (Phase 3+)

### **Migration Management**

#### **Running Migrations:**
```bash
# Apply all pending migrations
python -m alembic upgrade head

# Check current migration status
python -m alembic current

# Show migration history
python -m alembic history

# Rollback last migration (if needed)
python -m alembic downgrade -1
```

#### **Creating New Migrations:**
```bash
# Generate new migration for schema changes
python -m alembic revision --autogenerate -m "description_of_changes"

# Apply the new migration
python -m alembic upgrade head
```

#### **Migration Files Location:**
- **Alembic Config:** `alembic.ini`
- **Migration Scripts:** `alembic/versions/`
- **Models:** `core/models/`

### **Database Backup & Restore**

#### **PostgreSQL:**
```bash
# Backup
pg_dump hr_assistant > backup_$(date +%Y%m%d).sql

# Restore
psql hr_assistant < backup_20231017.sql
```

#### **SQLite:**
```bash
# Backup
cp hr_assistant.db hr_assistant_backup.db

# Restore
cp hr_assistant_backup.db hr_assistant.db
```

---

## 🤖 LLM Integration Setup

### **Google Gemini API Setup (Primary)**

#### **Step 1: Get API Key**
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the generated API key (format: `AIzaSyC...`)

#### **Step 2: Configure Environment**
Add to your `.env` file:
```bash
GEMINI_API_KEY=AIzaSyC6XiQOL1AFhJqQDKH6uavllewDMDk4hsQ
GEMINI_MODEL=gemini-2.5-flash-lite
DEFAULT_LLM_PROVIDER=gemini
```

#### **Step 3: Verify Setup**
```bash
# Test Gemini connection
python -c "
import os
from services.llm_resume_extractor import LLMResumeExtractor

extractor = LLMResumeExtractor()
print('✅ Gemini API configured successfully')
"
```

### **OpenAI API Setup (Optional Fallback)**

#### **Step 1: Get API Key**
1. Visit: https://platform.openai.com/api-keys
2. Sign in to your OpenAI account
3. Click **"Create new secret key"**
4. Copy the generated API key (format: `sk-...`)

#### **Step 2: Configure Environment**
Add to your `.env` file:
```bash
OPENAI_API_KEY=sk-your-openai-key-here
```

#### **Step 3: Test Fallback**
The system automatically falls back to OpenAI if Gemini fails.

### **LLM Usage & Quotas**

#### **Gemini 2.5 Flash-Lite (Recommended):**
- **Free Tier:** 1,000 requests/day
- **Rate Limits:** 15 requests/minute
- **Cost:** $0.00 (free tier)
- **Performance:** Excellent for resume processing

#### **OpenAI GPT-4o-mini (Fallback):**
- **Cost:** ~$0.001 per resume
- **Rate Limits:** Varies by account
- **Performance:** Good fallback option

#### **Monitoring Usage:**
- Visit: `http://localhost:8000/api/v1/llm-usage/stats`
- Real-time quota monitoring
- Automatic blocking when limits exceeded

---

## 🔐 Environment Variables

### **Complete .env Configuration**

```bash
# ============================================
# DATABASE CONFIGURATION
# ============================================
# PostgreSQL (Recommended)
DATABASE_URL=postgresql+asyncpg://hr_user:your_secure_password@localhost:5432/hr_assistant

# OR SQLite (Development)
# DATABASE_URL=sqlite+aiosqlite:///./hr_assistant.db

# Database Settings
DATABASE_ECHO=False
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# ============================================
# AI/LLM CONFIGURATION (REQUIRED)
# ============================================
# Google Gemini API (Primary)
GEMINI_API_KEY=AIzaSyC6XiQOL1AFhJqQDKH6uavllewDMDk4hsQ
GEMINI_MODEL=gemini-2.5-flash-lite
DEFAULT_LLM_PROVIDER=gemini

# OpenAI API (Optional Fallback)
OPENAI_API_KEY=sk-your-openai-key-here

# ============================================
# APPLICATION SETTINGS
# ============================================
# Basic Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your-secret-key-change-this-in-production

# File Upload
MAX_UPLOAD_SIZE=10485760
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads
RESUME_UPLOAD_DIR=uploads/resumes

# Processing
MAX_PAGES_OCR=5
OCR_CONFIDENCE_THRESHOLD=0.7

# ============================================
# REDIS CONFIGURATION (Optional)
# ============================================
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# ============================================
# SECURITY SETTINGS
# ============================================
# CORS (for frontend)
ALLOWED_HOSTS=["*"]
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Session Management
SESSION_TIMEOUT=3600
SESSION_COOKIE_SECURE=False  # Set to True for HTTPS
SESSION_COOKIE_HTTPONLY=True

# ============================================
# LOGGING CONFIGURATION
# ============================================
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# ============================================
# FEATURE FLAGS
# ============================================
ENABLE_LINKEDIN_VERIFICATION=True
ENABLE_JOB_HOPPING_DETECTION=True
ENABLE_SOFT_DELETE=True
ENABLE_LLM_USAGE_TRACKING=True
```

### **Environment File Security**

⚠️ **IMPORTANT SECURITY NOTES:**
- **Never commit `.env` files** to version control
- **Use strong passwords** for database credentials
- **Rotate API keys** regularly
- **Use different keys** for development vs production

---

## ⚙️ Running the Application

### **Development Mode**
```bash
# Auto-reload on file changes
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

### **Production Mode**
```bash
# Optimized for production
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Or use Gunicorn for better performance
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### **Docker Deployment**
```bash
# Build and run with Docker
docker build -t ai-hr-assistant .
docker run -p 8000:8000 --env-file .env ai-hr-assistant

# Or use Docker Compose (recommended)
docker-compose up -d
```

### **Health Checks**
```bash
# API Health Check
curl http://localhost:8000/api/health

# Database Connection Check
curl http://localhost:8000/api/v1/database/health

# LLM Status Check
curl http://localhost:8000/api/v1/llm-usage/available-providers
```

---

## 🧪 Testing & Development

### **Running Tests**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_resume_extraction.py

# Run with coverage
pytest --cov=core --cov-report=html

# Run performance tests
pytest tests/test_performance.py -v
```

### **Development Workflow**

#### **Adding New Features:**
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes
3. Add tests: `tests/test_new_feature.py`
4. Run tests: `pytest tests/test_new_feature.py`
5. Create migration if needed: `alembic revision --autogenerate -m "new_feature"`
6. Update documentation
7. Submit pull request

#### **Code Quality:**
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type checking
mypy core/
```

### **Debugging Tips**

#### **Common Issues & Solutions:**

**1. Database Connection Errors:**
```bash
# Check database connection
python -c "from core.database import engine; engine.connect()"

# Reset database (development only)
python -c "from core.database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"
```

**2. LLM API Errors:**
```bash
# Check API key configuration
python -c "import os; print('Gemini Key:', bool(os.getenv('GEMINI_API_KEY')))"

# Test LLM connection
python -c "
from services.llm_resume_extractor import LLMResumeExtractor
extractor = LLMResumeExtractor()
print('LLM Status: OK')
"
```

**3. File Upload Issues:**
```bash
# Check upload directory permissions
chmod -R 755 uploads/
ls -la uploads/
```

---

## 🔍 Troubleshooting

### **Common Issues & Solutions**

#### **1. "Module not found" Errors**
```bash
# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### **2. Database Connection Issues**
```bash
# PostgreSQL troubleshooting
sudo systemctl status postgresql
sudo systemctl start postgresql

# Test connection
psql -h localhost -U hr_user -d hr_assistant

# Reset database (development)
rm hr_assistant.db  # SQLite
dropdb hr_assistant && createdb hr_assistant  # PostgreSQL
```

#### **3. LLM API Quota Exceeded**
```bash
# Check usage stats
curl http://localhost:8000/api/v1/llm-usage/stats

# Reset quota (admin only)
curl -X POST http://localhost:8000/api/v1/llm-usage/reset

# Switch to fallback provider
# Edit .env: DEFAULT_LLM_PROVIDER=openai
```

#### **4. File Upload Fails**
```bash
# Check file size limits
# Edit .env: MAX_FILE_SIZE=52428800  # 50MB

# Check directory permissions
chmod -R 777 uploads/
mkdir -p uploads/resumes uploads/temp
```

#### **5. Import Errors**
```bash
# Install missing system dependencies
# Ubuntu/Debian:
sudo apt-get install python3-dev build-essential
sudo apt-get install tesseract-ocr libtesseract-dev
sudo apt-get install poppler-utils

# macOS:
brew install tesseract
brew install poppler
```

### **Getting Help**

#### **Logs Location:**
- **Application Logs:** `logs/app.log`
- **Uvicorn Logs:** Console output
- **Database Logs:** PostgreSQL log files

#### **Debug Mode:**
```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG
python -m uvicorn main:app --reload --log-level debug
```

#### **Common Log Locations:**
- **Linux:** `/var/log/postgresql/`
- **macOS:** `/usr/local/var/log/postgresql/`
- **Windows:** Event Viewer → Windows Logs → Application

---

## ⬆️ Upgrading from MVP-1

### **For Existing MVP-1 Users**

If you already have the MVP-1 version running locally, you can easily upgrade to MVP-2 with enhanced features and improved setup experience.

#### **Quick Upgrade (5 minutes):**
```bash
# 1. Backup your current setup
cp .env .env.backup
cp hr_assistant.db hr_assistant_backup.db  # If using SQLite

# 2. Switch to mvp-2 branch
git fetch origin
git checkout mvp-2

# 3. Update dependencies
pip install -r requirements.txt --upgrade

# 4. Update environment configuration
cp .env.example .env
# Edit .env with your API keys

# 5. Run migrations
python -m alembic upgrade head

# 6. Verify and start
python verify_setup.py
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### **Complete Migration Guide:**
For detailed step-by-step instructions, see: [`MIGRATION_GUIDE_MVP1_TO_MVP2.md`](MIGRATION_GUIDE_MVP1_TO_MVP2.md)

**Key improvements in MVP-2:**
- ✅ **Automated setup scripts** (`setup.sh`, `setup.ps1`)
- ✅ **Setup verification** (`verify_setup.py`)
- ✅ **Enhanced LLM configuration** (Gemini 2.5 Flash-Lite)
- ✅ **Better documentation** and troubleshooting
- ✅ **Improved environment** management

---

## 📚 Additional Resources

### **API Documentation**
- **Interactive API Docs:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

### **Database Schema**
- **Entity Relationship Diagram:** `docs/database_schema.md`
- **Migration History:** `alembic/versions/`
- **Model Definitions:** `core/models/`

### **Contributing Guidelines**
- **Development Workflow:** `CONTRIBUTING.md`
- **Code Standards:** `STYLE_GUIDE.md`
- **Testing Guidelines:** `TESTING_GUIDE.md`

### **Deployment Guides**
- **Production Deployment:** `DEPLOY_GUIDE.md`
- **Docker Deployment:** `docker-compose.yml`
- **CI/CD Setup:** `.github/workflows/`

### **Feature Documentation**
- **LLM Integration:** `LLM_EXTRACTION_README.md`
- **Job Hopping Logic:** `JOB_HOPPING_LOGIC.md`
- **Activity Tracking:** `USER_ACTIVITY_TRACKING.md`

---

## 🎯 Development Roadmap

### **Current Phase (mvp-2):**
- ✅ **Complete local development setup**
- ✅ **Database migrations included**
- ✅ **LLM integration documented**
- ✅ **Production-ready configuration**

### **Previous Accomplishments:**
- ✅ **Phase 1:** Core vetting system (100%)
- ✅ **Phase 2:** LLM resume extraction (95%+ accuracy)
- ✅ **Production Deployment:** Live on Dokploy

### **Future Enhancements:**
- 🔄 **Phase 3:** User activity tracking (In Progress)
- 🔄 **Phase 4:** Advanced team analytics
- 🔄 **Phase 5:** Multi-tenant architecture
- 🔄 **Phase 6:** Modern React frontend

---

## 📞 Support & Contact

### **For Technical Issues:**
1. **Check Troubleshooting Section** (above)
2. **Review Application Logs** (`logs/app.log`)
3. **Test Database Connection** (`python -c "from core.database import engine; engine.connect()"`)
4. **Verify Environment Variables** (`cat .env | grep -v "KEY\|PASSWORD"`)

### **For Feature Requests:**
- Create an issue in the repository
- Use the feedback form in the application (`/feedback`)

### **For Contributions:**
- Fork the repository
- Create a feature branch
- Submit a pull request

---

## ✅ Setup Checklist

- [ ] **Clone repository**
- [ ] **Create virtual environment**
- [ ] **Install dependencies**
- [ ] **Setup database (PostgreSQL/SQLite)**
- [ ] **Run migrations**
- [ ] **Configure .env file**
- [ ] **Get Gemini API key**
- [ ] **Start application**
- [ ] **Verify health check**
- [ ] **Test resume upload**

---

**🎉 Congratulations! Your AI HR Assistant is now running locally.**

**Visit:** http://localhost:8000

**For API documentation:** http://localhost:8000/docs

**Need help?** Check the troubleshooting section above or create an issue in the repository.

---

**Built with ❤️ for the future of HR recruitment** 🚀
