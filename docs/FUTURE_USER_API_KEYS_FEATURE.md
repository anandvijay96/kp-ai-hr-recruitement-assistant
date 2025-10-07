# 💡 Future Enhancement: User-Provided Google API Keys

**Feature:** Allow users to provide their own Google Search API credentials  
**Benefit:** Avoid API quota limits on server, let users use their own Google Cloud accounts  
**Status:** 📋 Planned for Future Implementation  
**Priority:** Medium-High  
**Estimated Effort:** 2-3 days  

---

## 🎯 Problem Statement

### Current Limitation

**Server-Side API Keys:**
- ✅ Simple for users (no setup required)
- ❌ Shared quota limit (100 free searches/day)
- ❌ Server bears the cost after free tier
- ❌ Can hit quota quickly with multiple users
- ❌ Need to manage billing/costs centrally

**Example Scenario:**
- 10 users each processing 20 resumes/day = 200 searches
- Free tier: 100/day → 100 searches require payment
- Monthly cost: ~$15-30 (depending on usage)
- **Problem:** Server admin pays for everyone's usage

### Your Solution ✨

**User-Provided API Keys:**
- ✅ Each user uses their own Google Cloud quota
- ✅ No shared limit issues
- ✅ Server doesn't bear API costs
- ✅ Scales infinitely (each user = separate quota)
- ✅ Users control their own billing

---

## 🔧 Proposed Implementation

### Option 1: OAuth 2.0 Flow (Recommended)

**User Experience:**
```
1. User clicks "Connect Google Account" button
2. Redirects to Google OAuth consent screen
3. User logs in with Google account
4. User grants permission: "Allow HR Assistant to use Custom Search API"
5. System receives OAuth token
6. Store token securely (encrypted in database)
7. Use token for Google Search API calls on behalf of user
```

**Benefits:**
- ✅ One-click setup (no manual API key copying)
- ✅ Secure (OAuth tokens, not API keys)
- ✅ Can revoke access anytime from Google account
- ✅ Professional user experience
- ✅ Automatic token refresh

**Technical Components:**
```python
# OAuth Flow
1. User initiates: GET /auth/google/connect
2. Redirect to Google OAuth URL
3. Google callback: GET /auth/google/callback?code=...
4. Exchange code for access token + refresh token
5. Store tokens encrypted in user profile
6. Use tokens for API calls

# Database Schema
users:
  - id
  - email
  - google_oauth_token (encrypted)
  - google_oauth_refresh_token (encrypted)
  - google_api_quota_used (track usage)
  - created_at
```

### Option 2: Manual API Key Entry (Simpler)

**User Experience:**
```
1. User clicks "Add Your API Key" button
2. Shows instructions: "Get your API key from Google Cloud Console"
3. User copies API key from Google Cloud
4. User pastes into form
5. System validates and saves (encrypted)
```

**Benefits:**
- ✅ Simpler to implement (no OAuth flow)
- ✅ User has direct control
- ✅ Works for users who already have keys

**Drawbacks:**
- ❌ Manual steps (copy-paste API key)
- ❌ Need to explain how to get API key
- ❌ Less secure (users handling raw API keys)
- ❌ No automatic refresh

---

## 🏗️ Architecture Design

### Database Schema

```sql
-- Users table (if not exists)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User API credentials (encrypted)
CREATE TABLE user_api_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    service_type VARCHAR(50) NOT NULL, -- 'google_search'
    
    -- OAuth credentials
    oauth_access_token TEXT, -- encrypted
    oauth_refresh_token TEXT, -- encrypted
    oauth_expires_at TIMESTAMP,
    
    -- Or manual API key
    api_key TEXT, -- encrypted
    api_engine_id TEXT, -- encrypted (for Google Search)
    
    -- Usage tracking
    quota_used_today INT DEFAULT 0,
    quota_limit_daily INT DEFAULT 100,
    last_reset_date DATE DEFAULT CURRENT_DATE,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, service_type)
);

-- API usage logs (for billing/analytics)
CREATE TABLE api_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    credential_id UUID REFERENCES user_api_credentials(id),
    service_type VARCHAR(50),
    endpoint VARCHAR(255),
    request_count INT DEFAULT 1,
    cost_estimate DECIMAL(10, 4), -- estimated cost
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

```python
# Authentication
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me

# OAuth Flow
GET    /api/auth/google/connect       # Initiate OAuth
GET    /api/auth/google/callback      # OAuth callback
DELETE /api/auth/google/disconnect    # Revoke access

