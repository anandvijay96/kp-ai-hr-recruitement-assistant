# UV Command Reference - Quick Guide

## 🚀 Essential Commands

### Setup & Installation
```bash
# Sync all dependencies from pyproject.toml
uv sync

# Sync and update all dependencies to latest versions
uv sync --upgrade

# Install a specific package
uv add package-name

# Install a dev dependency
uv add --dev package-name

# Remove a package
uv remove package-name
```

### Running the Application
```bash
# Run the FastAPI application
uv run uvicorn main:app --reload

# Run on a different port
uv run uvicorn main:app --reload --port 8001

# Run in production mode (no reload)
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_password_service.py

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=services --cov=api

# Run specific test function
uv run pytest tests/test_password_service.py::test_hash_password -v
```

### Database Operations
```bash
# View database (SQLite)
sqlite3 hr_recruitment.db

# Inside sqlite3:
.tables                    # List all tables
.schema users             # Show users table schema
SELECT * FROM users;      # View all users
.quit                     # Exit
```

### Development Workflow
```bash
# 1. Sync dependencies (after pulling changes)
uv sync

# 2. Run application
uv run uvicorn main:app --reload

# 3. Run tests before committing
uv run pytest

# 4. Format code (if black is installed)
uv run black .

# 5. Lint code (if ruff is installed)
uv run ruff check .
```

## 🧪 Testing the Authentication Feature

### Test Registration
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "mobile": "1234567890",
    "password": "TestPass123!",
    "confirm_password": "TestPass123!"
  }'
```

### Test Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "remember_me": false
  }'
```

### Test Protected Endpoint
```bash
# Replace YOUR_TOKEN with actual access token from login
curl -X GET "http://localhost:8000/api/auth/profile" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔧 Troubleshooting Commands

### Check UV Version
```bash
uv --version
```

### Check Python Version
```bash
python --version
# Should be >= 3.10
```

### List Installed Packages
```bash
uv pip list
```

### Check Virtual Environment
```bash
# Show virtual environment location
uv venv --show

# Activate virtual environment manually
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Clean and Reinstall
```bash
# Remove virtual environment
rm -rf .venv

# Recreate and sync
uv sync
```

### View Application Logs
```bash
# Run with more verbose logging
uv run uvicorn main:app --reload --log-level debug
```

## 📦 Dependency Management

### View Dependency Tree
```bash
uv pip tree
```

### Check for Outdated Packages
```bash
uv pip list --outdated
```

### Export Requirements
```bash
# Export to requirements.txt (for Docker, etc.)
uv pip compile pyproject.toml -o requirements.txt
```

### Lock Dependencies
```bash
# Create/update uv.lock file
uv lock
```

## 🐳 Docker Commands (if using Docker)

### Build Docker Image
```bash
docker build -t hr-recruitment-app .
```

### Run Docker Container
```bash
docker run -p 8000:8000 hr-recruitment-app
```

### Run with Environment Variables
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite+aiosqlite:///./hr_recruitment.db \
  -e JWT_SECRET_KEY=your-secret-key \
  hr-recruitment-app
```

## 🔍 Debugging Commands

### Interactive Python Shell
```bash
# Start Python shell with project context
uv run python

# Then import and test modules
>>> from services.password_service import PasswordService
>>> ps = PasswordService()
>>> ps.hash_password("test123")
```

### Check Database Content
```bash
# Quick check of users table
sqlite3 hr_recruitment.db "SELECT id, email, role, is_active, email_verified FROM users;"

# Check recent activity
sqlite3 hr_recruitment.db "SELECT action_type, status, timestamp FROM user_activity_log ORDER BY timestamp DESC LIMIT 5;"
```

### Test Email Service
```bash
# Run Python script to test email
uv run python -c "
from services.email_service import EmailService
import asyncio

async def test():
    email_service = EmailService()
    result = await email_service.send_verification_email(
        'test@example.com',
        'Test User',
        'test-token-123'
    )
    print(f'Email sent: {result}')

asyncio.run(test())
"
```

## 📊 Performance Testing

### Simple Load Test
```bash
# Install apache bench if needed
# Then test login endpoint
ab -n 100 -c 10 -p login.json -T application/json \
  http://localhost:8000/api/auth/login
```

### Monitor Application
```bash
# Run with reload and watch for changes
uv run uvicorn main:app --reload --log-level info
```

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync` |
| Run app | `uv run uvicorn main:app --reload` |
| Run tests | `uv run pytest` |
| Add package | `uv add package-name` |
| Remove package | `uv remove package-name` |
| View database | `sqlite3 hr_recruitment.db` |
| API docs | http://localhost:8000/docs |
| Login page | http://localhost:8000/login |
| Register page | http://localhost:8000/register |

## 🆘 Common Issues

### Issue: "uv: command not found"
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Issue: "Module not found"
```bash
# Ensure dependencies are synced
uv sync

# Or use uv run
uv run uvicorn main:app --reload
```

### Issue: "Port already in use"
```bash
# Use different port
uv run uvicorn main:app --reload --port 8001

# Or kill process using port 8000
# Linux/Mac: lsof -ti:8000 | xargs kill -9
# Windows: netstat -ano | findstr :8000
```

### Issue: "Database locked"
```bash
# Stop application
# Delete database
rm hr_recruitment.db
# Restart application
uv run uvicorn main:app --reload
```

---

**For detailed setup instructions, see `UV_SETUP_GUIDE.md`**
