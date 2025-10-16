# Gemini API Quota Fix - Realistic Limits

**Date:** October 16, 2025  
**Issue:** Misleading quota display (showed 1500 requests/day, actual limit is 50)

---

## **Problem**

The application displayed **incorrect Gemini API quota limits**:
- ❌ **Displayed:** 1500 requests/day
- ✅ **Actual:** 50 requests/day (Gemini 2.0 Flash Experimental - Free Tier)

**Impact:**
- Users hit quota limit after ~40-50 resumes
- Confusing error messages
- No warning about actual limits

---

## **Root Cause**

Gemini API has different limits for different models and tiers:

### **Gemini 2.0 Flash Experimental (Free Tier)**
```
Requests Per Minute (RPM): 15
Requests Per Day (RPD): 50  ⚠️ VERY LIMITED
Tokens Per Minute (TPM): 1,000,000
```

### **Gemini 2.0 Flash (Paid Tier 1)**
```
RPM: 1,000
RPD: 10,000+
TPM: 4,000,000
```

**Source:** https://ai.google.dev/gemini-api/docs/rate-limits

---

## **Fix Applied**

### **1. Updated Quota Constants**

**File:** `services/llm_usage_tracker.py`

```python
# Before (WRONG)
GEMINI_FREE_RPD = 1500  # ❌ Incorrect

# After (CORRECT)
GEMINI_FREE_RPD = 50  # ✅ Accurate for Gemini 2.0 Flash Experimental
```

### **2. Updated API Response**

**File:** `api/v1/llm_usage.py`

```python
"gemini": {
    "available": bool(gemini_key),
    "name": "Gemini 2.0 Flash (Free)",
    "limits": {
        "rpm": 15,
        "rpd": 50,  # Updated
        "tpm": 1000000
    },
    "warning": "⚠️ Free tier: 50 requests/day limit"
}
```

### **3. Updated Frontend Display**

**File:** `templates/vet_resumes.html`

```html
<!-- Before -->
<span>0 / 1,500 requests today</span>

<!-- After -->
<span>0 / 50 requests today</span>

<!-- Added Warning -->
<div class="alert alert-warning">
    <strong>Free Tier Limit:</strong> 50 requests/day • 15 requests/minute
</div>
```

---

## **Realistic Usage Expectations**

### **Free Tier (Current)**
- **50 requests/day** = ~40-50 resumes/day
- **15 requests/minute** = Batch processing limited
- **Resets:** Daily at midnight UTC

### **Recommendations for Production**

#### **Option 1: Multiple Free API Keys (Quick Fix)**
```bash
# Rotate between multiple Google accounts
GEMINI_API_KEY_1=AIza...  # Account 1: 50/day
GEMINI_API_KEY_2=AIza...  # Account 2: 50/day
GEMINI_API_KEY_3=AIza...  # Account 3: 50/day
# Total: 150 requests/day
```

#### **Option 2: Upgrade to Paid Tier (Recommended)**
```
Cost: Pay-as-you-go
Limits: 1,000 RPM, 10,000+ RPD
Best for: Production use
```

#### **Option 3: Hybrid Approach**
```
- Use Gemini for initial extraction (50/day)
- Fall back to traditional OCR + Regex
- Use OpenAI for critical candidates
```

---

## **Next Steps (Phase 3)**

### **1. Admin API Key Management** (HIGH PRIORITY)

Create admin panel to manage multiple API keys:

```python
# Database table
class LLMAPIKey(Base):
    id = Column(String(36), primary_key=True)
    provider = Column(String(20))  # 'gemini' or 'openai'
    api_key = Column(String(500), encrypted=True)
    label = Column(String(100))  # "Google Account 1"
    daily_quota = Column(Integer)  # 50 for free, 10000 for paid
    requests_today = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    added_by = Column(String(36))
    added_at = Column(DateTime)
```

**Features:**
- ✅ Add/remove API keys via admin UI
- ✅ Automatic key rotation (round-robin)
- ✅ Per-key quota tracking
- ✅ Disable exhausted keys automatically
- ✅ Email alerts when quota hits 80%

### **2. Smart Key Rotation**

```python
class LLMKeyRotator:
    def get_next_available_key(self, provider: str):
        """Get next API key with available quota"""
        keys = db.query(LLMAPIKey).filter(
            LLMAPIKey.provider == provider,
            LLMAPIKey.is_active == True,
            LLMAPIKey.requests_today < LLMAPIKey.daily_quota
        ).order_by(LLMAPIKey.requests_today.asc()).all()
        
        if not keys:
            raise QuotaExceededException("All API keys exhausted")
        
        return keys[0]
```

### **3. Better Error Handling**

```python
try:
    result = await llm_extractor.extract(resume_text)
except QuotaExceededException as e:
    # Show user-friendly message
    return {
        "error": "quota_exceeded",
        "message": "Daily API quota reached. Please try again tomorrow or contact admin to add more API keys.",
        "fallback": "traditional",
        "retry_after": "2025-10-17T00:00:00Z"
    }
```

---

## **Testing**

### **Verify Quota Display**

1. **Start server:**
   ```bash
   python main.py
   ```

2. **Check vetting page:**
   ```
   http://localhost:8000/vet-resumes
   ```

3. **Expected display:**
   ```
   Gemini 2.0 Flash (Free)
   0 / 50 requests today • 50 remaining
   ⚠️ Free Tier Limit: 50 requests/day • 15 requests/minute
   ```

### **Test Quota Exhaustion**

1. Upload 50+ resumes
2. Should see error after 50th request
3. Error message should be clear:
   ```
   "You exceeded your current quota, please check your plan and billing details"
   ```

---

## **Files Modified**

1. ✅ `services/llm_usage_tracker.py` - Updated GEMINI_FREE_RPD to 50
2. ✅ `api/v1/llm_usage.py` - Added limits and warning to provider info
3. ✅ `templates/vet_resumes.html` - Updated UI to show 50 requests/day + warning

---

## **Summary**

| Metric | Before | After |
|--------|--------|-------|
| Displayed Limit | 1500/day | 50/day |
| Actual Limit | 50/day | 50/day |
| User Confusion | High | None |
| Warning Shown | No | Yes |
| Realistic Expectations | No | Yes |

**Status:** ✅ Fixed and accurate

**Next:** Implement multi-key management in Phase 3
