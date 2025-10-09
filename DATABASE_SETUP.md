# Database Setup Guide

## Issue: "no such table: resumes" Error

This error occurs when the database tables haven't been created yet.

## Solution: Initialize the Database

Run the database initialization script:

```bash
python init_db.py
```

This will create all required tables:
- ✅ candidates
- ✅ resumes
- ✅ education
- ✅ work_experience
- ✅ skills
- ✅ candidate_skills

## Database Location

The SQLite database file is created at: `./hr_assistant.db`

## When to Run This

Run `python init_db.py` when:
1. **First time setup** - Before starting the application
2. **After cloning the repo** - Database file is not committed to git
3. **After database corruption** - Delete `hr_assistant.db` and re-run
4. **After model changes** - If you modify database models

## Alembic Migrations (Advanced)

For production or when making schema changes, use Alembic:

```bash
# Create a new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

**Note:** The existing migration file `add_fulltext_search_support.py` is for PostgreSQL. 
For SQLite, the `init_db.py` script creates all tables directly.

## Troubleshooting

### Error: "no such table: resumes"
**Solution:** Run `python init_db.py`

### Error: "database is locked"
**Solution:** 
1. Stop all running instances of the application
2. Close any database browser tools
3. Restart the application

### Error: "table already exists"
**Solution:**
1. Delete `hr_assistant.db`
2. Run `python init_db.py` again

## Complete Startup Sequence

```bash
# 1. Initialize database (first time only)
python init_db.py

# 2. Start Redis (for Celery background tasks)
redis-server

# 3. Start Celery worker (in a new terminal)
celery -A core.celery_app worker --loglevel=info

# 4. Start the API server
uvicorn main:app --reload --port 8000
```

## Verification

After initialization, you can verify the tables were created:

```bash
# Using sqlite3 command line
sqlite3 hr_assistant.db ".tables"

# Expected output:
# candidates  education  resumes  skills  work_experience  candidate_skills
```
