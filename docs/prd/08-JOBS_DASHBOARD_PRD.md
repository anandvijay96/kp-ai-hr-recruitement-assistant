# PRD: Jobs Dashboard & Management

**Feature ID:** 08  
**Feature Name:** Jobs Dashboard & Management  
**Priority:** P1 (High)  
**Complexity:** Medium  
**Estimated Effort:** 2-3 weeks  
**Phase:** 3 (Job Management & AI)  
**Dependencies:** Features 6, 7

---

## 1. Overview

### 1.1 Description
Centralized dashboard to manage all jobs with pipeline visualization, performance metrics, external job board posting capabilities, and comprehensive analytics.

### 1.2 Business Value
- **Visibility:** Real-time view of all hiring activities
- **Efficiency:** Reduce time managing multiple jobs by 50%
- **Reach:** Auto-post to LinkedIn, Naukri, Indeed
- **Insights:** Data-driven hiring decisions

### 1.3 Success Metrics
- Real-time dashboard updates
- Visual pipeline representation
- Accurate metrics calculation
- External portal integration working
- Export job reports

---

## 2. User Stories

### US-8.1: Jobs Dashboard View
```
As a hiring manager
I want to see all my jobs in one place
So that I can track hiring progress

Acceptance Criteria:
- [ ] See all jobs (draft, open, closed)
- [ ] Filter by status, department, recruiter
- [ ] Sort by date, applicants, urgency
- [ ] Quick stats for each job
- [ ] Visual status indicators
```

### US-8.2: Job Pipeline View
```
As a hiring manager
I want to see candidate pipeline for each job
So that I can track funnel metrics

Acceptance Criteria:
- [ ] Funnel visualization
- [ ] Stages: Applied → Screened → Interview → Offer → Hired
- [ ] Count per stage
- [ ] Conversion rates
- [ ] Bottleneck identification
```

### US-8.3: Job Performance Metrics
```
As a hiring manager
I want to see job performance metrics
So that I can measure hiring effectiveness

Acceptance Criteria:
- [ ] Total applications
- [ ] Shortlisted candidates
- [ ] Interviews scheduled/completed
- [ ] Offers made/accepted
- [ ] Hires completed
- [ ] Time-to-hire
- [ ] Cost-per-hire (if tracked)
```

### US-8.4: External Job Posting
```
As a recruiter
I want to post jobs to external boards
So that I can increase candidate reach

Acceptance Criteria:
- [ ] Post to LinkedIn
- [ ] Post to Naukri
- [ ] Post to Indeed
- [ ] Track posting status
- [ ] Sync applications (if supported)
- [ ] Edit/close external postings
```

### US-8.5: Job Analytics
```
As a hiring manager
I want to see hiring analytics
So that I can optimize our process

Acceptance Criteria:
- [ ] Jobs by status pie chart
- [ ] Applications over time graph
- [ ] Time-to-hire trend
- [ ] Source of hire breakdown
- [ ] Recruiter performance
- [ ] Export analytics report
```

---

## 3. Functional Requirements

### 3.1 Dashboard Components

**FR-8.1.1: Job Cards**
```json
{
    "job_id": 123,
    "title": "Senior Software Engineer",
    "status": "open",
    "department": "Engineering",
    "posted_date": "2025-10-01",
    "closing_date": "2025-11-30",
    "days_open": 35,
    "stats": {
        "total_applicants": 87,
        "new_applicants": 12,
        "shortlisted": 15,
        "interviewed": 8,
        "offers": 2,
        "hires": 0
    },
    "assigned_recruiters": ["Sarah", "Mike"],
    "urgency": "high"  // high, medium, low
}
```

**FR-8.1.2: Pipeline Visualization**
```
Applied (87) → Screened (45) → Interview (15) → Offer (3) → Hired (1)
  100%          52%             17%            3%          1%
```

### 3.2 Metrics Calculation

**FR-8.2.1: Time-to-Hire**
```python
time_to_hire = (hire_date - application_date).days

# Average across all hires for job
avg_time_to_hire = sum(time_to_hire_per_hire) / total_hires
```

