# Gemini API Quota Fix - Upgraded to 2.5 Flash-Lite

**Date:** October 16, 2025  
**Issue:** Misleading quota display + Using wrong model

---

## **Problem Evolution**

### **Initial Issue:**
- ❌ **Displayed:** 1500 requests/day
- ✅ **Actual:** 50 requests/day (Gemini 2.0 Flash Experimental)

### **Solution Found:**
- ✅ **Upgraded to:** Gemini 2.5 Flash-Lite
- ✅ **New Limit:** 1000 requests/day (20x improvement!)

---

## **Gemini Free Tier Model Comparison**

| Model | RPD | RPM | TPM | Best For |
|-------|-----|-----|-----|----------|
| **Gemini 2.5 Flash-Lite** ⭐ | **1,000** | 15 | 250K | **High-volume, production use** |
| Gemini 2.0 Flash | 200 | 15 | 1M | Balanced usage |
| Gemini 2.0 Flash Exp | 50 | 15 | 1M | Testing only |
| Gemini 2.5 Pro | 25 | 5 | 1M | Complex tasks, low volume |

**Winner:** Gemini 2.5 Flash-Lite provides the **highest free tier quota** (1000 RPD)

**Source:** https://ai.google.dev/gemini-api/docs/rate-limits

---

## **Fix Applied**

### **1. Switched to Better Model**

**File:** `services/llm_resume_extractor.py`

```python
# Before (Limited)
self.model = genai.GenerativeModel('gemini-2.0-flash-exp')  # 50 RPD

# After (20x Better!)
self.model = genai.GenerativeModel('gemini-2.5-flash-lite')  # 1000 RPD
```

### **2. Updated Quota Constants**

**File:** `services/llm_usage_tracker.py`

```python
# Before
GEMINI_FREE_RPD = 50  # Too limited

# After
GEMINI_FREE_RPD = 1000  # 20x improvement!
GEMINI_FREE_TPM = 250_000  # 250K tokens/minute
```

### **3. Updated API Response**

**File:** `api/v1/llm_usage.py`

```python
"gemini": {
    "available": bool(gemini_key),
    "name": "Gemini 2.5 Flash-Lite (Free)",
    "limits": {
        "rpm": 15,
        "rpd": 1000,  # 20x better!
        "tpm": 250000
    },
    "warning": "✅ Free tier: 1000 requests/day (best free model!)"
}
```

### **4. Updated Frontend Display**

**File:** `templates/vet_resumes.html`

```html
<!-- Before -->
<span>0 / 50 requests today</span>

<!-- After -->
<span>0 / 1,000 requests today</span>

<!-- Changed to Success Alert -->
<div class="alert alert-success">
    <strong>Free Tier:</strong> 1,000 requests/day • 15 requests/minute (Best free model!)
</div>
```

---

## **Realistic Usage Expectations**

### **Free Tier (Gemini 2.5 Flash-Lite) ⭐**
- **1,000 requests/day** = ~800-1000 resumes/day 🎉
- **15 requests/minute** = Batch processing supported
- **Resets:** Daily at midnight UTC
- **Perfect for:** Small-medium HR teams, testing, MVP

### **Production Scaling Options**

#### **Option 1: Single Free Key (Current) ✅**
```bash
GEMINI_API_KEY=AIza...  # 1000 requests/day
# Sufficient for most small teams!
```

#### **Option 2: Multiple Free Keys (If Needed)**
```bash
# Only if you exceed 1000/day
GEMINI_API_KEY_1=AIza...  # Account 1: 1000/day
GEMINI_API_KEY_2=AIza...  # Account 2: 1000/day
# Total: 2000 requests/day
```

#### **Option 3: Upgrade to Paid Tier (High Volume)**
```
Cost: Pay-as-you-go (~$0.10 per 1M tokens)
Limits: 1,000 RPM, 10,000+ RPD
Best for: Enterprise, 1000+ resumes/day
```

#### **Option 4: Hybrid Approach (Fallback)**
```
✅ Already implemented!
- Try Gemini 2.5 Flash-Lite (1000/day)
- Falls back to traditional OCR + Regex
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

1. ✅ `services/llm_resume_extractor.py` - Switched to gemini-2.5-flash-lite
2. ✅ `services/llm_usage_tracker.py` - Updated GEMINI_FREE_RPD to 1000
3. ✅ `api/v1/llm_usage.py` - Updated provider info with new limits
4. ✅ `templates/vet_resumes.html` - Updated UI to show 1000 requests/day
5. ✅ `GEMINI_QUOTA_FIX.md` - Complete documentation

---

## **Summary**

| Metric | Initial | After Fix 1 | After Fix 2 (Final) |
|--------|---------|-------------|---------------------|
| Model | 2.0 Flash Exp | 2.0 Flash Exp | **2.5 Flash-Lite** ⭐ |
| Displayed Limit | 1500/day | 50/day | **1000/day** |
| Actual Limit | 50/day | 50/day | **1000/day** |
| Resumes/Day | ~40 | ~40 | **~800-1000** 🎉 |
| User Confusion | High | None | None |
| Production Ready | No | No | **Yes** ✅ |

**Status:** ✅ Fixed and optimized with best free model

**Impact:** **20x improvement** in daily quota (50 → 1000 requests/day)

**Next:** Multi-key management only needed if exceeding 1000/day
