# Testing Guide: Soft Delete Feature

**Date:** October 16, 2025  
**Status:** ✅ Ready for Testing

---

## **Pre-Testing Checklist**

- [x] Database migration completed (4 new columns added)
- [x] Backend API endpoints implemented
- [x] Frontend UI added (list + detail pages)
- [x] Filter service updated to exclude deleted candidates
- [ ] Server restarted
- [ ] Browser cache cleared

---

## **Test Scenario 1: Delete from Candidates List**

### **Steps:**

1. **Navigate to Candidates Search**
   ```
   http://localhost:8000/search
   ```

2. **Identify Test Candidates**
   - Look for candidates with bad data:
     - "Senior Software" (name extraction failed)
     - Candidates with malformed education data
   - Note their names for verification

3. **Delete a Candidate**
   - Click the **red trash icon** button on any candidate card
   - Confirm the deletion dialog
   - Optionally enter a reason (e.g., "Bad data extraction - re-uploading")

4. **Expected Results:**
   - ✅ Confirmation dialog appears
   - ✅ Success message: "Candidate '[Name]' deleted successfully"
   - ✅ Candidate disappears from list immediately
   - ✅ Page refreshes with updated results

---

## **Test Scenario 2: Delete from Candidate Detail Page**

### **Steps:**

1. **Open a Candidate Detail Page**
   - Click on any candidate from the search results
   - URL: `http://localhost:8000/candidates/{id}`

2. **Locate Delete Button**
   - Look at the top-right corner
   - Should see: **"Back to Search"** and **"Delete Candidate"** buttons

3. **Delete the Candidate**
   - Click **"Delete Candidate"** button
   - Confirm the deletion dialog
   - Optionally enter a reason

4. **Expected Results:**
   - ✅ Confirmation dialog appears
   - ✅ Success message with redirect notice
   - ✅ Automatically redirected to search page
   - ✅ Deleted candidate no longer appears in search

---

## **Test Scenario 3: Verify Soft Delete (Not Hard Delete)**

### **Steps:**

1. **Open Database**
   ```bash
   sqlite3 hr_recruitment.db
   ```

2. **Query Deleted Candidates**
   ```sql
   SELECT id, full_name, email, is_deleted, deleted_at, deleted_by, deletion_reason
   FROM candidates
   WHERE is_deleted = TRUE
   ORDER BY deleted_at DESC;
   ```

3. **Expected Results:**
   - ✅ Deleted candidates still exist in database
   - ✅ `is_deleted = 1` (TRUE)
   - ✅ `deleted_at` has timestamp
   - ✅ `deleted_by = 'admin'`
   - ✅ `deletion_reason` shows your entered reason (if provided)

---

## **Test Scenario 4: Verify Candidates Are Hidden**

### **Steps:**

1. **Search for Deleted Candidate**
   - Go to search page
   - Enter the deleted candidate's name in search box
   - Click search

2. **Expected Results:**
   - ✅ No results found
   - ✅ Message: "No candidates found matching your criteria"

3. **Try Direct URL Access**
   - Navigate to: `http://localhost:8000/candidates/{deleted_id}`

4. **Expected Results:**
   - ✅ Shows "Candidate Not Found" error
   - ✅ Cannot access deleted candidate details

---

## **Test Scenario 5: Delete Multiple Candidates**

### **Steps:**

1. **Delete All Bad Candidates**
   - "Senior Software" (bad name extraction)
   - Any candidates with placeholder emails
   - Candidates with malformed education data

2. **Track Deletions**
   - Note how many candidates you delete
   - Check database to verify all are marked `is_deleted = TRUE`

3. **Expected Results:**
   - ✅ All deleted candidates disappear from UI
   - ✅ All remain in database with audit trail
   - ✅ Search results update correctly

---

## **Test Scenario 6: Re-Upload Fresh Candidates**

### **Steps:**

1. **Navigate to Vetting Page**
   ```
   http://localhost:8000/vet-resumes
   ```

2. **Upload Same Resumes Again**
   - Upload the resumes you just deleted
   - Use **AI-Powered Extraction (Gemini)**
   - Click "Scan Resumes for Authenticity"