**FR-8.2.2: Conversion Rates**
```python
screening_rate = screened / applied * 100
interview_rate = interviewed / screened * 100
offer_rate = offers / interviewed * 100
acceptance_rate = accepted / offers * 100
```

**FR-8.2.3: Cost-per-Hire (Optional)**
```python
cost_per_hire = (
    job_posting_costs +
    recruiter_time_costs +
    interview_time_costs +
    onboarding_costs
) / total_hires
```

### 3.3 External Job Posting

**FR-8.3.1: LinkedIn Integration**
```python
# LinkedIn Jobs API
POST https://api.linkedin.com/v2/jobs
Authorization: Bearer {access_token}

{
    "title": "Senior Software Engineer",
    "description": "...",
    "location": "San Francisco, CA",
    "employmentType": "FULL_TIME",
    "companyId": "1234567"
}
```

**FR-8.3.2: Naukri Integration**
```python
# Naukri API (if available)
# Otherwise: Manual XML/CSV feed
```

**FR-8.3.3: Indeed Integration**
```python
# Indeed Jobs API
POST https://api.indeed.com/v1/jobs
```

**FR-8.3.4: Posting Status Tracking**
```json
{
    "job_id": 123,
    "external_postings": [
        {
            "platform": "LinkedIn",
            "external_id": "ln_job_123",
            "status": "active",
            "posted_at": "2025-10-06",
            "url": "https://linkedin.com/jobs/123",
            "views": 1250,
            "applications": 45
        },
        {
            "platform": "Indeed",
            "external_id": "ind_job_456",
            "status": "active",
            "posted_at": "2025-10-06",
            "url": "https://indeed.com/viewjob?jk=456",
            "views": 890,
            "applications": 32
        }
    ]
}
```

---

## 4. Database Schema

```sql
CREATE TABLE job_external_postings (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    
    platform VARCHAR(50) NOT NULL,  -- linkedin, naukri, indeed
    external_id VARCHAR(255) NOT NULL,
    external_url VARCHAR(500),
    
    status VARCHAR(50) DEFAULT 'active',  -- active, paused, closed
    
    posted_at TIMESTAMP,
    closed_at TIMESTAMP,
    
    -- Metrics (synced from platform)
    views INTEGER DEFAULT 0,
    applications INTEGER DEFAULT 0,
    last_synced_at TIMESTAMP,
    
    posted_by INTEGER REFERENCES users(id),
    
    UNIQUE (job_id, platform),
    INDEX idx_external_postings_job (job_id),
    INDEX idx_external_postings_platform (platform)
);

CREATE TABLE job_metrics (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Candidate counts
    total_applicants INTEGER DEFAULT 0,
    screened_count INTEGER DEFAULT 0,
    interviewed_count INTEGER DEFAULT 0,
    offers_made INTEGER DEFAULT 0,
    offers_accepted INTEGER DEFAULT 0,
    hires_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    
    -- Time metrics (in days)
    avg_time_to_screen DECIMAL(6,2),
    avg_time_to_interview DECIMAL(6,2),
    avg_time_to_offer DECIMAL(6,2),
    avg_time_to_hire DECIMAL(6,2),
    
    -- Conversion rates (percentage)
    screening_rate DECIMAL(5,2),
    interview_rate DECIMAL(5,2),
    offer_rate DECIMAL(5,2),
    acceptance_rate DECIMAL(5,2),
    
    -- Cost (optional)
    total_cost DECIMAL(12,2),
    cost_per_hire DECIMAL(12,2),
    
    -- Last updated
    calculated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (job_id),
    INDEX idx_job_metrics_job (job_id)
);

-- Materialized view for dashboard performance
CREATE MATERIALIZED VIEW mv_jobs_dashboard AS
SELECT 
    j.id,
    j.title,
    j.status,
    j.department,
    j.created_at,
    j.closing_date,
    CURRENT_DATE - j.created_at::date as days_open,
    m.total_applicants,
    m.screened_count,
    m.interviewed_count,
    m.offers_made,
    m.hires_count,
    m.avg_time_to_hire,
    COUNT(DISTINCT jr.user_id) as recruiter_count
FROM jobs j
LEFT JOIN job_metrics m ON j.id = m.job_id
LEFT JOIN job_recruiters jr ON j.id = jr.job_id
GROUP BY j.id, m.id;

CREATE INDEX idx_mv_jobs_dashboard_status ON mv_jobs_dashboard(status);

-- Refresh materialized view periodically
CREATE OR REPLACE FUNCTION refresh_jobs_dashboard()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_jobs_dashboard;
END;
$$ LANGUAGE plpgsql;
```

