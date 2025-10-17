# Production Deployment Guide

## 🚨 SECURITY NOTICE
**DO NOT commit API keys, passwords, or sensitive data to this repository!**

---

## Prerequisites

1. **PostgreSQL Database** - Running and accessible
2. **Redis** - For caching and background jobs
3. **Gemini API Key** - Get from https://makersuite.google.com/app/apikey
4. **Chrome/Chromium** - For LinkedIn verification

---

## Environment Variables

Set these in your deployment platform (Dokploy, Heroku, etc.):

```bash
# AI/LLM Settings (REQUIRED)
GEMINI_API_KEY=<your-api-key-here>
GEMINI_MODEL=gemini-2.5-flash-lite
DEFAULT_LLM_PROVIDER=gemini

# Database (Set by platform)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Redis (Set by platform)
REDIS_URL=redis://host:6379/0

# Application
DEBUG=False
HOST=0.0.0.0
PORT=8000
```

---

## Database Migrations

Run PostgreSQL migrations after deployment:

```bash
# Connect to your app container
docker exec -it <container-name> bash

# Run migrations
psql -h <postgres-host> -U <username> -d <database> -f /app/migrations/postgres_phase2_migrations.sql

# Restart app
exit
docker restart <container-name>
```

---

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p uploads/resumes temp/vetting_sessions logs

# Set permissions
chmod -R 777 uploads temp logs
```

---

## Verification

After deployment, check:

1. **Health endpoint**: `GET /api/health`
2. **Dashboard loads**: Visit `/dashboard`
3. **Upload resume**: Test vetting flow
4. **Check logs**: No errors

---

## Troubleshooting

### Issue: "Google Gemini not available"
**Fix**: Install package and set API key
```bash
pip install google-generativeai
# Set GEMINI_API_KEY in environment
```

### Issue: "column does not exist"
**Fix**: Run database migrations
```bash
psql -f /app/migrations/postgres_phase2_migrations.sql
```

### Issue: Dashboard stuck loading
**Fix**: Check database connection and migrations

---

## Security Best Practices

1. ✅ Never commit `.env` files
2. ✅ Use environment variables for secrets
3. ✅ Rotate API keys regularly
4. ✅ Enable HTTPS in production
5. ✅ Set up database backups
6. ✅ Monitor logs for errors

---

For detailed setup, contact the development team.
