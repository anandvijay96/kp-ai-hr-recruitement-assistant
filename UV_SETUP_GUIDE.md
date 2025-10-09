# UV Setup Guide - Authentication Feature

## 🚀 Quick Start with UV

### Step 1: Sync Dependencies with UV
```bash
# Sync all dependencies from pyproject.toml
uv sync

# This will install all authentication dependencies including:
# - PyJWT (JWT tokens)
# - bcrypt (password hashing)
# - email-validator (email validation)
# - passlib (password utilities)
# - sqlalchemy[asyncio] (async database)
# - aiosqlite (SQLite async driver)
# - asyncpg (PostgreSQL async driver)
# - sendgrid (email service)
```

### Step 2: Run the Application with UV
```bash
# Run using uv
uv run uvicorn main:app --reload

# Or activate the virtual environment first
source .venv/bin/activate  # On Linux/Mac
# OR
.venv\Scripts\activate     # On Windows

# Then run normally
uvicorn main:app --reload
```

### Step 3: Access the Application
- **Main App**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Login Page**: http://localhost:8000/login
- **Register Page**: http://localhost:8000/register

## 📦 Dependencies Added to pyproject.toml

The following authentication dependencies have been added to `pyproject.toml`:

```toml
"PyJWT>=2.8.0",              # JWT token generation and validation
"bcrypt>=4.1.1",             # Password hashing
"email-validator>=2.1.0",    # Email validation
"passlib>=1.7.4",            # Password utilities
"sqlalchemy[asyncio]>=2.0.23", # Async ORM
"aiosqlite>=0.19.0",         # SQLite async driver
"asyncpg>=0.29.0",           # PostgreSQL async driver
"sendgrid>=6.11.0",          # Email service
```

## 🧪 Run Tests with UV

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_password_service.py -v

# Run with coverage
uv run pytest --cov=services --cov-report=html

# Run tests in watch mode (if pytest-watch is installed)
uv run ptw
```

## 🔧 Configuration

### Create .env File
```bash
# Create .env file for local configuration
cat > .env << EOF
# Database (SQLite for dev, PostgreSQL for production)
DATABASE_URL=sqlite+aiosqlite:///./hr_recruitment.db

# Redis (optional, falls back to in-memory)
REDIS_URL=redis://localhost:6379/0

# JWT Secret (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=dev-secret-key-change-in-production

# Email (optional for dev, required for production)
SENDGRID_API_KEY=
SENDER_EMAIL=noreply@hrrecruitment.com
FRONTEND_URL=http://localhost:8000

# Security Settings
PASSWORD_MIN_LENGTH=8
ACCOUNT_LOCKOUT_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=15
PASSWORD_HISTORY_COUNT=5
EOF
```

## 🎯 Test the Authentication Flow

### 1. Register a New User via API
```bash
# Using curl
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

### 2. Check Logs for Verification Token
Since SendGrid is not configured in dev mode, check the console output:
```
[DEV MODE] Email to test@example.com: Verify Your Email - HR Recruitment System
```

### 3. Verify Email
```bash
# Copy the token from logs and verify
curl -X GET "http://localhost:8000/api/auth/verify-email?token=YOUR_TOKEN_HERE"
```

### 4. Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "remember_me": false
  }'
```

### 5. Use the Access Token
```bash
# Save the access_token from login response
export ACCESS_TOKEN="your-access-token-here"

# Get profile
curl -X GET "http://localhost:8000/api/auth/profile" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Update profile
curl -X PUT "http://localhost:8000/api/auth/profile" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Updated Name",
    "mobile": "9876543210"
  }'

# Change password
curl -X POST "http://localhost:8000/api/auth/change-password" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "TestPass123!",
    "new_password": "NewPass456!",
    "confirm_password": "NewPass456!"
  }'
```

## 🌐 Using the Web Interface

### Register via Browser
1. Navigate to http://localhost:8000/register
2. Fill in the registration form
3. Submit and check console logs for verification token
4. Verify email via API or browser

### Login via Browser
1. Navigate to http://localhost:8000/login
2. Enter credentials
3. Login redirects to main page
4. Access token is stored in localStorage

## 🐛 Troubleshooting

### Issue: UV sync fails
```bash
# Update uv to latest version
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Then sync again
uv sync
```

### Issue: Module not found errors
```bash
# Ensure you're using uv run or have activated the venv
uv run uvicorn main:app --reload

