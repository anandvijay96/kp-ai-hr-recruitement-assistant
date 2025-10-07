# 🔐 OAuth 2.0 Setup Guide

**Feature:** User-provided Google API keys via OAuth  
**Status:** ✅ IMPLEMENTED - Ready for Setup & Testing  
**Date:** October 7, 2025  

---

## 📋 What's New

Users can now connect their own Google accounts to use their personal API quotas for LinkedIn verification. This means:

- ✅ Each user gets 100 free Google searches/day
- ✅ No shared server quota limits
- ✅ One-click OAuth setup
- ✅ Secure token storage
- ✅ Automatic token refresh

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install New Dependencies

```bash
pip install -r requirements.txt
```

**New packages:**
- `google-auth`
- `google-auth-oauthlib`
- `cryptography`
- `pyjwt`
- `python-jose`

### Step 2: Create Google OAuth App

1. **Go to Google Cloud Console**  
   https://console.cloud.google.com/

2. **Create or Select Project**
   - Click "Select a project" → "New Project"
   - Name: "HR Assistant OAuth"
   - Click "Create"

3. **Enable Custom Search API**
   - APIs & Services → Library
   - Search for "Custom Search API"
   - Click "Enable"

4. **Create OAuth Credentials**
   - APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "HR Assistant"
   
5. **Configure Authorized URLs**
   - Authorized JavaScript origins:
     ```
     http://localhost:8000
     ```
   
   - Authorized redirect URIs:
     ```
     http://localhost:8000/auth/google/callback
     ```
   
   - Click "Create"

