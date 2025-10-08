# Feature 8: Jobs Management - Product Requirements Document

**Document Version**: 1.0  
**Last Updated**: 2025-10-08  
**Status**: Draft  
**Owner**: Product Team  

---

## 1. OVERVIEW

### Description
Jobs Management is a comprehensive job lifecycle management system that provides HR teams with centralized control over all job postings, from creation through archival. It includes real-time analytics, status management, bulk operations, and external portal integration capabilities.

### Problem Statement
Current challenges in job management:
- **Scattered Information**: Job data and analytics are fragmented across multiple screens
- **Manual Tracking**: No automated status updates or archival processes
- **Limited Visibility**: Lack of real-time insights into job performance and application pipeline
- **Inefficient Operations**: No bulk operations for managing multiple jobs simultaneously
- **Manual Posting**: Jobs must be manually posted to external portals (LinkedIn, Naukri, Indeed)
- **Audit Gaps**: No comprehensive audit trail for job modifications and status changes

### Target Users

1. **HR Recruiters** (Primary)
   - Manage day-to-day job postings
   - Monitor application pipeline
   - Track job performance metrics

2. **HR Admins** (Primary)
   - Full administrative control including deletions
   - Bulk operations management
   - System-wide job oversight

3. **Hiring Managers** (Secondary)
   - View job analytics for their departments
   - Monitor application progress
   - Read-only access to job metrics

---

## 2. USER STORIES

### Story 1: Centralized Job Dashboard
**As a** HR Recruiter  
**I want** to view all jobs in a centralized dashboard with key metrics and filters  
**So that** I can quickly assess the status and performance of all active job postings without navigating multiple pages

### Story 2: Job Status Management
**As a** HR Admin  
**I want** to update job statuses (open/closed/on-hold/archived) with automated rules  
**So that** I can maintain accurate job states and prevent applications to closed positions

### Story 3: Job Analytics and Insights
**As a** Hiring Manager  
**I want** to view detailed analytics for each job including application funnel metrics  
**So that** I can make data-driven decisions about job requirements and recruitment strategies

### Story 4: Bulk Operations
**As a** HR Admin  
**I want** to perform bulk status updates on multiple jobs simultaneously  
**So that** I can efficiently manage seasonal hiring campaigns or organizational changes

### Story 5: External Portal Integration
**As a** HR Recruiter  
**I want** to post jobs to external portals (LinkedIn, Naukri, Indeed) from within the system  
**So that** I can maximize job visibility without manually re-entering job details on multiple platforms

### Story 6: Audit Trail
**As a** HR Admin  
**I want** to view a complete audit log of all job modifications and status changes  
**So that** I can maintain compliance and track accountability for job management actions

---

## 3. ACCEPTANCE CRITERIA

### Story 1: Centralized Job Dashboard

**Functional Requirements**:
- [ ] Dashboard displays all jobs with: title, department, status, posted date, application count, match score
- [ ] Filter by: status, department, date range, hiring manager
- [ ] Sort by: date posted, application count, match score, status
- [ ] Search by: job title, job ID, keywords
- [ ] Pagination: 20 jobs per page with infinite scroll option
- [ ] Quick actions: Edit, View Analytics, Change Status, Duplicate
- [ ] Visual status indicators (color-coded badges)
- [ ] Export to CSV/Excel functionality

**Non-Functional Requirements**:
- Dashboard loads in < 2 seconds with 1000+ jobs
- Real-time updates for application counts (WebSocket or 30s polling)
- Responsive design for tablet and desktop
- Accessible (WCAG 2.1 AA compliant)

### Story 2: Job Status Management

**Functional Requirements**:
- [ ] Manual status transitions: Open → Closed, Open → On-Hold, On-Hold → Open, Closed → Archived
- [ ] Confirmation dialog for status changes with reason field (optional)
- [ ] Automated rules:
  - Auto-close jobs after application deadline passes
  - Auto-archive jobs 90 days after closure
  - Prevent applications to closed/archived jobs
- [ ] Status change notifications to job creator and hiring manager
- [ ] Bulk status update (max 50 jobs)
- [ ] Status history timeline on job detail page

**Non-Functional Requirements**:
- Status updates processed in < 500ms
- Automated rules run daily at 2 AM UTC
- Transaction safety: rollback on failure for bulk operations

### Story 3: Job Analytics and Insights

**Functional Requirements**:
- [ ] Analytics dashboard per job showing:
  - **Funnel Metrics**: Views → Applications → Shortlisted → Interviewed → Offers → Hires
  - **Time Metrics**: Average time-to-fill, time-to-first-application
  - **Quality Metrics**: Average match score, acceptance rate
  - **Trend Charts**: Applications over time, match score distribution
- [ ] Date range selector (7d, 30d, 90d, custom)
- [ ] Comparison with similar jobs (same department/role)
- [ ] Export analytics report as PDF
- [ ] Downloadable applicant list with match scores

**Non-Functional Requirements**:
- Analytics calculated daily and cached
- Real-time metrics: view count, application count
- Charts render in < 1 second
- Historical data retained for 2 years

### Story 4: Bulk Operations

**Functional Requirements**:
- [ ] Multi-select checkbox on dashboard (max 50 jobs)
- [ ] Bulk actions:
  - Update status
  - Change hiring manager
  - Update application deadline
  - Archive jobs
  - Export selected jobs
- [ ] Preview changes before confirmation
- [ ] Progress indicator for bulk operations
- [ ] Error handling: partial success with detailed error report
- [ ] Undo capability for last bulk operation (within 5 minutes)

**Non-Functional Requirements**:
- Process 50 jobs in < 10 seconds
- Atomic operations: all or nothing for critical updates
- Background job processing for operations > 10 jobs
- Email notification on completion

### Story 5: External Portal Integration

**Functional Requirements**:
- [ ] "Post to External Portals" button on job detail page
- [ ] Portal selection: LinkedIn, Naukri, Indeed (multi-select)
- [ ] Field mapping configuration per portal
- [ ] Preview job posting before submission
- [ ] Track posting status: Pending, Posted, Failed
- [ ] Store external job IDs for reference
- [ ] Sync application status from external portals (optional)
- [ ] Repost/update existing external postings

**Non-Functional Requirements**:
- API integration with OAuth 2.0 authentication
- Retry logic: 3 attempts with exponential backoff
- Timeout: 30 seconds per portal
- Error logging and admin notifications

### Story 6: Audit Trail

**Functional Requirements**:
- [ ] Audit log captures:
  - Status changes (old → new, reason, timestamp, user)
  - Field modifications (job title, description, requirements, etc.)
  - Bulk operations
  - External portal postings
  - Deletions (soft delete with restoration capability)
