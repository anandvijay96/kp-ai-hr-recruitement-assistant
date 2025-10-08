# Testing Instructions - Resume Upload to Candidate Flow

## Prerequisites

1. **Start the application:**
   ```bash
   python main.py
   ```
   Or if using uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Ensure database is initialized:**
   - Database file should exist: `hr_recruitment.db`
   - Run migrations if needed

3. **Have test resume files ready:**
   - PDF, DOCX, or TXT format
   - Contains candidate information (name, email, phone, experience, skills)

## Test Scenario 1: Fresh Login and Upload

### Steps:
1. **Clear browser storage** (to simulate fresh session):
   - Open browser DevTools (F12)
   - Go to Application/Storage tab
   - Clear localStorage
   - Close DevTools

2. **Login:**
   - Navigate to: `http://localhost:8000/login`
   - Enter credentials
   - Verify redirect to home page

3. **Upload Resume:**
   - Navigate to: `http://localhost:8000/resumes/upload-new`
   - Drag & drop or browse for a resume file
   - Click "Upload All"
   - Wait for processing

4. **Verify Success:**
   - Modal shows "Upload Complete!"
   - Message says: "Candidates have been automatically created"
   - Click "Close"
   - **Expected**: Redirect to `http://localhost:8000/candidates`

5. **Verify Candidate Created:**
   - Check candidates list
   - **Expected**: New candidate appears with status "new"
   - Verify candidate details match resume content

### Expected Results:
✅ Resume uploads successfully  
✅ Candidate auto-created  
✅ Redirected to candidates page  
✅ New candidate visible in list  

---

## Test Scenario 2: Token Expiration Handling

### Steps:
1. **Login normally:**
   - Navigate to: `http://localhost:8000/login`
   - Enter credentials

2. **Manually expire token:**
   - Open browser DevTools (F12)
   - Go to Console tab
   - Run: `localStorage.setItem('access_token', 'invalid_token')`

3. **Try to upload:**
   - Navigate to: `http://localhost:8000/resumes/upload-new`
   - Select a resume file
   - Click "Upload All"

4. **Verify Token Expiration Handling:**
   - **Expected**: Alert shows "Your session has expired. Please login again."
   - **Expected**: Redirect to `/login`
   - **Expected**: Token cleared from localStorage

### Expected Results:
✅ Token expiration detected  
✅ User notified with alert  
✅ Redirected to login page  
✅ Token removed from storage  

---

## Test Scenario 3: Duplicate Detection

### Steps:
1. **Upload a resume** (follow Scenario 1)
2. **Upload the SAME resume again**
3. **Verify Duplicate Handling:**
   - **Expected**: Upload fails with "Duplicate resume detected"
   - Or: Duplicate candidates detected, user prompted to resolve

### Expected Results:
✅ Duplicate detected  
✅ User notified  
✅ No duplicate candidate created  

---

## Test Scenario 4: Bulk Upload

### Steps:
1. **Login**
2. **Navigate to upload page**
3. **Select multiple resume files** (2-5 files)
4. **Click "Upload All"**
5. **Monitor progress:**
   - Each file shows upload status
   - Progress bar updates
   - Success/failure indicated per file

6. **Verify Results:**
   - Click "Close" when complete
   - **Expected**: Redirect to candidates page
   - **Expected**: All successful uploads create candidates

### Expected Results:
✅ Multiple files upload  
✅ Progress tracked per file  
✅ Multiple candidates created  
✅ All visible in candidates list  

---

## Test Scenario 5: Navigation Flow

### Steps:
1. **From Candidates Page:**
   - Click "Upload Resume" button
   - **Expected**: Navigate to `/resumes/upload-new`

2. **From Candidates Page:**
   - Click "View Resumes" button
   - **Expected**: Navigate to `/resumes`

3. **From Upload Page:**
   - After successful upload, click "Close"
   - **Expected**: Navigate to `/candidates`

### Expected Results:
✅ All navigation links work  
✅ Proper redirects after actions  
✅ Breadcrumb trail makes sense  

---

## Debugging Tips

### If candidate doesn't appear:

1. **Check browser console** (F12 → Console):
   - Look for JavaScript errors
   - Check API response

2. **Check network tab** (F12 → Network):
   - Find `/api/resumes/upload` request
   - Check response status and body
   - Verify `candidate_created: true` in response

3. **Check server logs:**
   - Look for parsing errors
   - Check for duplicate detection messages
   - Verify database operations

4. **Verify database:**
   ```python
   # In Python console
   import sqlite3
   conn = sqlite3.connect('hr_recruitment.db')
   cursor = conn.cursor()
   cursor.execute("SELECT * FROM candidates ORDER BY created_at DESC LIMIT 5")
   print(cursor.fetchall())
   ```

### If token expired error persists:

1. **Check token in localStorage:**
   - DevTools → Application → Local Storage
   - Verify `access_token` exists and is valid

2. **Check token expiration time:**
   - Default is usually 30 minutes
   - May need to login again

3. **Clear all storage and re-login:**
   ```javascript
   localStorage.clear()
   sessionStorage.clear()
   ```

---

## API Testing with cURL

### Upload Resume:
```bash
# Get token first
TOKEN="your_access_token_here"

# Upload resume
curl -X POST http://localhost:8000/api/resumes/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@path/to/resume.pdf" \
  -F "auto_parse=true"
```

### List Candidates:
```bash
curl -X GET "http://localhost:8000/api/candidates?page=1&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Success Criteria

All tests pass if:
- ✅ Resume uploads successfully
- ✅ Candidate auto-created from parsed data
- ✅ User redirected to candidates page after upload
- ✅ New candidate visible in candidates list
- ✅ Token expiration handled gracefully
- ✅ Duplicate detection works
- ✅ Bulk uploads process correctly
- ✅ All navigation flows work

---

## Known Issues

1. **Parsing may fail for:**
   - Scanned PDFs without OCR
   - Heavily formatted documents
   - Non-standard resume layouts

2. **Token expiration:**
   - Default expiration time may be short
   - Consider implementing token refresh

3. **Large files:**
   - May timeout on slow connections
   - Consider chunked upload for very large files

---

## Next Steps

After successful testing:
1. Document any issues found
2. Test with real resume samples
3. Verify parsing accuracy
4. Test edge cases (empty files, corrupted PDFs, etc.)
5. Performance test with many concurrent uploads
