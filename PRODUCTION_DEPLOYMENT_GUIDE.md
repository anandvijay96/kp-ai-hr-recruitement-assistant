# Production Deployment Guide - Phase 2 to MVP-1

## 🚨 CRITICAL: Database Migrations Required

**IMPORTANT:** Run these migrations in order BEFORE deploying to production!

### Migration Order

```bash
# 1. Add responsibilities column to work_experience table
python migrations/add_responsibilities_to_work_experience.py

# 2. Add linkedin_suggestions column to candidates table  
python migrations/add_linkedin_suggestions.py
```

---

## 📋 Pre-Deployment Checklist

### 1. Database Backup
```bash
# Backup production database BEFORE running migrations
cp hr_recruitment.db hr_recruitment.db.backup_$(date +%Y%m%d_%H%M%S)
```

### 2. Verify Migrations Locally
```bash
# Test migrations on local database first
python migrations/add_responsibilities_to_work_experience.py
python migrations/add_linkedin_suggestions.py

# Verify columns were added
python scripts/check_linkedin_suggestions.py
```

### 3. Check for Breaking Changes
- ✅ All migrations are **additive only** (no data loss)
- ✅ Existing data is preserved
- ✅ New columns have default values (NULL)
- ✅ No foreign key constraints added
- ✅ Backward compatible

---

## 🔄 Deployment Steps

### Step 1: Merge to mvp-1 Branch
```bash
git checkout mvp-1
git merge feature/llm-extraction
git push origin mvp-1
```

**Note:** Auto-deployment will trigger on push to mvp-1

### Step 2: Run Migrations on Production

**SSH into production server:**
```bash
ssh user@production-server
cd /path/to/ai-hr-assistant
```

**Run migrations:**
```bash
# Backup first!
cp hr_recruitment.db hr_recruitment.db.backup_$(date +%Y%m%d_%H%M%S)

# Run migrations
python migrations/add_responsibilities_to_work_experience.py
python migrations/add_linkedin_suggestions.py
```

**Verify:**
```bash
python scripts/check_linkedin_suggestions.py
```

### Step 3: Restart Application
```bash
# Restart the application service
sudo systemctl restart ai-hr-assistant
# OR
pm2 restart ai-hr-assistant
```

### Step 4: Smoke Test
1. Visit production URL
2. Upload a test resume
3. Verify:
   - ✅ Work experience shows bullet points
   - ✅ Education displays correctly
   - ✅ Phone shows with +91 prefix
   - ✅ LinkedIn suggestions appear (if found)
   - ✅ Edit feature preserves all data

---

## 🆕 What's New in This Release

### Features Added:
1. **Work Experience Responsibilities** - Bullet point display
2. **Enhanced Education** - Indian schooling support (Intermediate, Secondary)
3. **LinkedIn Profile Selection** - HR can choose from multiple found profiles
4. **Phone Number Formatting** - Auto +91 prefix
5. **Edit Feature Fix** - No more data loss on edit
6. **Dashboard Fixes** - Correct candidate counts, proper sorting
7. **UI Improvements** - Removed BETA badges, cleaner layout

### Database Schema Changes:
```sql
-- work_experience table
ALTER TABLE work_experience ADD COLUMN responsibilities TEXT;

-- candidates table
ALTER TABLE candidates ADD COLUMN linkedin_suggestions TEXT;
```

---

## 🔍 Migration Details

### Migration 1: add_responsibilities_to_work_experience.py

**What it does:**
- Adds `responsibilities` column to `work_experience` table
- Type: TEXT (JSON array)
- Stores bullet points for each job

**Safe because:**
- Column is nullable (existing data unaffected)
- No data transformation required
- Backward compatible

**Rollback:**
```sql
ALTER TABLE work_experience DROP COLUMN responsibilities;
```

### Migration 2: add_linkedin_suggestions.py

**What it does:**
- Adds `linkedin_suggestions` column to `candidates` table
- Type: TEXT (JSON array)
- Stores LinkedIn profiles found during vetting

**Safe because:**
- Column is nullable (existing data unaffected)
- No data transformation required
- Backward compatible

**Rollback:**
```sql
ALTER TABLE candidates DROP COLUMN linkedin_suggestions;
```

---

## ⚠️ Potential Issues & Solutions

### Issue 1: Migration Fails with "column already exists"
**Solution:** Column was already added, safe to continue

### Issue 2: LinkedIn suggestions not showing
**Causes:**
1. Migration not run → Run migration
2. Candidate uploaded before feature → Re-upload candidate
3. No profiles found by DuckDuckGo → Expected behavior

**Debug:**
```bash
python scripts/check_linkedin_suggestions.py
```

### Issue 3: Work experience bullets not showing
**Causes:**
1. Migration not run → Run migration
2. Old data without responsibilities → Re-upload or edit candidate

**Solution:**
- New uploads will have responsibilities
- Edit existing candidates to add them

---

## 📊 Monitoring After Deployment

### Check Logs:
```bash
tail -f logs/app.log | grep -i "linkedin\|responsibilities"
```

### Watch for Errors:
```bash
tail -f logs/error.log
```

### Monitor Database:
```bash
# Check new columns exist
sqlite3 hr_recruitment.db "PRAGMA table_info(work_experience);"
sqlite3 hr_recruitment.db "PRAGMA table_info(candidates);"

# Check data
sqlite3 hr_recruitment.db "SELECT COUNT(*) FROM work_experience WHERE responsibilities IS NOT NULL;"
sqlite3 hr_recruitment.db "SELECT COUNT(*) FROM candidates WHERE linkedin_suggestions IS NOT NULL;"
```

---

## 🔙 Rollback Plan

If deployment fails:

### 1. Restore Database
```bash
cp hr_recruitment.db.backup_YYYYMMDD_HHMMSS hr_recruitment.db
```

### 2. Revert Code
```bash
git checkout mvp-1
git revert HEAD
git push origin mvp-1
```

### 3. Restart Application
```bash
sudo systemctl restart ai-hr-assistant
```

---

## ✅ Post-Deployment Verification

### Checklist:
- [ ] Migrations ran successfully
- [ ] No errors in logs
- [ ] Can upload new resumes
- [ ] Work experience shows bullet points
- [ ] LinkedIn suggestions appear (when available)
- [ ] Edit feature works without data loss
- [ ] Dashboard shows correct counts
- [ ] Phone numbers show +91 prefix
- [ ] All existing candidates still accessible

---

## 📞 Support

If issues occur:
1. Check logs first
2. Verify migrations ran
3. Test with new resume upload
4. Contact dev team with error logs

---

## 🎯 Success Criteria

Deployment is successful when:
1. ✅ All migrations completed without errors
2. ✅ Application starts without errors
3. ✅ New resumes upload successfully
4. ✅ Work experience displays with bullet points
5. ✅ LinkedIn suggestions work for new uploads
6. ✅ Edit feature preserves all data
7. ✅ No regression in existing features

---

**Deployment Date:** _____________
**Deployed By:** _____________
**Migration Status:** _____________
**Verification Status:** _____________
