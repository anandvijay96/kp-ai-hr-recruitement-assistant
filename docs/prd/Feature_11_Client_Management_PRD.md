# Feature 11: Client Management - Product Requirements Document

**Document Version**: 1.0  
**Last Updated**: 2025-10-10  
**Status**: Draft  
**Owner**: Product Team  

---

## 1. OVERVIEW

### Description
Client Management is a comprehensive module that enables HR teams to manage client organizations requesting recruitment or HR-related services. It provides centralized client information storage, relationship tracking, job request management, communication history, and performance evaluation capabilities.

### Problem Statement
- **Scattered Client Data**: Client information stored across emails, spreadsheets, and personal notes
- **Lost Communication History**: No centralized record of client interactions, leading to context loss during handoffs
- **Poor Visibility**: Lack of dashboard showing client activity, active jobs, and candidate pipeline per client
- **Manual Tracking**: No automated way to track client satisfaction and service delivery metrics
- **Relationship Gaps**: Difficulty maintaining consistent client relationships when account managers change
- **Compliance Risk**: Insufficient audit trail for client communications and agreements

### Target Users
1. **HR Admins** (Primary) - Full client management capabilities, deactivation rights
2. **HR Managers** (Primary) - Create and manage clients, submit feedback, generate reports
3. **Recruiters** (Secondary) - View client details and linked job requests

---

## 2. USER STORIES

### Story 1: Client Profile Creation
**As an** HR Admin  
**I want** to create comprehensive client profiles with contact information, industry details, and account manager assignment  
**So that** all client information is centralized and accessible to the team

### Story 2: Client Dashboard View
**As an** HR Manager  
**I want** to view a unified dashboard showing all client activities, active jobs, candidate status, and key metrics  
**So that** I can quickly assess client health and make informed decisions

### Story 3: Communication Tracking
**As a** Recruiter  
**I want** to log all client interactions (meetings, calls, emails) with notes and attachments  
**So that** the entire team has visibility into client communications and can maintain context

### Story 4: Client Performance Evaluation
**As an** HR Manager  
**I want** to collect and analyze client feedback and collaboration metrics  
**So that** I can identify areas for service improvement and strengthen client relationships

### Story 5: Job Request Linking
**As an** HR Manager  
**I want** to associate job postings with specific clients and track their recruitment pipeline  
**So that** I can monitor service delivery and candidate progress per client

---

## 3. ACCEPTANCE CRITERIA

### Story 1: Client Profile Creation

**Functional Requirements**:
- [ ] Create client form with fields: name, industry, address, primary contact, email, phone, website
- [ ] Auto-generate unique Client ID (format: CLT-YYYY-XXXX)
- [ ] Assign account manager (dropdown of HR Managers/Admins)
- [ ] Support multiple contact persons per client
- [ ] Email and phone number validation
- [ ] Duplicate client detection (by name and email domain)
- [ ] Client status: Active, Inactive, On-Hold, Archived
- [ ] Upload client logo (max 2MB, PNG/JPG)

**Non-Functional Requirements**:
- Client creation completes in < 2 seconds
- Client ID must be unique and immutable
- Only HR Admins can deactivate or delete clients

### Story 2: Client Dashboard View

**Functional Requirements**:
- [ ] Dashboard displays: Client info, active jobs count, total candidates, placements, revenue
- [ ] Timeline view of recent activities (jobs posted, candidates submitted, hires)
- [ ] Quick stats: Open positions, candidates in pipeline, avg. time-to-fill
- [ ] Filter by: Status, industry, account manager, date range
- [ ] Export dashboard data as PDF report
- [ ] Auto-refresh data daily at midnight
- [ ] Drill-down to job details and candidate lists

**Non-Functional Requirements**:
- Dashboard loads in < 3 seconds
- Support pagination for clients (20 per page)
- Mobile-responsive design

### Story 3: Communication Tracking

**Functional Requirements**:
- [ ] Log communication with: Type (meeting/call/email), date/time, participants, subject, notes
- [ ] Upload attachments (contracts, meeting notes, proposals) - max 10MB per file
- [ ] Tag communications with related job or project reference
- [ ] Search and filter communication history
- [ ] Communication types: Meeting, Phone Call, Email, Video Call, Contract Signed
- [ ] Mark communications as important/follow-up required
- [ ] Automatic email logging via integration (optional)
- [ ] Communication records are immutable (cannot be deleted, only marked as archived)

