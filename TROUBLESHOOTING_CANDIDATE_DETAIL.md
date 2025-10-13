# Troubleshooting: Candidate Detail Page

## Issue
Candidate detail page shows "Error loading candidate - Failed to retrieve candidate details"

## Diagnostic Steps

### Step 1: Check Browser Console
1. Open the candidate detail page
2. Press F12 to open DevTools
3. Go to Console tab
4. Look for error messages
5. Check what the console.log statements show:
   - "Fetching candidate: [ID]"
   - "Response status: [CODE]"
   - "Candidate data: [DATA]"

### Step 2: Check Network Tab
1. In DevTools, go to Network tab
2. Refresh the page
3. Find the request to `/api/candidates/[ID]`
4. Click on it and check:
   - **Status Code**: Should be 200
   - **Response**: Should contain candidate data
   - **Headers**: Check Authorization header is present

### Step 3: Test Debug Endpoint
Open this URL in your browser (replace [ID] with actual candidate ID):
```
http://localhost:8000/api/candidates/[ID]/debug
```

This will show if the candidate exists in the database.

### Step 4: Check Server Logs
Look at the terminal/console where the server is running for error messages like:
```
ERROR: Error getting candidate [ID]: [error message]
```

## Common Issues and Solutions

### Issue 1: Token Expired (401 Error)
**Symptoms:**
- Console shows "Response status: 401"
- Redirects to login page

**Solution:**
1. Login again at `/login`
2. Navigate back to candidate detail page

### Issue 2: Candidate Not Found (404 Error)
**Symptoms:**
- Console shows "Response status: 404"
- Error message: "Candidate not found"

**Solution:**
1. Verify the candidate ID in the URL is correct
2. Check if candidate exists: `/api/candidates/[ID]/debug`
3. Go back to candidates list and click on a valid candidate

### Issue 3: Server Error (500 Error)
**Symptoms:**
- Console shows "Response status: 500"
- Server logs show Python traceback

**Solution:**
1. Check server logs for the actual error
2. Common causes:
   - Database connection issue
   - Data serialization error
   - Missing fields in database

### Issue 4: CORS or Network Error
**Symptoms:**
- Console shows "Failed to fetch" or CORS error
- Network tab shows request failed

**Solution:**
1. Ensure server is running on port 8000
2. Check if you're accessing the correct URL
3. Try restarting the server

## Manual Testing

### Test 1: List All Candidates
```bash
curl -X GET "http://localhost:8000/api/candidates?page=1&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Test 2: Get Specific Candidate
```bash
curl -X GET "http://localhost:8000/api/candidates/CANDIDATE_ID_HERE" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Test 3: Debug Candidate
```bash
curl -X GET "http://localhost:8000/api/candidates/CANDIDATE_ID_HERE/debug" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## How to Get Your Token

### Method 1: From Browser
1. Open DevTools (F12)
2. Go to Application tab
3. Click on Local Storage → http://localhost:8000
4. Find `access_token`
5. Copy the value

### Method 2: Login via API
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_password"
  }'
```

## Database Check

### Check if Candidate Exists
```python
# Run in Python console
import sqlite3
conn = sqlite3.connect('hr_recruitment.db')
cursor = conn.cursor()

# List all candidates
cursor.execute("SELECT id, full_name, email, status FROM candidates LIMIT 10")
for row in cursor.fetchall():
    print(row)

# Check specific candidate
candidate_id = "YOUR_CANDIDATE_ID"
cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
print(cursor.fetchone())
```

### Check Related Data
```python
# Check education
cursor.execute("SELECT * FROM education WHERE candidate_id = ?", (candidate_id,))
print("Education:", cursor.fetchall())

# Check experience
cursor.execute("SELECT * FROM work_experience WHERE candidate_id = ?", (candidate_id,))
print("Experience:", cursor.fetchall())

# Check skills
cursor.execute("""
    SELECT s.name, cs.proficiency 
    FROM skills s
    JOIN candidate_skills cs ON s.id = cs.skill_id
    WHERE cs.candidate_id = ?
""", (candidate_id,))
print("Skills:", cursor.fetchall())
```

## Recent Code Changes

The following fixes were applied:

1. **Data Serialization** (`services/candidate_service.py`):
   - Converted datetime objects to ISO format strings
   - Replaced Pydantic model validation with plain dictionaries
   - Ensured all nested data (education, experience, skills, certifications) is properly serialized

2. **Error Handling** (`api/candidates.py`):
   - Added detailed logging
   - Improved error messages
   - Added debug endpoint

3. **Frontend** (`templates/candidates/detail.html`):
   - Added console logging
   - Better error display
   - Retry button

## Next Steps

1. **Check browser console** - This will show the exact error
2. **Check server logs** - Look for Python errors
3. **Test debug endpoint** - Verify candidate exists
4. **Share error details** - If still not working, share:
   - Console error message
   - Server log error
   - Response from debug endpoint

## Quick Fix Checklist

- [ ] Server is running
- [ ] You are logged in (token exists)
- [ ] Candidate ID in URL is valid
- [ ] Database file exists and is accessible
- [ ] No errors in server logs
- [ ] Browser console shows detailed logs
- [ ] Network tab shows successful API call
