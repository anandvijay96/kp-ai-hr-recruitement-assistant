# Simple Dokploy Deployment Guide

## 🚀 Quick Deployment Steps

### Step 1: SSH to Server
```bash
ssh ubuntu@158.69.219.206
```

### Step 2: Navigate to App Directory
```bash
# Find your app directory (Dokploy usually deploys to /app or similar)
cd /app/ai-hr-assistant
# OR
cd ~/ai-hr-assistant
# OR check with Dokploy
docker ps  # Find your container
docker exec -it <container-name> bash
```

### Step 3: Backup Database (IMPORTANT!)
```bash
# Inside the app directory, find hr_recruitment.db
# Create backup with timestamp
cp hr_recruitment.db hr_recruitment.db.backup_$(date +%Y%m%d_%H%M%S)

# Verify backup was created
ls -lh hr_recruitment.db*
```

### Step 4: Run Migrations
```bash
# Run the consolidated migration script
python migrations/run_all_phase2_migrations.py

# It will ask for confirmation, type: yes
```

### Step 5: Restart Application
```bash
# If using Docker (Dokploy default)
docker restart <container-name>

# OR if using systemd
sudo systemctl restart ai-hr-assistant

# OR if using PM2
pm2 restart ai-hr-assistant
```

### Step 6: Verify Deployment
Visit: http://158.69.219.206/
- Upload a test resume
- Check work experience shows bullet points
- Check LinkedIn suggestions appear (if found)
- Test edit feature

---

## 🔍 Finding Your Database

### Option 1: Docker Volume
```bash
# List volumes
docker volume ls

# Find your app's volume
docker volume inspect <volume-name>

# Database is usually at:
# /var/lib/docker/volumes/<volume-name>/_data/hr_recruitment.db
```

### Option 2: Inside Container
```bash
# Enter container
docker exec -it <container-name> bash

# Find database
find / -name "hr_recruitment.db" 2>/dev/null

# Backup from inside container
cp hr_recruitment.db hr_recruitment.db.backup_$(date +%Y%m%d_%H%M%S)

# Run migrations from inside container
python migrations/run_all_phase2_migrations.py
```

### Option 3: Dokploy Dashboard
1. Go to Dokploy dashboard
2. Find your app
3. Click "Terminal" or "Console"
4. Run commands directly

---

## 🆘 If Something Goes Wrong

### Restore Database
```bash
# List backups
ls -lh hr_recruitment.db.backup_*

# Restore from backup
cp hr_recruitment.db.backup_YYYYMMDD_HHMMSS hr_recruitment.db

# Restart app
docker restart <container-name>
```

---

## ✅ What the Migrations Do

1. **Add responsibilities column** - For work experience bullet points
2. **Add linkedin_suggestions column** - For LinkedIn profile selection

Both are:
- ✅ Safe (no data loss)
- ✅ Additive only
- ✅ Can run multiple times

---

## 📞 Quick Commands Reference

```bash
# SSH
ssh ubuntu@158.69.219.206

# Find container
docker ps | grep hr

# Enter container
docker exec -it <container-id> bash

# Backup DB
cp hr_recruitment.db hr_recruitment.db.backup_$(date +%Y%m%d_%H%M%S)

# Run migrations
python migrations/run_all_phase2_migrations.py

# Restart
docker restart <container-id>

# Check logs
docker logs -f <container-id>
```