3. **Review Results**
   - Check if extraction is better now
   - Verify job hopping analysis shows correctly
   - Check education data

4. **Upload to Database**
   - Select approved resumes
   - Click "Upload Selected to Database"

5. **Expected Results:**
   - ✅ New candidates created with fresh IDs
   - ✅ Better data extraction (using LLM)
   - ✅ Job hopping analysis works
   - ✅ Education data properly formatted

---

## **Test Scenario 7: Verify Candidate Detail Page**

### **Steps:**

1. **Open Newly Uploaded Candidate**
   - Go to search page
   - Click on a re-uploaded candidate

2. **Check All Sections:**
   - ✅ Personal Information (name, email, phone)
   - ✅ Work Experience (companies, roles, durations)
   - ✅ Education (degrees, institutions, years)
   - ✅ Skills (properly extracted)
   - ✅ Certifications (if any)

3. **Compare with Screenshot 2**
   - Should NOT show:
     - "as a product using Dell Boomi"
     - "as the Middle East"
     - "be a major success"
   - Should show proper education entries

---

## **Test Scenario 8: API Testing (Optional)**

### **Using cURL:**

```bash
# Delete a candidate
curl -X DELETE "http://localhost:8000/api/v1/candidates/1/soft-delete?reason=Test&deleted_by=admin"

# Expected Response:
{
  "success": true,
  "message": "Candidate 'John Doe' deleted successfully",
  "candidate_id": 1,
  "deleted_at": "2025-10-16T17:30:00",
  "deleted_by": "admin"
}

# Verify candidate is hidden
curl "http://localhost:8000/api/v1/candidates/search" \
  -H "Content-Type: application/json" \
  -d '{}'

# Should NOT include deleted candidate in results

# Restore candidate (if needed)
curl -X POST "http://localhost:8000/api/v1/candidates/1/restore"
```

---

## **Common Issues & Solutions**

### **Issue 1: Delete button not showing**
**Solution:** Hard refresh browser (Ctrl+Shift+R)

### **Issue 2: Candidate still appears after deletion**
**Solution:** 
- Check if deletion was successful (check console)
- Refresh the page
- Check database: `SELECT * FROM candidates WHERE id = X;`

### **Issue 3: Error "Candidate already deleted"**
**Solution:** Candidate was already deleted, check database

### **Issue 4: Cannot access deleted candidate**
**Solution:** This is expected behavior - deleted candidates are hidden

---

## **Success Criteria**

- ✅ Delete button appears on both list and detail pages
- ✅ Deletion requires confirmation
- ✅ Deleted candidates disappear from UI immediately
- ✅ Deleted candidates remain in database with audit trail
- ✅ Cannot search or access deleted candidates
- ✅ Can re-upload same candidates with fresh data
- ✅ New extraction shows better data quality

---

## **Next Steps After Testing**

1. **Delete all bad candidates** (Senior Software, malformed data, etc.)
2. **Re-upload resumes** using LLM extraction
3. **Verify candidate detail pages** show correct data
4. **Compare education extraction** - should be much better
5. **Test job hopping analysis** - should show proper risk levels
6. **Close Phase 2** 🎉

---

## **Database Queries for Verification**

```sql
-- View all deleted candidates
SELECT id, full_name, email, deleted_at, deleted_by, deletion_reason
FROM candidates
WHERE is_deleted = TRUE;

-- Count active vs deleted
SELECT 
  SUM(CASE WHEN is_deleted = FALSE THEN 1 ELSE 0 END) as active_count,
  SUM(CASE WHEN is_deleted = TRUE THEN 1 ELSE 0 END) as deleted_count
FROM candidates;

-- View deletion audit trail
SELECT 
  deleted_by,
  COUNT(*) as deletion_count,
  MIN(deleted_at) as first_deletion,
  MAX(deleted_at) as last_deletion
FROM candidates
WHERE is_deleted = TRUE
GROUP BY deleted_by;

-- Restore a specific candidate (if needed)
UPDATE candidates 
SET is_deleted = FALSE, deleted_at = NULL, deleted_by = NULL, deletion_reason = NULL
WHERE id = 1;
```

---

**Ready to test! Start with Test Scenario 1 and work your way through.** 🚀
