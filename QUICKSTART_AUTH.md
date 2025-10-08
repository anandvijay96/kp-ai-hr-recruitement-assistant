# Quick Start Guide - Authentication Feature

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

**Using UV (Recommended):**
```bash
# Sync dependencies from pyproject.toml
uv sync
```

**Using pip (Alternative):**
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application

**Using UV:**
```bash
uv run uvicorn main:app --reload
```

**Using pip:**
```bash
uvicorn main:app --reload
```

### Step 3: Access the Application
- **Main App**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Login Page**: http://localhost:8000/login
- **Register Page**: http://localhost:8000/register

## 📝 Test the Authentication Flow

### 1. Register a New User
1. Go to http://localhost:8000/register
2. Fill in the form:
   - Full Name: `Test User`
   - Email: `test@example.com`
   - Mobile: `1234567890`
   - Password: `TestPass123!`
   - Confirm Password: `TestPass123!`
3. Click "Create Account"

### 2. Verify Email (Development Mode)
Since SendGrid is not configured, check the console logs for the verification token:
```
[DEV MODE] Email to test@example.com: Verify Your Email
```

The verification link will be in the format:
```
http://localhost:8000/verify-email?token=<UUID>
```

Copy the token from logs and visit:
```
http://localhost:8000/api/auth/verify-email?token=<YOUR_TOKEN>
```

### 3. Login
1. Go to http://localhost:8000/login
2. Enter credentials:
   - Email: `test@example.com`
   - Password: `TestPass123!`
3. Click "Login"
4. You'll be redirected to the main page with authentication

### 4. Test API Endpoints

**Get Profile** (requires authentication):
```bash
# First, login and get the access token from the response
curl -X GET "http://localhost:8000/api/auth/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Change Password**:
```bash
curl -X POST "http://localhost:8000/api/auth/change-password" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "TestPass123!",
    "new_password": "NewPass456!",
    "confirm_password": "NewPass456!"
  }'
```

## 🔧 Configuration (Optional)

### Using PostgreSQL Instead of SQLite
Update `.env`:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/hr_recruitment
```

### Using Redis for Token Blacklist
1. Install and start Redis:
```bash
# On Windows (using WSL or Docker)
docker run -d -p 6379:6379 redis

# On Linux/Mac
redis-server
```

2. Update `.env`:
```env
REDIS_URL=redis://localhost:6379/0
```

### Configuring Email (SendGrid)
1. Sign up for SendGrid: https://sendgrid.com
2. Get your API key
3. Update `.env`:
```env
SENDGRID_API_KEY=your-api-key-here
SENDER_EMAIL=noreply@yourcompany.com
```

## 🧪 Run Tests
```bash
# Run password service tests
pytest tests/test_password_service.py -v

# Run all tests
pytest tests/ -v
```

## 📊 Database

The application uses SQLite by default. The database file `hr_recruitment.db` will be created automatically on first run.

**View Database**:
```bash
# Install sqlite3 if not available
sqlite3 hr_recruitment.db

# List tables
.tables

# View users
SELECT * FROM users;

# Exit
.quit
```

## 🔐 Security Features

✅ **Password Security**
- Bcrypt hashing with cost factor 12
- Password complexity requirements enforced
- Password history (last 5 passwords)

✅ **Token Security**
- JWT with 15-minute access tokens
- 7-day refresh tokens
- Token blacklisting on logout

✅ **Account Security**
- Email verification required
- Account lockout after 5 failed attempts
- Activity logging for audit trail

## 🐛 Troubleshooting

### Issue: "Module not found" errors
**Solution**: Make sure all dependencies are installed
```bash
pip install -r requirements.txt
```

### Issue: Database errors
**Solution**: Delete and recreate the database
```bash
rm hr_recruitment.db
uvicorn main:app --reload
```

### Issue: Redis connection failed
**Solution**: The app will work without Redis using in-memory fallback. No action needed for development.

### Issue: Emails not sending
**Solution**: In development mode, emails are logged to console. Check the application logs for verification tokens and reset links.

## 📚 API Endpoints Reference

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | User login | No |
| POST | `/api/auth/logout` | User logout | Yes |
| POST | `/api/auth/refresh` | Refresh access token | Yes |
| POST | `/api/auth/forgot-password` | Request password reset | No |
| POST | `/api/auth/reset-password` | Reset password with token | No |
| GET | `/api/auth/verify-email` | Verify email address | No |
| GET | `/api/auth/profile` | Get user profile | Yes |
| PUT | `/api/auth/profile` | Update user profile | Yes |
| POST | `/api/auth/change-password` | Change password | Yes |

## 🎯 Next Steps

1. **Test all authentication flows**
2. **Configure production settings** (PostgreSQL, Redis, SendGrid)
3. **Add remaining HTML templates** (forgot password, reset password, profile)
4. **Implement role-based access control** for protected routes
5. **Add integration tests** for complete flows
6. **Deploy to production** following the deployment checklist

## 📖 Documentation

- **Full Implementation Guide**: `docs/AUTH_IMPLEMENTATION.md`
- **Technical Specification**: `docs/prd/Feature_1_Technical_Implementation.md`
- **Product Requirements**: `docs/prd/Feature_1_User_Creation_Authentication_PRD.md`
- **API Documentation**: http://localhost:8000/docs (when running)

## 💡 Tips

1. **Use the Swagger UI** at `/docs` to test API endpoints interactively
2. **Check application logs** for detailed error messages and email content
3. **Use a REST client** like Postman or Insomnia for API testing
4. **Keep the access token** from login response for authenticated requests
5. **Test account lockout** by intentionally failing login 5 times

---

**Happy Coding! 🎉**

For issues or questions, refer to the full documentation in `docs/AUTH_IMPLEMENTATION.md`