6. **Copy Credentials**
   - You'll see Client ID and Client Secret
   - Copy both (you'll need them next)

### Step 3: Configure Environment

Add to your `.env` file:

```bash
# OAuth Settings
GOOGLE_OAUTH_CLIENT_ID=your_client_id_from_step_2
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret_from_step_2
OAUTH_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Security Settings
JWT_SECRET_KEY=your-randomly-generated-secret-key
ENCRYPTION_KEY=your-randomly-generated-encryption-key
```

**Generate Secret Keys:**

```bash
# Generate JWT secret (32 bytes hex)
openssl rand -hex 32

# Generate Encryption Key (Python)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 4: Initialize Database

The database will auto-initialize on startup, but you can also run:

```python
from models.database import init_db
init_db()
```

### Step 5: Restart Application

```bash
uvicorn main:app --reload
```

**Check logs for:**
```
INFO: Database initialized successfully
INFO: Google Search verification enabled for LinkedIn profile checks
```

---

## 🧪 Testing OAuth Flow

### Test 1: Connect Google Account

1. Start application: `uvicorn main:app --reload`
2. Open browser: http://localhost:8000/settings
3. Click "Connect Google Account"
4. Authorize with your Google account
5. Should redirect back with success message

**Expected Result:**
- ✅ Redirected to Google OAuth consent screen
- ✅ After authorization, redirected back to settings
- ✅ Status shows "Connected"
- ✅ Can see API usage stats

### Test 2: Upload Resume with User's API

1. Upload a resume (with or without LinkedIn)
2. System should use your personal Google API quota
3. Check settings page for updated usage stats

**Expected Result:**
- ✅ Resume analyzed successfully
- ✅ LinkedIn verification performed using your API
- ✅ Usage counter incremented

### Test 3: Disconnect Account

1. Go to settings
2. Click "Disconnect Google Account"
3. Confirm disconnection

**Expected Result:**
- ✅ Status shows "Not Connected"
- ✅ System falls back to server API (if configured)

---

## 📸 User Experience

### Settings Page

```
┌─────────────────────────────────────────────┐
│  ⚙️ Settings - Google API Configuration     │
├─────────────────────────────────────────────┤
│                                             │
│  🔍 Google Search API for LinkedIn          │
│  ─────────────────────────────────────────  │
│                                             │
│  Current Status: 🔴 Not Connected           │
│                                             │
│  [🔗 Connect Google Account]                │
│                                             │
│  • One-click setup                          │
│  • 100 free searches per day                │
│  • Your own API quota                       │
│  • Secure OAuth authentication              │
│                                             │
└─────────────────────────────────────────────┘
```

### After Connecting

```
┌─────────────────────────────────────────────┐
│  ⚙️ Settings - Google API Configuration     │
├─────────────────────────────────────────────┤
│                                             │
│  🔍 Google Search API                       │
│  ─────────────────────────────────────────  │
│                                             │
│  Current Status: ✅ Connected               │
│  Account: user@gmail.com                    │
│                                             │
│  📊 Usage Statistics                        │
│  ─────────────────────────────────────────  │
│  • Today: 5 / 100 searches (5%)            │
│  [████░░░░░░░░░░░░░░░░░░░]                │
│  • Remaining: 95 searches                   │
│                                             │
│  [View History] [Disconnect]                │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🔄 OAuth Flow Diagram

```
1. User clicks "Connect Google Account"
   ↓
2. Redirected to Google OAuth consent screen
   ↓
3. User logs in with Google account
   ↓
4. User grants permissions:
   - View email address
   - View basic profile
   ↓
5. Google redirects back with authorization code
   ↓
6. Server exchanges code for OAuth tokens:
   - Access Token (for API calls)
   - Refresh Token (to get new access tokens)
   ↓
7. Tokens encrypted and stored in database
   ↓
8. Success page displayed
   ↓
9. Redirected to settings page
```

---

## 🔐 Security Features

### 1. **Encrypted Token Storage**
```python
# Tokens are encrypted before storing in database
encrypted_token = credential_encryptor.encrypt(access_token)
```

### 2. **JWT Authentication**
```python
# Each user gets a JWT token for session management
token = create_access_token(data={"sub": user.id})
```

### 3. **Automatic Token Refresh**
```python
# Expired OAuth tokens are automatically refreshed
if credentials.oauth_expires_at < datetime.now():
    new_token = refresh_oauth_token(credentials.refresh_token)
```

### 4. **Secure Cookie Handling**
```python
# HTTP-only cookies prevent XSS attacks
response.set_cookie(
    key="access_token",
    httponly=True,
    samesite="lax"
)
```

---

## 📊 Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    hashed_password VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- API Credentials (encrypted)
CREATE TABLE user_api_credentials (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    service_type VARCHAR(50), -- 'google_search'
    
    -- OAuth
    oauth_access_token TEXT, -- encrypted
    oauth_refresh_token TEXT, -- encrypted
    oauth_expires_at TIMESTAMP,
    
    -- Manual API key
    api_key TEXT, -- encrypted
    api_engine_id VARCHAR(255),
    
    -- Usage tracking
    quota_used_today INT DEFAULT 0,
    quota_limit_daily INT DEFAULT 100,
    last_reset_date DATE,
    
    is_active BOOLEAN DEFAULT TRUE
);

-- Usage logs
CREATE TABLE api_usage_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    service_type VARCHAR(50),
    request_count INT DEFAULT 1,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🌐 API Endpoints

### Authentication
```
POST   /auth/register              # Register new user
POST   /auth/login                 # Login with password
GET    /auth/me                    # Get current user info
POST   /auth/logout                # Logout
```

### OAuth
```
GET    /auth/google/connect        # Initiate OAuth flow
GET    /auth/google/callback       # OAuth callback
DELETE /auth/google/disconnect     # Disconnect OAuth
```

### API Key Management
```
POST   /auth/api-keys              # Add manual API key
GET    /auth/api-keys              # Get user's credentials
DELETE /auth/api-keys              # Delete credentials
```

---

## 🧪 Testing Checklist

- [ ] Install new dependencies (`pip install -r requirements.txt`)
- [ ] Create Google OAuth app
- [ ] Configure `.env` with OAuth credentials
- [ ] Generate and set security keys
- [ ] Restart application
- [ ] Database tables created automatically
- [ ] Visit `/settings` page
- [ ] Click "Connect Google Account"
- [ ] Authorize with Google
- [ ] See success message and redirect
- [ ] Upload resume to test LinkedIn verification
- [ ] Check usage stats in settings
- [ ] Disconnect account
- [ ] Re-connect to verify flow works multiple times

---

## ⚠️ Troubleshooting

### Issue: "OAuth not configured"

**Solution:**
- Verify `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` in `.env`
- Restart application after adding credentials

### Issue: "Invalid redirect URI"

**Solution:**
- Check Google Cloud Console → Credentials
- Ensure redirect URI matches exactly: `http://localhost:8000/auth/google/callback`
- No trailing slash!

### Issue: "Token encryption failed"

**Solution:**
- Generate proper encryption key:
  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- Add to `.env` as `ENCRYPTION_KEY`

### Issue: Database errors

**Solution:**
- Application auto-creates tables on startup
- If issues persist, check database connection string
- For SQLite (development): `sqlite:///./hr_assistant.db`

---

## 📈 Benefits Over Server API Keys

| Feature | Server API | User OAuth | Winner |
|---------|------------|------------|--------|
| **Setup** | Admin only | Self-service | User OAuth |
| **Quota** | Shared 100/day | 100/day per user | User OAuth |
| **Cost** | Server pays | User pays | User OAuth |
| **Scaling** | Limited | Unlimited | User OAuth |
| **Security** | Server key exposure | Per-user tokens | User OAuth |

---

## 🎯 Next Steps

1. **Test the OAuth flow** with your Google account
2. **Update settings page UI** (optional beautification)
3. **Add usage analytics dashboard** (future enhancement)
4. **Deploy to production** with HTTPS

---

## ✅ Summary

**What's Implemented:**
- ✅ OAuth 2.0 flow with Google
- ✅ User authentication (JWT)
- ✅ Encrypted credential storage
- ✅ Automatic token refresh
- ✅ Usage tracking
- ✅ Settings page
- ✅ API endpoints
- ✅ Database schema

**Status:** ✅ Ready for testing!

**Time to Setup:** ~5 minutes  
**Time to Test:** ~10 minutes  

**Your idea is now fully implemented! 🎉**
