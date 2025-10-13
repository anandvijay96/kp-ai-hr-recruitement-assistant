# Dokploy Redeployment Steps - LinkedIn Verification

**📅 Date:** October 13, 2025 - 6:02 PM IST  
**🎯 Critical:** Chrome installation added to Dockerfile

---

## ⚠️ **IMPORTANT:**

The latest commit (`2a7bc00`) adds **Google Chrome** to the Docker container using modern GPG method.  
**This is REQUIRED for LinkedIn verification to work in production.**

### **Recent Fixes:**
- `2a7bc00` - Fixed apt-key deprecation (use gpg instead)
- `a47216b` - Added Chrome installation
- `01315e5` - LinkedIn verification fixes

---

## 🚀 **Step-by-Step Deployment:**

### **Step 1: Add Environment Variable**

In Dokploy dashboard:

1. Go to your application
2. Click **"Environment"** tab
3. Add new variable:
   - **Name:** `USE_SELENIUM_VERIFICATION`
   - **Value:** `true`
4. Click **"Save"**

---

### **Step 2: Rebuild and Redeploy**

**IMPORTANT:** You must **rebuild** the Docker image (not just restart) because we added Chrome to the Dockerfile.

In Dokploy:

1. Go to your application
2. Click **"Deploy"** or **"Redeploy"** button
3. **Wait 5-10 minutes** (Chrome installation takes time)
4. Monitor the build logs

---

### **Step 3: Verify Chrome Installation**

Check the build logs for:

```
✓ Installing google-chrome-stable
✓ Chrome installed successfully
```

---

### **Step 4: Check Application Logs**

After deployment completes, check logs for:

```
✅ Selenium LinkedIn verifier initialized
Google Search verification enabled for LinkedIn profile checks
```

**Should NOT see:**
```
❌ /bin/sh: 1: google-chrome: not found
```

---

### **Step 5: Test LinkedIn Verification**

1. Go to: `http://158.69.219.206/vet-resumes`
2. Upload a resume (e.g., `Naukri_NatikalaShivaShankar[7y_4m].docx`)
3. Click "Scan Resumes for Authenticity"
4. Wait for scan to complete
5. Click "View Details" (ℹ️ button)

**Expected Results:**
```
✅ Online Verification Results
✓ Verified via DuckDuckGo

Verification Source:
🔍 View DuckDuckGo Search: "Natikala Shiva Shankar ... LinkedIn"

Matched LinkedIn Profile(s):
💼 linkedin.com/in/...
```

---

### **Step 6: Check Production Logs**

After uploading a resume, check Dokploy logs for:

```
INFO:api.v1.vetting:✅ Using name from filename: Natikala Shiva Shankar
INFO:services.resume_analyzer:Using Selenium for LinkedIn verification: Natikala Shiva Shankar
INFO:services.selenium_linkedin_verifier:Initializing Chrome WebDriver...
INFO:services.selenium_linkedin_verifier:Using local Chrome/Chromium
INFO:services.selenium_linkedin_verifier:Navigating to DuckDuckGo: https://duckduckgo.com/?q=...
INFO:services.selenium_linkedin_verifier:Found LinkedIn link: linkedin.com/in/...
```

**Should NOT see:**
```
❌ ERROR: Failed to initialize WebDriver: 'NoneType' object has no attribute 'split'
❌ /bin/sh: 1: google-chrome: not found
```

---

## 📊 **What Changed:**

### **Commit a47216b - Dockerfile Update:**
```dockerfile
# Added Chrome installation
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable
```

---

## ⏱️ **Expected Build Time:**

- **Normal build:** 2-3 minutes
- **With Chrome installation:** 5-10 minutes (first time)
- **Subsequent builds:** 3-5 minutes (cached layers)

---

## 🐛 **Troubleshooting:**

### **Issue: Build fails with "Unable to locate package google-chrome-stable"**

**Solution:**
- Check internet connectivity from Dokploy server
- Verify Google's repository is accessible
- Try rebuilding (may be temporary network issue)

### **Issue: Still seeing "google-chrome: not found"**

**Solution:**
- Verify the build completed successfully
- Check if Chrome was actually installed in build logs
- Try a full rebuild (clear cache)

### **Issue: "WebDriver initialization failed"**

**Solution:**
- Check Chrome version: `google-chrome --version`
- Verify webdriver-manager is installed: `pip list | grep webdriver-manager`
- Check logs for specific error message

---

## ✅ **Success Checklist:**

After deployment, verify:

- [ ] Build completed without errors
- [ ] Chrome installed in container
- [ ] Application starts successfully
- [ ] Environment variable `USE_SELENIUM_VERIFICATION=true` is set
- [ ] Logs show "Selenium LinkedIn verifier initialized"
- [ ] Can access `/vet-resumes` page
- [ ] Can upload resumes
- [ ] LinkedIn verification runs (check logs)
- [ ] Search query is displayed in results
- [ ] DuckDuckGo search link works
- [ ] Matched profiles are shown
- [ ] No "google-chrome: not found" errors

---

## 🎉 **Expected Result:**

**LinkedIn verification will work exactly like in local testing:**
- Name extracted from filename
- DuckDuckGo search performed
- Search terms displayed with clickable link
- Matched LinkedIn profiles shown

---

## 📞 **If Issues Persist:**

1. Share the **build logs** (especially Chrome installation part)
2. Share the **application logs** (after uploading a resume)
3. Verify Chrome is installed: Run command in container: `google-chrome --version`
4. Check if webdriver-manager can find Chrome: `python -c "from selenium import webdriver; print('OK')"`

---

**Rebuild and redeploy now to enable LinkedIn verification in production!** 🚀
