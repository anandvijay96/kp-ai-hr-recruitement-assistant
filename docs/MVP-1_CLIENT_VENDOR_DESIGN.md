# MVP-1 Client & Vendor Management Design
**Created:** October 13, 2025  
**Purpose:** Specification for new Client and Vendor Management modules

---

## Overview

Client and Vendor Management are new features not mentioned in the original High-Level PRD. These modules are essential for a complete recruitment platform as they manage the organizations that create job requirements (Clients) and external agencies that supply candidates (Vendors).

---

## 1. Client Management Module

### Business Requirements

**What is a Client?**
- An organization/company that posts job requisitions
- Can have multiple HR managers assigned
- Has subscription/contract with the platform
- Tracks recruitment performance metrics

**Why do we need it?**
- Support multi-tenancy (multiple client organizations)
- Track client-specific recruitment metrics
- Manage client subscriptions and billing
- Assign HR managers to specific clients
- Filter jobs and candidates by client

### Database Schema

```sql
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    company_code VARCHAR(50) UNIQUE NOT NULL,
    industry VARCHAR(100),
    website VARCHAR(255),
    logo_url VARCHAR(255),
    
    -- Contact Information
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'USA',
    postal_code VARCHAR(20),
    
    -- Primary Contact Person
    contact_person_name VARCHAR(255),
    contact_person_email VARCHAR(255),
    contact_person_phone VARCHAR(50),
    contact_person_title VARCHAR(100),
    
    -- Subscription Details
    subscription_plan VARCHAR(50) DEFAULT 'basic',  -- basic, premium, enterprise
    subscription_start_date DATE,
    subscription_end_date DATE,
    max_job_posts INTEGER DEFAULT 10,
    max_active_jobs INTEGER DEFAULT 5,
    features_enabled JSONB,  -- {"ai_matching": true, "bulk_upload": true}
    
    -- Status & Verification
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, suspended, trial
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP,
    
    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    
    CONSTRAINT valid_status CHECK (status IN ('active', 'inactive', 'suspended', 'trial'))
);

-- Client-HR Assignment Junction Table
CREATE TABLE client_hr_assignments (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id),
    is_primary BOOLEAN DEFAULT FALSE,
    UNIQUE(client_id, user_id)
);

-- Link jobs to clients
ALTER TABLE jobs ADD COLUMN client_id INTEGER REFERENCES clients(id);
CREATE INDEX idx_jobs_client ON jobs(client_id);

-- Indexes for performance
CREATE INDEX idx_clients_status ON clients(status);
CREATE INDEX idx_clients_company_code ON clients(company_code);
CREATE INDEX idx_client_hr_client ON client_hr_assignments(client_id);
CREATE INDEX idx_client_hr_user ON client_hr_assignments(user_id);
```

### API Endpoints

```python
# Client CRUD
POST   /api/v1/clients                  # Create new client
GET    /api/v1/clients                  # List all clients (paginated)
GET    /api/v1/clients/{id}             # Get client details
PUT    /api/v1/clients/{id}             # Update client
DELETE /api/v1/clients/{id}             # Soft delete client

# HR Assignments
POST   /api/v1/clients/{id}/assign-hr   # Assign HR to client
DELETE /api/v1/clients/{id}/remove-hr/{user_id}  # Remove HR
GET    /api/v1/clients/{id}/hr-managers # List assigned HRs

# Client Metrics
GET    /api/v1/clients/{id}/metrics     # Get client performance metrics
GET    /api/v1/clients/{id}/jobs        # Get client's jobs
GET    /api/v1/clients/{id}/candidates  # Get candidates for client jobs

# Subscription Management
PUT    /api/v1/clients/{id}/subscription # Update subscription
GET    /api/v1/clients/{id}/usage        # Get usage stats vs limits
```

### Frontend Pages

#### 1. Client List Page (`/clients`)

