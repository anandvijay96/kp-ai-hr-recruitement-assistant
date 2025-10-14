# Quick Fix Commands for Dokploy

## Step 1: Pull Latest Code

**In Dokploy Dashboard:**
1. Go to your AI HR Assistant application
2. Click "Redeploy" or "Pull & Restart"
3. Wait for deployment to complete

**OR via SSH:**
```bash
# SSH to Dokploy server
ssh your-dokploy-server

# Navigate to app directory (adjust path as needed)
cd /path/to/ai-hr-assistant

# Pull latest code
git pull origin mvp-1

# Restart container
docker-compose restart
```

---

## Step 2: Run Migration Script

**Option A: Via Docker Exec (Recommended)**
```bash
# Find your container ID
docker ps | grep ai-hr-assistant

# Run migration inside container
docker exec -it <container-id> python scripts/add_professional_summary_column.py
```

**Option B: Direct PostgreSQL**
```bash
# Find PostgreSQL container
docker ps | grep postgres

# Connect to database
docker exec -it <postgres-container-id> psql -U postgres -d ai_hr_db

# Run SQL
ALTER TABLE candidates ADD COLUMN professional_summary TEXT;

# Exit
\q
```

---

## Step 3: Verify Fix

**Test the vetting upload:**
1. Go to your production URL: `https://your-domain.com/vet-resumes`
2. Upload a test resume
3. Click "Approve"
4. Click "Upload to Database"
5. Should see "Upload Successful!" ✅

**Check logs:**
```bash
# View live logs
docker logs <container-id> -f --tail 100

# Should NOT see: "professional_summary does not exist"
# Should see: "Created new candidate: [Name]"
```

---

## Quick Troubleshooting

**If migration script fails:**
```bash
# Check Python is available in container
docker exec -it <container-id> python --version

# Check script exists
docker exec -it <container-id> ls -la scripts/

# Run with full path
docker exec -it <container-id> python /app/scripts/add_professional_summary_column.py
```

**If SQL fails:**
```bash
# Check if column already exists
docker exec -it <postgres-container-id> psql -U postgres -d ai_hr_db -c "\d candidates"

# If column exists, you're done!
```

---

## What Changed in Latest Push

✅ **Backward-compatible code:** App won't crash if column is missing  
✅ **Migration script:** Safe script to add the column  
✅ **Detailed guide:** Full documentation in PRODUCTION_FIX_GUIDE.md  

**The app will now:**
- Work even if column is missing (logs warning)
- Create candidates without professional_summary if needed
- Continue functioning until migration is run

---

## Timeline

**Immediate (Already Done):**
- ✅ Code pushed to GitHub
- ✅ App won't crash on production

**Next (You need to do):**
1. Pull latest code on Dokploy (5 min)
2. Run migration script (2 min)
3. Test vetting upload (2 min)

**Total time:** ~10 minutes

---

## Contact Points

**If you need help:**
- Check `PRODUCTION_FIX_GUIDE.md` for detailed steps
- View logs: `docker logs <container-id> -f`
- Database UI: Use Dokploy's built-in database management

---

## Status

✅ **Code:** Pushed to mvp-1 branch  
✅ **Local:** Working perfectly  
⏳ **Production:** Needs migration script run  

**Once migration is run:** ✅ Production will be fully fixed!
