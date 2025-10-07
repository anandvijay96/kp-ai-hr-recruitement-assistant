# 🧹 Branch Cleanup Plan

## Problem
The `feature/authenticity-only` branch accidentally includes files from `feature/resume-upload` that should NOT be deployed yet (database, OAuth, Celery, etc.).

## Solution Options

### **Option 1: Cherry-Pick Only What We Need (RECOMMENDED)**

Create a fresh branch from `main` and cherry-pick ONLY the commits we need:

```bash
# Start fresh from main
git checkout main
git pull origin main
git checkout -b feature/authenticity-clean

# Cherry-pick ONLY these commits (in order):
git cherry-pick <commit-hash-1>  # Selenium verifier files
git cherry-pick <commit-hash-2>  # Resume analyzer updates
git cherry-pick <commit-hash-3>  # Browserless support
git cherry-pick <commit-hash-4>  # Google search fix
git cherry-pick <commit-hash-5>  # Font normalization

# Push clean branch
git push origin feature/authenticity-clean
```

### **Option 2: Remove Unwanted Files from Current Branch**

```bash
git checkout feature/authenticity-only

# Remove files that shouldn't be there
git rm -r models/db/
git rm -r api/v1/
git rm -r tasks/
git rm core/security.py
git rm core/celery_app.py
git rm core/database.py
git rm -r static/css/
git rm -r static/js/
git rm -r alembic/
# ... etc

git commit -m "Remove database/OAuth/Celery files - not ready for deployment"
git push origin feature/authenticity-only
```

### **Option 3: Create New Branch with Manual File Copy (SAFEST)**

```bash
# Checkout main
git checkout main
git pull origin main

# Create new clean branch
git checkout -b feature/authenticity-final

# Copy ONLY the files we need from feature/authenticity-only
git checkout feature/authenticity-only -- services/selenium_linkedin_verifier.py
git checkout feature/authenticity-only -- services/google_search_verifier.py
git checkout feature/authenticity-only -- services/resume_analyzer.py
git checkout feature/authenticity-only -- services/document_processor.py
git checkout feature/authenticity-only -- nixpacks.toml
git checkout feature/authenticity-only -- requirements.txt
git checkout feature/authenticity-only -- core/config.py
git checkout feature/authenticity-only -- main.py
git checkout feature/authenticity-only -- templates/upload.html
git checkout feature/authenticity-only -- BROWSERLESS_SETUP.md

# Commit
git commit -m "feat: Add LinkedIn verification with Browserless (clean)"
git push origin feature/authenticity-final
```

---

## ✅ **Files That SHOULD Be Deployed**

### **Core Authenticity Features:**
- `services/resume_analyzer.py` ✅
- `services/selenium_linkedin_verifier.py` ✅ (NEW)
- `services/google_search_verifier.py` ✅ (NEW)
- `services/document_processor.py` ✅ (font normalization)
- `services/jd_matcher.py` ✅
- `services/result_storage.py` ✅

### **Configuration:**
- `core/config.py` ✅ (add selenium settings only)
- `requirements.txt` ✅ (add selenium, beautifulsoup4)
- `nixpacks.toml` ✅ (remove chromium, keep tesseract)
- `main.py` ✅ (selenium initialization only)

### **Templates:**
- `templates/upload.html` ✅ (enhanced UI)

### **Documentation:**
- `BROWSERLESS_SETUP.md` ✅ (NEW)

---

## ❌ **Files That Should NOT Be Deployed**

### **Database (Phase 2):**
- `models/database.py` ❌
- `models/db/` ❌
- `models/user.py` ❌
- `models/candidate.py` ❌
- `core/database.py` ❌
- `alembic/` ❌
- `alembic.ini` ❌
- `init_db.py` ❌

### **OAuth/Auth (Phase 2):**
- `core/security.py` ❌
- `api/v1/auth.py` ❌
- `api/v1/candidates.py` ❌
- `api/v1/resumes.py` ❌
- `services/auth_service.py` ❌

### **Celery/Redis (Phase 2):**
- `core/celery_app.py` ❌
- `tasks/` ❌