**Non-Functional Requirements**:
- Communication log loads in < 2 seconds
- Support up to 1000 communication records per client
- Attachments stored securely with access control

### Story 4: Client Performance Evaluation

**Functional Requirements**:
- [ ] Feedback form with ratings: Responsiveness, Communication, Requirements Clarity, Decision Speed
- [ ] Overall satisfaction score (1-5 stars)
- [ ] Written feedback field (optional)
- [ ] Quarterly feedback collection reminder
- [ ] Performance report generation with trend charts
- [ ] Compare client performance across time periods
- [ ] Only HR Managers can finalize performance reports
- [ ] Feedback history tracking

**Non-Functional Requirements**:
- Feedback submission completes in < 2 seconds
- Reports generate in < 5 seconds
- Historical data retained for 5 years

### Story 5: Job Request Linking

**Functional Requirements**:
- [ ] Link job postings to client during job creation
- [ ] View all jobs associated with a client
- [ ] Track candidate pipeline per client (screened, shortlisted, interviewed, hired)
- [ ] Client-specific job analytics: Time-to-fill, candidate quality, offer acceptance rate
- [ ] Bulk link existing jobs to clients
- [ ] Unlink jobs (with audit trail)

**Non-Functional Requirements**:
- Job linking is immediate
- Support up to 500 jobs per client
- Maintain referential integrity

---

## 4. TECHNICAL DESIGN

### Database Schema

#### Table: `clients`
```sql
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    website VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    logo_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active',
    account_manager_id UUID REFERENCES users(id),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deactivated_at TIMESTAMP,
    deactivation_reason TEXT,
    
    INDEX idx_clients_status (status),
    INDEX idx_clients_account_manager (account_manager_id),
    INDEX idx_clients_industry (industry)
);
```

#### Table: `client_contacts`
```sql
CREATE TABLE client_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    title VARCHAR(100),
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    mobile VARCHAR(50),
    is_primary BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_client_contacts_client_id (client_id),
    INDEX idx_client_contacts_email (email)
);
```

#### Table: `client_communications`
```sql
CREATE TABLE client_communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    communication_type VARCHAR(50) NOT NULL,
    subject VARCHAR(500),
    notes TEXT,
    communication_date TIMESTAMP NOT NULL,
    participants JSONB,
    job_reference_id UUID REFERENCES jobs(id),
    logged_by UUID NOT NULL REFERENCES users(id),
    is_important BOOLEAN DEFAULT false,
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_date DATE,
    attachments JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_client_communications_client_id (client_id),
    INDEX idx_client_communications_date (communication_date),
    INDEX idx_client_communications_type (communication_type)
);
```

#### Table: `client_feedback`
```sql
CREATE TABLE client_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    feedback_period VARCHAR(20),
    feedback_date DATE NOT NULL,
    responsiveness_rating INTEGER CHECK (responsiveness_rating BETWEEN 1 AND 5),
    communication_rating INTEGER CHECK (communication_rating BETWEEN 1 AND 5),
    requirements_clarity_rating INTEGER CHECK (requirements_clarity_rating BETWEEN 1 AND 5),
    decision_speed_rating INTEGER CHECK (decision_speed_rating BETWEEN 1 AND 5),
    overall_satisfaction INTEGER CHECK (overall_satisfaction BETWEEN 1 AND 5),
    written_feedback TEXT,
    submitted_by UUID NOT NULL REFERENCES users(id),
    finalized_by UUID REFERENCES users(id),
    is_finalized BOOLEAN DEFAULT false,
    finalized_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_client_feedback_client_id (client_id),
    INDEX idx_client_feedback_date (feedback_date)
);
```

#### Table: `client_job_assignments`
```sql
CREATE TABLE client_job_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    assigned_by UUID NOT NULL REFERENCES users(id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    unassigned_at TIMESTAMP,
    unassigned_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(client_id, job_id),
    INDEX idx_client_job_assignments_client_id (client_id),
    INDEX idx_client_job_assignments_job_id (job_id)
);
```

#### Table: `client_analytics`
```sql
CREATE TABLE client_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    active_jobs_count INTEGER DEFAULT 0,
    total_candidates_count INTEGER DEFAULT 0,
    screened_count INTEGER DEFAULT 0,
    shortlisted_count INTEGER DEFAULT 0,
    interviewed_count INTEGER DEFAULT 0,
    hired_count INTEGER DEFAULT 0,
    avg_time_to_fill_days DECIMAL(10,2),
    avg_candidate_quality_score DECIMAL(5,2),
    revenue_generated DECIMAL(15,2),
    
    UNIQUE(client_id, date),
    INDEX idx_client_analytics_client_id (client_id),
    INDEX idx_client_analytics_date (date)
);
```

