# Production Deployment Checklist
**Date:** October 18, 2025  
**Version:** MVP-2  
**Branch:** mvp-2

## ✅ All Features Implemented

### 1. **Navbar Access Updates**
- ✅ Recruiters now have direct access to **Vetting** and **Candidates** links in navbar
- ✅ HR Managers have access to **Vetting** and **Candidates** links in navbar
- ✅ No longer need to go through dashboard to access these features

### 2. **Candidate Deletion System**

#### **Soft Delete** (Recruiter/Manager/Admin)
- ✅ Endpoint: `DELETE /api/v1/candidates/{id}/soft-delete`
- ✅ Sets `is_deleted=True`, records who/when/why
- ✅ Candidates hidden from normal queries but remain in database
- ✅ Can be restored by admin

#### **Hard Delete** (Admin Only)
- ✅ Endpoint: `DELETE /api/v1/candidates/{id}/hard-delete`
- ✅ Permanently removes candidate from database (IRREVERSIBLE)
- ✅ CASCADE deletes all related data (resumes, skills, work experience, etc.)
- ✅ Logged with warning level for audit trail

#### **Restore** (Admin Only)
- ✅ Endpoint: `POST /api/v1/candidates/{id}/restore`
- ✅ Restores soft-deleted candidate to active status
- ✅ Clears deletion metadata

#### **Admin Management UI**
- ✅ New page: `/admin/deleted-candidates`
- ✅ View all soft-deleted candidates with pagination
- ✅ See deletion metadata (who deleted, when, reason)
- ✅ Restore candidates with confirmation dialog
- ✅ Hard delete with double-confirmation warning
- ✅ Accessible from admin dropdown menu in navbar

### 3. **Activity Dashboard - Real-Time Charts**

#### **Activity Trend Chart** (Line Chart)
- ✅ Shows daily activity volume for last 7 days
- ✅ Real data from `user_activity_log` table
- ✅ Auto-updates every 10 seconds

#### **Activity Distribution Chart** (Doughnut Chart)
- ✅ Shows activity breakdown by category
- ✅ Categories: Vetting, Viewing, Creating, Searching, Other
- ✅ Color-coded visualization

#### **Top Performers This Month**
- ✅ Leaderboard with productivity scores
- ✅ Shows resumes vetted, candidates created
- ✅ Ranked by performance

#### **Recent Activity Feed**
- ✅ Live feed of latest user actions
- ✅ Shows user name, action type, time ago
- ✅ Icons for different action types
- ✅ Updates every 10 seconds

### 4. **Team-Wide Activity Metrics**
- ✅ Dashboard now shows **team-wide** metrics instead of per-user
- ✅ Active Users count shows unique users (not active days)
- ✅ Resumes Vetted shows all team members' vetting
- ✅ Interviews Scheduled tracks all team interviews

---

## 🗄️ Database Migration Required

### **Migration Script:** `migrations/add_soft_delete_columns.py`

**Columns Added to `candidates` table:**
- `is_deleted` (INTEGER, default 0, indexed)
- `deleted_at` (DATETIME)
- `deleted_by` (VARCHAR(255))
- `deletion_reason` (TEXT)

### **Migration Status:**
✅ **Already Applied** - Migration ran successfully on development database

### **To Run Migration on Production:**
```bash
python migrations/add_soft_delete_columns.py
```

**Expected Output:**
```
🔄 Starting migration: Add soft delete columns to candidates table
  ➕ Adding column: is_deleted
  ➕ Adding column: deleted_at
  ➕ Adding column: deleted_by
  ➕ Adding column: deletion_reason
  ✓ Created index on is_deleted
✅ Migration completed successfully!
```

---

## 📋 Pre-Deployment Steps

### 1. **Backup Database**
```bash
# SQLite backup
cp hr_assistant.db hr_assistant.db.backup_$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup (if using Postgres in production)
pg_dump -U username -d hr_assistant > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. **Run Migration**
```bash
python migrations/add_soft_delete_columns.py
```

### 3. **Verify Migration**
```bash
python check_db_columns.py
```

Expected output should show:
```
✅ Soft delete columns found:
  - is_deleted: INTEGER
  - deleted_at: DATETIME
  - deleted_by: VARCHAR(255)