- [ ] Audit log viewer: filterable by date, user, action type
- [ ] Export audit log as CSV
- [ ] Immutable log entries (append-only)

**Non-Functional Requirements**:
- Audit entries created synchronously with actions
- Retention: 7 years for compliance
- Indexed for fast querying
- Tamper-proof (cryptographic hashing)

---

## 4. TECHNICAL DESIGN

### Database Schema

#### Table: `job_analytics`
```sql
CREATE TABLE job_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Funnel Metrics
    view_count INTEGER DEFAULT 0,
    application_count INTEGER DEFAULT 0,
    shortlist_count INTEGER DEFAULT 0,
    interview_count INTEGER DEFAULT 0,
    offer_count INTEGER DEFAULT 0,
    hire_count INTEGER DEFAULT 0,
    
    -- Quality Metrics
    avg_match_score DECIMAL(5,2),
    median_match_score DECIMAL(5,2),
    
    -- Time Metrics
    time_to_fill INTEGER, -- days from posting to hire
    time_to_first_application INTEGER, -- hours
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(job_id, date),
    INDEX idx_job_analytics_job_id (job_id),
    INDEX idx_job_analytics_date (date)
);
```

#### Table: `job_status_history`
```sql
CREATE TABLE job_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    reason TEXT,
    changed_by UUID NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_job_status_history_job_id (job_id),
    INDEX idx_job_status_history_changed_at (changed_at)
);
```

#### Table: `job_external_postings`
```sql
CREATE TABLE job_external_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    portal VARCHAR(50) NOT NULL, -- 'linkedin', 'naukri', 'indeed'
    external_job_id VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- 'pending', 'posted', 'failed', 'expired'
    posted_at TIMESTAMP,
    expires_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB, -- portal-specific data
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(job_id, portal),
    INDEX idx_job_external_postings_job_id (job_id),
    INDEX idx_job_external_postings_status (status)
);
```

#### Table: `job_audit_log`
```sql
CREATE TABLE job_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL, -- 'create', 'update', 'status_change', 'delete', 'bulk_update'
    entity_type VARCHAR(50) NOT NULL, -- 'job', 'job_status', 'external_posting'
    old_values JSONB,
    new_values JSONB,
    user_id UUID NOT NULL REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    checksum VARCHAR(64), -- SHA-256 hash for tamper detection
    
    INDEX idx_job_audit_log_job_id (job_id),
    INDEX idx_job_audit_log_timestamp (timestamp),
    INDEX idx_job_audit_log_user_id (user_id),
    INDEX idx_job_audit_log_action_type (action_type)
);
```

#### Table: `bulk_operations`
```sql
CREATE TABLE bulk_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_type VARCHAR(50) NOT NULL, -- 'status_update', 'archive', 'update_deadline'
    job_ids UUID[] NOT NULL,
    parameters JSONB NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'pending', 'processing', 'completed', 'failed', 'partial'
    total_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    error_details JSONB,
    initiated_by UUID NOT NULL REFERENCES users(id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_bulk_operations_status (status),
    INDEX idx_bulk_operations_initiated_by (initiated_by)
);
```

#### Modifications to Existing `jobs` Table
```sql
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'open';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_archived_at ON jobs(archived_at);
```

### API Endpoints

#### 1. Dashboard Endpoint
```
GET /api/jobs-management/dashboard
```

