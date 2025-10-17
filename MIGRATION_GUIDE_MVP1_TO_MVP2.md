# 🚀 Migration Guide: Upgrading from MVP-1 to MVP-2

**Date:** October 17, 2025
**Target Audience:** Developers with existing MVP-1 setup
**Estimated Time:** 10-15 minutes

---

## 📋 Overview

This guide helps you upgrade from the `mvp-1` branch to the `mvp-2` branch, which includes:
- ✅ **Complete local development setup** documentation
- ✅ **Automated setup scripts** for easy onboarding
- ✅ **Updated LLM configuration** (Gemini 2.5 Flash-Lite)
- ✅ **Enhanced environment** configuration
- ✅ **Improved database** migration handling

---

## ⚡ Quick Migration (5 minutes)

### **Step 1: Switch to MVP-2 Branch**
```bash
# Fetch latest changes and switch to mvp-2
git fetch origin
git checkout mvp-2

# Verify you're on the correct branch
git branch --show-current
# Should output: mvp-2
```

### **Step 2: Update Dependencies**
```bash
# Update Python packages
pip install -r requirements.txt --upgrade

# Verify key packages are updated
pip list | grep -E "(fastapi|sqlalchemy|google-generativeai)"
```

### **Step 3: Update Environment Configuration**
```bash
# Backup your current .env file
cp .env .env.backup

# Update with new template
cp .env.example .env

# Edit .env file with your API keys (CRITICAL!)
nano .env  # or use your preferred editor

# Required updates in .env:
# - GEMINI_API_KEY=your_actual_key_here (from https://makersuite.google.com/app/apikey)
# - DATABASE_URL=sqlite+aiosqlite:///./hr_assistant.db (or PostgreSQL)
# - SECRET_KEY=your_secure_secret_here
```

### **Step 4: Run Database Migrations**
```bash
# Apply any new database migrations
python -m alembic upgrade head

# Verify migration completed
python -c "from core.database import engine; print('✅ Database ready')"
```

### **Step 5: Test the Upgrade**
```bash
# Run the setup verification script
python verify_setup.py

# If all checks pass, start the application
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**🎉 Visit: http://localhost:8000**

---

## 🔧 Detailed Migration Steps

### **Step 1: Branch Management**

#### **Check Current Status:**
```bash
# See current branch
git branch --show-current

# See available branches
git branch -a

# Check if you have uncommitted changes
git status
```

#### **Safe Branch Switch:**
```bash
# Stash any uncommitted changes (optional)
git stash

# Switch to mvp-2 branch
git checkout mvp-2

# Restore stashed changes if needed
git stash pop
```

### **Step 2: Dependency Updates**

#### **Check for Updates:**
```bash
# See what packages need updating
pip list --outdated

# Update all packages
pip install -r requirements.txt --upgrade

# Verify critical packages
python -c "
import fastapi, sqlalchemy, google.generativeai as genai
print('✅ All critical packages imported successfully')
"
```

### **Step 3: Database Migration**

#### **Migration Safety:**
```bash
# Backup your database first (IMPORTANT!)
cp hr_assistant.db hr_assistant_backup_$(date +%Y%m%d_%H%M%S).db

# Check current migration status
python -m alembic current

# See migration history
python -m alembic history

# Apply pending migrations
python -m alembic upgrade head
```

#### **If Migration Fails:**
```bash
# Check for specific errors
python -m alembic upgrade head --sql  # See what SQL would be executed

# Manual migration (if needed)
# Edit the migration file in alembic/versions/ and fix issues

# Retry migration
python -m alembic upgrade head
```

### **Step 4: Environment Configuration**

#### **Compare Configuration Files:**
```bash
# See differences between your .env and the new template
diff .env .env.example

# Or use a visual diff tool
# code --diff .env .env.example
```

#### **Required Updates in .env:**

```bash
# ============================================
# CRITICAL UPDATES FOR MVP-2
# ============================================

# LLM Configuration (REQUIRED)
GEMINI_API_KEY=your_actual_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash-lite

# Database (Updated default)
DATABASE_URL=sqlite+aiosqlite:///./hr_assistant.db

# Security (Generate new secret key)
SECRET_KEY=your_new_secret_key_here

# New Features (Optional)
ENABLE_LLM_USAGE_TRACKING=True
LOG_LEVEL=INFO
```

#### **Get Your Gemini API Key:**
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (format: `AIzaSyC...`)
5. Add to your `.env` file

### **Step 5: Verify Everything Works**

#### **Run Verification Script:**
```bash
# Comprehensive setup check
python verify_setup.py
```

#### **Expected Output:**
```
🚀 AI HR Assistant - Setup Verification
==================================================

🔗 Checking database connection...
   ✅ Database connected successfully

🤖 Checking LLM configuration...
   ✅ Gemini API configured (Provider: gemini)

📦 Checking Python dependencies...
   ✅ fastapi
   ✅ sqlalchemy
   ✅ google-generativeai

📁 Checking file upload setup...
   ✅ uploads (writable)
   ✅ uploads/resumes (writable)

🔐 Checking environment configuration...
   ✅ Environment file exists and configured

