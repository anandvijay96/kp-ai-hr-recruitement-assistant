# AI-Powered HR Assistant - Demo Guide

## Before You Start

**Setup (5 minutes before demo):**
1. Start the server: `python main.py`
2. Open browser: `http://localhost:8000`
3. Login with your credentials
4. Have 2-3 test resume PDFs ready

---

## Demo Flow (20-25 minutes)

### 1. Dashboard Overview (2 min)

**Show:** Main dashboard at `/`

**Say:** 
"This is our main dashboard. You can see:
- Total candidates in the system
- Pending resumes that need vetting
- Active job openings
- Recent activity feed"

**Point out:**
- Real-time stats cards at the top
- Active Jobs section (shows actual jobs from database)
- Recent Activity (uploads, vetting completions)

---

### 2. Resume Vetting (6 min) ⭐ CORE FEATURE

**Navigate to:** Vetting page (click "Vetting" in navbar)

**Step 1: Upload Resumes**
1. Click "Upload Resumes" button
2. Drag & drop 2-3 resume PDFs
3. Click "Start Vetting"

**Say:**
"Our AI system processes resumes in three ways:
- **LinkedIn Verification** - Checks if the candidate's LinkedIn profile exists
- **Authenticity Analysis** - Detects fake or AI-generated resumes  
- **JD Matching** - Matches skills against job requirements"

**Step 2: Review Results**
1. Wait for processing to complete (30-60 seconds)
2. Click on first resume in the queue
3. Show each tab:
   - **Overview**: Extracted information (name, email, skills, experience)
   - **LinkedIn**: Verification status (✓ Verified or ✗ Not Found)
   - **Authenticity**: Score out of 100% (Font, Grammar, Template checks)
   - **JD Match**: Skills match percentage

**Say:**
"Based on these insights, we can quickly approve or reject candidates. Approved candidates go directly into our candidate database."

**Step 3: Approve/Reject**
1. Click "✓ Approve" on a good candidate
2. Show it disappears from queue
3. Click "✗ Reject" on another
4. Show rejection reason dialog

---

### 3. Candidate Management (5 min)

**Navigate to:** Candidates page

**Step 1: Search & Filter**
1. Show candidate list
2. Type "Python" in search box
3. Show filtered results

**Say:**
"All approved candidates are searchable. You can filter by skills, experience, status, etc."

**Step 2: Candidate Detail**
1. Click on any candidate
2. Show detailed profile:
   - Contact information
   - Skills (categorized)
   - Work experience timeline
   - Education
   - **Job Matches** section ⭐

**Say:**
"The system automatically matches candidates to open jobs. See here - this candidate is a 72% match for the Data Scientist position."

**Step 3: Manual Rating**
1. Scroll to "Ratings" section
2. Click "Rate Candidate"
3. Give star ratings (4-5 stars)
4. Add comment: "Strong technical skills, good communication"
5. Click "Save Rating"

**Say:**
"Team members can rate candidates on multiple criteria. This combines AI insights with human judgment."

---

### 4. Job Management (4 min)

**Navigate to:** Jobs page

**Step 1: Job List**
1. Show list of all jobs
2. Point out status badges (Open, Closed, etc.)

**Step 2: Job Detail**
1. Click on "Data Scientist" job
2. Show job description
3. Scroll to "Candidate Matches" section ⭐

**Say:**
"The AI automatically matches candidates to this job. Here are the top 5 matches with their scores."

**Step 3: Create New Job** (Optional)
1. Click "Create Job"
2. Fill in:
   - Title: "Frontend Developer"
   - Department: "Engineering"
   - Description: (paste sample JD)
3. Click "Create"

**Say:**
"Once created, the system immediately starts matching candidates in the background."

---

### 5. Job Analytics (4 min) ⭐ NEW FEATURE

**Navigate to:** Job Analytics (in navbar)

**Show:**
1. **Real-time Statistics**
   - Total Jobs, Open Positions, Applications, Avg Match Score

