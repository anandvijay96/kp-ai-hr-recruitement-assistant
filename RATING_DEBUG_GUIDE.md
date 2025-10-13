# Rating System - Debugging Guide

## 🐛 **ISSUE: Nothing happens when clicking "Save Rating"**

### **✅ FIXES APPLIED:**

1. **Enhanced Console Logging**
   - Added console.log at every step
   - Shows button click event
   - Shows candidate ID
   - Shows payload being sent
   - Shows API response

2. **Better Error Handling**
   - Check if candidate ID exists
   - Show specific error messages
   - Display error details in alert

3. **Visual Feedback**
   - Button changes to "Saving..." with spinner
   - Button disabled during save
   - Button re-enabled after completion

---

## 🔍 **HOW TO DEBUG:**

### **Step 1: Open Browser Console**
1. Press **F12** (or right-click → Inspect)
2. Click **Console** tab
3. Clear console (trash icon)

### **Step 2: Try Saving Rating**
1. Fill out the rating form
2. Click "Save Rating"
3. Watch the console output

### **Expected Console Output:**
```
Save Rating button clicked!
Candidate ID: abc-123-def-456
Rating payload: {candidate_id: "abc-123-def-456", technical_skills: 4, ...}
Sending request to: /api/v1/candidates/abc-123-def-456/rate
Response status: 200
Success: {id: "rating-123", message: "Rating created successfully"}
```

---

## 🚨 **COMMON ISSUES & FIXES:**

### **Issue 1: "Candidate ID not found"**
**Symptom:** Alert says "Candidate ID not found. Please refresh the page."

**Cause:** `window.currentCandidateId` is undefined

**Fix:**
1. Refresh the page
2. Check if candidate details loaded properly
3. Check console for errors during page load

---

### **Issue 2: Network Error**
**Symptom:** Console shows "Error saving rating: Failed to fetch"

**Cause:** API server not running or CORS issue

**Fix:**
1. Check if server is running: `http://localhost:8000`
2. Check terminal for errors
3. Restart server: `python main.py`

---

### **Issue 3: 401 Unauthorized**
**Symptom:** Response status: 401

**Cause:** User not logged in

**Fix:**
1. Make sure you're logged in
2. Check session cookie
3. Try logging out and back in

---

### **Issue 4: 404 Not Found**
**Symptom:** Response status: 404

**Cause:** API endpoint not registered or wrong URL

**Fix:**
1. Check if ratings router is registered in `main.py`
2. Verify URL: `/api/v1/candidates/{id}/rate`
3. Check server logs for routing errors

---

### **Issue 5: 500 Internal Server Error**
**Symptom:** Response status: 500

**Cause:** Server-side error (database, validation, etc.)

**Fix:**
1. Check server terminal for error traceback
2. Check database connection
3. Verify candidate exists in database

---

## 🧪 **TESTING CHECKLIST:**

### **Test 1: Basic Save**
- [ ] Click "Add Rating" button
- [ ] Rate all 4 categories (click stars)
- [ ] Select recommendation
- [ ] Add comment
- [ ] Click "Save Rating"
- [ ] See "Saving..." button text
- [ ] See success alert
- [ ] Modal closes
- [ ] Rating appears in summary

### **Test 2: Minimal Save**
- [ ] Click "Add Rating"
- [ ] Rate only 1 category
- [ ] Don't fill other fields
- [ ] Click "Save Rating"
- [ ] Should still save successfully

### **Test 3: Console Logging**
- [ ] Open browser console
- [ ] Click "Save Rating"
- [ ] See all console.log messages
- [ ] No errors in console

### **Test 4: Multiple Ratings**
- [ ] Save first rating
- [ ] Click "Add Rating" again
- [ ] Save second rating
- [ ] Both should appear in history

---

## 📊 **WHAT TO CHECK IN CONSOLE:**

### **Good Output:**
```javascript
Save Rating button clicked!
Candidate ID: "550e8400-e29b-41d4-a716-446655440000"
Rating payload: {
  candidate_id: "550e8400-e29b-41d4-a716-446655440000",
  technical_skills: 4,
  communication: 3,
  culture_fit: 4,
  experience_level: 4,
  recommendation: "maybe",
  comments: "TEst",
  strengths: "test",
  concerns: "test"
}
Sending request to: /api/v1/candidates/550e8400-e29b-41d4-a716-446655440000/rate
Response status: 200
Success: {id: "...", overall_rating: 4, message: "Rating created successfully"}
```

### **Bad Output (No Click Event):**
```javascript
(nothing appears when clicking button)
```
**Fix:** jQuery not loaded or button selector wrong

### **Bad Output (No Candidate ID):**
```javascript
Save Rating button clicked!
Candidate ID: undefined
```
**Fix:** Page didn't load candidate data properly

### **Bad Output (Network Error):**
```javascript
Save Rating button clicked!
Candidate ID: "..."
Rating payload: {...}
Sending request to: /api/v1/candidates/.../rate
Error saving rating: Failed to fetch
```
**Fix:** Server not running or network issue

---

## 🔧 **SERVER-SIDE DEBUGGING:**

### **Check Server Logs:**
Look for these in the terminal:

**Good:**
```
INFO:     127.0.0.1:xxxxx - "POST /api/v1/candidates/abc-123/rate HTTP/1.1" 200 OK
```

**Bad (404):**
```
INFO:     127.0.0.1:xxxxx - "POST /api/v1/candidates/abc-123/rate HTTP/1.1" 404 Not Found
```
**Fix:** Router not registered

**Bad (500):**
```
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  ...
```
**Fix:** Check error traceback for specific issue

---

## 🎯 **QUICK FIXES:**

### **Fix 1: Hard Refresh**
```
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

### **Fix 2: Clear Cache**
```
F12 → Network tab → Disable cache (checkbox)
```

### **Fix 3: Check jQuery**
```javascript
// In console, type:
typeof $
// Should return: "function"
```

### **Fix 4: Check Bootstrap**
```javascript
// In console, type:
typeof bootstrap
// Should return: "object"
```

### **Fix 5: Manual API Test**
```javascript
// In console, paste this:
fetch('/api/v1/candidates/YOUR_CANDIDATE_ID/rate', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    candidate_id: 'YOUR_CANDIDATE_ID',
    technical_skills: 4,
    overall_rating: 4
  })
}).then(r => r.json()).then(console.log);
```

---

## ✅ **CURRENT STATUS:**

**Changes Made:**
- ✅ Added extensive console logging
- ✅ Added candidate ID validation
- ✅ Added visual feedback (Saving... button)
- ✅ Added better error messages
- ✅ Added button disable/enable

**Next Steps:**
1. Refresh the page (Ctrl+Shift+R)
2. Open browser console (F12)
3. Try saving a rating
4. Check console output
5. Report what you see in console

---

## 📞 **WHAT TO REPORT:**

If still not working, please provide:

1. **Console Output:** Copy all console.log messages
2. **Network Tab:** Check if request was sent (F12 → Network)
3. **Server Logs:** Copy terminal output
4. **Error Messages:** Any alerts or errors shown

---

**Server restarted with enhanced logging. Please try again!** 🚀