🌐 Testing API endpoints...
   ✅ Health endpoint responding

==================================================
📊 VERIFICATION SUMMARY
==================================================
Dependencies        ✅ PASS
Environment File    ✅ PASS
Database           ✅ PASS
LLM Configuration  ✅ PASS
File Uploads       ✅ PASS
API Endpoints      ✅ PASS

🎯 Overall: 6/6 checks passed

🎉 CONGRATULATIONS!
✅ Your AI HR Assistant is properly configured!
```

### **Step 6: Start the Application**

#### **Development Mode:**
```bash
# Start with auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access points:
# - Web interface: http://localhost:8000
# - API docs: http://localhost:8000/docs
# - Health check: http://localhost:8000/api/health
```

#### **Production Mode:**
```bash
# Optimized for production
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Or use Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🔍 Troubleshooting Migration Issues

### **Problem 1: "Module not found" Errors**
```bash
# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

### **Problem 2: Database Migration Conflicts**
```bash
# Check migration status
python -m alembic current

# If conflicts exist, you may need to:
# 1. Backup your data
# 2. Drop and recreate the database
# 3. Restore data manually

# For development (SQLite):
rm hr_assistant.db
python -m alembic upgrade head

# For production (PostgreSQL):
# dropdb hr_assistant && createdb hr_assistant
# python -m alembic upgrade head
```

### **Problem 3: Environment Variable Issues**
```bash
# Check if .env file is loaded
python -c "import os; print('DATABASE_URL:', os.getenv('DATABASE_URL', 'NOT SET'))"

# Test database connection manually
python -c "
from core.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('✅ Database OK')
except Exception as e:
    print('❌ Database error:', e)
"
```

### **Problem 4: LLM API Key Issues**
```bash
# Test Gemini API key
python -c "
import os
from services.llm_resume_extractor import LLMResumeExtractor

try:
    extractor = LLMResumeExtractor()
    print('✅ LLM configured:', extractor.provider)
except Exception as e:
    print('❌ LLM error:', e)
"
```

---

## 📚 New Features in MVP-2

### **🆕 Enhanced Setup Experience:**
- **Automated setup scripts** (`setup.sh` for Linux/Mac, `setup.ps1` for Windows)
- **Setup verification script** (`verify_setup.py`) for automated testing
- **Comprehensive documentation** (`README_LOCAL_SETUP.md`)

### **🆕 Improved LLM Integration:**
- **Updated Gemini model** (`gemini-2.5-flash-lite`)
- **Better error handling** and fallback mechanisms
- **Usage monitoring** and quota management

### **🆕 Enhanced Configuration:**
- **Updated environment template** with all current settings
- **Better security defaults**
- **Development vs production** configuration guidance

### **🆕 Database Improvements:**
- **Better migration handling**
- **SQLite default** for easier development
- **PostgreSQL production** instructions

---

## 🔄 Rollback Instructions (If Needed)

### **Revert to MVP-1:**
```bash
# Switch back to mvp-1
git checkout mvp-1

# If you want to keep your data
# 1. Backup current database
# 2. Switch branch
# 3. Restore database backup

# Restore your .env backup
cp .env.backup .env
```

### **Database Rollback:**
```bash
# Check migration history
python -m alembic history

# Rollback last migration
python -m alembic downgrade -1

# Rollback multiple migrations
python -m alembic downgrade -3  # Last 3 migrations
```

---

## ✅ Migration Checklist

- [ ] **Switch to mvp-2 branch** (`git checkout mvp-2`)
- [ ] **Update dependencies** (`pip install -r requirements.txt --upgrade`)
- [ ] **Backup .env file** (`cp .env .env.backup`)
- [ ] **Update .env with API keys** (Gemini key required)
- [ ] **Run database migrations** (`python -m alembic upgrade head`)
- [ ] **Test setup verification** (`python verify_setup.py`)
- [ ] **Start application** (`python -m uvicorn main:app --reload`)
- [ ] **Verify web interface works** (http://localhost:8000)
- [ ] **Test resume upload** functionality

---

## 📞 Getting Help

### **If Migration Fails:**
1. **Check the troubleshooting section** above
2. **Run the verification script:** `python verify_setup.py`
3. **Check application logs** in `logs/app.log`
4. **Review the complete setup guide:** `README_LOCAL_SETUP.md`

### **Common Issues:**
- **Database errors:** Check your `DATABASE_URL` in `.env`
- **LLM errors:** Verify your `GEMINI_API_KEY` is correct
- **Import errors:** Run `pip install -r requirements.txt --upgrade`
- **Port conflicts:** Make sure port 8000 is available

---

## 🎉 Migration Complete!

After following these steps, you'll have:
- ✅ **Latest MVP-2 features** and improvements
- ✅ **Automated setup scripts** for easy onboarding
- ✅ **Updated LLM integration** with better performance
- ✅ **Enhanced documentation** and troubleshooting
- ✅ **Production-ready** local development environment

**Your AI HR Assistant is now running on MVP-2 with all the latest improvements!** 🚀

**Visit:** http://localhost:8000

---

*For the complete setup guide, see:* `README_LOCAL_SETUP.md`