**Query Parameters**:
- `status`: Filter by status (open, closed, on-hold, archived)
- `department`: Filter by department
- `hiring_manager_id`: Filter by hiring manager
- `date_from`, `date_to`: Date range filter
- `search`: Search query
- `sort_by`: Sort field (created_at, application_count, match_score)
- `sort_order`: asc/desc
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "id": "uuid",
      "title": "Senior Software Engineer",
      "department": "Engineering",
      "status": "open",
      "posted_date": "2025-09-15T10:00:00Z",
      "application_deadline": "2025-11-15T23:59:59Z",
      "application_count": 45,
      "avg_match_score": 78.5,
      "hiring_manager": {
        "id": "uuid",
        "name": "John Doe"
      },
      "external_postings": ["linkedin", "naukri"],
      "last_updated": "2025-10-01T14:30:00Z"
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "limit": 20,
    "total_pages": 8
  },
  "summary": {
    "total_jobs": 150,
    "open": 45,
    "closed": 80,
    "on_hold": 15,
    "archived": 10
  }
}
```

#### 2. Update Job Status
```
PUT /api/jobs-management/{job_id}/status
```

**Request Body**:
```json
{
  "status": "closed",
  "reason": "Position filled internally"
}
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "status": "closed",
  "closed_at": "2025-10-08T10:18:00Z",
  "message": "Job status updated successfully"
}
```

**Validation Rules**:
- Valid status transitions only
- Reason required for closure
- Admin role required for archival

#### 3. Get Job Analytics
```
GET /api/jobs-management/{job_id}/analytics
```

**Query Parameters**:
- `date_from`, `date_to`: Date range (default: last 30 days)

**Response** (200 OK):
```json
{
  "job_id": "uuid",
  "date_range": {
    "from": "2025-09-08",
    "to": "2025-10-08"
  },
  "funnel": {
    "views": 1250,
    "applications": 45,
    "shortlisted": 12,
    "interviewed": 8,
    "offers": 3,
    "hires": 2
  },
  "conversion_rates": {
    "view_to_application": 3.6,
    "application_to_shortlist": 26.7,
    "shortlist_to_interview": 66.7,
    "interview_to_offer": 37.5,
    "offer_to_hire": 66.7
  },
  "quality_metrics": {
    "avg_match_score": 78.5,
    "median_match_score": 82.0,
    "match_score_distribution": {
      "90-100": 5,
      "80-89": 15,
      "70-79": 18,
      "60-69": 7
    }
  },
  "time_metrics": {
    "time_to_fill_days": 32,
    "time_to_first_application_hours": 4,
    "avg_time_to_shortlist_days": 5
  },
  "trends": [
    {
      "date": "2025-09-08",
      "applications": 2,
      "views": 45
    }
  ],
  "comparison": {
    "similar_jobs_avg_match_score": 75.2,
    "similar_jobs_avg_time_to_fill": 38
  }
}
```

#### 4. Bulk Update Jobs
```
POST /api/jobs-management/bulk-update
```

**Request Body**:
```json
{
  "job_ids": ["uuid1", "uuid2", "uuid3"],
  "operation": "status_update",
  "parameters": {
    "status": "on-hold",
    "reason": "Budget review pending"
  }
}
```

**Response** (202 Accepted):
```json
{
  "operation_id": "uuid",
  "status": "processing",
  "total_count": 3,
  "message": "Bulk operation initiated. Check status at /api/jobs-management/bulk-operations/{operation_id}"
}
```

**Validation Rules**:
- Maximum 50 jobs per operation
- Admin role required for certain operations
- Preview mode available with `dry_run: true`

#### 5. Get Bulk Operation Status
```
GET /api/jobs-management/bulk-operations/{operation_id}
```

**Response** (200 OK):
```json
{
  "operation_id": "uuid",
  "operation_type": "status_update",
  "status": "completed",
  "total_count": 3,
  "success_count": 3,
  "failure_count": 0,
  "error_details": [],
  "started_at": "2025-10-08T10:18:00Z",
  "completed_at": "2025-10-08T10:18:05Z"
}
```

#### 6. Delete Job (Soft Delete)
```
DELETE /api/jobs-management/{job_id}
```

**Query Parameters**:
- `permanent`: Boolean (default: false, requires super admin)

**Response** (200 OK):
```json
{
  "id": "uuid",
  "status": "archived",
  "archived_at": "2025-10-08T10:18:00Z",
  "message": "Job archived successfully. Can be restored within 90 days."
}
```

**Authorization**: HR Admin role required

#### 7. Post to External Portal
```
POST /api/jobs-management/{job_id}/external-postings
```

**Request Body**:
```json
{
  "portals": ["linkedin", "naukri"],
  "field_mappings": {
    "linkedin": {
      "job_function": "Engineering",
      "seniority_level": "Mid-Senior level"
    },
    "naukri": {
      "industry": "IT-Software",
      "role_category": "Software Development"
    }
  },
  "expires_in_days": 30
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "uuid",
  "postings": [
    {
      "portal": "linkedin",
      "status": "pending",
      "estimated_completion": "2025-10-08T10:20:00Z"
    },
    {
      "portal": "naukri",
      "status": "pending",
      "estimated_completion": "2025-10-08T10:20:00Z"
    }
  ]
}
```

#### 8. Get Audit Log
```
GET /api/jobs-management/{job_id}/audit-log
```

**Query Parameters**:
- `action_type`: Filter by action type
- `user_id`: Filter by user
- `date_from`, `date_to`: Date range
- `page`, `limit`: Pagination

**Response** (200 OK):
```json
{
  "audit_entries": [
    {
      "id": "uuid",
      "action_type": "status_change",
      "old_values": {"status": "open"},
      "new_values": {"status": "closed", "reason": "Position filled"},
      "user": {
        "id": "uuid",
        "name": "Jane Smith",
        "email": "jane@company.com"
      },
      "timestamp": "2025-10-08T10:18:00Z",
      "ip_address": "192.168.1.100"
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "limit": 20
  }
}
```

### UI Components and User Flow

#### Component 1: Jobs Dashboard
**Location**: `/jobs-management/dashboard`

**Layout**:
- **Header**: Title, "Create Job" button, Export button
- **Filters Bar**: Status dropdown, Department dropdown, Date range picker, Search input
- **Summary Cards**: Total Jobs, Open, Closed, On-Hold, Archived (with counts)
- **Jobs Table**: 
  - Columns: Checkbox, Job Title, Department, Status, Posted Date, Applications, Avg Match Score, Actions
  - Bulk actions toolbar (appears when jobs selected)
  - Pagination controls

**Interactions**:
- Click job title → Navigate to job detail page
- Click "View Analytics" → Open analytics modal/page
- Click status badge → Quick status change dropdown
- Select multiple jobs → Show bulk actions toolbar
- Click "Export" → Download CSV with current filters applied

#### Component 2: Job Analytics Page
**Location**: `/jobs-management/{job_id}/analytics`

**Layout**:
- **Header**: Job title, Back button, Export PDF button
- **Date Range Selector**: 7d, 30d, 90d, Custom
- **Funnel Visualization**: Sankey diagram or funnel chart
- **Metrics Grid**: 
  - Time to Fill
  - Time to First Application
  - Avg Match Score
  - Conversion Rates
- **Trends Chart**: Line chart showing applications and views over time
- **Match Score Distribution**: Bar chart
- **Comparison Section**: Benchmark against similar jobs
- **Applicant List**: Table with download option

#### Component 3: Bulk Operations Modal
**Trigger**: Select jobs + Click bulk action

**Layout**:
- **Step 1**: Select operation (Status Update, Archive, Update Deadline)
- **Step 2**: Configure parameters (e.g., new status, reason)
- **Step 3**: Preview changes (table showing job titles and changes)
- **Step 4**: Confirmation with progress bar
- **Step 5**: Results summary (success/failure counts, error details)

#### Component 4: External Posting Modal
**Location**: Job detail page → "Post to External Portals" button

**Layout**:
- **Portal Selection**: Checkboxes for LinkedIn, Naukri, Indeed
- **Field Mapping**: Portal-specific fields with tooltips
- **Preview**: Side-by-side preview of how job will appear on each portal
- **Posting Status**: Real-time status updates
- **Success/Error Messages**: Detailed feedback per portal

#### Component 5: Audit Log Viewer
**Location**: `/jobs-management/{job_id}/audit-log`

**Layout**:
- **Filters**: Action type, User, Date range
- **Timeline View**: Chronological list of changes
- **Entry Details**: Expandable cards showing old/new values, user, timestamp, IP
- **Export Button**: Download audit log as CSV

### User Flow: Update Job Status

1. User navigates to Jobs Dashboard
2. User finds job using filters/search
3. User clicks status badge on job row
4. Dropdown appears with valid status transitions
5. User selects new status (e.g., "Closed")
6. If closing, modal prompts for reason (optional)
7. User confirms change
8. System validates permission and status transition
9. Status updates in database
10. Audit log entry created
11. Notifications sent to job creator and hiring manager
12. Dashboard refreshes with new status
13. Success toast notification appears

### User Flow: Bulk Archive Jobs

1. User navigates to Jobs Dashboard
2. User applies filters (e.g., status = "Closed", closed_date > 90 days ago)
3. User selects multiple jobs (checkboxes)
4. Bulk actions toolbar appears
5. User clicks "Archive" button
6. Bulk operations modal opens
7. Preview shows list of jobs to be archived
8. User confirms operation
9. System creates bulk operation record
10. Background job processes each job:
    - Update status to "archived"
    - Set archived_at timestamp
    - Create audit log entry
11. Progress bar updates in real-time
12. On completion, results summary shown
13. User can download error report if any failures
14. Dashboard refreshes automatically

### Integration Points

#### 1. Authentication & Authorization
- **Module**: `services/auth_service.py`
- **Integration**: 
  - Check user role for admin-only operations
  - Validate JWT tokens on all endpoints
  - Audit log captures user_id from auth context

#### 2. Job Creation Module
- **Module**: `api/jobs.py`, `services/job_service.py`
- **Integration**:
  - Initialize job status as "open" on creation
  - Create initial audit log entry
  - Initialize analytics record with zero counts

#### 3. Application Management
- **Module**: `services/application_service.py`
- **Integration**:
  - Prevent applications to closed/archived jobs
  - Update application_count in job_analytics
  - Trigger analytics recalculation on new application

#### 4. Candidate Matching
- **Module**: `services/jd_matcher.py`
- **Integration**:
  - Update avg_match_score in job_analytics
  - Provide match score distribution for analytics

#### 5. Notification System
- **Module**: `services/notification_service.py`
- **Integration**:
  - Send notifications on status changes
  - Alert admins on bulk operation completion
  - Notify on external posting failures

#### 6. Background Jobs
- **Module**: `services/scheduler_service.py` (to be created)
- **Integration**:
  - Daily job: Auto-close jobs past deadline
  - Daily job: Auto-archive jobs closed > 90 days
  - Daily job: Calculate and cache analytics
  - Hourly job: Update view counts from cache

---

## 5. DEPENDENCIES

### External Libraries

#### Python Packages
```
# API Integration
httpx==0.25.0              # Async HTTP client for external portal APIs
python-linkedin-v2==0.1.0  # LinkedIn API wrapper
naukri-api==1.0.0          # Naukri API wrapper (if available, else custom)
indeed-api==2.0.0          # Indeed API wrapper

# Background Jobs
celery==5.3.4              # Distributed task queue
redis==5.0.1               # Message broker for Celery

# Data Processing
pandas==2.1.3              # Analytics calculations
numpy==1.26.2              # Numerical operations

# Charting (if server-side rendering needed)
plotly==5.18.0             # Interactive charts
matplotlib==3.8.2          # Static charts for PDF export

# PDF Generation
reportlab==4.0.7           # PDF generation for analytics reports
weasyprint==60.1           # HTML to PDF conversion

# Existing
fastapi>=0.104.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
```

#### Frontend Libraries (if applicable)
```json
{
  "dependencies": {
    "recharts": "^2.10.0",           // Charts for analytics
    "react-table": "^7.8.0",         // Data tables
    "date-fns": "^2.30.0",           // Date manipulation
    "react-query": "^3.39.0",        // Data fetching and caching
    "zustand": "^4.4.0"              // State management
  }
}
```

### External Services

#### 1. LinkedIn Jobs API
- **Purpose**: Post jobs to LinkedIn
- **Authentication**: OAuth 2.0
- **Rate Limits**: 100 requests/day (free tier)
- **Documentation**: https://docs.microsoft.com/en-us/linkedin/talent/job-postings

#### 2. Naukri API
- **Purpose**: Post jobs to Naukri.com
- **Authentication**: API Key
- **Rate Limits**: 500 requests/day
- **Documentation**: https://www.naukri.com/api-docs

#### 3. Indeed API
- **Purpose**: Post jobs to Indeed
- **Authentication**: Publisher ID + API Key
- **Rate Limits**: 1000 requests/day
- **Documentation**: https://indeed.com/publisher/api

#### 4. Redis
- **Purpose**: 
  - Celery message broker
  - Cache for real-time metrics (view counts)
  - Rate limiting
- **Version**: 7.0+
- **Deployment**: Managed service (Railway Redis, AWS ElastiCache)

### Internal Modules

#### Modifications Required

1. **`models/job_schemas.py`**
   - Add status field with enum validation
   - Add archived_at, closed_at fields
   - Add view_count field

2. **`services/job_service.py`**
   - Add status transition validation logic
   - Add soft delete method
   - Add view count increment method

3. **`services/notification_service.py`**
   - Add job status change notification template
   - Add bulk operation completion notification

4. **`core/database.py`**
   - Add connection pooling optimization for analytics queries
   - Add read replica support for dashboard queries

5. **`api/jobs.py`**
   - Add permission checks for admin operations
   - Add rate limiting for bulk operations

#### New Modules to Create

1. **`services/job_analytics_service.py`**
   - Calculate daily analytics
   - Generate analytics reports
   - Comparison logic with similar jobs

2. **`services/bulk_operations_service.py`**
   - Process bulk operations
   - Error handling and rollback logic
   - Progress tracking

3. **`services/external_posting_service.py`**
   - Portal API integrations
   - Field mapping logic
   - Retry and error handling

4. **`services/audit_service.py`**
   - Create audit log entries
   - Generate checksums
   - Query audit logs

5. **`services/scheduler_service.py`**
   - Celery task definitions
   - Scheduled job logic (auto-close, auto-archive)

### Prerequisites

1. **Database**
   - PostgreSQL 14+ (for JSONB support)
   - Run migrations to create new tables

2. **Redis**
   - Redis 7.0+ instance running
   - Configure Celery to use Redis as broker

3. **API Credentials**
   - LinkedIn OAuth app credentials
   - Naukri API key
   - Indeed Publisher ID and API key

4. **Permissions**
   - HR Admin role defined in auth system
   - Permission matrix updated for new endpoints

---

## 6. TESTING PLAN

### Unit Tests

#### Test Suite 1: Job Status Management (`tests/test_job_status_service.py`)

```python
# Test cases:
- test_valid_status_transition_open_to_closed()
- test_invalid_status_transition_closed_to_open()
- test_status_change_creates_audit_log()
- test_status_change_sends_notification()
- test_prevent_application_to_closed_job()
- test_admin_only_can_archive()
- test_status_history_recorded()
```

#### Test Suite 2: Job Analytics (`tests/test_job_analytics_service.py`)

```python
# Test cases:
- test_calculate_funnel_metrics()
- test_calculate_conversion_rates()
- test_calculate_time_to_fill()
- test_match_score_distribution()
- test_analytics_date_range_filter()
- test_comparison_with_similar_jobs()
- test_analytics_caching()
- test_handle_zero_applications()
```

#### Test Suite 3: Bulk Operations (`tests/test_bulk_operations_service.py`)

```python
# Test cases:
- test_bulk_status_update_success()
- test_bulk_operation_max_50_jobs()
- test_bulk_operation_partial_failure()
- test_bulk_operation_rollback_on_error()
- test_bulk_operation_progress_tracking()
- test_bulk_operation_undo()
- test_concurrent_bulk_operations()
```

#### Test Suite 4: External Posting (`tests/test_external_posting_service.py`)

```python
# Test cases:
- test_post_to_linkedin_success()
- test_post_to_naukri_success()
- test_post_to_indeed_success()
- test_handle_api_rate_limit()
- test_handle_api_timeout()
- test_retry_on_failure()
- test_field_mapping_validation()
- test_store_external_job_id()
- test_update_existing_posting()
```

#### Test Suite 5: Audit Logging (`tests/test_audit_service.py`)

```python
# Test cases:
- test_create_audit_log_on_status_change()
- test_create_audit_log_on_field_update()
- test_audit_log_captures_user_info()
- test_audit_log_checksum_generation()
- test_audit_log_immutability()
- test_query_audit_log_with_filters()
- test_audit_log_retention()
```

#### Test Suite 6: Automated Rules (`tests/test_job_automation.py`)

```python
# Test cases:
- test_auto_close_after_deadline()
- test_auto_archive_after_90_days()
- test_scheduled_task_runs_daily()
- test_handle_timezone_correctly()
- test_skip_already_closed_jobs()
```

### Integration Tests

#### Test Suite 1: Dashboard API (`tests/integration/test_jobs_dashboard_api.py`)

```python
# Test cases:
- test_get_dashboard_with_filters()
- test_dashboard_pagination()
- test_dashboard_sorting()
- test_dashboard_search()
- test_dashboard_performance_1000_jobs()
- test_dashboard_unauthorized_access()
- test_dashboard_real_time_updates()
```

#### Test Suite 2: Status Management Flow (`tests/integration/test_status_management_flow.py`)

```python
# Test cases:
- test_complete_status_lifecycle()
- test_status_change_prevents_applications()
- test_status_change_notification_sent()
- test_status_change_audit_trail()
- test_concurrent_status_updates()
```

#### Test Suite 3: Analytics Generation (`tests/integration/test_analytics_generation.py`)

```python
# Test cases:
- test_analytics_updated_on_new_application()
- test_analytics_calculation_accuracy()
- test_analytics_export_pdf()
- test_analytics_caching_invalidation()
```

#### Test Suite 4: Bulk Operations End-to-End (`tests/integration/test_bulk_operations_e2e.py`)

```python
# Test cases:
- test_bulk_archive_50_jobs()
- test_bulk_status_update_with_notifications()
- test_bulk_operation_error_handling()
- test_bulk_operation_background_processing()
```

#### Test Suite 5: External Posting Integration (`tests/integration/test_external_posting_integration.py`)

```python
# Test cases (using mock APIs):
- test_post_to_multiple_portals()
- test_handle_portal_specific_errors()
- test_sync_application_status_from_portal()
- test_repost_expired_job()
```

### Manual Testing Scenarios

#### Scenario 1: Dashboard Usability
1. Navigate to Jobs Dashboard
2. Verify all summary cards show correct counts
3. Apply various filters and verify results
4. Test sorting by each column
5. Test search functionality with partial matches
6. Test pagination (navigate to page 5, then back to page 1)
7. Verify responsive design on tablet (1024px width)
8. Test keyboard navigation (tab through filters, use arrow keys in dropdowns)

#### Scenario 2: Status Management
1. Create a new job (status should be "open")
2. Change status to "on-hold" with reason
3. Verify status badge updates immediately
4. Check notification received by hiring manager
5. View status history timeline on job detail page
6. Attempt to apply to job (should still work for on-hold)
7. Change status to "closed"
8. Attempt to apply (should be blocked with message)
9. Verify audit log shows both status changes

#### Scenario 3: Analytics Dashboard
1. Open analytics for a job with 50+ applications
2. Verify funnel chart renders correctly
3. Change date range to last 7 days
4. Verify metrics update accordingly
5. Check trends chart shows daily breakdown
6. Verify match score distribution chart
7. Export analytics as PDF
8. Verify PDF contains all charts and metrics
9. Compare with similar jobs section

#### Scenario 4: Bulk Operations
1. Select 10 jobs from dashboard
2. Click "Update Status" bulk action
3. Choose "on-hold" status and add reason
4. Review preview of changes
5. Confirm operation
6. Watch progress bar (should complete in < 5 seconds)
7. Verify all 10 jobs updated
8. Check audit log for each job
9. Test undo operation (within 5 minutes)
10. Verify jobs reverted to previous status

#### Scenario 5: External Posting
1. Open job detail page
2. Click "Post to External Portals"
3. Select LinkedIn and Naukri
4. Fill in portal-specific fields
5. Preview job posting for each portal
6. Submit posting
7. Verify status changes to "pending"
8. Wait for posting to complete (or mock completion)
9. Verify external job IDs stored
10. Check error handling (disconnect network, retry)

#### Scenario 6: Automated Rules
1. Create a job with application deadline = today
2. Wait for next scheduled task run (or trigger manually)
3. Verify job status changed to "closed"
4. Create a job and manually close it
5. Update closed_at to 91 days ago (via database)
6. Run scheduled task
7. Verify job status changed to "archived"

### Edge Cases to Consider

1. **Concurrent Updates**
   - Two users update same job status simultaneously
   - Expected: Last write wins, both changes logged in audit

2. **Large Bulk Operations**
   - User attempts to bulk update 100 jobs (exceeds limit)
   - Expected: Error message "Maximum 50 jobs allowed"

3. **Expired External Postings**
   - External job posting expires on portal
   - Expected: System detects expiration, updates status, notifies user

4. **Zero Applications**
   - Job has no applications, user views analytics
   - Expected: Graceful handling, show "No data yet" message

5. **Deleted User**
   - User who created job is deleted from system
   - Expected: Job remains, audit log shows "[Deleted User]"

6. **Network Failure During External Posting**
   - Network drops while posting to LinkedIn
   - Expected: Retry 3 times, then mark as "failed" with error message

7. **Bulk Operation Timeout**
   - Bulk operation takes > 30 seconds
   - Expected: Move to background job, notify user on completion

8. **Invalid Status Transition**
   - User attempts to change archived job to open
   - Expected: Error message "Cannot reopen archived job. Please create a new job."

9. **Analytics Date Range Exceeds Data Retention**
   - User selects date range from 3 years ago
   - Expected: Show data only for available range (2 years)

10. **Audit Log Tampering Attempt**
    - Attacker modifies audit log entry in database
    - Expected: Checksum validation fails, alert admin

### Performance Testing

#### Load Tests
- **Dashboard**: 100 concurrent users, < 2s response time
- **Analytics**: 50 concurrent users, < 3s response time
- **Bulk Operations**: 10 concurrent operations, no deadlocks
- **External Posting**: 20 concurrent postings, < 30s completion

#### Stress Tests
- **Database**: 10,000 jobs, dashboard query < 2s
- **Analytics**: 1,000 applications per job, calculation < 5s
- **Audit Log**: 100,000 entries, query with filters < 1s

---

## 7. IMPLEMENTATION PLAN

### Phase 1: Core Infrastructure (Week 1-2)

**Estimated Effort**: 60 hours

#### Tasks:

1. **Database Schema Setup** (8 hours)
   - [ ] Create migration scripts for all new tables
   - [ ] Add indexes for performance
   - [ ] Modify existing jobs table
   - [ ] Write rollback scripts
   - [ ] Test migrations on staging database

2. **API Endpoints - Basic CRUD** (12 hours)
   - [ ] Implement GET /api/jobs-management/dashboard
   - [ ] Implement PUT /api/jobs-management/{id}/status
   - [ ] Implement DELETE /api/jobs-management/{id}
   - [ ] Add authentication middleware
   - [ ] Add permission checks (admin-only operations)
   - [ ] Write API documentation (OpenAPI/Swagger)

3. **Job Status Service** (10 hours)
   - [ ] Implement status transition validation logic
   - [ ] Create status change method with audit logging
   - [ ] Add notification triggers
   - [ ] Implement soft delete functionality
   - [ ] Write unit tests (80% coverage target)

4. **Audit Logging Service** (8 hours)
   - [ ] Create audit log entry creation method
   - [ ] Implement checksum generation (SHA-256)
   - [ ] Add audit log query methods with filters
   - [ ] Write unit tests

5. **Dashboard UI - Basic Version** (12 hours)
   - [ ] Create jobs table component with sorting
   - [ ] Add filter controls (status, department, date)
   - [ ] Implement search functionality
   - [ ] Add pagination
   - [ ] Connect to API endpoints
   - [ ] Add loading states and error handling

6. **Status Management UI** (10 hours)
   - [ ] Create status badge component
   - [ ] Implement status change dropdown
   - [ ] Add confirmation modal with reason field
   - [ ] Create status history timeline component
   - [ ] Add success/error notifications

**Deliverables**:
- Working dashboard with basic filtering and sorting
- Job status management with audit trail
- API documentation

**Risks & Mitigation**:
- **Risk**: Database migration fails on production
  - **Mitigation**: Test migrations thoroughly on staging, have rollback plan ready
- **Risk**: Performance issues with large datasets
  - **Mitigation**: Add database indexes, implement pagination early

### Phase 2: Analytics & Bulk Operations (Week 3-4)

**Estimated Effort**: 70 hours

#### Tasks:

1. **Analytics Service** (16 hours)
   - [ ] Implement funnel metrics calculation
   - [ ] Add time metrics calculation (time-to-fill, etc.)
   - [ ] Create match score distribution logic
   - [ ] Implement comparison with similar jobs
   - [ ] Add caching layer (Redis)
   - [ ] Write unit tests

2. **Analytics API Endpoints** (8 hours)
   - [ ] Implement GET /api/jobs-management/{id}/analytics
   - [ ] Add date range filtering
   - [ ] Optimize query performance
   - [ ] Add response caching
   - [ ] Write integration tests

3. **Analytics UI** (18 hours)
   - [ ] Create analytics dashboard layout
   - [ ] Implement funnel visualization (Recharts/D3)
   - [ ] Add metrics cards with trend indicators
   - [ ] Create trends line chart
   - [ ] Add match score distribution bar chart
   - [ ] Implement date range selector
   - [ ] Add export to PDF functionality
   - [ ] Make responsive for tablet/desktop

4. **Bulk Operations Service** (12 hours)
   - [ ] Create bulk operation processing logic
   - [ ] Implement transaction management (rollback on error)
   - [ ] Add progress tracking
   - [ ] Implement undo functionality (5-minute window)
   - [ ] Add background job processing (Celery)
   - [ ] Write unit tests

5. **Bulk Operations API** (6 hours)
   - [ ] Implement POST /api/jobs-management/bulk-update
   - [ ] Implement GET /api/jobs-management/bulk-operations/{id}
   - [ ] Add validation (max 50 jobs)
   - [ ] Add dry-run mode
   - [ ] Write integration tests

6. **Bulk Operations UI** (10 hours)
   - [ ] Create multi-select checkboxes on dashboard
   - [ ] Add bulk actions toolbar
   - [ ] Create bulk operations modal (4-step wizard)
   - [ ] Implement preview changes table
   - [ ] Add progress bar with real-time updates
   - [ ] Create results summary view
   - [ ] Add undo button

**Deliverables**:
- Complete analytics dashboard with charts
- Bulk operations functionality with undo capability
- Background job processing setup

**Risks & Mitigation**:
- **Risk**: Analytics calculations too slow
  - **Mitigation**: Pre-calculate daily, cache results, use database aggregations
- **Risk**: Bulk operations cause database deadlocks
  - **Mitigation**: Use proper transaction isolation, process sequentially if needed
- **Risk**: Chart rendering performance issues
  - **Mitigation**: Limit data points, use virtualization, optimize re-renders

### Phase 3: External Posting & Automation (Week 5-6)

**Estimated Effort**: 65 hours

#### Tasks:

1. **External Posting Service** (20 hours)
   - [ ] Implement LinkedIn API integration (OAuth 2.0)
   - [ ] Implement Naukri API integration
   - [ ] Implement Indeed API integration
   - [ ] Create field mapping logic per portal
   - [ ] Add retry mechanism with exponential backoff
   - [ ] Implement error handling and logging
   - [ ] Add rate limiting
   - [ ] Write unit tests with mocked APIs

2. **External Posting API** (8 hours)
   - [ ] Implement POST /api/jobs-management/{id}/external-postings
   - [ ] Implement GET /api/jobs-management/{id}/external-postings
   - [ ] Add webhook endpoints for portal callbacks
   - [ ] Write integration tests

3. **External Posting UI** (12 hours)
   - [ ] Create "Post to External Portals" modal
   - [ ] Add portal selection checkboxes
   - [ ] Create field mapping forms (portal-specific)
   - [ ] Implement preview pane (side-by-side)
   - [ ] Add posting status indicators
   - [ ] Create external postings list on job detail page
   - [ ] Add repost/update functionality

4. **Automated Rules Service** (10 hours)
   - [ ] Implement auto-close after deadline logic
   - [ ] Implement auto-archive after 90 days logic
   - [ ] Create Celery scheduled tasks
   - [ ] Add timezone handling
   - [ ] Implement notification triggers
   - [ ] Write unit tests

5. **Scheduler Setup** (8 hours)
   - [ ] Configure Celery with Redis broker
   - [ ] Set up Celery beat for scheduled tasks
   - [ ] Create monitoring dashboard (Flower)
   - [ ] Add error alerting
   - [ ] Write deployment documentation

6. **Audit Log UI** (7 hours)
   - [ ] Create audit log viewer page
   - [ ] Add filters (action type, user, date)
   - [ ] Implement timeline view
   - [ ] Add expandable entry details
   - [ ] Add export to CSV functionality

**Deliverables**:
- External portal posting functionality for LinkedIn, Naukri, Indeed
- Automated job status management (auto-close, auto-archive)
- Complete audit logging system
- Celery background job processing

**Risks & Mitigation**:
- **Risk**: External API rate limits exceeded
  - **Mitigation**: Implement queue system, respect rate limits, add retry delays
- **Risk**: OAuth token expiration during posting
  - **Mitigation**: Implement token refresh logic, handle auth errors gracefully
- **Risk**: Scheduled tasks don't run reliably
  - **Mitigation**: Use managed Celery service, add monitoring and alerts
- **Risk**: API credentials security
  - **Mitigation**: Store in environment variables, use secrets management service

### Phase 4: Testing, Optimization & Documentation (Week 7)

**Estimated Effort**: 35 hours

#### Tasks:

1. **Comprehensive Testing** (15 hours)
   - [ ] Write remaining unit tests (target: 85% coverage)
   - [ ] Write integration tests for all API endpoints
   - [ ] Perform manual testing of all scenarios
   - [ ] Test all edge cases
   - [ ] Perform cross-browser testing (Chrome, Firefox, Safari)
   - [ ] Test responsive design on various screen sizes
   - [ ] Accessibility testing (WCAG 2.1 AA)

2. **Performance Optimization** (10 hours)
   - [ ] Optimize database queries (add missing indexes)
   - [ ] Implement query result caching
   - [ ] Optimize frontend bundle size
   - [ ] Add lazy loading for analytics charts
   - [ ] Optimize API response times
   - [ ] Load test with 1000+ jobs
   - [ ] Profile and fix performance bottlenecks

3. **Documentation** (8 hours)
   - [ ] Write user guide with screenshots
   - [ ] Create admin documentation
   - [ ] Document API endpoints (Swagger/OpenAPI)
   - [ ] Write deployment guide
   - [ ] Create troubleshooting guide
   - [ ] Document external API setup (credentials, OAuth)

4. **Security Review** (2 hours)
   - [ ] Review permission checks on all endpoints
   - [ ] Audit SQL injection vulnerabilities
   - [ ] Check XSS vulnerabilities in UI
   - [ ] Review audit log tamper-proofing
   - [ ] Verify API credentials storage security

**Deliverables**:
- 85%+ test coverage
- Performance benchmarks met
- Complete documentation
- Security audit passed

**Risks & Mitigation**:
- **Risk**: Critical bugs found late in testing
  - **Mitigation**: Start testing early in each phase, not just at the end
- **Risk**: Performance targets not met
  - **Mitigation**: Profile early, optimize incrementally, consider database scaling

### Overall Timeline

| Phase | Duration | Effort | Deliverables |
|-------|----------|--------|--------------|
| Phase 1: Core Infrastructure | Week 1-2 | 60 hours | Dashboard, Status Management, Audit Logging |
| Phase 2: Analytics & Bulk Ops | Week 3-4 | 70 hours | Analytics Dashboard, Bulk Operations |
| Phase 3: External & Automation | Week 5-6 | 65 hours | External Posting, Automated Rules |
| Phase 4: Testing & Docs | Week 7 | 35 hours | Testing, Optimization, Documentation |
| **Total** | **7 weeks** | **230 hours** | **Complete Feature** |

**Team Composition** (Recommended):
- 1 Backend Developer (full-time)
- 1 Frontend Developer (full-time)
- 1 QA Engineer (half-time, weeks 2-7)
- 1 DevOps Engineer (quarter-time, for Celery setup)

### Critical Path
1. Database schema → API endpoints → UI components (sequential)
2. Analytics service → Analytics API → Analytics UI (sequential)
3. External posting service can be parallel with analytics work
4. Testing and optimization throughout, not just at the end

---

## 8. SUCCESS METRICS

### Primary Metrics (Must Achieve)

1. **Feature Adoption Rate**
   - **Target**: 80% of HR users access Jobs Management dashboard within first month
   - **Measurement**: Track unique users accessing `/jobs-management/dashboard`
   - **Success Criteria**: ≥ 80% adoption

2. **Time Savings**
   - **Target**: Reduce time spent on job management tasks by 40%
   - **Measurement**: Compare average time spent on job-related tasks before/after (user surveys + analytics)
   - **Success Criteria**: ≥ 40% reduction

3. **Bulk Operations Usage**
   - **Target**: 30% of status updates done via bulk operations
   - **Measurement**: Count bulk operations vs. individual updates
   - **Success Criteria**: ≥ 30% of updates are bulk

4. **External Posting Adoption**
   - **Target**: 50% of jobs posted to at least one external portal
   - **Measurement**: Count jobs with external postings / total jobs
   - **Success Criteria**: ≥ 50% of jobs posted externally

### Performance Metrics (Must Meet)

1. **Dashboard Load Time**
   - **Target**: < 2 seconds for 1000+ jobs
   - **Measurement**: Server response time + frontend render time
   - **Success Criteria**: 95th percentile < 2s

2. **Analytics Generation Time**
   - **Target**: < 3 seconds for 30-day analytics
   - **Measurement**: API response time for analytics endpoint
   - **Success Criteria**: 95th percentile < 3s

3. **Bulk Operation Processing Time**
   - **Target**: < 10 seconds for 50 jobs
   - **Measurement**: Time from initiation to completion
   - **Success Criteria**: 95th percentile < 10s

4. **System Uptime**
   - **Target**: 99.5% uptime
   - **Measurement**: Uptime monitoring service
   - **Success Criteria**: ≥ 99.5% uptime

### Quality Metrics (Must Meet)

1. **Bug Rate**
   - **Target**: < 2 critical bugs per month after launch
   - **Measurement**: Bug tracking system (Jira, GitHub Issues)
   - **Success Criteria**: < 2 critical bugs/month

2. **Test Coverage**
   - **Target**: ≥ 85% code coverage
   - **Measurement**: Coverage reports from pytest
   - **Success Criteria**: ≥ 85% coverage

3. **API Error Rate**
   - **Target**: < 0.5% error rate
   - **Measurement**: API monitoring (5xx errors / total requests)
   - **Success Criteria**: < 0.5% error rate

4. **User-Reported Issues**
   - **Target**: < 5 support tickets per week
   - **Measurement**: Support ticket system
   - **Success Criteria**: < 5 tickets/week after first month

### Business Impact Metrics (Track & Improve)

1. **Job Posting Efficiency**
   - **Metric**: Average time from job creation to external posting
   - **Baseline**: TBD (measure current state)
   - **Target**: 50% reduction from baseline

2. **Application Volume**
   - **Metric**: Average applications per job (with external posting vs. without)
   - **Hypothesis**: Jobs posted externally receive 2x more applications
   - **Target**: 2x increase for externally posted jobs

3. **Time-to-Fill**
   - **Metric**: Average days from job posting to hire
   - **Baseline**: TBD (measure current state)
   - **Target**: 15% reduction from baseline (due to better visibility and analytics)

4. **Job Closure Rate**
   - **Metric**: Percentage of jobs successfully filled (not archived unfilled)
   - **Baseline**: TBD
   - **Target**: 10% improvement from baseline

### User Satisfaction Metrics (Track & Improve)

1. **Net Promoter Score (NPS)**
   - **Target**: NPS ≥ 40
   - **Measurement**: In-app survey after 2 weeks of usage
   - **Question**: "How likely are you to recommend this feature to a colleague?"

2. **Feature Satisfaction**
   - **Target**: ≥ 4.0/5.0 average rating
   - **Measurement**: In-app feedback widget
   - **Question**: "How satisfied are you with the Jobs Management feature?"

3. **Task Completion Rate**
   - **Target**: ≥ 90% task completion rate
   - **Measurement**: Analytics tracking (e.g., % of users who complete bulk operation after starting)
   - **Success Criteria**: ≥ 90% completion rate

### Monitoring & Reporting

#### Daily Monitoring
- API error rates (alert if > 1%)
- System uptime (alert if down > 5 minutes)
- Background job failures (alert if > 5% failure rate)

#### Weekly Reports
- Feature usage statistics (dashboard views, bulk operations, external postings)
- Performance metrics (load times, processing times)
- User-reported issues summary

#### Monthly Reviews
- All success metrics reviewed
- User satisfaction survey results
- Business impact analysis
- Identify areas for improvement

#### Tools
- **Analytics**: Google Analytics, Mixpanel, or custom analytics service
- **Performance Monitoring**: New Relic, Datadog, or Sentry
- **Uptime Monitoring**: Pingdom, UptimeRobot
- **User Feedback**: In-app feedback widget, UserVoice, or similar

---

## APPENDIX

### A. Glossary

- **Job Lifecycle**: The stages a job posting goes through from creation to archival (open → on-hold → closed → archived)
- **Soft Delete**: Marking a record as deleted without physically removing it from the database
- **Time-to-Fill**: Number of days from job posting to successful hire
- **Match Score**: Percentage score indicating how well a candidate matches job requirements
- **Funnel Metrics**: Sequential stages in the hiring process (views → applications → shortlisted → interviewed → offers → hires)
- **Bulk Operation**: Action performed on multiple jobs simultaneously
- **Audit Trail**: Chronological record of all changes made to a job
- **External Portal**: Third-party job board (LinkedIn, Naukri, Indeed)

### B. Related Documents

- [Feature 6: Job Creation PRD](./06-JOB_CREATION_PRD.md)
- [Feature 7: Job Matching PRD](./07-JOB_MATCHING_PRD.md)
- [Authentication Implementation Guide](../AUTH_IMPLEMENTATION.md)
- [Deployment Guide](../DEPLOYMENT.md)

### C. API Credentials Setup Guide

#### LinkedIn Jobs API
1. Create LinkedIn Developer App at https://www.linkedin.com/developers/
2. Request access to "Job Postings" product
3. Configure OAuth 2.0 redirect URI
4. Store credentials in environment variables:
   ```
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_client_secret
   LINKEDIN_REDIRECT_URI=https://yourdomain.com/api/auth/linkedin/callback
   ```

#### Naukri API
1. Contact Naukri B2B sales for API access
2. Receive API key and documentation
3. Store in environment variables:
   ```
   NAUKRI_API_KEY=your_api_key
   NAUKRI_API_ENDPOINT=https://api.naukri.com/v1
   ```

#### Indeed API
1. Register for Indeed Publisher account at https://www.indeed.com/publisher
2. Obtain Publisher ID and API key
3. Store in environment variables:
   ```
   INDEED_PUBLISHER_ID=your_publisher_id
   INDEED_API_KEY=your_api_key
   ```

### D. Database Migration Script Example

```sql
-- Migration: 008_create_jobs_management_tables.sql

BEGIN;

-- Create job_analytics table
CREATE TABLE IF NOT EXISTS job_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    view_count INTEGER DEFAULT 0,
    application_count INTEGER DEFAULT 0,
    shortlist_count INTEGER DEFAULT 0,
    interview_count INTEGER DEFAULT 0,
    offer_count INTEGER DEFAULT 0,
    hire_count INTEGER DEFAULT 0,
    avg_match_score DECIMAL(5,2),
    median_match_score DECIMAL(5,2),
    time_to_fill INTEGER,
    time_to_first_application INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(job_id, date)
);