```

### 4. **Pull Latest Code**
```bash
git checkout mvp-2
git pull origin mvp-2
```

### 5. **Install Dependencies** (if any new packages)
```bash
pip install -r requirements.txt
```

### 6. **Restart Application**
```bash
# Stop current process
# Then start:
python main.py
```

---

## 🧪 Post-Deployment Testing

### **Test 1: Navbar Access (Recruiter)**
1. Login as recruiter
2. ✅ Verify "Vetting" link visible in navbar
3. ✅ Verify "Candidates" link visible in navbar
4. ✅ Click both links and verify access

### **Test 2: Soft Delete**
1. Login as recruiter/manager
2. Go to candidate detail page
3. ✅ Click "Reject Candidate" or delete button
4. ✅ Verify candidate disappears from candidate list
5. ✅ Verify candidate NOT in search results

### **Test 3: Admin Deleted Candidates Page**
1. Login as admin
2. Click profile dropdown → "Deleted Candidates"
3. ✅ Verify deleted candidate appears in list
4. ✅ Verify deletion metadata (who, when, reason) is shown
5. ✅ Click "Restore" → verify candidate returns to active list
6. ✅ Delete again, then click "Delete Forever"
7. ✅ Verify permanent deletion with confirmation dialog

### **Test 4: Activity Dashboard Charts**
1. Login as admin
2. Go to Activity Dashboard
3. ✅ Verify "Activity Trend" chart shows real data (not placeholder)
4. ✅ Verify "Activity Distribution" chart shows real data
5. ✅ Verify "Top Performers" shows actual users
6. ✅ Verify "Recent Activity" shows latest actions
7. ✅ Wait 10 seconds, verify auto-refresh works
8. ✅ Click refresh button, verify manual refresh works

### **Test 5: Team-Wide Metrics**
1. Login as admin → Activity Dashboard
2. ✅ Verify "Active Users" count shows 2+ (if multiple users logged in)
3. Login as recruiter → vet a resume
4. ✅ Verify admin dashboard updates "Resumes Vetted" count
5. ✅ Verify "Total Actions" increases

---

## 🔒 Security Checklist

- ✅ Hard delete is admin-only (enforced in API)
- ✅ Soft delete available to recruiter/manager/admin
- ✅ Deleted candidates page is admin-only
- ✅ Activity dashboard endpoints are admin-only
- ✅ All endpoints have authentication checks
- ✅ Confirmation dialogs for destructive actions

---

## 📊 Performance Considerations

- ✅ `is_deleted` column is indexed for fast queries
- ✅ Filter service excludes soft-deleted candidates by default
- ✅ Activity queries use indexed timestamp column
- ✅ Dashboard auto-refresh is 10 seconds (not too aggressive)
- ✅ Recent activity limited to 10 items
- ✅ Leaderboard limited to 5 users

---

## 🐛 Known Issues / Limitations

**None** - All features tested and working as expected.

---

## 📞 Rollback Plan

If issues arise after deployment:

### **Rollback Code:**
```bash
git checkout <previous-commit-hash>
# Restart application
```

### **Rollback Database:**
The migration is **additive only** (adds columns, doesn't modify existing data).
- No rollback needed for database
- New columns will simply be ignored by old code
- If needed, columns can be dropped manually:
  ```sql
  ALTER TABLE candidates DROP COLUMN is_deleted;
  ALTER TABLE candidates DROP COLUMN deleted_at;
  ALTER TABLE candidates DROP COLUMN deleted_by;
  ALTER TABLE candidates DROP COLUMN deletion_reason;
  ```

---

## ✅ Deployment Sign-Off

- [x] All features implemented and tested
- [x] Database migration script ready
- [x] Migration tested on development database
- [x] Code committed and pushed to `mvp-2` branch
- [x] Documentation complete
- [x] Rollback plan documented

**Ready for Production Deployment!** 🚀

---

## 📝 Additional Notes

### **New Files Created:**
- `templates/admin/deleted_candidates.html` - Admin UI for managing deleted candidates
- `migrations/add_soft_delete_columns.py` - Database migration script
- `check_db_columns.py` - Utility to verify migration

### **Modified Files:**
- `templates/components/unified_navbar.html` - Navbar access updates
- `api/v1/candidates.py` - Hard delete, restore, get deleted endpoints
- `api/v1/activity.py` - Chart data endpoints
- `services/activity_tracker.py` - Chart data methods
- `templates/admin/activity_dashboard.html` - Real-time chart updates
- `main.py` - Route for deleted candidates page

### **Commits:**
1. `7a0c3ef` - Dashboard team-wide metrics fix
2. `b7079f5` - Soft/hard delete with admin UI
3. `f9cd977` - Real-time activity dashboard charts

---

**Deployment Date:** _____________  
**Deployed By:** _____________  
**Production URL:** _____________  
**Status:** _____________