**Layout:**
```
┌─ Clients ──────────────────────────────────────────────────┐
│                                                             │
│  [+ Add Client]  [Import CSV]  [Export]   🔍 Search...     │
│                                                             │
│  Filters: [ All Status ▼ ] [ All Industries ▼ ] [ Active ▼]│
│                                                             │
│  ┌────────────────────────────────────────────────────────┐│
│  │ TechCorp Inc.            │ Technology  │ Active │ [⋮]  ││
│  │ Code: TC001             │ 8 Jobs      │ Premium │      ││
│  │ 3 HR Managers           │ 45 Candidates│ 🟢     │      ││
│  ├────────────────────────────────────────────────────────┤│
│  │ StartupXYZ LLC          │ SaaS        │ Trial  │ [⋮]  ││
│  │ Code: SX002             │ 3 Jobs      │ Basic   │      ││
│  │ 1 HR Manager            │ 12 Candidates│ 🟡     │      ││
│  └────────────────────────────────────────────────────────┘│
│                                                             │
│  Showing 1-10 of 45 clients    [ < ] [ 1 2 3 ] [ > ]      │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Search by name, code, or industry
- Filter by status, subscription plan
- Sort by name, created date, active jobs
- Bulk operations (export, status change)
- Quick actions dropdown (view, edit, deactivate)

#### 2. Client Detail Page (`/clients/{id}`)

**Layout:**
```
┌─ TechCorp Inc. (TC001) ─────────────────────────────────────┐
│  [Edit Client] [Deactivate] [View Jobs]                     │
│                                                              │
│  📊 Quick Metrics                                            │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│  │💼 Total Jobs │📄 Candidates │✅ Hired      │⏱ Avg TTH  │ │
│  │      18      │      145     │      23      │  32 days  │ │
│  └──────────────┴──────────────┴──────────────┴───────────┘ │
│                                                              │
│  Company Information                                         │
│  ┌──────────────────────────────────────────────────────── │
│  │ Industry: Technology                                     │
│  │ Website: www.techcorp.com                                │
│  │ Email: contact@techcorp.com                              │
│  │ Phone: +1 555-0123                                       │
│  │ Address: 123 Tech Street, San Francisco, CA 94105       │
│  └────────────────────────────────────────────────────────  │
│                                                              │
│  Primary Contact                                             │
│  ┌──────────────────────────────────────────────────────── │
│  │ Name: John Smith                                         │
│  │ Title: HR Director                                       │
│  │ Email: john.smith@techcorp.com                           │
│  │ Phone: +1 555-0124                                       │
│  └────────────────────────────────────────────────────────  │
│                                                              │
│  Subscription Details                                        │
│  ┌──────────────────────────────────────────────────────── │
│  │ Plan: Premium                                            │
│  │ Status: ✅ Active                                         │
│  │ Valid: Jan 1, 2025 - Dec 31, 2025                       │
│  │ Job Posts Limit: 8/50 used                               │
│  │ Active Jobs Limit: 5/20 used                             │
│  │ Features: AI Matching ✅ Bulk Upload ✅ Analytics ✅      │
│  │ [Upgrade Plan] [Renew Subscription]                      │
│  └────────────────────────────────────────────────────────  │
│                                                              │
│  Assigned HR Managers (3)        [+ Assign HR]              │
│  ┌──────────────────────────────────────────────────────── │
│  │ • Sarah Johnson (sarah@hr.com) - Primary                 │
│  │ • Mike Davis (mike@hr.com)                               │
│  │ • Emily Chen (emily@hr.com)                              │
│  └────────────────────────────────────────────────────────  │
│                                                              │
│  Recent Jobs (Last 30 Days)      [View All Jobs]            │
│  ┌──────────────────────────────────────────────────────── │
│  │ Senior Java Developer   │ Open      │ 12 Candidates     │
│  │ UI/UX Designer         │ Filled    │ 8 Candidates      │
│  │ Product Manager        │ Open      │ 15 Candidates     │
│  └────────────────────────────────────────────────────────  │
└──────────────────────────────────────────────────────────────┘
```

#### 3. Client Create/Edit Form

**Fields:**
- **Basic Info:** Name*, Company Code*, Industry, Website, Logo
- **Contact:** Email*, Phone, Full Address
- **Primary Contact:** Name, Title, Email, Phone
- **Subscription:** Plan*, Start Date*, End Date, Limits, Features
- **Status:** Active/Inactive/Trial/Suspended
- **Notes:** Internal notes (admin only)

*Required fields

### Business Logic

**Client Creation Workflow:**
1. Admin fills client form
2. System generates unique company code (if not provided)
3. Client record created with "trial" status
4. Admin assigns HR managers
5. HR managers receive welcome email with client details
6. Client can now create jobs

**HR Assignment Rules:**
- HR user can be assigned to multiple clients
- One HR can be marked as "primary" per client
- Primary HR receives all client notifications
- HR users see only their assigned clients' jobs

**Subscription Limits:**
- System enforces max job posts and active jobs limits
- Warning at 80% usage
- Block job creation at 100% usage
- Admin can override limits

---

## 2. Vendor Management Module

### Business Requirements

**What is a Vendor?**
- External recruitment agency/staffing firm
- Submits candidate resumes for job openings
- Works on commission basis
- Has limited access to platform

**Why do we need it?**
- Expand candidate sourcing channels
- Track vendor performance and quality
- Manage vendor contracts and commissions
- Control vendor access to jobs and candidates

### Database Schema

```sql
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    vendor_code VARCHAR(50) UNIQUE NOT NULL,
    agency_type VARCHAR(100),  -- staffing, recruiting, freelance, consulting
    website VARCHAR(255),
    logo_url VARCHAR(255),
    
    -- Contact Information
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'USA',
    postal_code VARCHAR(20),
    
    -- Primary Contact Person
    contact_person_name VARCHAR(255),
    contact_person_email VARCHAR(255),
    contact_person_phone VARCHAR(50),
    
    -- Contract Details
    contract_start_date DATE,
    contract_end_date DATE,
    commission_rate DECIMAL(5,2),  -- Percentage (e.g., 15.00 = 15%)
    payment_terms TEXT,  -- Net 30, Net 60, etc.
    contract_document_url VARCHAR(255),
    
    -- Performance Metrics (updated periodically)
    total_submissions INTEGER DEFAULT 0,
    total_accepted INTEGER DEFAULT 0,
    total_interviewed INTEGER DEFAULT 0,
    total_hired INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),  -- Percentage
    avg_quality_score DECIMAL(3,2),  -- Out of 5
    
    -- Access Control
    allowed_job_categories TEXT[],  -- e.g., {"IT", "Engineering"}
    allowed_client_ids INTEGER[],   -- Restrict to specific clients
    submission_limit_per_month INTEGER DEFAULT 100,
    
    -- Status & Verification
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, suspended, pending
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP,
    
    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    
    CONSTRAINT valid_vendor_status CHECK (status IN ('active', 'inactive', 'suspended', 'pending'))
);