---

## 5. API Specifications

### 5.1 Get Jobs Dashboard

**Endpoint:** `GET /api/dashboard/jobs`

**Query Parameters:**
```
?status=open
&department=Engineering
&assigned_to=5
&sort_by=applicants_desc
```

**Response:**
```json
{
    "summary": {
        "total_jobs": 45,
        "open_jobs": 32,
        "draft_jobs": 8,
        "closed_jobs": 5,
        "total_applicants": 1250,
        "total_hires": 12
    },
    "jobs": [
        {
            "id": 123,
            "title": "Senior Software Engineer",
            "status": "open",
            "department": "Engineering",
            "days_open": 35,
            "metrics": {
                "applicants": 87,
                "screened": 45,
                "interviewed": 15,
                "offers": 3,
                "hires": 1
            },
            "recruiters": ["Sarah", "Mike"],
            "urgency": "high"
        }
    ]
}
```

### 5.2 Get Job Pipeline

**Endpoint:** `GET /api/jobs/{job_id}/pipeline`

**Response:**
```json
{
    "job_id": 123,
    "pipeline": [
        {
            "stage": "applied",
            "count": 87,
            "percentage": 100
        },
        {
            "stage": "screened",
            "count": 45,
            "percentage": 52,
            "conversion_from_previous": 52
        },
        {
            "stage": "interviewed",
            "count": 15,
            "percentage": 17,
            "conversion_from_previous": 33
        },
        {
            "stage": "offered",
            "count": 3,
            "percentage": 3,
            "conversion_from_previous": 20
        },
        {
            "stage": "hired",
            "count": 1,
            "percentage": 1,
            "conversion_from_previous": 33
        }
    ],
    "avg_time_to_hire": 42
}
```

### 5.3 Post Job to External Platform

**Endpoint:** `POST /api/jobs/{job_id}/post-external`

**Request:**
```json
{
    "platforms": ["linkedin", "indeed"],
    "customizations": {
        "linkedin": {
            "application_url": "https://company.com/apply/123"
        }
    }
}
```

**Response:**
```json
{
    "job_id": 123,
    "postings": [
        {
            "platform": "linkedin",
            "status": "success",
            "external_id": "ln_123",
            "url": "https://linkedin.com/jobs/123"
        },
        {
            "platform": "indeed",
            "status": "success",
            "external_id": "ind_456",
            "url": "https://indeed.com/viewjob?jk=456"
        }
    ]
}
```

### 5.4 Get Analytics

**Endpoint:** `GET /api/analytics/jobs`

**Query Parameters:**
```
?start_date=2025-09-01
&end_date=2025-10-31
&department=Engineering
```

**Response:**
```json
{
    "period": {
        "start": "2025-09-01",
        "end": "2025-10-31"
    },
    "overview": {
        "total_jobs_created": 25,
        "total_applications": 1500,
        "total_hires": 8,
        "avg_time_to_hire": 38
    },
    "by_status": {
        "open": 15,
        "draft": 5,
        "closed": 5
    },
    "applications_over_time": [
        {"date": "2025-09-01", "count": 45},
        {"date": "2025-09-02", "count": 52}
    ],
    "source_of_hire": {
        "internal": 3,
        "linkedin": 3,
        "indeed": 2
    },
    "recruiter_performance": [
        {
            "recruiter": "Sarah",
            "jobs_managed": 10,
            "hires": 5,
            "avg_time_to_hire": 35
        }
    ]
}
```

---

## 6. UI/UX Specifications

### 6.1 Jobs Dashboard

