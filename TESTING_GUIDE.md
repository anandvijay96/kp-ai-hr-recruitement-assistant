# HR Dashboard Testing Guide
**Quick Start Guide for Testing the New Dashboard**

---

## 🚀 Quick Start

### 1. Start the Application (WSL)
```bash
cd /path/to/ai-hr-assistant
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Open in Browser
```
http://localhost:8000/
```

### 3. What to Expect

**If you're logged in:**
- You'll see the new HR Dashboard with:
  - 4 stat cards showing metrics
  - Quick action buttons
  - 4 widget cards with data
  - Real-time data from your database

**If you're not logged in:**
- You'll be redirected to the login page
- After login, you'll see the dashboard

---

## 🧪 Testing Checklist

### Visual Tests
- [ ] Dashboard loads without errors
- [ ] Purple gradient navbar at top
- [ ] 4 stat cards display correctly
- [ ] Quick actions section visible
- [ ] All 4 widgets show up
- [ ] No console errors (F12 → Console)

### Functional Tests
- [ ] Click "Vet Resumes" → Goes to `/vet-resumes`
- [ ] Click "Upload Resume" → Goes to `/upload`
- [ ] Click "Search Candidates" → Goes to `/candidates`
- [ ] Click "Create Job" → Goes to `/jobs/create`
- [ ] Click "View All" links in widgets → Navigate correctly
- [ ] Candidate cards are clickable
- [ ] Job cards are clickable

### Data Tests
- [ ] Stats show real numbers from database
- [ ] Pending vetting shows unvetted resumes
- [ ] Recent candidates show latest additions
- [ ] Activity feed shows recent actions
- [ ] Empty states show when no data

### Responsive Tests
- [ ] Resize browser to mobile size
- [ ] Stat cards stack vertically
- [ ] Widgets stack on small screens
- [ ] Navigation collapses to hamburger menu

---

## 🐛 If Something Doesn't Work

### Dashboard doesn't load
**Check:**
1. Is the app running? Look for errors in terminal
2. Open browser console (F12) - any errors?
3. Try: `http://localhost:8000/landing` to see old page

### API returns errors
**Check:**
1. Database connection working?
2. Check terminal for error messages
3. Try API directly: `http://localhost:8000/api/v1/dashboard/hr`

### No data showing
**Possible causes:**
1. Database is empty - Upload some resumes first
2. API endpoint not returning data
3. JavaScript error - Check browser console

### Widgets show "Loading..." forever
**Fix:**
1. Check browser console for errors
2. Verify API endpoint is accessible
3. Check network tab (F12 → Network) for failed requests

---

## 📊 Expected Data

### Quick Stats
- **Total Candidates:** Count of all candidates in database
- **Pending Vetting:** Resumes without authenticity score
- **Shortlisted:** Candidates with status = "shortlisted"
- **Active Jobs:** Currently shows 8 (mock data)

### Pending Vetting Widget
- Shows up to 10 resumes that haven't been vetted
- Each item shows: name, time uploaded, position
- "Review" button goes to vetting page

### Recent Candidates Widget
- Shows up to 10 most recently added candidates
- Each shows: name, score, status, position, time
- Color-coded score badges (green/yellow/red)
- Clickable to go to candidate detail page

### Active Jobs Widget
- Currently shows mock data (3 jobs)
- Will show real jobs once Job model is integrated
- Each shows: title, candidate count, days open, department

### Recent Activity Widget
- Shows up to 20 recent activities
- Types: uploads, vetting, status changes
- Sorted by most recent first
- Color-coded icons by activity type

---

## 🔍 Debugging Tips

### Check API Response
```bash
# In browser or curl
curl http://localhost:8000/api/v1/dashboard/hr
```

Should return JSON like:
```json
{
  "stats": {
    "total_candidates": 245,
    "pending_vetting": 12,
    "shortlisted": 38,
    "active_jobs": 8
  },
  "pending_vetting": [...],
  "recent_candidates": [...],
  "active_jobs": [...],
  "recent_activity": [...]
}
```

### Check Browser Console
```
F12 → Console tab
Look for:
- Red errors
- Failed network requests
- JavaScript exceptions
```

### Check Network Requests
```
F12 → Network tab
Filter: XHR
Look for:
- /api/v1/dashboard/hr request
- Status should be 200
- Response should have data
```

---

## ✅ Success Criteria

Dashboard is working correctly if:
1. ✅ Page loads without errors
2. ✅ Stats show real numbers
3. ✅ At least one widget shows data
4. ✅ Quick actions navigate correctly
5. ✅ No console errors
6. ✅ Responsive on mobile

---

## 📞 Need Help?

**Common Issues:**

**Issue:** "Module not found: dashboard"
**Fix:** Make sure `api/v1/dashboard.py` exists

**Issue:** Database errors
**Fix:** Check database connection in `core/database.py`

**Issue:** Empty widgets
**Fix:** Upload some test data first

**Issue:** 404 on dashboard route
**Fix:** Restart the app to reload routes

---

## 🎯 Next Steps After Testing

1. **If it works:** Great! Move on to updating other templates
2. **If issues:** Document them and we'll fix together
3. **Feedback:** Note what you like/don't like about the design

---

**Happy Testing! 🚀**
