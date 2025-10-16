# Production Deployment Checklist

## 🚨 CRITICAL - Must Do Before App Works

### 1. ✅ Environment Variables (Dokploy Dashboard)

**Navigate to:** Dokploy → AI HR Assistant → Environment Variables

**Add these CRITICAL variables:**

```
GEMINI_API_KEY=AIzaSyC6XiQOL1AFhJqQDKH6uavllewDMDk4hsQ
GEMINI_MODEL=gemini-1.5-flash-002
DEFAULT_LLM_PROVIDER=gemini
DEBUG=False
```

**Why Critical:**
- Without `GEMINI_API_KEY`: Resume extraction will fail
- Wrong `GEMINI_MODEL`: Will hit quota limits (2.0-flash-exp is experimental)
- Without `DEFAULT_LLM_PROVIDER`: App won't know which AI to use

---

### 2. ✅ Database Migrations

**Run PostgreSQL migrations:**

```bash
# SSH to server
ssh ubuntu@158.69.219.206

# Enter app container
docker exec -it <app-container> bash

# Run migration
psql -h ai-hr-assistant-hrpostgres-h65kfg -p 5432 -U hr_user -d hr_assistant_db -f /app/migrations/postgres_phase2_migrations.sql
# Password: Hrms@2025
```

**Verify:**
```sql
\c hr_assistant_db
\d candidates
\d work_experience
```

Should show:
- `candidates.is_deleted`
- `candidates.linkedin_suggestions`
- `work_experience.responsibilities`

---

### 3. ✅ Create Required Directories

```bash
# In app container
mkdir -p /app/uploads/resumes
mkdir -p /app/temp/vetting_sessions
mkdir -p /app/results
mkdir -p /app/feedback_submissions
mkdir -p /app/logs

# Set permissions
chmod -R 777 /app/uploads
chmod -R 777 /app/temp
chmod -R 777 /app/logs
```

---

### 4. ✅ Verify Dependencies

```bash
# Check Chrome/Chromium (for LinkedIn verification)
which google-chrome || which chromium

# If missing, install:
apt-get update
apt-get install -y chromium chromium-driver

# Check Python packages
pip list | grep -E "sqlalchemy|asyncpg|fastapi|selenium"
```

---

### 5. ✅ Restart Application

```bash
# Exit container
exit

# Restart app
docker restart <app-container-name>

# Watch logs
docker logs -f <app-container-name>
```

---

## ⚠️ IMPORTANT - Should Do

### 6. Security Settings

**In Dokploy Environment Variables:**

```
SECRET_KEY=<generate-random-32-char-string>
SESSION_COOKIE_SECURE=True
ALLOWED_HOSTS=["158.69.219.206", "yourdomain.com"]
```

**Generate SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

---

### 7. Database Backup

```bash
# Create backup script
docker exec ai-hr-assistant-hrpostgres-h65kfg pg_dump -U hr_user hr_assistant_db > backup_$(date +%Y%m%d).sql

# Set up daily backups (cron)
0 2 * * * docker exec ai-hr-assistant-hrpostgres-h65kfg pg_dump -U hr_user hr_assistant_db > /backups/hr_$(date +\%Y\%m\%d).sql
```

---

### 8. Monitoring & Logging

**Check logs location:**
```bash
docker logs <app-container> --tail 100
```

**Set up log rotation:**
```bash
# In app container
cat > /etc/logrotate.d/hr-assistant << EOF
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
}
EOF
```

---

### 9. Performance Tuning

**Database Connection Pool:**
```env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

**Redis Cache:**
```env
REDIS_URL=redis://hr-redis:6379/0
REDIS_CACHE_TTL=3600
```

---

### 10. SSL/HTTPS Setup

**If using custom domain:**
1. Point domain to 158.69.219.206
2. Set up Nginx reverse proxy
3. Install Let's Encrypt SSL
4. Update CORS settings

---

## 📋 Post-Deployment Verification

### Test Checklist:

- [ ] **Homepage loads** - Visit http://158.69.219.206/
- [ ] **Dashboard loads** - No "Loading..." stuck
- [ ] **Upload resume** - Test vetting flow
- [ ] **View candidate** - Check all data displays
- [ ] **Edit candidate** - Verify data preservation
- [ ] **LinkedIn suggestions** - Check if they appear
- [ ] **Work experience bullets** - Verify display
- [ ] **Phone +91 prefix** - Check formatting
- [ ] **Search works** - Test candidate search
- [ ] **No errors in logs** - Check docker logs

---

## 🔍 Common Issues & Fixes

### Issue 1: Dashboard stuck on "Loading..."
**Cause:** Missing database columns
**Fix:** Run PostgreSQL migrations

### Issue 2: Resume upload fails
**Cause:** Missing GEMINI_API_KEY
**Fix:** Add to Dokploy environment variables

### Issue 3: LinkedIn verification fails
**Cause:** Chrome/Chromium not installed
**Fix:** Install chromium in container

### Issue 4: "500 Internal Server Error"
**Cause:** Check logs for specific error
**Fix:** `docker logs -f <container>`

---

## 🎯 Critical Environment Variables Summary

**Minimum Required:**
```
GEMINI_API_KEY=AIzaSyC6XiQOL1AFhJqQDKH6uavllewDMDk4hsQ
GEMINI_MODEL=gemini-1.5-flash-002
DEFAULT_LLM_PROVIDER=gemini
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
DEBUG=False
```

**Recommended:**
```
SECRET_KEY=<random-string>
LOG_LEVEL=INFO
ENABLE_LINKEDIN_VERIFICATION=True
ENABLE_SOFT_DELETE=True
```

---

## ✅ Deployment Complete When:

1. ✅ All environment variables set
2. ✅ Database migrations run successfully
3. ✅ Directories created with proper permissions
4. ✅ App restarts without errors
5. ✅ Dashboard loads and shows data
6. ✅ Can upload and vet resumes
7. ✅ All features work as expected

---

## 📞 Quick Commands Reference

```bash
# SSH
ssh ubuntu@158.69.219.206

# List containers
docker ps

# Enter app container
docker exec -it <app-container> bash

# Check environment
env | grep -E "GEMINI|DATABASE|REDIS"

# Run migration
psql -h ai-hr-assistant-hrpostgres-h65kfg -U hr_user -d hr_assistant_db -f /app/migrations/postgres_phase2_migrations.sql

# Restart app
docker restart <app-container>

# View logs
docker logs -f <app-container>

# Check database
docker exec -it ai-hr-assistant-hrpostgres-h65kfg psql -U hr_user -d hr_assistant_db
```

---

**Priority Order:**
1. 🔴 Environment Variables (CRITICAL)
2. 🔴 Database Migrations (CRITICAL)
3. 🟡 Directories & Permissions (IMPORTANT)
4. 🟡 Dependencies Verification (IMPORTANT)
5. 🟢 Security & Monitoring (RECOMMENDED)
