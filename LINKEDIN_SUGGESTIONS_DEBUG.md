# LinkedIn Suggestions Feature - Debugging Guide

## Issue
LinkedIn profile selection options are not showing on the candidate detail page.

## Root Cause Analysis

The feature is fully implemented but LinkedIn suggestions aren't appearing because:

1. **Migration not run yet** - The `linkedin_suggestions` column doesn't exist in the database
2. **No LinkedIn profiles found** - DuckDuckGo searches are returning empty arrays

## How the Feature Works

### Backend Flow:
1. During vetting, DuckDuckGo searches for candidate's LinkedIn profile
2. Results stored in `vetting_session.json` under:
   ```
   resumes[].authenticity_analysis.linkedin_profile_check.google_verification.linkedin_profiles[]
   ```
3. When uploading approved resumes, this array is extracted and stored in `candidates.linkedin_suggestions`
4. API returns `linkedin_suggestions` in candidate detail response

### Frontend Flow:
1. JavaScript checks if `linkedin_suggestions` exists and has items
2. If yes, displays radio buttons for HR to select
3. On "Save Selection", calls `PATCH /api/v1/candidates/{id}/linkedin` to save choice

## Steps to Fix

### 1. Run Migration
```bash
python migrations/add_linkedin_suggestions.py
```

### 2. Restart Server
```bash
python main.py
```

### 3. Test with New Resume Upload

**Important:** Existing candidates won't have LinkedIn suggestions because:
- They were uploaded before the feature was implemented
- Their vetting sessions likely have empty `linkedin_profiles[]` arrays

To test:
1. Upload a NEW resume with a candidate who has a common name
2. Wait for vetting to complete (DuckDuckGo search)
3. Check vetting session JSON for `linkedin_profiles`
4. Approve and upload to database
5. View candidate detail page

### 4. Check Browser Console

Open candidate detail page and check console for:
```javascript
LinkedIn URL: null
LinkedIn Suggestions: ["https://linkedin.com/in/...", ...]
```

If you see:
- `LinkedIn Suggestions: []` → DuckDuckGo didn't find profiles
- `LinkedIn Suggestions: null` → Migration not run or data not stored
- `LinkedIn Suggestions: [...]` → Feature should be working!

## Manual Test

To manually test the feature without waiting for DuckDuckGo:

### Option 1: Direct Database Update
```sql
UPDATE candidates 
SET linkedin_suggestions = '["https://linkedin.com/in/test1", "https://linkedin.com/in/test2"]'
WHERE id = 'YOUR_CANDIDATE_ID';
```

### Option 2: Use Python Script
```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from core.config import settings

async def add_test_suggestions():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.execute(text("""
            UPDATE candidates 
            SET linkedin_suggestions = :suggestions
            WHERE email = 'lahariofficial799@gmail.com'
        """), {"suggestions": '["https://linkedin.com/in/lahari-test1", "https://linkedin.com/in/lahari-test2"]'})
    await engine.dispose()

asyncio.run(add_test_suggestions())
```

## Expected UI

When LinkedIn suggestions exist, you should see:

```
LinkedIn
🔍 Found LinkedIn profiles - Select the correct one:
○ https://linkedin.com/in/profile1
○ https://linkedin.com/in/profile2
○ https://linkedin.com/in/profile3
[Save Selection]
```

## Troubleshooting

### Suggestions not showing?
1. Check browser console for logs
2. Check API response: `/api/v1/candidates/{id}` should include `linkedin_suggestions`
3. Verify migration ran successfully
4. Check database: `SELECT linkedin_suggestions FROM candidates WHERE id = '...'`

### DuckDuckGo not finding profiles?
- This is expected for uncommon names or candidates without online presence
- Feature will only work when profiles are actually found
- Consider adding manual LinkedIn URL entry as fallback

## Future Enhancements

1. **Manual URL Entry**: Add input field for HR to manually enter LinkedIn URL
2. **Better Search**: Improve DuckDuckGo search query to find more profiles
3. **LinkedIn API**: Use official LinkedIn API (requires paid subscription)
4. **Profile Preview**: Show profile preview/snippet before selection
