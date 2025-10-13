# Testing Instructions - LinkedIn Verification Fix

**📅 Date:** October 13, 2025  
**🎯 Purpose:** Test LinkedIn verification and vet-resumes functionality

---

## ✅ **What Was Fixed:**

### **1. Enabled Selenium LinkedIn Verification**
- Added `USE_SELENIUM_VERIFICATION=true` to `.env`
- This enables DuckDuckGo-based verification (no CAPTCHAs)

### **2. Fixed JD Matching in Vet-Resumes** ⚠️ **CRITICAL FIX**
- **Bug:** `jd_matcher.match()` method doesn't exist
- **Fix:** Changed to `jd_matcher.match_resume_with_jd()` (correct method name)
- **File:** `api/v1/vetting.py` line 114
- JD is passed correctly from frontend (line 266 in vet_resumes.html)
- Matching results are displayed in details panel

### **3. Confirmed Results Display**
- LinkedIn verification details ARE shown (lines 542-662)
- Search terms, search URLs, and matched profiles all displayed
- Same detailed display as upload page

---

## 🧪 **Testing Steps:**

### **Test 1: LinkedIn Verification with DuckDuckGo**

1. **Start the application:**
   ```bash
   cd d:\Projects\BMAD\ai-hr-assistant
   python main.py
   ```

2. **Go to vet-resumes page:**
   ```
   http://localhost:8000/vet-resumes
   ```

3. **Upload a resume** with a clear candidate name (e.g., "Susmitha Addanki")

4. **Check the logs** for these messages:
   ```
   INFO:main:Using Selenium for LinkedIn verification: Susmitha Addanki
   INFO:services.selenium_linkedin_verifier:Navigating to DuckDuckGo: https://duckduckgo.com/?q=...
   INFO:services.selenium_linkedin_verifier:Found LinkedIn link: ...
   ```

5. **Click "View Details" (ℹ️ button)** on the scanned resume

6. **Verify you see:**
   - ✅ "🔍 Online Verification Results"
   - ✅ "✓ Verified via DuckDuckGo"
   - ✅ Search query displayed
   - ✅ "View DuckDuckGo Search" button/link
   - ✅ List of matched LinkedIn profiles

### **Test 2: JD Matching in Vet-Resumes**

1. **Upload resumes** with a job description:
   ```
   Job Description:
   - 5+ years Python experience
   - React.js frontend development
   - AWS cloud experience
   - Team leadership skills
   ```

2. **Scan the resumes**

3. **Click "View Details"** and verify:
   - ✅ "🎯 Job Description Matching Analysis" section appears
   - ✅ Overall match percentage shown
   - ✅ Skills match, Experience match, Education match displayed
   - ✅ Matched skills shown in green badges
   - ✅ Missing skills shown in red badges

### **Test 3: Compare with Upload Page**

1. **Go to upload page:**
   ```
   http://localhost:8000/upload
   ```

2. **Upload the SAME resume** with the SAME JD

3. **Compare results:**
   - ✅ LinkedIn verification details should match
   - ✅ Search terms should be the same
   - ✅ Matched profiles should be the same
   - ✅ JD matching scores should be similar

---

## 📊 **Expected Results:**

### **LinkedIn Verification Section:**

```
🔗 Professional Profile Analysis

📄 Not Found in Resume
No LinkedIn URL detected in the resume. However, we found a profile through online search (see below).

🔍 Online Verification Results
✓ Verified  via DuckDuckGo

Verification Source:
🔍 View DuckDuckGo Search: "Susmitha Addanki susmithaaddanki007@gmail.com LinkedIn"

Matched LinkedIn Profile(s):
💼 linkedin.com/in/susmitha-addanki-a44b5b47
💼 linkedin.com/pub/dir
💼 linkedin.com/in/susmitha-addanki-ab0b81212

💡 Why this matters: HR can click the verification link to confirm this is the correct person and not someone with a similar name.
```

### **JD Matching Section:**

```
🎯 Job Description Matching Analysis

Overall Match: 75%

Skills Match: 80%
Experience Match: 70%
Education Match: 75%

✓ Matched Skills (5):
Python  React  AWS  JavaScript  Docker

✗ Missing Skills (2):
Kubernetes  GraphQL
```

---

## 🐛 **Troubleshooting:**

### **Issue: No LinkedIn verification happening**

**Check:**
1. `.env` has `USE_SELENIUM_VERIFICATION=true`
2. Logs show "Using Selenium for LinkedIn verification"
3. Chrome/Chromium is installed: `which chromium-browser` or `which google-chrome`

**Fix:**
```bash
# Install Chrome (if missing)
sudo apt-get update
sudo apt-get install chromium-browser

# Or install Chrome driver
pip install webdriver-manager
```

### **Issue: "ModuleNotFoundError: No module named 'selenium'"**

**Fix:**
```bash
pip install selenium beautifulsoup4
```

### **Issue: DuckDuckGo search not working**

**Check logs for:**
- Timeout errors
- Network errors
- CAPTCHA challenges (shouldn't happen with DuckDuckGo)

**Try:**
- Increase timeout in `selenium_linkedin_verifier.py` (line 255)
- Check internet connection
- Verify DuckDuckGo is accessible: `curl https://duckduckgo.com`

### **Issue: JD matching not showing**

**Check:**
1. Job description was entered in the text area
2. Logs show "JD matching if job description provided"
3. `matching_result` is not None in scan result

---

## 📝 **Test Checklist:**

- [ ] `.env` has `USE_SELENIUM_VERIFICATION=true`
- [ ] Application starts without errors
- [ ] Can access vet-resumes page
- [ ] Can upload resumes
- [ ] LinkedIn verification runs (check logs)
- [ ] Search query is displayed
- [ ] DuckDuckGo search link works
- [ ] Matched profiles are shown
- [ ] JD matching works when JD is provided
- [ ] Matching scores are displayed
- [ ] Results match upload page display

---

## 🚀 **After Successful Testing:**

1. **Commit changes:**
   ```bash
   git add .env
   git commit -m "Enable Selenium LinkedIn verification for DuckDuckGo search"
   ```

2. **Push to mvp-1:**
   ```bash
   git push origin mvp-1
   ```

3. **Update production `.env` in Dokploy:**
   - Add `USE_SELENIUM_VERIFICATION=true`
   - Redeploy application

4. **Test on production:**
   - Upload resume on `http://158.69.219.206/vet-resumes`
   - Verify LinkedIn verification works
   - Verify search terms are displayed

---

## 📞 **Need Help?**

If LinkedIn verification still doesn't work after these steps:

1. Share the application logs (especially lines with "LinkedIn" or "Selenium")
2. Share a screenshot of the results display
3. Confirm Chrome/Chromium version: `chromium-browser --version`
4. Check if Selenium can start: `python -c "from selenium import webdriver; print('OK')"`

---

**Start testing now! The fix should restore all LinkedIn verification functionality with DuckDuckGo search.** 🎯