CREATE INDEX idx_job_analytics_job_id ON job_analytics(job_id);
CREATE INDEX idx_job_analytics_date ON job_analytics(date);

-- Create job_status_history table
CREATE TABLE IF NOT EXISTS job_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    reason TEXT,
    changed_by UUID NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_job_status_history_job_id ON job_status_history(job_id);
CREATE INDEX idx_job_status_history_changed_at ON job_status_history(changed_at);

-- Create job_external_postings table
CREATE TABLE IF NOT EXISTS job_external_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    portal VARCHAR(50) NOT NULL,
    external_job_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    posted_at TIMESTAMP,
    expires_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(job_id, portal)
);

CREATE INDEX idx_job_external_postings_job_id ON job_external_postings(job_id);
CREATE INDEX idx_job_external_postings_status ON job_external_postings(status);

-- Create job_audit_log table
CREATE TABLE IF NOT EXISTS job_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id UUID NOT NULL REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    checksum VARCHAR(64)
);

CREATE INDEX idx_job_audit_log_job_id ON job_audit_log(job_id);
CREATE INDEX idx_job_audit_log_timestamp ON job_audit_log(timestamp);
CREATE INDEX idx_job_audit_log_user_id ON job_audit_log(user_id);
CREATE INDEX idx_job_audit_log_action_type ON job_audit_log(action_type);

-- Create bulk_operations table
CREATE TABLE IF NOT EXISTS bulk_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_type VARCHAR(50) NOT NULL,
    job_ids UUID[] NOT NULL,
    parameters JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    error_details JSONB,
    initiated_by UUID NOT NULL REFERENCES users(id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bulk_operations_status ON bulk_operations(status);
CREATE INDEX idx_bulk_operations_initiated_by ON bulk_operations(initiated_by);

-- Modify jobs table
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'open';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_archived_at ON jobs(archived_at);

COMMIT;
```

### E. Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-08 | Product Team | Initial PRD creation |

---

**End of Document**