### **Advanced Features (Phase 2):**
- `services/candidate_service.py` ❌
- `services/resume_service.py` ❌
- `services/filter_service.py` ❌
- `services/preset_service.py` ❌
- `services/resume_data_extractor.py` ❌

### **Static Files (Phase 2):**
- `static/css/filter-dashboard.css` ❌
- `static/css/style.css` ❌ (if it's the new one)
- `static/js/filter.js` ❌
- `static/js/resume_upload.js` ❌

### **Templates (Phase 2):**
- `templates/candidate_dashboard.html` ❌
- `templates/resume_upload.html` ❌

### **Test Files:**
- `test_google_api*.py` ❌
- `test_selenium_quick.py` ❌
- `tests/test_database_models.py` ❌
- `tests/test_filters.py` ❌
- `tests/test_resumes.py` ❌

### **Reference:**
- `temp_selenium_reference/` ❌

---

## 🎯 **Recommended Action Plan**

### **Step 1: Create Clean Branch (Option 3)**
This is the safest approach - manually copy only what we need.

### **Step 2: Close Current PR**
- Close the PR from `feature/authenticity-only`
- Add comment: "Closing this PR - it contains too many files. Creating clean PR."

### **Step 3: Create New PR from Clean Branch**
- Create PR from `feature/authenticity-final` → `main`
- Title: "feat: Add LinkedIn Verification with Browserless"
- Description: List only the authenticity features

### **Step 4: After Merge, Return to Feature Branch**
```bash
# After main is updated with authenticity features
git checkout feature/resume-upload

# Rebase on updated main to get the authenticity features
git rebase main

# Resolve any conflicts (there should be minimal conflicts)
git push origin feature/resume-upload --force-with-lease
```

---

## 🔄 **Handling Conflicts After Merge**

When you return to `feature/resume-upload` and rebase on main:

### **Expected Conflicts:**
1. **`services/resume_analyzer.py`** - Both branches modified it
   - Resolution: Keep feature branch version (has more features)
   
2. **`main.py`** - Both branches modified it
   - Resolution: Merge both changes (selenium + database initialization)
   
3. **`core/config.py`** - Both branches added settings
   - Resolution: Merge both (selenium settings + database settings)

### **No Conflicts Expected:**
- New files in feature branch (database models, OAuth, etc.)
- Files only modified in one branch

---

## 📝 **Git Commands for Clean Deployment**

```bash
# 1. Create clean branch
git checkout main
git pull origin main
git checkout -b feature/authenticity-final

# 2. Copy only needed files
git checkout feature/authenticity-only -- services/selenium_linkedin_verifier.py
git checkout feature/authenticity-only -- services/google_search_verifier.py
git checkout feature/authenticity-only -- services/resume_analyzer.py
git checkout feature/authenticity-only -- services/document_processor.py
git checkout feature/authenticity-only -- nixpacks.toml
git checkout feature/authenticity-only -- BROWSERLESS_SETUP.md

# 3. Manually update these files (don't copy entire file):
# - requirements.txt (add only: selenium, webdriver-manager, beautifulsoup4, lxml)
# - core/config.py (add only: selenium settings)
# - main.py (add only: selenium initialization)
# - templates/upload.html (if it has authenticity UI changes)

# 4. Commit and push
git add .
git commit -m "feat: Add LinkedIn verification with Browserless

- Selenium-based LinkedIn profile verification
- Browserless integration for Railway
- Font normalization (weight variants)
- Google search with site:linkedin.com
- Cross-verification logic

No database, OAuth, or Celery features included."

git push origin feature/authenticity-final

# 5. Create PR from feature/authenticity-final → main
```

---

## ✅ **After Deployment**

Once the clean PR is merged to main:

```bash
# Switch back to feature branch
git checkout feature/resume-upload

# Rebase on updated main
git rebase main

# Resolve conflicts (should be minimal)
# - Keep feature branch changes for database/OAuth
# - Merge selenium initialization in main.py

# Continue Phase 2 work
```

---

## 🚨 **Important Notes**

1. **Don't merge current PR as-is** - it has too many files
2. **Create clean branch** - copy only what's needed
3. **Minimal conflicts expected** - most files are new in feature branch
4. **Test after rebase** - ensure everything still works

---

**This approach keeps deployment clean and makes returning to feature branch smooth!** 🎯
