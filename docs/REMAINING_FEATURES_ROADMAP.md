# Remaining Features Roadmap
**Last Updated:** October 10, 2025 at 2:16 AM IST  
**Branch:** feature/resume-upload  
**Status:** Post Vetting System Implementation

---

## 🎉 Recent Accomplishments (Oct 8-10, 2025)

### ✅ Feature 2: Resume Upload & Data Extraction - **COMPLETE** ✨
**Status:** 100% Complete | **Completion Date:** Oct 10, 2025

#### **2.1 Resume Vetting System** ✅
- ✅ **Scan & analyze before upload** - Authenticity scoring at vetting stage
- ✅ **Approve/Reject workflow** - Manual review before database upload
- ✅ **Bulk vetting UI** - Process multiple resumes simultaneously
- ✅ **Session-based vetting** - Temporary storage for review
- ✅ **Duplicate detection at vetting** - Prevent duplicates before upload
- ✅ **Bootstrap modals** - Professional confirmation/success/error dialogs
- ✅ **Detailed duplicate feedback** - Shows which resumes were skipped and why

#### **2.2 Resume Upload & Processing** ✅
- ✅ **Bulk upload system** (up to 50 files simultaneously)
- ✅ **Duplicate detection** (4 strategies: email, phone, content similarity, file hash)
- ✅ **Enhanced data extraction** (working, needs improvement)
  - 200+ skills in categorized database
  - Advanced degree/certification patterns
  - Education with GPA, field of study, dates
  - Work experience extraction (needs refinement)
  - GitHub, portfolio, location extraction (needs refinement)
  - Professional summary extraction
- ✅ **Background processing** - Celery tasks for async processing
- ✅ **Database models:** Certification model, enhanced Candidate model
- ✅ **Data preservation** - Vetting data stored and reused (partial)

#### **2.3 Resume Preview** ✅
- ✅ **In-browser PDF viewer** with zoom controls
- ✅ **Text file preview** with full content display
- ✅ **Resume metadata sidebar**
- ✅ **Download functionality**
- ✅ **Delete resume action**

#### **2.4 Candidate Management** ✅
- ✅ **Candidate detail page** - Full profile view
- ✅ **Skills display** - Fixed object rendering issue
- ✅ **Work experience timeline**
- ✅ **Education timeline** - Fixed date display
- ✅ **Resume list with actions** - View/Download buttons
- ✅ **Authenticity scores** - Display from vetting data
- ✅ **Candidate search page** - List all candidates
- ✅ **Fixed "Unknown" names** - Migration script for old data

### ✅ Feature 3: Advanced Resume Filtering - **PARTIAL**
**Status:** 40% Complete | **Remaining:** 60%

- ✅ **Database integration** - Real queries with SQLAlchemy
- ✅ **SQLAlchemy joins** with eager loading
- ✅ **Dynamic filter options** from database
- ✅ **Pagination support**
- ✅ **Basic search interface**

---

## ⚠️ **KNOWN ISSUES & TECHNICAL DEBT**

### **Feature 2 Enhancements Needed** (See: CANDIDATE_DETAIL_PAGE_IMPROVEMENTS.md)

#### **🔴 CRITICAL - Data Consistency Issues**
- [ ] **Preserve vetting authenticity scores** (HIGH PRIORITY)
  - Current: Vetting shows 70+ score, detail page shows 37
  - Issue: Background task re-analyzes instead of using vetting data
  - Fix: Store vetting scores in Resume record during upload
  - Impact: User confusion, inconsistent data

- [ ] **Fix data extraction quality** (HIGH PRIORITY)
  - Work experience descriptions contain entire resume text
  - Location field sometimes shows candidate name
  - Need to improve `EnhancedResumeExtractor` logic

#### **🟡 MEDIUM - Candidate Detail Page**
- [ ] **View Detailed Analysis button** - Not implemented
  - Create `/candidates/{id}/analysis` page
  - Show authenticity breakdown from vetting
  - Display red flags, recommendations