```
┌──────────────────────────────────────────────────────────┐
│ 💼 Jobs Dashboard                       [+ Create Job]   │
│ ┌─────────┬─────────┬─────────┬─────────┬─────────────┐ │
│ │ Total   │ Open    │ Draft   │ Closed  │ Applicants  │ │
│ │   45    │   32    │    8    │    5    │   1,250     │ │
│ └─────────┴─────────┴─────────┴─────────┴─────────────┘ │
├──────────────────────────────────────────────────────────┤
│ Filter: [Open ▼] [Engineering ▼] [All Recruiters ▼]    │
│ Sort: [Most Applicants ▼]                               │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ ┌──────────────────────────────────────────────────────┐│
│ │ 🔴 Senior Software Engineer          [Open] [⚡High]  ││
│ │ Engineering • 35 days open • Closes Nov 30           ││
│ │                                                        ││
│ │ Pipeline: 87 → 45 → 15 → 3 → 1                       ││
│ │ ████████░░░░░░░░                                      ││
│ │                                                        ││
│ │ Recruiters: Sarah, Mike                               ││
│ │ External: LinkedIn (45), Indeed (32)                  ││
│ │                                                        ││
│ │ [View Details] [View Pipeline] [Analytics]            ││
│ └──────────────────────────────────────────────────────┘│
│                                                           │
│ ┌──────────────────────────────────────────────────────┐│
│ │ 🟡 Product Manager                   [Open] [⚡Med]   ││
│ │ Product • 20 days open • Closes Dec 15               ││
│ │                                                        ││
│ │ Pipeline: 45 → 25 → 8 → 2 → 0                        ││
│ │ ████░░░░░░░░░░░░                                      ││
│ │                                                        ││
│ │ [View Details] [View Pipeline] [Analytics]            ││
│ └──────────────────────────────────────────────────────┘│
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 6.2 Job Pipeline View

```
┌──────────────────────────────────────────────────────────┐
│ 📊 Pipeline: Senior Software Engineer                    │
│ Time-to-Hire: 42 days (avg)                             │
├──────────────────────────────────────────────────────────┤
│                                                           │
│   Applied      Screened    Interview   Offer    Hired   │
│     (87)         (45)        (15)       (3)      (1)    │
│      │           │            │          │        │      │
│      ▼           ▼            ▼          ▼        ▼      │
│    ████        ████          ██          █       █       │
│    100%         52%          17%         3%      1%      │
│                                                           │
│    ↓52%        ↓33%         ↓20%       ↓33%             │
│  Conversion   Conversion   Conversion  Conversion        │
│                                                           │
│ ── Key Metrics ──                                         │
│ • Screening Rate: 52% (45/87)                            │
│ • Interview Rate: 33% (15/45)                            │
│ • Offer Rate: 20% (3/15)                                 │
│ • Acceptance Rate: 33% (1/3)                             │
│                                                           │
│ ⚠️ Bottleneck: Interview → Offer (only 20% conversion)  │
│                                                           │
│ [View Candidates] [Export Report]                        │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 6.3 External Posting

```
┌──────────────────────────────────────────────────────────┐
│ 🌐 Post to External Job Boards                           │
│ Job: Senior Software Engineer                            │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Select Platforms:                                        │
│ ☑ LinkedIn                        [Configure →]          │
│   Estimated reach: 10,000 professionals                  │
│   Cost: Free (company page)                              │
│                                                           │
│ ☑ Indeed                          [Configure →]          │
│   Estimated reach: 15,000 job seekers                    │
│   Cost: $5/day (sponsored)                               │
│                                                           │
│ ☐ Naukri                          [Configure →]          │
│   Estimated reach: 8,000 candidates                      │
│   Cost: $10/month                                        │
│                                                           │
│ [Cancel] [Post to Selected Platforms]                    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 7. Implementation Plan

### Week 1: Dashboard Backend
- Database schema for metrics
- Metrics calculation logic
- Dashboard API endpoints
- Materialized views

### Week 2: External Integration
- LinkedIn API integration
- Indeed API integration
- Posting management
- Status sync

### Week 3: UI & Analytics
- Dashboard UI
- Pipeline visualization
- Analytics charts
- Testing

---

**Status:** Ready for Implementation  
**Dependencies:** Features 6, 7  
**External APIs:** LinkedIn, Indeed, Naukri
