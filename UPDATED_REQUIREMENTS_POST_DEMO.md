# Updated Requirements Post-Demo (October 15, 2025)

**Status:** New requirements received from management  
**Impact:** High - Affects multiple phases  
**Priority:** Integrate into existing 6-week plan

---

## 🎯 NEW REQUIREMENTS FROM DEMO FEEDBACK

### **1. USER ACTIVITY TRACKING & REPORTING** 🆕
**Priority:** HIGH  
**Requested By:** Management

#### **Requirement:**
Track how HR team (recruiters) are utilizing the platform and provide monitoring capabilities for admins.

#### **What to Track:**
- **Login Activity:**
  - Login/logout timestamps
  - Session duration
  - Login frequency (daily/weekly/monthly)
  
- **Resume Processing:**
  - Number of resumes uploaded
  - Number of resumes vetted (approved/rejected)
  - Time spent per resume
  - Vetting decision patterns
  
- **Candidate Management:**
  - Candidates viewed
  - Candidates contacted
  - Status changes made
  - Ratings provided
  
- **Job Management:**
  - Jobs created
  - Jobs modified
  - Job applications processed
  
- **Search Activity:**
  - Number of searches performed
  - Search filters used
  - Search result click-through rates

#### **Reporting Requirements:**
- **Daily Reports:**
  - Activity summary
  - Key metrics (resumes vetted, candidates contacted)
  - Anomaly detection (unusually low/high activity)
  
- **Weekly Reports:**
  - Productivity trends
  - Comparison with team average
  - Top performers
  
- **Monthly Reports:**
  - Comprehensive performance review
  - Monthly statistics
  - Goal achievement tracking
  - Export to PDF/Excel

#### **Admin Dashboard Features:**
- Real-time activity monitoring
- Individual recruiter performance metrics
- Team-wide analytics
- Activity heatmaps (by hour/day/week)
- Contribution leaderboard
- Alerts for inactivity

#### **Implementation Needs:**
1. **Database Tables:**
   - `user_activity_log` (detailed event tracking)
   - `user_daily_stats` (aggregated daily metrics)
   - `user_weekly_stats` (aggregated weekly metrics)
   - `user_monthly_stats` (aggregated monthly metrics)

2. **API Endpoints:**
   - GET `/api/v1/admin/user-activity/{user_id}`
   - GET `/api/v1/admin/user-stats/{user_id}?period=daily|weekly|monthly`
   - GET `/api/v1/admin/team-analytics`
   - GET `/api/v1/admin/activity-report?start_date=X&end_date=Y`
   - POST `/api/v1/admin/export-report` (PDF/Excel)

3. **UI Pages:**
   - Admin User Activity Dashboard
   - Individual User Performance Page
   - Team Analytics Page
   - Report Generation & Export Page