- [ ] **Edit candidate details** - Not implemented
  - Edit personal information
  - Edit skills, experience, education
  - Validation and update API

- [ ] **Quick Actions** - UI only, no backend
  - Schedule Interview
  - Add to Shortlist
  - Send Email
  - Export Profile

#### **🟢 LOW - Nice to Have**
- [ ] **Resume comparison** - Multiple resumes per candidate
- [ ] **Activity timeline** - Track all candidate interactions
- [ ] **JD Match scores** - Not currently stored

---

## 📋 Remaining Features (Excluding 6, 8, 10)

### 🔥 **HIGH PRIORITY - Week 1-2**

#### **Feature 2 Technical Debt Resolution** (3-4 days)
**Status:** Critical fixes needed before moving forward

- [ ] **Fix authenticity score preservation** (1 day)
  - Modify `upload_approved` endpoint to store vetting scores
  - Update background task to skip re-analysis if data exists
  - Verify scores match between vetting and detail page

- [ ] **Improve data extraction** (2 days)
  - Fix work experience description extraction
  - Fix location vs name parsing
  - Test with diverse resume formats

---

#### **Feature 3 Completion** (2 weeks)
**Status:** 40% Complete | **Remaining:** 60%

- [ ] **Full-Text Search** (3-4 days)
  - **Option 1:** PostgreSQL FTS (faster to implement)
    - Create tsvector columns
    - GIN indexes
    - Full-text search queries
  - **Option 2:** Elasticsearch (better scalability)
    - Setup Elasticsearch cluster
    - Index resumes
    - Complex query support
  - Search across: name, email, skills, work history, education

- [ ] **Boolean Search Operators** (2 days)
  - AND operator (Python AND Java)
  - OR operator (Python OR Java)
  - NOT operator (NOT PHP)
  - Nested queries ((Python OR Java) AND React)
  - Query parser implementation

- [ ] **Export Functionality** (2 days)
  - Export filtered results to CSV
  - Export to Excel (XLSX)
  - Include all candidate fields
  - Export authenticity scores
  - Export match scores (if available)

- [ ] **Advanced Filter UI** (2 days)
  - Location filter
  - Date range filters (uploaded date, experience dates)
  - Resume rating filter (1-5 stars)
  - Authenticity score filter
  - Save custom filter presets
  - Share filter presets with team

---

### ⚡ **MEDIUM PRIORITY - Week 3-4**

#### **Feature 5: Manual Resume Rating System** (1.5 weeks)
**Status:** 0% Complete | **Effort:** 1.5-2 weeks