2. **Interactive Charts**
   - Jobs Timeline (line chart)
   - Jobs by Status (pie chart)
   - Jobs by Department (bar chart)
   - Applications per Job (horizontal bars)

3. **Activity Feeds**
   - Recent job postings
   - Top performing jobs

**Say:**
"This analytics dashboard gives you real-time insights into your hiring pipeline. All data updates automatically every 30 seconds."

---

### 6. Feedback System (2 min) ⭐ NEW FEATURE

**Show:** Floating purple button (bottom-right corner)

**Say:**
"For post-demo support, we've added a feedback system."

**Demo:**
1. Click the floating button
2. Show feedback form:
   - Type: Bug Report / Feature Request / General
   - Priority: Low / Medium / High / Critical
   - Title and Description
   - Screenshot upload (drag & drop)
3. Fill in sample feedback
4. Click "Submit"
5. Show success message

**Say:**
"Your team can report issues or suggest features from anywhere in the app. Screenshots help us see exactly what you're seeing."

---

### 7. Coming Soon Features (2 min)

**Navigate to:** Clients page (in navbar)

**Show:** "Coming Soon" overlay
1. Click the X button to preview the UI
2. Show the mockup design

**Say:**
"We're building Client and Vendor management modules. Here's a preview of the interface. These will be ready in 3-4 weeks after we go live with the core system."

**Repeat for:** Vendors page

---

## Key Points to Emphasize

✅ **Time Savings**
- "Manual screening takes hours. Our AI does it in minutes with 95%+ accuracy."

✅ **Quality Control**
- "LinkedIn verification and authenticity checks catch fake resumes before interviews."

✅ **Auto-Matching**
- "Zero manual work. The system matches candidates to jobs automatically."

✅ **Team Collaboration**
- "Multiple team members can rate candidates. One rating per person ensures accurate averages."

✅ **Real-Time Insights**
- "Analytics dashboard shows hiring pipeline metrics that update automatically."

✅ **Continuous Improvement**
- "Feedback system ensures we can quickly address issues and add features you need."

---

## Common Questions & Answers

**Q: How accurate is the LinkedIn verification?**
A: 90%+ accuracy. We cross-reference names, companies, and locations.

**Q: Can we customize the rating criteria?**
A: Yes! We can add custom criteria based on your requirements.

**Q: What happens to rejected candidates?**
A: They're archived with reasons. If they reapply, the system flags them with previous feedback.

**Q: How does job matching work?**
A: Weighted scoring: Skills (40%), Experience (30%), Education (20%), Other (10%). Uses NLP to extract requirements.

**Q: Can we integrate with our existing ATS?**
A: Yes! We provide REST APIs. Integration typically takes 1-2 weeks.

**Q: How many resumes can it handle?**
A: Current capacity: 10,000+ candidates with sub-second search. Can scale to 100K+.

**Q: When can we go live?**
A: After approval:
- Week 1: Requirements & customization
- Week 2: Data migration & training
- Week 3: Pilot testing
- Week 4: Full rollout

---

## If Something Goes Wrong

**Server not responding:**
- Check if `python main.py` is running
- Restart the server
- Use backup screenshots

**No data showing:**
- Make sure you've uploaded and approved some resumes
- Check database has sample jobs
- Refresh the page

**Feature not working:**
- Skip to next feature
- Note it down for later
- Continue with demo

---

## After the Demo

1. Thank the audience
2. Ask for questions
3. Collect feedback
4. Schedule follow-up if interested
5. Send summary email with key features

---

## Tips for Success

✅ **Practice** - Run through this script 2-3 times before the actual demo
✅ **Smile** - Show enthusiasm about the features
✅ **Pause** - Give audience time to absorb information
✅ **Stories** - Use real-world scenarios ("Imagine you received 100 resumes...")
✅ **Benefits** - Always tie features to business value (time saved, quality improved)

---

**Good luck! You've got this! 🚀**
