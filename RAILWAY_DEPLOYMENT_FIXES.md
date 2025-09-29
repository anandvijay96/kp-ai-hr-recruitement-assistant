# 🚂 Railway Deployment - Complete Troubleshooting Guide

This document contains all the fixes applied to successfully deploy the AI HR Assistant to Railway, and serves as a reference for future deployments.

---

## 📋 Table of Contents
1. [PORT Environment Variable Issues](#1-port-environment-variable-issues)
2. [Pydantic Environment Variable Parsing](#2-pydantic-environment-variable-parsing)
3. [Missing Static Directory](#3-missing-static-directory)
4. [NLTK Data Missing](#4-nltk-data-missing)
5. [Complete Working Configuration](#5-complete-working-configuration)
6. [General Deployment Checklist](#6-general-deployment-checklist)

---

## 1. PORT Environment Variable Issues

### ❌ Problem:
```
Error: Invalid value for '--port': '$PORT' is not a valid integer.
```

### 🔍 Root Cause:
Railway sets `PORT` as an environment variable, but shell commands don't expand `$PORT` correctly in nixpacks configuration.

### ✅ Solution:

**Option A: Use Python to handle PORT (Recommended)**

In `nixpacks.toml`:
```toml
[start]
cmd = "python -c \"import os; import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))\""
```

**Option B: Modify main.py**

```python
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

Then in `nixpacks.toml`:
```toml
[start]
cmd = "python main.py"
```

### 📝 Key Takeaway:
**Always handle dynamic PORT in Python code, not in shell commands.**

---

## 2. Pydantic Environment Variable Parsing

### ❌ Problem:
```
ValidationError: Input should be a valid integer, unable to parse string as an integer
[type=int_parsing, input_value='10485760\n', input_type=str]
```

### 🔍 Root Cause:
Railway environment variables may contain trailing newlines or whitespace, which Pydantic can't parse as integers.

### ✅ Solution:

Add field validator in `core/config.py`:

```python
from pydantic import field_validator

class Settings(BaseSettings):
    max_file_size: int = 10 * 1024 * 1024
    
    @field_validator('max_file_size', 'max_upload_size', mode='before')
    @classmethod
    def parse_int_with_strip(cls, v):
        """Strip whitespace and newlines from integer fields"""
        if isinstance(v, str):
            return int(v.strip())
        return v
```

### 📝 Key Takeaway:
**Always strip() string values before parsing to int in Pydantic models when reading from environment variables.**

---

## 3. Missing Static Directory

### ❌ Problem:
```
RuntimeError: Directory 'static' does not exist
```

### 🔍 Root Cause:
FastAPI's `StaticFiles` requires the directory to exist, but it wasn't in the git repository.

### ✅ Solution:

**Step 1: Make mount conditional in `main.py`:**
```python
# Mount static files (only if directory exists)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
```

**Step 2: Create directory with .gitkeep:**
```bash
mkdir static
echo "# Keep directory" > static/.gitkeep
git add static/.gitkeep
```

### 📝 Key Takeaway:
**Always make directory mounts conditional OR ensure directories exist in repository with .gitkeep files.**

---

## 4. NLTK Data Missing

### ❌ Problem:
```
OSError: No such file or directory: '/root/nltk_data/tokenizers/punkt/PY3_tab'
```

### 🔍 Root Cause:
NLTK requires data files to be downloaded before use. These aren't included in the pip package.

### ✅ Solution:

Add NLTK data download to build phase in `nixpacks.toml`:

```toml
[phases.install]
cmds = [
    "pip install -r requirements.txt",
    "python -c \"import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)\""
]
```

**Alternative: Download on first run (not recommended for production):**

```python
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
```

### 📝 Key Takeaway:
**Download NLTK data during build phase, not at runtime, for faster startup and reliability.**

---

## 5. Complete Working Configuration

### 📄 `nixpacks.toml` (Final Version)

```toml
[phases.setup]
aptPkgs = ["tesseract-ocr", "tesseract-ocr-eng"]

[phases.install]
cmds = [
    "pip install -r requirements.txt",
    "python -c \"import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)\""
]

[start]
cmd = "python -c \"import os; import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))\""
```

### 📄 `railway.toml` (Optional but Recommended)

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python -c 'import os; import uvicorn; uvicorn.run(\"main:app\", host=\"0.0.0.0\", port=int(os.environ.get(\"PORT\", 8000)))'"
healthcheckPath = "/api/health"
restartPolicyType = "ON_FAILURE"
```

### 📄 `core/config.py` (Key Sections)

```python
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    max_file_size: int = 10 * 1024 * 1024
    
    @field_validator('max_file_size', 'max_upload_size', mode='before')
    @classmethod
    def parse_int_with_strip(cls, v):
        if isinstance(v, str):
            return int(v.strip())
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### 📄 `main.py` (Key Sections)

```python
# Conditional static files mount
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Create directories on startup
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.results_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True)
```

---

## 6. General Deployment Checklist

### 🔧 Pre-Deployment Checklist

- [ ] **Environment Variables**
  - [ ] Add validators for all env vars that need type conversion
  - [ ] Strip whitespace in Pydantic validators
  - [ ] Handle PORT dynamically in code

- [ ] **System Dependencies**
  - [ ] List all apt packages in `nixpacks.toml` under `[phases.setup]`
  - [ ] Test locally with Docker to verify dependencies

- [ ] **Python Dependencies**
  - [ ] Ensure `requirements.txt` is up to date
  - [ ] Download any required data files (NLTK, spaCy models) during build

- [ ] **Directories**
  - [ ] Create all required directories with `.gitkeep`
  - [ ] Make directory mounts conditional
  - [ ] Create directories programmatically in code

- [ ] **Static Files**
  - [ ] Ensure static directory exists or mount is conditional
  - [ ] Add `.gitkeep` to empty directories

- [ ] **Configuration Files**
  - [ ] `nixpacks.toml` - Build and start commands
  - [ ] `railway.toml` - Railway-specific settings (optional)
  - [ ] `.gitignore` - Don't commit sensitive files
  - [ ] `Aptfile` - Alternative to nixpacks for system deps

### 🚀 Deployment Steps

1. **Commit all configuration files:**
```bash
git add nixpacks.toml railway.toml core/config.py main.py static/.gitkeep
git commit -m "Add Railway deployment configuration"
git push origin main
```

2. **Connect to Railway:**
   - Go to [railway.app](https://railway.app)
   - Create new project
   - Deploy from GitHub repo
   - Select your repository

3. **Monitor Build Logs:**
   - Watch for errors in build phase
   - Verify system packages install correctly
   - Check Python dependencies install
   - Confirm NLTK data downloads

4. **Monitor Deploy Logs:**
   - Check for startup errors
   - Verify PORT is correctly detected
   - Confirm application starts successfully

5. **Test Deployment:**
   - Generate domain in Railway dashboard
   - Test health check: `https://your-app.up.railway.app/api/health`
   - Test main page: `https://your-app.up.railway.app/`
   - Test upload functionality

### 🐛 Common Deployment Errors & Quick Fixes

| Error | Quick Fix |
|-------|-----------|
| `$PORT is not a valid integer` | Use Python to read PORT from os.environ |
| `ValidationError: unable to parse string as integer` | Add field_validator with .strip() |
| `Directory 'static' does not exist` | Make mount conditional or add .gitkeep |
| `OSError: No such file or directory: nltk_data` | Download NLTK data in build phase |
| `ModuleNotFoundError` | Add missing package to requirements.txt |
| `tesseract: command not found` | Add to aptPkgs in nixpacks.toml |
| `Permission denied` | Check file permissions, use chmod in build |

### 📊 Verification Commands

After deployment, test these endpoints:

```bash
# Health check
curl https://your-app.up.railway.app/api/health

# Statistics
curl https://your-app.up.railway.app/api/statistics

# Upload page (should return HTML)
curl https://your-app.up.railway.app/upload
```

---

## 7. Platform-Specific Notes

### Railway
- ✅ Uses Nixpacks by default
- ✅ Auto-detects Python apps
- ✅ Sets PORT environment variable
- ⚠️ Free tier: $5 credit/month
- ⚠️ Charges based on usage

### Render
- ✅ Uses `Aptfile` for system dependencies
- ✅ Uses `render.yaml` for configuration
- ✅ Free tier: 750 hours/month
- ⚠️ Cold starts after 15 min inactivity

### Heroku
- ✅ Uses `Procfile` for start command
- ✅ Uses buildpacks for dependencies
- ❌ No free tier
- 💰 Starts at $7/month

---

## 8. Best Practices Summary

### ✅ DO:
1. **Handle PORT dynamically** in Python code
2. **Strip environment variables** before type conversion
3. **Make directory mounts conditional**
4. **Download data files during build**, not runtime
5. **Test locally with Docker** before deploying
6. **Use health check endpoints** for monitoring
7. **Keep configuration files in git**
8. **Document all environment variables**

### ❌ DON'T:
1. **Don't hardcode ports** - use environment variables
2. **Don't assume directories exist** - create or check first
3. **Don't download large files at runtime** - do it in build
4. **Don't commit secrets** - use environment variables
5. **Don't skip error handling** - wrap in try/except
6. **Don't ignore logs** - they're your best debugging tool

---

## 9. Quick Reference Commands

### Local Testing
```bash
# Test with Docker
docker build -t test-app .
docker run -p 8000:8000 -e PORT=8000 test-app

# Test with UV
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Railway CLI (Optional)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# View logs
railway logs

# Run locally with Railway env
railway run python main.py
```

---

## 10. Troubleshooting Workflow

```
Deployment Failed?
    ↓
Check Build Logs
    ↓
System deps installed? → NO → Add to aptPkgs
    ↓ YES
Python deps installed? → NO → Check requirements.txt
    ↓ YES
Check Deploy Logs
    ↓
PORT error? → Use Python to handle PORT
    ↓
Validation error? → Add field validators
    ↓
Directory error? → Make mounts conditional
    ↓
NLTK error? → Download in build phase
    ↓
Still failing? → Check application logs
```

---

## 📞 Support Resources

- **Railway Docs**: https://docs.railway.app
- **Nixpacks Docs**: https://nixpacks.com
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/
- **Pydantic Settings**: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

**Last Updated**: 2025-09-30
**Status**: ✅ All issues resolved, deployment successful

---

## ✅ Success Criteria

Your deployment is successful when:
- [ ] Build completes without errors
- [ ] Application starts without crashes
- [ ] Health check endpoint returns 200
- [ ] Upload page loads correctly
- [ ] File upload and analysis works
- [ ] No errors in deploy logs
- [ ] Application responds to requests

**Congratulations! Your app is now deployed! 🎉**