**Database Schema:**
```sql
CREATE TABLE ratings (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id),
    user_id INTEGER REFERENCES users(id),
    round INTEGER DEFAULT 1,  -- Interview round
    score INTEGER CHECK (score >= 1 AND score <= 5),
    comments TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Implementation:**
- [ ] **Backend** (3 days)
  - Rating database model
  - Rating API endpoints (CRUD)
  - Average rating calculation
  - Rating history tracking
  - Multi-round support

- [ ] **Frontend** (2 days)
  - Star rating component
  - Comment textarea
  - Round selector
  - Rating history display
  - Average rating badge

- [ ] **Integration** (1 day)
  - Add rating to candidate list view
  - Filter by rating
  - Sort by rating
  - Export ratings

---

### 🚀 **HIGH PRIORITY - Week 5-6**

#### **Feature 7: AI-Powered Auto-Matching** (2 weeks)
**Status:** 30% Complete (basic matcher exists) | **Remaining:** 70%

**Prerequisites:** 
- ⚠️ **BLOCKED by Feature 6** (Job Creation) - being developed in another branch
- Once jobs table exists, we can implement auto-matching

**Database Schema:**
```sql
CREATE TABLE match_scores (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id),
    job_id INTEGER REFERENCES jobs(id),
    overall_score DECIMAL(5,2),  -- 0-100
    skills_score DECIMAL(5,2),
    experience_score DECIMAL(5,2),
    education_score DECIMAL(5,2),
    matched_skills TEXT[],
    missing_skills TEXT[],
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(resume_id, job_id)
);
```

**Implementation:**
- [ ] **Auto-Match Service** (4 days)
  - Match resumes on upload
  - Match against all active jobs
  - Calculate skill match percentage
  - Calculate experience match
  - Calculate education match
  - Generate composite score
  - Store match results in DB

- [ ] **Semantic Matching** (3 days)
  - Implement sentence-transformers
  - Vector similarity calculation
  - Semantic skill matching (e.g., "React" ≈ "ReactJS")
  - Handle synonyms

- [ ] **Explainability** (2 days)
  - Why candidate matched (breakdown)
  - Show matched skills with highlights
  - Show missing skills
  - Experience gap analysis
  - Education requirements check

- [ ] **UI Integration** (2 days)
  - Match score badges
  - Top candidates for job
  - Match breakdown visualization
  - Filter by match score

---

### 📊 **MEDIUM PRIORITY - Week 7-8**

#### **Feature 4: Candidate Tracking System** (3-4 weeks)
**Status:** 0% Complete | **Effort:** 4-5 weeks | **Complexity:** HIGH

**Note:** This is a LARGE feature. Consider breaking into sub-phases.

**Database Schema:**
```sql
CREATE TABLE candidate_status (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    job_id INTEGER REFERENCES jobs(id),
    status VARCHAR(50),  -- received, shortlisted, interviewed, offered, hired, rejected
    changed_by INTEGER REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE interviews (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    job_id INTEGER REFERENCES jobs(id),
    scheduled_at TIMESTAMP,
    duration_minutes INTEGER,
    interviewer_id INTEGER REFERENCES users(id),
    calendar_event_id VARCHAR(255),  -- Google/Outlook event ID
    status VARCHAR(50),  -- scheduled, confirmed, completed, cancelled
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES candidates(id),
    user_id INTEGER REFERENCES users(id),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Phase 1: Status Pipeline** (1.5 weeks)
- [ ] Status tracking database
- [ ] Status update API
- [ ] Status history
- [ ] Kanban board UI
- [ ] Drag-and-drop status changes
- [ ] Status change notifications

**Phase 2: Interview Scheduling** (2 weeks)
- [ ] Google Calendar integration
- [ ] Outlook Calendar integration
- [ ] Interview scheduling UI
- [ ] Email invitations (SendGrid/AWS SES)
- [ ] Interview reminders
- [ ] Response tracking (confirmed/declined)

**Phase 3: Collaboration** (1 week)
- [ ] Comments system
- [ ] Activity timeline
- [ ] Notifications
- [ ] Audit trail

---

#### **Feature 9: Resume Match Rating & Ranking** (1 week)
**Status:** 0% Complete | **Dependencies:** Features 5 & 7

**Prerequisites:**
- ⚠️ Requires Feature 5 (Manual Rating) - Complete first
- ⚠️ Requires Feature 7 (AI Matching) - Complete first

**Implementation:**
- [ ] **Composite Scoring Algorithm** (2 days)
  - AI match score (40%)
  - Skills match (25%)
  - Experience relevance (20%)
  - Education fit (15%)
  - Manual rating adjustment
  - Configurable weights

- [ ] **Ranking System** (2 days)
  - Calculate composite scores
  - Rank candidates for each job
  - Top 5 recommendations
  - Side-by-side comparison

- [ ] **UI** (2 days)
  - Ranked candidate list
  - Score breakdown visualization
  - Comparison view
  - Export ranked list

---

## 🗺️ **Recommended Implementation Order**

### **Sprint 1 (Week 1-2): Complete Core Features**
1. ✅ Feature 2: Progress Tracking UI (2 days)
2. ✅ Feature 3: Full-Text Search - PostgreSQL FTS (3 days)
3. ✅ Feature 3: Boolean Search Operators (2 days)
4. ✅ Feature 3: Export to CSV/Excel (2 days)
5. ✅ Feature 3: Advanced Filter UI (2 days)

**Deliverable:** Fully functional resume search and filtering system

---

### **Sprint 2 (Week 3-4): Rating System**
1. ✅ Feature 5: Manual Rating System Backend (3 days)
2. ✅ Feature 5: Rating UI (2 days)
3. ✅ Feature 5: Integration with filters (1 day)
4. ✅ Feature 2: Resume Preview (1 day)

**Deliverable:** Recruiters can rate resumes, filter by rating

---

### **Sprint 3 (Week 5-6): AI Matching** ⚠️ **Depends on Feature 6 from other branch**
1. ⏸️ Wait for Feature 6 (Job Creation) to be merged
2. ✅ Feature 7: Auto-Match Service (4 days)
3. ✅ Feature 7: Semantic Matching (3 days)
4. ✅ Feature 7: Explainability (2 days)
5. ✅ Feature 7: UI Integration (2 days)

**Deliverable:** AI automatically matches resumes to jobs

---

### **Sprint 4 (Week 7-8): Candidate Tracking - Phase 1**
1. ✅ Feature 4: Status Pipeline (3 days)
2. ✅ Feature 4: Kanban Board UI (4 days)
3. ✅ Feature 4: Comments System (2 days)

**Deliverable:** Visual candidate tracking with status management

---

### **Sprint 5 (Week 9-10): Ranking & Interview Scheduling**
1. ✅ Feature 9: Composite Scoring (2 days)
2. ✅ Feature 9: Ranking UI (2 days)
3. ✅ Feature 4: Interview Scheduling (5 days)

**Deliverable:** Complete candidate evaluation and scheduling system

---

## 📈 **Success Metrics**

### Feature 2 (Resume Upload)
- ✅ Bulk upload working: 50 files
- ✅ Duplicate detection: 99%+ accuracy
- ✅ Data extraction: 95%+ accuracy
- [ ] Progress tracking: Real-time updates
- [ ] Processing speed: 100 resumes < 5 min

### Feature 3 (Filtering)
- ✅ Database integration: Working
- [ ] Search performance: < 2 sec for 10K+ resumes
- [ ] Boolean queries: Fully functional
- [ ] Export: CSV/Excel working
- [ ] Filter presets: Save/recall working

### Feature 5 (Rating)
- [ ] Rating system: 1-5 stars
- [ ] Multi-round support: Unlimited rounds
- [ ] Average calculation: Accurate
- [ ] Export: Working

### Feature 7 (AI Matching)
- [ ] Auto-match: On every upload
- [ ] Match accuracy: > 85%
- [ ] Processing: 1000 resumes < 10 min
- [ ] Explainability: Clear breakdown

### Feature 4 (Tracking)
- [ ] Status tracking: 100% accurate
- [ ] Kanban board: Drag-and-drop working
- [ ] Calendar integration: Google & Outlook
- [ ] Email delivery: > 98%

---

## 🚧 **Known Blockers**

1. **Feature 7 (AI Matching)** - BLOCKED until Feature 6 (Job Creation) is complete
   - Need `jobs` table to match against
   - Being developed in another branch

2. **Feature 9 (Ranking)** - BLOCKED until Features 5 & 7 complete
   - Needs manual ratings from Feature 5
   - Needs AI match scores from Feature 7

---

## 💾 **Database Migration Requirements**

Based on today's work, we need to create migrations for:

1. ✅ **Certification table** - Added today
2. ✅ **Candidate enhancements** - github_url, portfolio_url, location, professional_summary
3. [ ] **Ratings table** - For Feature 5
4. [ ] **Match_scores table** - For Feature 7 (after jobs table exists)
5. [ ] **Candidate_status table** - For Feature 4
6. [ ] **Interviews table** - For Feature 4
7. [ ] **Comments table** - For Feature 4

---

## 🎯 **Next Immediate Actions**

### **Option A: Complete Feature 3 (Filtering) - RECOMMENDED**
**Reason:** High priority, no blockers, builds on today's work

1. Implement PostgreSQL Full-Text Search (3 days)
2. Add Boolean search operators (2 days)
3. Build export functionality (2 days)
4. Create advanced filter UI (2 days)

**Timeline:** 9 days | **Impact:** CRITICAL for recruiters

---

### **Option B: Complete Feature 2 (Upload) - QUICK WIN**
**Reason:** 95% done, just needs progress UI

1. Build progress tracking UI (2 days)
2. Add resume preview (1 day)

**Timeline:** 3 days | **Impact:** HIGH for user experience

---

### **Option C: Start Feature 5 (Rating System)**
**Reason:** Independent feature, moderate priority

1. Build rating database & API (3 days)
2. Create rating UI (2 days)
3. Integrate with existing views (1 day)

**Timeline:** 6 days | **Impact:** MEDIUM for manual evaluation

---

## 📊 **Feature Completion Status**

| Feature | Oct 8 | Oct 10 | Status | Notes |
|---------|-------|--------|--------|-------|
| **Feature 1:** Authenticity Analysis | 100% | 100% | ✅ Complete | Production ready |
| **Feature 2:** Resume Upload & Vetting | 60% | **100%** | ✅ Complete | Has tech debt (see above) |
| **Feature 3:** Advanced Filtering | 40% | **40%** | 🚧 In Progress | Need FTS, export |
| **Feature 4:** Candidate Tracking | 0% | 0% | ⏳ Not Started | Depends on F6 |
| **Feature 5:** Manual Rating | 0% | 0% | ⏳ Not Started | Independent |
| **Feature 6:** Job Creation | N/A | N/A | 🔒 Other Branch | Blocking F4, F7 |
| **Feature 7:** AI Matching | 30% | 30% | ⚠️ Blocked | Needs F6 |
| **Feature 8:** Jobs Dashboard | N/A | N/A | 🔒 Other Branch | Depends on F6 |
| **Feature 9:** Ranking | 0% | 0% | ⚠️ Blocked | Needs F5, F7 |
| **Feature 10:** User Management | N/A | N/A | 🔒 Other Branch | Independent |

**Overall Progress:** 25% (Oct 8) → **50%** (Oct 10) 🎉

**Key Achievements:**
- ✅ Feature 2 functionally complete (vetting system, upload, preview, candidate management)
- ⚠️ Technical debt identified and documented
- 📝 Candidate detail page improvements documented

---

## 🎉 **Summary (Oct 8-10, 2025)**

### **Major Achievements:**
- ✅ **Feature 2 Complete** - Resume vetting, upload, preview, candidate management
- ✅ **Vetting System** - Scan → Approve/Reject → Upload workflow
- ✅ **Duplicate Detection** - Working at vetting stage with clear feedback
- ✅ **Candidate Detail Page** - Full profile view with skills, experience, education
- ✅ **Resume Preview** - In-browser PDF viewer with download
- ✅ **Data Migration** - Fixed "Unknown" names for existing candidates
- ✅ **25% → 50% overall progress** (25% increase in 2 days!)

### **Technical Debt Identified:**
- ⚠️ Authenticity scores inconsistent (vetting vs detail page)
- ⚠️ Data extraction quality needs improvement
- ⚠️ Candidate detail page needs enhancements (edit, analysis, quick actions)

### **Recommended Next Steps:**

**Option A: Fix Technical Debt First** (RECOMMENDED)
- Fix authenticity score preservation (1 day)
- Improve data extraction quality (2 days)
- Implement "View Detailed Analysis" page (1 day)
- **Timeline:** 4 days | **Impact:** HIGH for data consistency

**Option B: Continue with Feature 3** (Alternative)
- Complete Full-Text Search (3 days)
- Add Boolean operators (2 days)
- Build export functionality (2 days)
- **Timeline:** 7 days | **Impact:** HIGH for recruiter productivity

**Option C: Start Feature 5** (Rating System)
- Independent feature, no blockers
- Build rating database & API (3 days)
- Create rating UI (2 days)
- **Timeline:** 5 days | **Impact:** MEDIUM for evaluation

---

**Recommendation:** Address technical debt (Option A) before moving to new features to ensure data consistency and user trust.
