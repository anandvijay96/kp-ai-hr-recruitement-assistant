# Production Database Migration Guide
**For:** Dokploy PostgreSQL Deployment  
**Migration:** Make `resumes.uploaded_by` nullable  
**Date:** October 16, 2025

---

## 🎯 Overview

This guide explains how to run the database migration on your Dokploy-hosted PostgreSQL database to fix the `uploaded_by` NOT NULL constraint issue.

---

## 🔍 The Issue

**Error:**
```
(sqlite3.IntegrityError) NOT NULL constraint failed: resumes.uploaded_by
```

**Cause:**
- Vetting workflow uploads resumes without user context
- Database has NOT NULL constraint on `uploaded_by`
- Model definition has `nullable=True` but database schema is out of sync

**Solution:**
- Make `uploaded_by` column nullable in database

---

## 📋 Migration Options for Dokploy

### **Option 1: Using Dokploy Database Console (Recommended)**

#### **Step 1: Access Dokploy Dashboard**
1. Log in to your Dokploy dashboard
2. Navigate to your application
3. Go to **Database** section
4. Click on your PostgreSQL database

#### **Step 2: Open Database Console**
1. Look for **"Console"** or **"SQL Editor"** tab
2. This gives you direct SQL access to your database

#### **Step 3: Run Migration SQL**
```sql
-- Make uploaded_by nullable
ALTER TABLE resumes ALTER COLUMN uploaded_by DROP NOT NULL;

-- Verify the change
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'resumes' AND column_name = 'uploaded_by';
```

**Expected Output:**
```
column_name  | is_nullable
-------------+-------------
uploaded_by  | YES
```

#### **Step 4: Restart Application**
1. Go back to your application in Dokploy
2. Click **"Restart"** or **"Redeploy"**
3. Wait for application to come back online

---

### **Option 2: Using psql CLI via Dokploy Terminal**

#### **Step 1: Access Container Terminal**
1. In Dokploy dashboard, go to your application
2. Find **"Terminal"** or **"Shell"** option
3. This opens a terminal inside your container

#### **Step 2: Connect to PostgreSQL**
```bash
# Get database credentials from environment
echo $DATABASE_URL

# Connect using psql
psql $DATABASE_URL

# Or connect manually
psql -h <host> -U <user> -d <database>
```

#### **Step 3: Run Migration**
```sql
-- Make uploaded_by nullable
ALTER TABLE resumes ALTER COLUMN uploaded_by DROP NOT NULL;

-- Verify
\d resumes

-- Exit
\q
```

#### **Step 4: Restart Application**
```bash
# Exit terminal and restart app from Dokploy dashboard
```

---

### **Option 3: Using External PostgreSQL Client**

#### **Step 1: Get Database Connection Details**
From Dokploy dashboard:
- **Host:** Your database host (e.g., `db.dokploy.com`)
- **Port:** Usually `5432`
- **Database:** Your database name
- **Username:** Your database user
- **Password:** Your database password

#### **Step 2: Connect Using Client**

**Using pgAdmin:**
1. Open pgAdmin
2. Add new server
3. Enter connection details
4. Connect

**Using DBeaver:**
1. Open DBeaver
2. New Database Connection → PostgreSQL
3. Enter connection details
4. Test connection

**Using psql (Local):**
```bash
psql -h <host> -p 5432 -U <user> -d <database>
```

#### **Step 3: Run Migration SQL**
```sql
ALTER TABLE resumes ALTER COLUMN uploaded_by DROP NOT NULL;
```

#### **Step 4: Restart Application**
Go to Dokploy dashboard and restart your app.

---

### **Option 4: Using Migration Script via SSH**

#### **Step 1: SSH into Dokploy Server**
```bash
ssh user@your-dokploy-server.com
```

#### **Step 2: Navigate to Application Directory**
```bash
cd /path/to/your/app
```

#### **Step 3: Create Migration File**
```bash
cat > migrate_uploaded_by.sql << 'EOF'
-- Migration: Make uploaded_by nullable
-- Date: 2025-10-16
-- Reason: Vetting uploads don't have user context

ALTER TABLE resumes ALTER COLUMN uploaded_by DROP NOT NULL;

-- Verify
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'resumes' AND column_name = 'uploaded_by';
EOF
```

#### **Step 4: Run Migration**
```bash
# Using psql
psql $DATABASE_URL -f migrate_uploaded_by.sql

# Or with explicit connection
psql -h <host> -U <user> -d <database> -f migrate_uploaded_by.sql
```

#### **Step 5: Restart Application**
```bash
# Using Docker (if applicable)
docker restart <container_name>

# Or via Dokploy dashboard
```

---

## 🔒 Safety Precautions

### **Before Running Migration:**

1. **Backup Database**
   ```bash
   # Using pg_dump
   pg_dump $DATABASE_URL > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql
   
   # Or via Dokploy dashboard (if available)
   # Look for "Backup" or "Export" option
   ```

2. **Test on Staging First** (if available)
   - Run migration on staging environment
   - Test resume uploads
   - Verify no errors