# Manual API Key Management
POST   /api/settings/api-keys          # Add API key manually
GET    /api/settings/api-keys          # Get user's API keys (masked)
PUT    /api/settings/api-keys/:id      # Update API key
DELETE /api/settings/api-keys/:id      # Delete API key

# Usage Analytics
GET    /api/usage/stats                # Get usage statistics
GET    /api/usage/history              # Get usage history
```

### Service Layer

```python
# services/user_api_manager.py

class UserAPIManager:
    """Manages user-provided API credentials"""
    
    def get_user_google_credentials(self, user_id: str) -> Optional[Dict]:
        """Get Google API credentials for user"""
        # Check database for user's credentials
        # Decrypt and return
        pass
    
    def use_google_search(self, user_id: str, query: str) -> Dict:
        """
        Perform Google search using user's credentials
        Falls back to server credentials if user doesn't have any
        """
        # Get user credentials
        user_creds = self.get_user_google_credentials(user_id)
        
        if user_creds:
            # Use user's API key/token
            # Track usage
            # Update quota
            return self._search_with_user_creds(user_creds, query)
        else:
            # Fallback to server credentials
            return self._search_with_server_creds(query)
    
    def refresh_oauth_token(self, user_id: str):
        """Refresh expired OAuth token"""
        pass
    
    def check_quota_remaining(self, user_id: str) -> Dict:
        """Check how much quota user has left today"""
        pass
```

---

## 🎨 UI/UX Design

### Settings Page

```
┌─────────────────────────────────────────────┐
│  ⚙️ Settings - Google Search Configuration  │
├─────────────────────────────────────────────┤
│                                             │
│  🔍 Google Search API                       │
│  ─────────────────────────────              │
│                                             │
│  Current Status: 🔴 Not Connected           │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Option 1: Connect with Google (🌟)  │  │
│  │                                       │  │
│  │  [🔗 Connect Google Account]         │  │
│  │                                       │  │
│  │  • One-click setup                   │  │
│  │  • Secure OAuth flow                 │  │
│  │  • 100 free searches/day             │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │  Option 2: Enter API Key Manually    │  │
│  │                                       │  │
│  │  [📝 Add API Key Manually]           │  │
│  │                                       │  │
│  │  • For advanced users                │  │
│  │  • Direct control                    │  │
│  └──────────────────────────────────────┘  │
│                                             │
│  📊 Usage Today: 0 / 100 searches           │
│                                             │
└─────────────────────────────────────────────┘
```

### After Connection

```
┌─────────────────────────────────────────────┐
│  ⚙️ Settings - Google Search Configuration  │
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
│  • Today: 23 / 100 searches (23%)          │
│  • This Week: 145 / 700 searches           │
│  • This Month: 580 searches                │
│                                             │
│  [View Detailed Usage] [Disconnect]         │
│                                             │
│  💡 Pro Tip: You can process ~100 resumes   │
│     per day with LinkedIn verification.     │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🔐 Security Considerations

### 1. **Encryption at Rest**

```python
# Use Fernet encryption for API keys/tokens
from cryptography.fernet import Fernet

class CredentialEncryption:
    def __init__(self, encryption_key: str):
        self.fernet = Fernet(encryption_key.encode())
    
    def encrypt(self, plaintext: str) -> str:
        return self.fernet.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        return self.fernet.decrypt(ciphertext.encode()).decode()
```

### 2. **Environment Variables**

```bash
# .env
ENCRYPTION_KEY=your-32-byte-encryption-key-here
GOOGLE_OAUTH_CLIENT_ID=your-oauth-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-oauth-client-secret
OAUTH_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

### 3. **Token Refresh**

```python
# Automatically refresh expired OAuth tokens
def ensure_valid_token(user_id: str):
    creds = get_user_credentials(user_id)
    
    if creds.oauth_expires_at < datetime.now():
        # Token expired, refresh it
        new_token = refresh_oauth_token(creds.oauth_refresh_token)
        update_user_credentials(user_id, new_token)
```

### 4. **Rate Limiting**

```python
# Prevent abuse even with user's own API
@rate_limit(max_calls=100, period=86400)  # 100/day
def perform_search(user_id: str, query: str):
    pass