#### Modifications to Existing Tables

```sql
-- Add client_id to jobs table
ALTER TABLE jobs ADD COLUMN client_id UUID REFERENCES clients(id);
CREATE INDEX idx_jobs_client_id ON jobs(client_id);

-- Add client_id to resumes table for direct client submissions
ALTER TABLE resumes ADD COLUMN client_id UUID REFERENCES clients(id);
CREATE INDEX idx_resumes_client_id ON resumes(client_id);
```

### API Endpoints

#### 1. Create Client
```
POST /api/clients
Authorization: HR Admin, HR Manager

Request Body:
{
    "name": "Tech Corp Inc.",
    "industry": "Information Technology",
    "website": "https://techcorp.com",
    "address": "123 Tech Street",
    "city": "San Francisco",
    "state": "CA",
    "country": "USA",
    "postal_code": "94102",
    "account_manager_id": "uuid",
    "contacts": [
        {
            "full_name": "John Doe",
            "title": "HR Director",
            "email": "john@techcorp.com",
            "phone": "+1-555-1234",
            "is_primary": true
        }
    ]
}

Response: 201 Created
{
    "id": "uuid",
    "client_code": "CLT-2025-0001",
    "name": "Tech Corp Inc.",
    "status": "active",
    "created_at": "2025-10-10T11:52:15Z"
}
```

#### 2. List Clients
```
GET /api/clients
Query: status, industry, account_manager_id, search, sort_by, page, limit
Response: 200 OK with clients[], pagination, summary
```

#### 3. Get Client Details
```
GET /api/clients/{client_id}
Response: 200 OK with full client details, contacts, stats
```

#### 4. Update Client
```
PUT /api/clients/{client_id}
Authorization: HR Admin, HR Manager
Body: Updated client fields
```

#### 5. Deactivate Client
```
POST /api/clients/{client_id}/deactivate
Authorization: HR Admin only
Body: {reason, reason_details}
```

#### 6. Get Client Dashboard
```
GET /api/clients/{client_id}/dashboard
Response: Client info, active jobs, pipeline summary, metrics
```

#### 7-9. Communication Endpoints
```
POST /api/clients/{client_id}/communications
GET /api/clients/{client_id}/communications
POST /api/clients/{client_id}/communications/{comm_id}/attachments
```

#### 10-12. Feedback Endpoints
```
POST /api/clients/{client_id}/feedback
GET /api/clients/{client_id}/feedback
POST /api/clients/{client_id}/reports/performance
```

#### 13-14. Job Linking Endpoints
```
POST /api/clients/{client_id}/jobs/{job_id}
GET /api/clients/{client_id}/jobs
```

#### 15. Bulk Operations
```
POST /api/clients/bulk-operations
Body: {client_ids[], operation, parameters, dry_run}
```

### UI Components and User Flow

**Client List Page** (`/clients`): Search, filter, client cards, pagination  
**Client Dashboard** (`/clients/{id}`): Info card, stats, timeline, tabs  
**Client Creation** (`/clients/new`): Multi-step form with validation  
**Communication Log**: Timeline view with filter and log form  
**Feedback Form**: Rating sliders, text area, period selector  

### Integration Points

1. **Job Management Module** - Link jobs to clients
2. **Resume Tracking System** - Track candidates per client
3. **Email Gateway** - Notifications and communication logging
4. **CRM System** - Optional sync for extended features
5. **Cloud Storage** - Store logos, attachments, reports
6. **Analytics Dashboard** - Client performance metrics

---

## 5. DEPENDENCIES

### External Libraries
```
pydantic[email]==2.5.0
phonenumbers==8.13.26
pandas==2.1.3
matplotlib==3.8.2
reportlab==4.0.7
pillow==10.1.0
python-magic==0.4.27
fastapi-mail==1.4.1
celery==5.3.4
redis==5.0.1
```

### External Services
- Email Service (SendGrid/AWS SES)
- Cloud Storage (AWS S3/Azure Blob)
- GeoIP Service (optional)
- CRM Integration (Salesforce/HubSpot - optional)