3. **Schedule Maintenance Window**
   - Notify users of brief downtime
   - Run during low-traffic period
   - Have rollback plan ready

---

## ✅ Verification Steps

### **After Running Migration:**

1. **Check Column Constraint**
   ```sql
   SELECT column_name, is_nullable, data_type
   FROM information_schema.columns 
   WHERE table_name = 'resumes' AND column_name = 'uploaded_by';
   ```
   
   **Expected:**
   ```
   column_name  | is_nullable | data_type
   -------------+-------------+-----------
   uploaded_by  | YES         | character varying
   ```

2. **Test Resume Upload**
   - Go to vetting page
   - Upload a test resume
   - Verify it uploads successfully
   - Check database for new record

3. **Check Application Logs**
   ```bash
   # In Dokploy dashboard, check logs
   # Look for any errors related to resumes
   ```

4. **Test Bulk Upload**
   - Upload 5-10 resumes
   - Verify all upload successfully
   - Check "Upload Approved to Database" works

---

## 🔄 Rollback Plan

### **If Something Goes Wrong:**

1. **Restore from Backup**
   ```bash
   # Stop application
   # Restore database
   psql $DATABASE_URL < backup_before_migration_YYYYMMDD_HHMMSS.sql
   
   # Restart application
   ```

2. **Revert Migration** (if backup not available)
   ```sql
   -- This will fail if NULL values exist
   ALTER TABLE resumes ALTER COLUMN uploaded_by SET NOT NULL;
   ```

3. **Contact Support**
   - If issues persist, contact Dokploy support
   - Provide error logs and migration details

---

## 📊 Expected Impact

### **Before Migration:**
- ❌ Vetting uploads fail with NOT NULL error
- ❌ 12 resumes failed to upload
- ❌ Skills binding errors

### **After Migration:**
- ✅ Vetting uploads work without user context
- ✅ All resumes upload successfully
- ✅ Skills properly stored in database
- ✅ No breaking changes to existing functionality

---

## 🎯 Post-Migration Checklist

- [ ] Migration SQL executed successfully
- [ ] Column constraint verified (is_nullable = YES)
- [ ] Application restarted
- [ ] Test resume upload successful
- [ ] Bulk upload tested (5+ resumes)
- [ ] No errors in application logs
- [ ] Existing resumes still accessible
- [ ] Database backup created
- [ ] Migration documented in changelog

---

## 📝 Dokploy-Specific Tips

### **Finding Database Console:**
- Look for **"Database"** tab in your app
- Or **"Services"** → **"PostgreSQL"** → **"Console"**
- Or **"Addons"** → **"Database"** → **"Manage"**

### **Common Dokploy Paths:**
```bash
# Application directory
/app

# Database connection string (environment variable)
$DATABASE_URL

# Logs
/var/log/app.log
```

### **Dokploy Environment Variables:**
```bash
# View all environment variables
env | grep DATABASE

# Common variables
DATABASE_URL=postgresql://user:pass@host:5432/dbname
POSTGRES_HOST=db.dokploy.com
POSTGRES_PORT=5432
POSTGRES_DB=hr_recruitment
POSTGRES_USER=admin
POSTGRES_PASSWORD=xxxxx
```

---

## 🆘 Troubleshooting

### **Issue: Can't find database console**
**Solution:** 
- Check Dokploy documentation for your version
- Try accessing via terminal/shell
- Use external client (pgAdmin, DBeaver)

### **Issue: Permission denied**
**Solution:**
```sql
-- Grant permissions if needed
GRANT ALL PRIVILEGES ON TABLE resumes TO your_user;
```

### **Issue: Migration takes too long**
**Solution:**
- This migration should be instant (no data changes)
- If stuck, check for locks: `SELECT * FROM pg_locks WHERE relation = 'resumes'::regclass;`

### **Issue: Application still shows errors**
**Solution:**
- Ensure application restarted after migration
- Clear application cache if applicable
- Check if using correct database connection

---

## 📞 Support

### **If You Need Help:**

1. **Check Dokploy Documentation:**
   - https://docs.dokploy.com/

2. **Dokploy Community:**
   - Discord, Forum, or Support channels

3. **Database Migration Support:**
   - Provide error logs
   - Share migration SQL used
   - Include database version

---

## ✅ Success Confirmation

**You'll know migration succeeded when:**
1. ✅ SQL command returns: `ALTER TABLE`
2. ✅ Verification query shows `is_nullable = YES`
3. ✅ Test resume uploads without errors
4. ✅ Application logs show no database errors
5. ✅ Bulk upload completes successfully

---

**Next Steps After Migration:**
1. Test thoroughly with real resumes
2. Monitor application logs for 24 hours
3. Merge `feature/llm-extraction` to `mvp-1` branch
4. Deploy to production
5. Update documentation

---

**Migration File Location:** `migrations/fix_uploaded_by_nullable.sql`  
**Estimated Downtime:** < 1 minute  
**Risk Level:** LOW (simple column constraint change)  
**Reversible:** YES (if no NULL values inserted)