#### **Privacy Considerations:**
- Track work-related activity only
- No keystroke logging or screenshot capture
- Transparent to users (they should know they're being tracked)
- GDPR/privacy compliance

---

### **2. EDUCATION VERIFICATION** 🆕
**Priority:** MEDIUM  
**Challenge:** LinkedIn scraping will get us blocked

#### **Requirement:**
Verify candidate's year of passing (education completion date) without scraping LinkedIn.

#### **Current Problem:**
- HR team manually checks LinkedIn for education dates
- Automated scraping = account blocks
- Need alternative verification method

#### **Proposed Solutions:**

**Option 1: Resume-Based Verification (RECOMMENDED)**
- Extract education dates from resume during vetting
- Compare against claimed dates
- Flag discrepancies for manual review
- Confidence score for date extraction

**Option 2: Third-Party Verification APIs**
- Integrate with education verification services:
  - **National Student Clearinghouse** (USA)
  - **Hedd** (UK)
  - **India Stack / DigiLocker** (India)
- Paid APIs but official verification
- Requires candidate consent

**Option 3: Email Verification**
- Verify using university email domains
- Check if `@university.edu` email is valid
- Works for recent graduates only

**Option 4: Document Upload**
- Request scanned degree/transcript upload
- OCR to extract dates
- Compare with resume claims
- Manual verification by HR

**Option 5: Hybrid Approach (BEST)**
1. Extract dates from resume (primary)
2. Cross-reference with uploaded documents (secondary)
3. Optionally use verification API (tertiary)
4. Flag major discrepancies (>2 years difference)
5. Manual review for flagged cases

#### **Implementation:**
- Add `education_verification_status` field to candidates
- Add `education_documents` table for uploaded proofs
- Add verification workflow to vetting process
- Display verification status in candidate profile

#### **Decision Needed:**
- Which verification method to implement?
- Budget for third-party APIs?
- Level of verification required (basic vs thorough)?

---

### **3. MULTI-TENANT ARCHITECTURE** 🆕
**Priority:** HIGH  
**Impact:** Major architectural change

#### **Requirement:**
Separate logins and data access for Vendors and Clients with strict data isolation.

#### **Access Control Requirements:**

**A. VENDOR USERS:**
- **Login:** Separate vendor portal (`/vendor/login`)
- **Dashboard:** Vendor-specific dashboard
- **Candidates:**
  - ✅ View ONLY candidates they submitted
  - ❌ Cannot see candidates from other vendors
  - ❌ Cannot see internal candidates
  - ✅ Can edit their own candidates
  - ✅ Can see status updates for their candidates
- **Jobs:**
  - ✅ View all open jobs (to submit candidates)
  - ✅ See job requirements
  - ❌ Cannot create/edit/delete jobs
- **Reports:**
  - ✅ Own submission statistics
  - ✅ Acceptance/rejection rates
  - ❌ Cannot see company-wide data

**B. CLIENT USERS:**
- **Login:** Separate client portal (`/client/login`)
- **Dashboard:** Client-specific dashboard
- **Jobs:**
  - ✅ View ONLY their own jobs
  - ❌ Cannot see jobs of other clients
  - ✅ Can create new job requisitions
  - ✅ Can edit their own jobs
  - ✅ Can see applicant statistics for their jobs
- **Candidates:**
  - ✅ View candidates applied to their jobs
  - ✅ See candidate profiles (approved ones only)
  - ❌ Cannot see all candidates in database
  - ✅ Can shortlist/reject candidates
- **Reports:**
  - ✅ Job-specific analytics
  - ✅ Hiring pipeline metrics
  - ❌ Cannot see other clients' data

**C. INTERNAL HR TEAM:**
- **Login:** Main portal (`/login`)
- **Dashboard:** Full admin dashboard
- **Candidates:**
  - ✅ View ALL candidates (internal, vendor-submitted, client-submitted)
  - ✅ Full CRUD operations
  - ✅ Assign to jobs
  - ✅ Vet and approve
- **Jobs:**
  - ✅ View ALL jobs (all clients)
  - ✅ Full CRUD operations
  - ✅ Assign candidates
- **Reports:**
  - ✅ Complete system-wide analytics
  - ✅ Vendor performance metrics
  - ✅ Client satisfaction metrics

#### **Database Schema Changes:**

**1. Add Tenant Identification:**
```sql
-- Add to candidates table
ALTER TABLE candidates ADD COLUMN submitted_by_vendor_id VARCHAR(36);
ALTER TABLE candidates ADD COLUMN submitted_by_user_id VARCHAR(36);
ALTER TABLE candidates ADD COLUMN is_internal BOOLEAN DEFAULT TRUE;

-- Add to jobs table
ALTER TABLE jobs ADD COLUMN client_id VARCHAR(36);
ALTER TABLE jobs ADD COLUMN created_by_client BOOLEAN DEFAULT FALSE;
```

**2. Add Vendor Table:**
```sql
CREATE TABLE vendors (
    id VARCHAR(36) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    status VARCHAR(50) DEFAULT 'active',
    commission_rate DECIMAL(5,2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**3. Add Client Table:**
```sql
CREATE TABLE clients (
    id VARCHAR(36) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    contact_person VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    address TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**4. Update Users Table:**
```sql
ALTER TABLE users ADD COLUMN user_type VARCHAR(20) DEFAULT 'internal';
-- user_type: 'internal', 'vendor', 'client'
ALTER TABLE users ADD COLUMN vendor_id VARCHAR(36);
ALTER TABLE users ADD COLUMN client_id VARCHAR(36);
```

#### **Implementation Requirements:**

**1. Authentication & Authorization:**
- Separate login endpoints for each user type
- Role-based access control (RBAC)
- Row-level security (RLS) for data isolation
- JWT tokens with user_type claim

**2. API Layer:**
- Middleware to enforce tenant isolation
- Query filters based on user_type
- Prevent cross-tenant data leakage

**3. UI Layer:**
- Separate portals with different layouts
- Context-aware navigation (based on user_type)
- Tenant-specific branding (optional)

**4. Testing:**
- Security testing for data isolation
- Penetration testing to prevent unauthorized access
- Test all edge cases (user switching roles, etc.)

---

### **4. JOB HOPPING CRITERIA** 🆕
**Priority:** MEDIUM  
**Category:** Vetting Enhancement

#### **Requirement:**
Add job hopping detection as a vetting criteria (currently missing from vetting system).

#### **What is Job Hopping?**
Multiple job changes in short periods indicating instability.

#### **Detection Rules:**

**Rule 1: Tenure Threshold**
- Job duration < 12 months = Red flag
- Job duration < 18 months = Yellow flag
- 2+ jobs < 12 months in last 5 years = Job hopper

**Rule 2: Pattern Detection**
- 3+ jobs in 3 years = Frequent job changer
- 4+ jobs in 5 years = Job hopper

**Rule 3: Career Level Adjustments**
- **Junior (<3 years exp):** More lenient (1-2 year stints acceptable)
- **Mid-level (3-7 years):** Moderate (2+ year stints expected)
- **Senior (7+ years):** Strict (3+ year stints expected)

**Rule 4: Exceptions (Don't penalize):**
- Contract/Freelance work (if labeled as such)
- Layoffs (if mentioned in resume)
- Company closures
- Startups (known for shorter tenures)
- Career changes (switching industries)

#### **Scoring Impact:**

**Severity Levels:**
- **Low Risk (Score: -5):** 1 short stint in otherwise stable career
- **Medium Risk (Score: -15):** 2 short stints in last 5 years
- **High Risk (Score: -30):** 3+ short stints, pattern of job hopping
- **Critical (Score: -50):** Extreme job hopping (5+ jobs in 3 years)

**Auto-Reject vs Penalize:**
- **Recommendation:** PENALIZE, don't auto-reject
- Reduce overall score but allow manual review
- Display prominently in vetting UI
- HR can override if candidate explains situation

#### **UI Display:**
```
⚠️ Job Hopping Alert: High Risk (-30 points)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 4 jobs in last 5 years
• Average tenure: 13 months
• Pattern detected: Frequent job changes

Recent Work History:
├─ Company D (Current): 8 months
├─ Company C: 11 months
├─ Company B: 15 months
└─ Company A: 18 months

⚠️ Consider asking about:
- Reasons for frequent changes
- Career goals and stability
- Long-term commitment
```

#### **Implementation:**
1. Add `job_hopping_score` to vetting results
2. Add `tenure_analysis` field with detailed breakdown
3. Update vetting algorithm to calculate job hopping risk
4. Add UI component to display job hopping analysis
5. Allow manual override with comment

---

## 📋 CLARIFICATIONS ON EXISTING VETTING CRITERIA

### **1. LinkedIn Profile Validation**

#### **Decision Required:**
- **Basic Check (RECOMMENDED):** Just verify URL exists and is accessible
- **Advanced Check:** Validate it's active (requires API calls, costs $$$)

**Recommendation:**
- Check URL format and accessibility (free)
- Don't verify if profile is active (expensive, rate-limited)
- Consider integrating LinkedIn API later if budget allows

#### **Alternative Profiles:**
**Question:** Accept GitHub, portfolio, personal website?

**Recommendation:** ✅ YES
- Accept professional profiles as alternatives:
  - GitHub (for developers)
  - Behance (for designers)
  - Medium (for content creators)
  - Personal portfolio websites
- Weight slightly lower than LinkedIn (e.g., LinkedIn = 10 points, Others = 7 points)
- But don't penalize if they have strong professional presence elsewhere

---

### **2. Capitalization Consistency**

#### **Decision Required:**
**Ignore proper nouns and acronyms?**

**Recommendation:** ✅ YES
- Whitelist common proper nouns:
  - Technologies: JavaScript, TypeScript, AWS, GCP, Azure, React, Node.js
  - Companies: Google, Microsoft, Amazon, Facebook, Apple
  - Locations: New York, San Francisco, Bangalore, Mumbai
- Whitelist common acronyms:
  - MBA, PhD, CEO, CTO, HR, IT, AI, ML, DevOps
- Only flag inconsistency in regular text (e.g., "worked at GOOGLE" vs "worked at google")

**Threshold for "Inconsistent":**
- **Lenient:** >20% of text has inconsistent capitalization
- **Moderate (RECOMMENDED):** >15% inconsistent
- **Strict:** >10% inconsistent

---

### **3. Job Hopping Rules**

#### **Auto-Reject or Penalize?**
**Recommendation:** PENALIZE, don't auto-reject
- Reduce score significantly but allow manual review
- Different situations require different handling

#### **Junior vs Senior:**
**Recommendation:** ✅ YES, different rules
- **Junior (<3 years):** Allow 1-2 year stints
- **Mid-level (3-7 years):** Expect 2+ year stints
- **Senior (7+ years):** Expect 3+ year stints

#### **Contract/Freelance Work:**
**Recommendation:** Don't count against job hopping
- Detect if labeled as "Contract", "Freelance", "Consultant"
- Exclude from job hopping calculation
- But mention in summary for context

---

### **4. Career Gaps**

#### **Affect Fake/Real Score?**
**Recommendation:** NO, don't affect authenticity score
- Career gaps don't indicate fake resume
- Many legitimate reasons (health, family, education, travel)
- Common for women (maternity leave, childcare)

**However:**
- ✅ Display prominently in UI for manual review
- ✅ Highlight gaps > 6 months
- ✅ Ask candidate to explain in interview
- ❌ Don't reduce authenticity score

#### **UI Display:**
```
ℹ️ Career Gap Detected: 14 months
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gap Period: Jan 2020 - Mar 2021
Duration: 14 months

💡 Common reasons (for reference):
• Personal/health issues
• Further education/certifications
• Family responsibilities
• Career transition/exploration
• Pandemic-related layoff

⚠️ Recommend asking candidate during interview
```

---

### **5. Scoring Thresholds**

#### **Decision Required:**
Option A: Lenient (Score >= 70 = Qualified, < 50 = Reject, 50-70 = Review)  
Option B: Strict (Score >= 80 = Qualified, < 60 = Reject)

**Recommendation:** MODERATE (between A and B)
- **Score >= 75:** ✅ **Auto-Qualified** (green badge)
- **Score 60-74:** ⚠️ **Manual Review Required** (yellow badge)
- **Score < 60:** ❌ **Likely Reject** (red badge, but not auto-reject)

**Rationale:**
- Lenient enough to not reject good candidates with minor issues
- Strict enough to filter out obvious fakes
- Large "manual review" zone (60-74) for edge cases
- HR always has final decision (no auto-reject)

**Score Breakdown Example:**
```
Overall Score: 68 / 100 ⚠️ Manual Review

✅ LinkedIn Present: +10
✅ Email Valid: +10
✅ Phone Valid: +10
⚠️ Capitalization Issues: -5
⚠️ Job Hopping Detected: -15
✅ Education Verified: +10
✅ Skills Match: +20
⚠️ Career Gap (1 year): 0 (no penalty)
✅ No Red Flags: +28

Recommendation: REVIEW - Candidate has job hopping 
history but otherwise solid profile. Recommend interview
to understand job changes.
```

---

### **6. False Positives Handling**

#### **Edge Cases to Handle:**

**A. Career Changers**
- Person switching from teaching to tech (low skills match)
- **Solution:** Don't penalize if resume explains career change
- Detect phrases: "career change", "transitioning to", "pivoting to"

**B. Returning Parents**
- Long career gap (2-3 years) for childcare
- **Solution:** Don't penalize gaps for this reason
- Detect phrases: "maternity leave", "childcare", "family responsibilities"

**C. Recent Graduates**
- No work experience, only education
- **Solution:** Separate scoring for entry-level candidates
- Lower experience weight, higher education weight

**D. International Candidates**
- Different date formats, name formats
- **Solution:** Support international formats in extraction
- Don't penalize formatting differences

**E. Freelancers/Consultants**
- Multiple short projects (looks like job hopping)
- **Solution:** Detect freelance/contract keywords
- Treat differently from regular employment

#### **Manual Override:**
**Recommendation:** ✅ YES, must have
- HR can override any vetting decision
- Require comment explaining override
- Track override patterns (if one HR overrides frequently, may need training)

**UI Feature:**
```
┌─────────────────────────────────────────┐
│ Override Vetting Decision               │
├─────────────────────────────────────────┤
│ Current Score: 58 (Likely Reject)      │
│                                         │
│ Override to: [Qualified ▼]             │
│                                         │
│ Reason (required):                      │
│ ┌─────────────────────────────────────┐ │
│ │ Candidate explained job hopping was │ │
│ │ due to startup closures. Has strong │ │
│ │ skills and good interview presence. │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Cancel]  [Override & Approve]         │
└─────────────────────────────────────────┘
```

---

## 📊 UPDATED 6-WEEK IMPLEMENTATION PLAN

### **PHASE 1: Core Fixes** ✅ COMPLETE
- Week 1-2: Fix filters, improve extraction

### **PHASE 2: Clients & Vendors**
- Week 3: UPDATED WITH MULTI-TENANT

**Original Plan:**
- Clients management module
- Vendors management module

**Updated Plan:**
- ✅ Clients management module
- ✅ Vendors management module
- 🆕 Multi-tenant architecture implementation
- 🆕 Separate login portals
- 🆕 Data isolation layer
- 🆕 Role-based access control

**Estimated Time:** 4-5 days (was 3 days)

### **PHASE 3: Enhanced Candidate Features**
- Week 4: UPDATED WITH VETTING ENHANCEMENTS

**Original Plan:**
- Candidate status workflow
- Interview scheduling
- Email templates

**Updated Plan:**
- ✅ Candidate status workflow
- ✅ Interview scheduling
- ✅ Email templates
- 🆕 Job hopping detection in vetting
- 🆕 Education verification workflow
- 🆕 Enhanced vetting criteria with clarifications
- 🆕 Manual override UI

**Estimated Time:** 4-5 days (was 3 days)

### **PHASE 4: Reporting & User Management**
- Week 5: HEAVILY UPDATED

**Original Plan:**
- User management & RBAC
- Advanced analytics
- Export functionality

**Updated Plan:**
- ✅ User management & enhanced RBAC (internal/vendor/client roles)
- ✅ Advanced analytics
- ✅ Export functionality
- 🆕 **USER ACTIVITY TRACKING SYSTEM** (major addition)
- 🆕 Real-time activity monitoring
- 🆕 Daily/weekly/monthly reports
- 🆕 Admin monitoring dashboard
- 🆕 Productivity analytics
- 🆕 Team performance metrics

**Estimated Time:** 5-6 days (was 2-3 days) - SIGNIFICANT INCREASE

### **PHASE 5: Production Ready**
- Week 6: AS PLANNED
- Performance optimization
- Security audit (CRITICAL with multi-tenant)
- Documentation

---

## 🎯 UPDATED PRIORITY MATRIX

### **MUST HAVE (P0):**
1. ✅ Fix candidate filters (COMPLETE)
2. ✅ Improve resume extraction (COMPLETE)
3. 🆕 Multi-tenant architecture (Vendors/Clients login)
4. 🆕 User activity tracking & reporting
5. Clients management module
6. Vendors management module

### **SHOULD HAVE (P1):**
7. 🆕 Job hopping detection in vetting
8. 🆕 Education verification workflow
9. Enhanced candidate workflow
10. Interview scheduling
11. User management & RBAC

### **NICE TO HAVE (P2):**
12. Email templates & automation
13. Advanced analytics
14. Export functionality
15. Performance optimization

---

## 📅 REVISED TIMELINE

### **Week 1-2: Phase 1** ✅ COMPLETE
- Candidate filters
- Resume extraction improvements

### **Week 3: Phase 2 (Extended)**
**Day 1-2:**
- Multi-tenant database schema
- Authentication layer for vendors/clients

**Day 3-4:**
- Clients management module
- Client portal UI

**Day 5:**
- Vendors management module
- Vendor portal UI

### **Week 4: Phase 3 (Expanded)**
**Day 1-2:**
- Job hopping detection algorithm
- Education verification workflow
- Enhanced vetting UI

**Day 2-3:**
- Candidate status workflow
- Interview scheduling

**Day 4-5:**
- Email templates
- Manual override functionality

### **Week 5: Phase 4 (MAJOR)**
**Day 1-2:**
- User activity tracking infrastructure
- Activity logging middleware

**Day 3:**
- Daily/weekly/monthly report generation
- Report export (PDF/Excel)

**Day 4-5:**
- Admin monitoring dashboard
- Team analytics page

### **Week 6: Phase 5**
**Day 1-2:**
- Performance optimization
- Query optimization
- Caching

**Day 3:**
- Security audit
- Penetration testing
- Multi-tenant security validation

**Day 4-5:**
- Documentation
- Deployment preparation
- Training materials

---

## 💰 BUDGET CONSIDERATIONS

### **Third-Party Services (Optional):**
1. **Education Verification APIs:**
   - National Student Clearinghouse: $2-5 per verification
   - Budget: $500-1000/month for moderate usage

2. **LinkedIn API (Optional):**
   - LinkedIn Talent Solutions: $500-2000/month
   - Only if we want active profile verification

### **Development Time:**
- Original estimate: 6 weeks
- Revised estimate: 6-7 weeks (same timeline, more features, tighter sprint)

---

## ❓ DECISIONS NEEDED FROM MANAGEMENT

### **1. Education Verification:**
- [ ] Which method to implement? (Resume-based vs API vs Hybrid)
- [ ] Budget for third-party verification APIs?
- [ ] Level of verification required?

### **2. Job Hopping:**
- [ ] Auto-reject or penalize? (Recommend: PENALIZE)
- [ ] Threshold for "job hopper"? (Recommend: 3+ jobs in 3 years)

### **3. Scoring Thresholds:**
- [ ] Lenient vs Strict? (Recommend: MODERATE - 75/60 cutoffs)
- [ ] Auto-reject at low scores? (Recommend: NO, always manual review)

### **4. LinkedIn Validation:**
- [ ] Basic check or API integration? (Recommend: Basic check only)
- [ ] Accept alternative profiles? (Recommend: YES)

### **5. Multi-Tenant:**
- [ ] When to start? (Recommend: Week 3 - Phase 2)
- [ ] Custom branding per tenant? (Optional, can be Phase 6)

### **6. Activity Tracking:**
- [ ] Level of detail to track? (Recommend: Moderate - no keystroke logging)
- [ ] Privacy policy updates needed?
- [ ] Inform users about tracking?

---

## 📝 NEXT STEPS

### **Immediate (After Phase 1 Testing):**
1. Get management decisions on above questions
2. Finalize education verification approach
3. Confirm multi-tenant architecture requirements
4. Start Phase 2 with updated requirements

### **Documentation Updates:**
1. Update API documentation with new endpoints
2. Create multi-tenant security guidelines
3. Document activity tracking implementation
4. Create admin training materials

---

## ✅ CHECKLIST FOR MANAGEMENT REVIEW

- [ ] Review new requirements (Activity Tracking, Multi-tenant, Education Verification)
- [ ] Approve budget for third-party APIs (if needed)
- [ ] Confirm vetting criteria decisions (job hopping, scoring, LinkedIn)
- [ ] Approve extended Phase 4 timeline (user activity tracking)
- [ ] Confirm priority order (if any changes needed)
- [ ] Sign off on multi-tenant security requirements
- [ ] Approve privacy policy for activity tracking

---

**Document Created:** October 15, 2025  
**Last Updated:** October 15, 2025  
**Status:** Awaiting Management Decisions  
**Next Review:** After Phase 1 deployment testing