### Internal Dependencies
- Job Management Module (must exist)
- User Management Module (for account managers)
- Resume Tracking Module (for pipeline)
- Authentication System (for RBAC)

### New Modules to Create
1. `services/client_management_service.py`
2. `services/client_communication_service.py`
3. `services/client_feedback_service.py`
4. `services/client_analytics_service.py`
5. `api/clients.py`
6. `templates/clients/` directory

---

## 6. TESTING PLAN

### Unit Tests
- Client CRUD operations
- Client code auto-generation
- Duplicate detection
- Communication logging
- Attachment validation
- Feedback submission and validation
- Rating calculations
- Analytics aggregation
- Report generation

### Integration Tests
- Client creation flow
- Dashboard data accuracy
- Communication with attachments
- Feedback submission and finalization
- Job linking and unlinking
- Bulk operations
- Email notifications

### Manual Testing Scenarios

**Scenario 1: New Client Onboarding**
1. Create client "Acme Corp"
2. Add contacts
3. Assign account manager
4. Upload logo
5. Link jobs
6. Verify dashboard
**Expected**: Client created, dashboard accurate

**Scenario 2: Communication Tracking**
1. Log meeting
2. Upload notes
3. Tag with job
4. Mark follow-up
5. View history
**Expected**: Communication visible, attachment downloadable

**Scenario 3: Performance Review**
1. Submit Q3 feedback
2. Rate criteria
3. Generate report
4. Compare with Q2
**Expected**: Feedback saved, report with trends

### Edge Cases
- Duplicate client detection
- File size/format validation
- Rating range validation
- Job linking conflicts
- Account manager changes
- Performance with large datasets

---

## 7. IMPLEMENTATION PLAN

### Phase 1: Foundation & Core CRUD (Weeks 1-2) - 75 hours
- Database setup and migrations
- Client management service
- Core API endpoints (CRUD)
- Client list and creation UI

**Risks**: Schema changes require coordination  
**Mitigation**: Team review, backward-compatible migrations

### Phase 2: Dashboard & Analytics (Weeks 3-4) - 80 hours
- Analytics service and aggregation
- Dashboard UI with charts
- Performance metrics
- Report generation
- Job linking functionality

**Risks**: Performance with large datasets  
**Mitigation**: Caching, query optimization, background jobs

### Phase 3: Communication & Feedback (Weeks 5-6) - 70 hours
- Communication service
- Attachment handling
- Feedback service
- Communication and feedback UI
- Email notifications

**Risks**: File upload security  
**Mitigation**: Virus scanning, validation, secure storage

### Phase 4: Advanced Features (Weeks 7-8) - 60 hours
- Bulk operations
- External integrations
- UI polish and responsiveness
- Performance optimization

**Risks**: Integration failures  
**Mitigation**: Retry mechanisms, error handling, fallbacks

### Phase 5: Testing & Documentation (Week 9) - 40 hours
- Unit and integration tests (85% coverage)
- Manual testing
- Performance and security testing
- Documentation (API, user, developer)
- Deployment and monitoring

**Risks**: Late-stage bugs  
**Mitigation**: Continuous testing, early beta

**Total**: 9 weeks, 325 hours

---

## 8. SUCCESS METRICS

### Primary Metrics
1. **Feature Adoption**: 90% of HR Managers use within first month
2. **Client Data Centralization**: 100% of active clients in system within 3 months
3. **Communication Logging**: 80% of client interactions logged
4. **Feedback Completion**: 75% quarterly feedback completion rate

### Performance Metrics
1. **Dashboard Load Time**: < 3 seconds (95th percentile)
2. **Client Creation**: < 2 seconds
3. **Communication Log**: < 2 seconds
4. **Report Generation**: < 5 seconds
5. **System Uptime**: 99.5%

### Quality Metrics
1. **Bug Rate**: < 2 critical bugs/month
2. **Test Coverage**: ≥ 85%
3. **API Error Rate**: < 0.5%
4. **User Satisfaction**: > 4.0/5.0

### Business Impact
1. **Client Retention**: Improve by 15%
2. **Response Time**: Reduce by 30%
3. **Account Manager Efficiency**: Increase by 40%
4. **Client Satisfaction**: Increase by 20%

### Monitoring
- **Daily**: API errors, uptime, background jobs
- **Weekly**: Feature usage, performance metrics
- **Monthly**: Success metrics, user surveys

---

**End of Document**