-- Vendor Submissions Tracking
CREATE TABLE vendor_submissions (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER REFERENCES vendors(id) ON DELETE CASCADE,
    candidate_id INTEGER REFERENCES candidates(id),
    job_id INTEGER REFERENCES jobs(id),
    resume_id INTEGER REFERENCES resumes(id),
    
    -- Submission Details
    submitted_at TIMESTAMP DEFAULT NOW(),
    vendor_notes TEXT,
    expected_salary DECIMAL(12,2),
    notice_period_days INTEGER,
    
    -- Status Tracking
    status VARCHAR(50) DEFAULT 'submitted',  -- submitted, accepted, rejected, interviewed, hired
    status_updated_at TIMESTAMP DEFAULT NOW(),
    rejection_reason TEXT,
    
    -- Commission Tracking
    commission_amount DECIMAL(12,2),
    commission_status VARCHAR(50),  -- pending, approved, paid
    commission_paid_at TIMESTAMP,
    
    UNIQUE(vendor_id, candidate_id, job_id)
);

-- Vendor Performance Reviews
CREATE TABLE vendor_reviews (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER REFERENCES vendors(id),
    reviewer_id INTEGER REFERENCES users(id),
    submission_id INTEGER REFERENCES vendor_submissions(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_vendors_status ON vendors(status);
CREATE INDEX idx_vendors_code ON vendors(vendor_code);
CREATE INDEX idx_submissions_vendor ON vendor_submissions(vendor_id);
CREATE INDEX idx_submissions_job ON vendor_submissions(job_id);
CREATE INDEX idx_submissions_status ON vendor_submissions(status);
```

### API Endpoints

```python
# Vendor CRUD
POST   /api/v1/vendors                  # Create new vendor
GET    /api/v1/vendors                  # List all vendors (paginated)
GET    /api/v1/vendors/{id}             # Get vendor details
PUT    /api/v1/vendors/{id}             # Update vendor
DELETE /api/v1/vendors/{id}             # Soft delete vendor

# Vendor Submissions
POST   /api/v1/vendors/{id}/submit      # Submit candidate for job
GET    /api/v1/vendors/{id}/submissions # List vendor's submissions
GET    /api/v1/submissions/{id}         # Get submission details
PUT    /api/v1/submissions/{id}/status  # Update submission status

# Vendor Performance
GET    /api/v1/vendors/{id}/metrics     # Get performance metrics
GET    /api/v1/vendors/{id}/reviews     # Get vendor reviews
POST   /api/v1/vendors/{id}/reviews     # Add vendor review

# Commission Management
GET    /api/v1/vendors/{id}/commissions # List commissions
PUT    /api/v1/commissions/{id}/approve # Approve commission
PUT    /api/v1/commissions/{id}/pay     # Mark as paid

# Available Jobs (Vendor View)
GET    /api/v1/vendors/available-jobs   # Jobs vendor can submit for
```

### Frontend Pages

#### 1. Vendor List Page (`/vendors`)

**Layout:**
```
┌─ Vendors ──────────────────────────────────────────────────┐
│                                                             │
│  [+ Add Vendor]  [Import]  [Export]   🔍 Search...         │
│                                                             │
│  Filters: [ All Status ▼ ] [ All Types ▼ ] [ Success ▼ ]  │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐│
│  │ TalentX Agency         │ Staffing    │ Active │ [⋮]   ││
│  │ Code: VN001           │ Success: 78%│ ⭐4.5   │       ││
│  │ 45 Submissions        │ 35 Accepted │ 8 Hired │       ││
│  ├────────────────────────────────────────────────────────┤│
│  │ RecruitPro LLC        │ Recruiting  │ Active │ [⋮]   ││
│  │ Code: VN002           │ Success: 65%│ ⭐4.2   │       ││
│  │ 28 Submissions        │ 18 Accepted │ 5 Hired │       ││
│  └────────────────────────────────────────────────────────┘│
│                                                             │
│  Showing 1-10 of 23 vendors    [ < ] [ 1 2 3 ] [ > ]      │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Vendor Detail Page (Admin View)

**Layout:**
```
┌─ TalentX Agency (VN001) ────────────────────────────────────┐
│  [Edit Vendor] [Suspend] [View Submissions]                 │
│                                                              │
│  📊 Performance Metrics                                      │
│  ┌──────────────┬──────────────┬──────────────┬───────────┐ │
│  │📤 Submitted  │✅ Accepted   │🎯 Hired      │⭐ Rating  │ │
│  │      45      │      35      │      8       │  4.5/5    │ │
│  └──────────────┴──────────────┴──────────────┴───────────┘ │
│  Success Rate: 78% 📈 | Commission Earned: $45,000          │
│                                                              │
│  Agency Information                                          │
│  ┌──────────────────────────────────────────────────────── │
│  │ Type: Staffing Agency                                    │
│  │ Website: www.talentx.com                                 │
│  │ Email: contact@talentx.com                               │
│  │ Phone: +1 555-0200                                       │
│  │ Address: 456 Recruit Ave, New York, NY 10001            │
│  └────────────────────────────────────────────────────────  │
│                                                              │
│  Contract Details                                            │
│  ┌──────────────────────────────────────────────────────── │
│  │ Commission Rate: 15%                                     │
│  │ Payment Terms: Net 30                                    │
│  │ Contract Period: Jan 1, 2025 - Dec 31, 2025            │
│  │ Monthly Limit: 35/100 submissions used                   │
│  │ [View Contract] [Renew Contract]                         │
│  └────────────────────────────────────────────────────────  │
│                                                              │
│  Access Permissions                                          │
│  ┌──────────────────────────────────────────────────────── │
│  │ Allowed Categories: IT, Engineering, Sales               │
│  │ Assigned Clients: TechCorp, StartupXYZ                   │
│  │ [Manage Permissions]                                     │
│  └────────────────────────────────────────────────────────  │
│                                                              │
│  Recent Submissions              [View All]                  │
│  ┌──────────────────────────────────────────────────────── │
│  │ John Doe → TechCorp (Java Dev) │ Shortlisted │ Oct 12  │
│  │ Jane Smith → StartupXYZ (Designer) │ Hired │ Oct 10    │
│  │ Mike Johnson → TechCorp (DevOps) │ Under Review│ Oct 11│
│  └────────────────────────────────────────────────────────  │
│                                                              │
│  Commission Summary                                          │
│  ┌──────────────────────────────────────────────────────── │
│  │ Pending: $12,500 (3 placements)                          │
│  │ Approved: $8,000 (2 placements)                          │
│  │ Paid: $24,500 (3 placements)                             │
│  │ [View Commission Details]                                │
│  └────────────────────────────────────────────────────────  │
└──────────────────────────────────────────────────────────────┘
```

#### 3. Vendor Dashboard (Vendor User View)

See `MVP-1_ROLE_BASED_FLOWS.md` for complete vendor dashboard design.

### Business Logic

**Vendor Onboarding:**
1. Admin creates vendor account
2. Sets commission rate, contract terms
3. Defines access permissions (job categories, clients)
4. Vendor receives credentials and onboarding email
5. Vendor can browse available jobs and submit candidates

**Submission Workflow:**
1. Vendor browses available jobs
2. Selects job and uploads candidate resume
3. System runs authenticity check (must pass threshold)
4. Vendor adds notes and salary expectations
5. Submission created with "submitted" status
6. HR/Admin receives notification
7. HR reviews and accepts/rejects submission
8. Vendor tracked in vendor_submissions table

**Commission Calculation:**
1. Candidate hired → Commission automatically calculated
2. Commission = (Candidate Salary × Commission Rate)
3. Status: "pending" → awaits admin approval
4. Admin approves → Status: "approved"
5. Payment processed → Status: "paid"
6. Vendor can track all commissions in dashboard

---

## Integration Points

### With Existing Features

**Job Management:**
- Jobs can be linked to clients
- Jobs can be made available to specific vendors
- Filter jobs by client or vendor availability

**Candidate Management:**
- Track candidate source (vendor_id if vendor-submitted)
- Vendor-submitted candidates marked in UI
- Vendor notes visible to HR team

**User Management:**
- Client contacts can be converted to HR users
- Vendor contacts get limited platform access
- Role-based permissions enforce access control

**Analytics:**
- Client-specific recruitment metrics
- Vendor performance dashboards
- Commission reports and tracking

---

## Implementation Priority

### Phase 1 (Weeks 7-8): Client Management
- Database schema and migrations
- Backend API endpoints
- Client list and detail pages
- HR assignment functionality
- Basic metrics display

### Phase 2 (Weeks 9-10): Vendor Management
- Database schema and migrations
- Backend API endpoints
- Vendor list and detail pages
- Submission workflow
- Performance tracking

### Phase 3 (Week 11): Integration
- Link existing jobs to clients
- Enable vendor submissions for jobs
- Update candidate views to show source
- Commission calculation automation

### Phase 4 (Week 12): Testing & Polish
- End-to-end testing
- Performance optimization
- UI/UX refinements
- Documentation

---

## Success Metrics

**Client Management:**
- All jobs linked to clients
- HR managers assigned to clients
- Client metrics displaying correctly
- Subscription limits enforced

**Vendor Management:**
- Vendors can submit candidates
- Submissions tracked accurately
- Performance metrics calculated
- Commission tracking functional

**Overall:**
- No data integrity issues
- Fast performance (<2sec page loads)
- Intuitive user experience
- Complete audit trail