```

---

## 📋 Implementation Phases

### Phase 1: Foundation (1 day)
- [ ] Create database schema (users, credentials, usage_logs)
- [ ] Implement encryption service
- [ ] Add user authentication (JWT)
- [ ] Create settings page UI

### Phase 2: OAuth Flow (1 day)
- [ ] Set up Google OAuth app
- [ ] Implement OAuth endpoints
- [ ] Create "Connect Google" button
- [ ] Handle OAuth callback
- [ ] Store tokens securely

### Phase 3: API Integration (1 day)
- [ ] Modify GoogleSearchVerifier to accept user credentials
- [ ] Implement credential fallback (user → server)
- [ ] Add usage tracking
- [ ] Implement quota checking
- [ ] Add token refresh logic

### Phase 4: UI & Analytics (1 day)
- [ ] Build settings page
- [ ] Add usage dashboard
- [ ] Show quota warnings
- [ ] Add disconnect functionality
- [ ] Create admin panel for monitoring

### Phase 5: Testing & Documentation (1 day)
- [ ] Test OAuth flow
- [ ] Test credential encryption
- [ ] Test quota limits
- [ ] Write user documentation
- [ ] Write developer documentation

---

## 🎯 Success Metrics

1. **User Adoption**
   - % of users connecting their own API keys
   - Target: 70%+ of active users

2. **Cost Savings**
   - Reduction in server API costs
   - Target: 80%+ reduction

3. **User Satisfaction**
   - Ease of setup (survey)
   - Target: 4.5/5 rating

4. **System Health**
   - API errors reduced
   - Target: <1% error rate

---

## 💰 Cost-Benefit Analysis

### Before (Server API Keys)
```
10 users × 20 resumes/day × 30 days = 6,000 searches/month
Free tier: 100/day × 30 = 3,000 free
Paid: 3,000 searches @ $5/1000 = $15/month

Cost to server: $15/month
```

### After (User API Keys)
```
Each user uses their own account:
- User 1: 20 resumes/day × 30 = 600/month (free tier)
- User 2: 20 resumes/day × 30 = 600/month (free tier)
- ... (all users within free tier)

Cost to server: $0/month
Savings: $15/month (or more as usage grows)
```

**ROI:** Immediate positive ROI, scales infinitely

---

## 🚀 Rollout Strategy

### Stage 1: Beta Test (Week 1-2)
- Enable for 5-10 test users
- Gather feedback
- Fix bugs

### Stage 2: Opt-In (Week 3-4)
- Announce feature to all users
- Keep server API as fallback
- Monitor adoption

### Stage 3: Encourage Migration (Month 2)
- Show benefits (quota, speed)
- Add usage dashboard
- Offer support for setup

### Stage 4: Default Mode (Month 3+)
- Make user API preferred
- Server API as backup only
- Deprecate server API eventually

---

## 📚 User Documentation

### Quick Setup Guide

**Step 1: Go to Settings**
1. Click your profile icon
2. Select "Settings"
3. Navigate to "API Configuration"

**Step 2: Connect Google Account**
1. Click "Connect Google Account"
2. Log in with your Google account
3. Click "Allow" when prompted
4. Done! ✅

**That's it!** You now have 100 free searches per day.

### FAQ

**Q: Why do I need to connect my Google account?**  
A: This gives you 100 free LinkedIn verifications per day using your own Google Cloud quota instead of sharing a limited server quota.

**Q: Will this cost me money?**  
A: No! Google provides 100 free searches per day. Unless you process 100+ resumes daily, you'll stay in the free tier.

**Q: Is it secure?**  
A: Yes! We use OAuth (the same technology Google uses for "Sign in with Google"). You can revoke access anytime from your Google account settings.

**Q: What if I don't connect my account?**  
A: The system will still work, but LinkedIn verification may be limited due to shared server quotas.

---

## 🔮 Future Enhancements

### Multi-Provider Support
- Support different search engines (Bing, DuckDuckGo)
- Let users choose preferred provider
- Automatic failover between providers

### Team Billing
- Organization accounts
- Shared quota across team members
- Billing dashboard for admins

### Advanced Analytics
- Detailed usage reports
- Cost forecasting
- Optimization suggestions

---

## ✅ Conclusion

**Your Idea is Excellent! ✨**

**Benefits:**
1. ✅ Eliminates server API cost burden
2. ✅ Scales infinitely (each user = separate quota)
3. ✅ Better user experience (no shared limits)
4. ✅ Users control their own billing
5. ✅ Professional-grade OAuth implementation

**Implementation Priority:** High  
**Estimated Timeline:** 1 week for MVP  
**ROI:** Immediate positive (cost savings + better UX)

**Recommendation:** Implement this feature in the next sprint after current Phase 2 work is complete. The OAuth flow is the best approach for user experience and security.

---

**Status:** 📋 Documented and ready for implementation planning  
**Next Step:** Add to backlog for next development cycle