# Or activate venv first
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Issue: Database errors
```bash
# Delete and recreate database
rm hr_recruitment.db
uv run uvicorn main:app --reload
```

### Issue: Redis connection failed
**Solution**: The app works without Redis using in-memory fallback. No action needed for development.

### Issue: Port already in use
```bash
# Use a different port
uv run uvicorn main:app --reload --port 8001
```

## 📊 Database Management

### View Database with SQLite
```bash
# Install sqlite3 if needed
# Then open database
sqlite3 hr_recruitment.db

# List all tables
.tables

# View users
SELECT id, email, full_name, role, is_active, email_verified FROM users;

# View activity log
SELECT action_type, status, timestamp FROM user_activity_log ORDER BY timestamp DESC LIMIT 10;

# Exit
.quit
```

### Using PostgreSQL (Production)
```bash
# Update .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/hr_recruitment

# Create database
createdb hr_recruitment

# Run application (tables will be created automatically)
uv run uvicorn main:app --reload
```

## 🔐 Security Testing

### Test Account Lockout
```bash
# Try logging in with wrong password 5 times
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "WrongPassword",
      "remember_me": false
    }'
  echo "\nAttempt $i"
done

# 6th attempt should return account locked error
```

### Test Password Strength
```bash
# Try registering with weak password (should fail)
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test2@example.com",
    "mobile": "1234567890",
    "password": "weak",
    "confirm_password": "weak"
  }'
```

## 📈 Performance Testing

### Load Testing with Apache Bench
```bash
# Install apache bench
# Ubuntu: sudo apt-get install apache2-utils
# Mac: brew install apache-bench

# Test login endpoint
ab -n 100 -c 10 -p login.json -T application/json \
  http://localhost:8000/api/auth/login

# Where login.json contains:
# {"email":"test@example.com","password":"TestPass123!","remember_me":false}
```

## 🚀 Production Deployment with UV

### Build for Production
```bash
# Lock dependencies
uv lock

# Export requirements.txt (if needed for Docker)
uv pip compile pyproject.toml -o requirements.txt

# Build wheel
uv build
```

### Docker with UV
```dockerfile
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
WORKDIR /app
COPY . .

# Install dependencies
RUN uv sync --frozen

# Run application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📝 Development Workflow

### Daily Development
```bash
# 1. Pull latest changes
git pull

# 2. Sync dependencies (if pyproject.toml changed)
uv sync

# 3. Run application
uv run uvicorn main:app --reload

# 4. Run tests before committing
uv run pytest

# 5. Commit changes
git add .
git commit -m "Your message"
git push
```

### Adding New Dependencies
```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Update all dependencies
uv sync --upgrade
```

## 🎓 Learning Resources

- **UV Documentation**: https://docs.astral.sh/uv/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **JWT Best Practices**: https://jwt.io/introduction

## ✅ Verification Checklist

- [ ] UV installed and updated
- [ ] Dependencies synced with `uv sync`
- [ ] Application runs with `uv run uvicorn main:app --reload`
- [ ] Can access http://localhost:8000/docs
- [ ] Registration works via API or web interface
- [ ] Email verification token appears in logs
- [ ] Login works after email verification
- [ ] Protected endpoints require authentication
- [ ] Tests pass with `uv run pytest`

## 🆘 Getting Help

If you encounter issues:

1. **Check UV version**: `uv --version` (should be >= 0.1.0)
2. **Check Python version**: `python --version` (should be >= 3.10)
3. **Check logs**: Application logs contain detailed error information
4. **Check database**: `sqlite3 hr_recruitment.db` and inspect tables
5. **Review documentation**: 
   - `docs/AUTH_IMPLEMENTATION.md`
   - `QUICKSTART_AUTH.md`
   - API docs at http://localhost:8000/docs

---

**Happy Development with UV! 🚀**

For detailed implementation information, see `docs/AUTH_IMPLEMENTATION.md`
