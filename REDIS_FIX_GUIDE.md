# Redis Connection Fix Guide

## Issue
Application is trying to connect to Redis at `localhost:6379`, but in Docker, Redis is running in a separate container and needs to be accessed via the service name.

**Error:**
```
Error 111 connecting to localhost:6379. Connection refused.
```

---

## Solution

### Option 1: Update Environment Variables (Recommended)

**In Dokploy Dashboard:**

1. Go to your AI HR Assistant application
2. Click on "Environment Variables"
3. Add/Update these variables:

```bash
# Redis Configuration
REDIS_URL=redis://ai-hr-assistant-hrredis-sf2gzi:6379/0
CELERY_BROKER_URL=redis://ai-hr-assistant-hrredis-sf2gzi:6379/0
CELERY_RESULT_BACKEND=redis://ai-hr-assistant-hrredis-sf2gzi:6379/0
```

**Note:** Replace `ai-hr-assistant-hrredis-sf2gzi` with your actual Redis service name if different.

4. Click "Save"
5. Redeploy the application

---

### Option 2: Use Docker Network Name

If you're using Docker Compose, the service name should match what's in your `docker-compose.yml`:

```bash
# If your Redis service is named "redis" in docker-compose.yml
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

### Option 3: Find Redis Service Name

**Find your Redis container name:**
```bash
docker ps | grep redis
```

Output will show something like:
```
1f8d787f89d2   redis:7   ...   ai-hr-assistant-hrredis-sf2gzi
```

Use the last part (service name) in your Redis URL.

---

## Verification

**After updating environment variables and redeploying:**

1. **Check logs:**
```bash
docker logs <app-container-id> -f --tail 50
```

Should NOT see:
- ❌ `Error 111 connecting to localhost:6379`
- ❌ `Connection to Redis lost`

Should see:
- ✅ `Triggered background processing for resume`

2. **Test upload:**
- Go to `/vet-resumes`
- Upload a resume
- Approve and upload
- Check logs for successful background task

---

## Current Status (Temporary Fix)

✅ **Code Updated:** Application now handles Redis connection failures gracefully

**What this means:**
- Resume uploads will **succeed** even if Redis is unavailable
- Background processing will be **skipped** (not critical for MVP)
- No more error messages shown to users
- Logs will show warnings but won't crash

**What you lose (temporarily):**
- Background resume processing tasks
- Async job matching updates
- Email notifications (if configured)

**What still works:**
- ✅ Resume vetting and scoring
- ✅ Candidate creation
- ✅ Database storage
- ✅ All UI features
- ✅ Search and filtering

---

## Recommended Action

**For Production:**
1. Update environment variables with correct Redis URL
2. Redeploy application
3. Verify Redis connection in logs
4. Background tasks will resume automatically

**For MVP Demo:**
- Current fix is sufficient
- All core features work
- Background processing is optional

---

## Docker Compose Example

If you're using docker-compose, ensure services can communicate:

```yaml
version: '3.8'

services:
  app:
    image: ai-hr-assistant:latest
    environment:
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
    networks:
      - app-network

  redis:
    image: redis:7
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

---

## Quick Fix Commands

**Check Redis connectivity from app container:**
```bash
# Enter app container
docker exec -it <app-container-id> sh

# Try to ping Redis (if redis-cli is available)
redis-cli -h ai-hr-assistant-hrredis-sf2gzi ping

# Or use telnet
telnet ai-hr-assistant-hrredis-sf2gzi 6379

# Exit
exit
```

**Check Redis container logs:**
```bash
docker logs 1f8d787f89d2 -f --tail 50
```

---

## Summary

**Problem:** App trying to connect to `localhost:6379` but Redis is in separate container

**Immediate Fix:** ✅ Code updated to handle Redis failures gracefully

**Permanent Fix:** Update environment variables with correct Redis service name

**Impact:** 
- ✅ Uploads work now
- ⚠️ Background tasks disabled until Redis is properly configured
- ✅ All core features functional

---

**For your demo, the current fix is sufficient. Update Redis URL later for full functionality!** 🚀
