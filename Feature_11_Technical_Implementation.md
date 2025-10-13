# Feature 11: Client Management - Technical Implementation Guide

**Version**: 1.0  
**Date**: 2025-10-10  
**Status**: Implementation Ready

---

## 1. DATABASE DESIGN

### New Tables

**`clients`**
- `id` (String/UUID, PK), `client_code` (String, Unique), `name` (String), `industry` (String)
- `website`, `address`, `city`, `state`, `country`, `postal_code`
- `logo_url` (String), `status` (String, default='active')
- `account_manager_id` (FK → users.id), `created_by` (FK → users.id)
- `created_at`, `updated_at`, `deactivated_at`, `deactivation_reason`
- **Indexes**: status, account_manager_id, industry

**`client_contacts`**
- `id` (PK), `client_id` (FK → clients.id, CASCADE)
- `full_name`, `title`, `email`, `phone`, `mobile`
- `is_primary` (Boolean), `is_active` (Boolean)
- `created_at`, `updated_at`
- **Indexes**: client_id, email

**`client_communications`**
- `id` (PK), `client_id` (FK → clients.id, CASCADE)
- `communication_type`, `subject`, `notes`, `communication_date`
- `participants` (JSONB), `job_reference_id` (FK → jobs.id, nullable)
- `logged_by` (FK → users.id), `is_important`, `follow_up_required`, `follow_up_date`
- `attachments` (JSONB), `created_at`
- **Indexes**: client_id, communication_date, communication_type

**`client_feedback`**
- `id` (PK), `client_id` (FK → clients.id, CASCADE)
- `feedback_period`, `feedback_date`
- `responsiveness_rating`, `communication_rating`, `requirements_clarity_rating`, `decision_speed_rating`
- `overall_satisfaction` (1-5 CHECK constraint)
- `written_feedback`, `submitted_by` (FK → users.id)
- `finalized_by` (FK → users.id), `is_finalized`, `finalized_at`, `created_at`
- **Indexes**: client_id, feedback_date

**`client_job_assignments`**
- `id` (PK), `client_id` (FK → clients.id, CASCADE), `job_id` (FK → jobs.id, CASCADE)
- `assigned_by` (FK → users.id), `assigned_at`
- `unassigned_at`, `unassigned_by` (FK → users.id), `is_active`
- **Unique**: (client_id, job_id)
- **Indexes**: client_id, job_id

**`client_analytics`**
- `id` (PK), `client_id` (FK → clients.id, CASCADE), `date` (Date)
- `active_jobs_count`, `total_candidates_count`, `screened_count`, `shortlisted_count`, `interviewed_count`, `hired_count`
- `avg_time_to_fill_days`, `avg_candidate_quality_score`, `revenue_generated`
- **Unique**: (client_id, date)
- **Indexes**: client_id, date

### Table Modifications

**`jobs`** - Add: `client_id` (FK → clients.id, nullable), Index on client_id  
**`resumes`** - Add: `client_id` (FK → clients.id, nullable), Index on client_id

### Migration Script
```python
# migrations/011_add_client_management.py
# - Create all 6 tables with constraints
# - Alter jobs and resumes tables
# - Create indexes
# - Add CHECK constraints for ratings (1-5)
# - Add status constraints ('active', 'inactive', 'on-hold', 'archived')
```

---

## 2. API DESIGN

### Endpoints Overview

**Client CRUD**
1. `POST /api/clients` - Create client (Admin, Manager)
2. `GET /api/clients` - List clients with filters (All)
3. `GET /api/clients/{id}` - Get client details (All)
4. `PUT /api/clients/{id}` - Update client (Admin, Manager)
5. `POST /api/clients/{id}/deactivate` - Deactivate (Admin only)
6. `POST /api/clients/{id}/reactivate` - Reactivate (Admin only)

**Dashboard & Analytics**
7. `GET /api/clients/{id}/dashboard` - Client dashboard (All)
8. `GET /api/clients/{id}/analytics` - Analytics data (All)
9. `POST /api/clients/{id}/reports/performance` - Generate report (Manager, Admin)

**Communications**
10. `POST /api/clients/{id}/communications` - Log communication (All)
11. `GET /api/clients/{id}/communications` - List communications (All)
12. `POST /api/clients/{id}/communications/{comm_id}/attachments` - Upload attachment (All)
13. `GET /api/clients/{id}/communications/{comm_id}/attachments/{att_id}` - Download attachment (All)

**Feedback**
14. `POST /api/clients/{id}/feedback` - Submit feedback (Manager, Admin)
15. `GET /api/clients/{id}/feedback` - List feedback (Manager, Admin)
16. `POST /api/clients/{id}/feedback/{feedback_id}/finalize` - Finalize feedback (Manager only)

**Job Linking**
17. `POST /api/clients/{id}/jobs/{job_id}` - Link job (Manager, Admin)
18. `DELETE /api/clients/{id}/jobs/{job_id}` - Unlink job (Manager, Admin)
19. `GET /api/clients/{id}/jobs` - List client jobs (All)

**Bulk Operations**
20. `POST /api/clients/bulk-operations` - Bulk update (Admin only)

### Pydantic Models (models/client_schemas.py)

**Request Schemas**
- `ClientContactCreate` - full_name, title, email, phone, mobile, is_primary
- `ClientCreateRequest` - name, industry, website, address, city, state, country, postal_code, account_manager_id, contacts[]
- `ClientUpdateRequest` - Partial fields from create
- `ClientDeactivateRequest` - reason, reason_details
- `CommunicationCreateRequest` - type, subject, notes, date, participants[], job_reference_id, is_important, follow_up_required, follow_up_date
- `FeedbackCreateRequest` - period, date, responsiveness_rating, communication_rating, requirements_clarity_rating, decision_speed_rating, overall_satisfaction, written_feedback
- `BulkOperationRequest` - client_ids[], operation, parameters{}, dry_run

**Response Schemas**
- `ClientContactResponse` - All fields + id, created_at
- `ClientResponse` - All fields + id, client_code, account_manager{}, contacts[], created_at
- `ClientListResponse` - clients[], pagination{total, page, limit, total_pages}, summary{active, inactive, on_hold, archived}
- `ClientDashboardResponse` - client{}, stats{active_jobs, total_candidates, hires, avg_time_to_fill}, recent_activities[], pipeline_summary{}
- `CommunicationResponse` - All fields + id, logged_by{}, attachments[]
- `FeedbackResponse` - All fields + id, submitted_by{}, finalized_by{}
- `AnalyticsResponse` - All analytics fields
- `BulkOperationResponse` - operation_id, status, results[], errors[]

### Query Parameters

**List Clients** (`GET /api/clients`)
- status, industry, account_manager_id, search, sort_by, page (default=1), limit (default=20, max=100)

**List Communications** (`GET /api/clients/{id}/communications`)
- type, date_from, date_to, important_only, page, limit

**List Jobs** (`GET /api/clients/{id}/jobs`)
- status, date_from, date_to

---

## 3. SERVICE LAYER

### services/client_management_service.py

**ClientManagementService**
- `__init__(db_session)` - Initialize with DB session
- `generate_client_code()` - Auto-generate CLT-YYYY-XXXX format
- `check_duplicate_client(name, email_domain)` - Duplicate detection
- `create_client(data, current_user)` - Create with contacts, return client
- `list_clients(filters, pagination)` - Query with filters, return list + pagination
- `get_client_by_id(client_id)` - Get full details with contacts
- `update_client(client_id, data, current_user)` - Update fields
- `deactivate_client(client_id, reason, current_user)` - Soft delete (admin only)
- `reactivate_client(client_id, current_user)` - Reactivate
- `add_contact(client_id, contact_data)` - Add contact person
- `update_contact(contact_id, data)` - Update contact
- `set_primary_contact(client_id, contact_id)` - Change primary

### services/client_communication_service.py

**ClientCommunicationService**
- `__init__(db_session, file_storage_service)` - Initialize
- `log_communication(client_id, data, current_user)` - Create record
- `list_communications(client_id, filters, pagination)` - Get history
- `upload_attachment(comm_id, file, current_user)` - Upload to S3/Azure, store metadata
- `download_attachment(comm_id, attachment_id, current_user)` - Generate presigned URL
- `mark_important(comm_id, is_important)` - Toggle importance
- `set_follow_up(comm_id, follow_up_date, notes)` - Set follow-up

### services/client_feedback_service.py

**ClientFeedbackService**
- `__init__(db_session)` - Initialize
- `submit_feedback(client_id, data, current_user)` - Create feedback
- `list_feedback(client_id, filters)` - Get feedback history
- `calculate_averages(client_id, date_from, date_to)` - Compute average ratings
- `finalize_feedback(feedback_id, current_user)` - Manager finalization
- `get_feedback_trends(client_id, periods)` - Trend analysis
- `generate_performance_report(client_id, date_from, date_to)` - PDF report with charts

### services/client_analytics_service.py

**ClientAnalyticsService**
- `__init__(db_session)` - Initialize
- `aggregate_daily_analytics(client_id, date)` - Calculate daily stats
- `get_dashboard_data(client_id)` - Fetch dashboard metrics
- `get_client_pipeline(client_id)` - Candidate counts by stage
- `calculate_time_to_fill(client_id)` - Average days
- `get_recent_activities(client_id, limit)` - Timeline events
- `export_dashboard_pdf(client_id)` - Generate PDF export
- Background job: `daily_analytics_aggregation()` - Run at midnight

### services/client_job_service.py

**ClientJobService**
- `__init__(db_session)` - Initialize
- `link_job_to_client(client_id, job_id, current_user)` - Create assignment
- `unlink_job(client_id, job_id, current_user)` - Soft delete, audit trail
- `bulk_link_jobs(client_id, job_ids, current_user)` - Bulk assignment
- `list_client_jobs(client_id, filters)` - Get jobs with stats
- `get_job_analytics(client_id, job_id)` - Job-specific metrics

---

## 4. UI/UX DESIGN

### Templates (templates/clients/)

**list.html** - Client list page
- Search bar, filter sidebar (status, industry, account manager)
- Client cards/table view toggle, pagination
- "Create Client" button (Manager, Admin only)

**create.html** - Client creation form
- Multi-step: Basic Info → Contacts → Review
- Validation: Email, phone, duplicate detection alert
- Logo upload preview

**detail.html** - Client dashboard
- Header: Client info card, account manager, status badge
- Stats widgets: Active jobs, candidates, placements, avg time-to-fill
- Tabs: Overview, Jobs, Communications, Feedback, Analytics
- Action buttons: Edit, Deactivate, Export PDF

**communications.html** - Communication log
- Timeline view with filters (type, date, important)
- "Log Communication" modal form
- Attachment icons with download links
- Follow-up indicators

**feedback.html** - Feedback form & history
- Rating sliders (1-5) with labels
- Written feedback textarea
- Feedback history table with trend charts
- "Generate Report" button

**dashboard_tab.html** - Dashboard overview tab
- Recent activities timeline (last 30 days)
- Pipeline funnel chart (candidates by stage)
- Job status pie chart
- Quick actions panel

### Static Files (static/clients/)

**clients.js**
- Form validation, AJAX submissions
- Duplicate detection on name blur
- Dynamic contact person add/remove
- Chart rendering (Chart.js)
- File upload with progress bar

**clients.css**
- Client card styling, status badges
- Timeline component styles
- Dashboard grid layout
- Rating slider styling

### User Flows

**Create Client**: Dashboard → Clients → Create → Fill form → Add contacts → Submit → Redirect to client detail  
**Log Communication**: Client detail → Communications tab → Log → Fill modal → Upload attachment → Submit → Refresh timeline  
**Submit Feedback**: Client detail → Feedback tab → Submit → Rate criteria → Add notes → Submit → View history  
**Link Job**: Client detail → Jobs tab → Link Job → Search/select job → Confirm → Refresh list

---

## 5. INTEGRATION POINTS

### Existing Modules

**Job Management** (`api/jobs.py`, `services/job_service.py`)
- Modify: Add `client_id` to job creation form
- Update: Job detail page to show client name (if linked)
- Integration: Filter jobs by client in job list

**User Management** (`services/user_management_service.py`)
- Use: Get account managers list (role='manager' or 'admin')
- Integration: User dropdown in client form

**Resume Tracking** (`api/candidates.py`, `services/candidate_service.py`)
- Query: Count candidates per client via job linkage
- Integration: Candidate pipeline metrics for dashboard

**File Storage** (`services/file_storage_service.py`)
- Use: Upload client logos and communication attachments
- Methods: `upload_file()`, `generate_download_url()`, `delete_file()`

**Email Service** (`services/email_service.py`)
- Use: Send welcome emails, feedback reminders
- Templates: `client_welcome.html`, `feedback_reminder.html`

**Permission Service** (`services/permission_service.py`)
- Use: Check user permissions for deactivate, finalize feedback
- Methods: `check_permission()`, `require_role()`

### External Services

**AWS S3 / Azure Blob** - Logo and attachment storage, presigned URLs for downloads  
**SendGrid / AWS SES** - Email notifications  
**ReportLab / Matplotlib** - PDF report generation with charts  
**Celery + Redis** - Background jobs for analytics aggregation, report generation

### New Integration Code

**main.py** - Add client router
```python
from api.clients import router as clients_router
app.include_router(clients_router, prefix="/api/clients", tags=["Clients"])
```

**Background Jobs** (celery_tasks.py)
```python
@celery_app.task
def daily_client_analytics():
    # Run at midnight, aggregate analytics for all clients
    pass

@celery_app.task
def send_quarterly_feedback_reminders():
    # Check last feedback date, send reminders
    pass
```

---

## 6. FILE STRUCTURE

### New Files to Create

```
models/
  client_schemas.py              # Pydantic schemas (20+ models)

services/
  client_management_service.py   # Core CRUD (~400 lines)
  client_communication_service.py # Communication logic (~250 lines)
  client_feedback_service.py     # Feedback & reports (~200 lines)
  client_analytics_service.py    # Analytics aggregation (~300 lines)
  client_job_service.py          # Job linking (~150 lines)

api/
  clients.py                     # API endpoints (~600 lines)

templates/clients/
  list.html                      # Client list
  create.html                    # Create form
  detail.html                    # Client dashboard
  communications.html            # Communication log
  feedback.html                  # Feedback form
  _client_card.html              # Reusable client card component
  _communication_modal.html      # Communication form modal
  _feedback_form.html            # Feedback form component

static/clients/
  clients.js                     # Client-specific JS
  clients.css                    # Client-specific CSS

migrations/
  011_add_client_management.py   # Database migration

tests/
  test_client_management_service.py    # Unit tests
  test_client_communication_service.py
  test_client_feedback_service.py
  test_client_analytics_service.py
  test_clients_api.py                  # Integration tests
```

### Files to Modify

**models/database.py** - Add Client, ClientContact, ClientCommunication, ClientFeedback, ClientJobAssignment, ClientAnalytics models  
**main.py** - Import and include clients router  
**api/jobs.py** - Add client_id to job creation endpoint  
**templates/jobs/create.html** - Add client dropdown  
**templates/jobs/detail.html** - Display client name  
**services/job_service.py** - Update create_job to accept client_id  
**requirements.txt** - Add: matplotlib, reportlab, phonenumbers  
**.env** - Add: S3_BUCKET_NAME, S3_REGION, SENDGRID_API_KEY

---

## 7. TESTING STRATEGY

### Unit Tests

**test_client_management_service.py**
- `test_generate_client_code()` - Format validation
- `test_create_client_success()` - Valid creation
- `test_create_client_duplicate()` - Duplicate detection
- `test_update_client()` - Update fields
- `test_deactivate_client_admin_only()` - Permission check
- `test_list_clients_with_filters()` - Filter logic

**test_client_communication_service.py**
- `test_log_communication()` - Create record
- `test_upload_attachment()` - File validation, storage
- `test_attachment_size_limit()` - Max 10MB check
- `test_list_communications_with_filters()` - Date, type filters

**test_client_feedback_service.py**
- `test_submit_feedback()` - Valid submission
- `test_rating_validation()` - 1-5 range check
- `test_calculate_averages()` - Average computation
- `test_finalize_feedback_manager_only()` - Permission check
- `test_generate_report()` - PDF generation

**test_client_analytics_service.py**
- `test_aggregate_daily_analytics()` - Correct counts
- `test_dashboard_metrics()` - Accurate calculations
- `test_time_to_fill_calculation()` - Date math

### Integration Tests

**test_clients_api.py**
- `test_create_client_flow()` - POST → GET verification
- `test_client_list_pagination()` - Page navigation
- `test_log_communication_with_attachment()` - Full upload flow
- `test_feedback_submission_and_finalization()` - Multi-step workflow
- `test_link_job_to_client()` - Job assignment
- `test_bulk_operations()` - Bulk update
- `test_unauthorized_access()` - Permission enforcement

### Manual Testing Checklist

- [ ] Create client with 3 contacts, verify primary contact badge
- [ ] Upload logo > 2MB, confirm error
- [ ] Log 10 communications, test filtering by type and date
- [ ] Upload PDF attachment, download and verify
- [ ] Submit feedback with ratings 1-5, check validation
- [ ] Generate performance report, verify charts and data
- [ ] Link 5 jobs to client, verify dashboard stats update
- [ ] Deactivate client as recruiter, confirm permission denied
- [ ] Deactivate as admin, verify jobs remain linked
- [ ] Test pagination with 50+ clients
- [ ] Test dashboard load time with 500 jobs
- [ ] Test search by client name (partial match)

### Performance Tests
- Dashboard load with 500+ jobs: < 3s
- Communication list with 1000 records: < 2s
- Report generation: < 5s
- Bulk operation (50 clients): < 30s

---

## 8. DEPLOYMENT CONSIDERATIONS

### Environment Variables (.env)
```bash
# Storage
S3_BUCKET_NAME=hr-app-client-files
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>

# Email
SENDGRID_API_KEY=<key>
FEEDBACK_REMINDER_FROM_EMAIL=noreply@hrapp.com

# Features
ENABLE_CLIENT_MANAGEMENT=true
CLIENT_LOGO_MAX_SIZE_MB=2
COMMUNICATION_ATTACHMENT_MAX_SIZE_MB=10
```

### Migration Steps
1. **Backup database**: `pg_dump hrdb > backup_pre_feature11.sql`
2. **Run migration**: `python migrations/011_add_client_management.py`
3. **Verify tables**: Check all 6 tables created, indexes added
4. **Test rollback**: Ensure migration is reversible
5. **Deploy code**: Update services, API, templates
6. **Restart services**: Celery workers for background jobs
7. **Verify**: Create test client, log communication, submit feedback

### Background Jobs Setup

**Celery Beat Schedule** (Add to celery config)
```python
beat_schedule = {
    'daily-client-analytics': {
        'task': 'celery_tasks.daily_client_analytics',
        'schedule': crontab(hour=0, minute=0),  # Midnight daily
    },
    'quarterly-feedback-reminders': {
        'task': 'celery_tasks.send_quarterly_feedback_reminders',
        'schedule': crontab(day_of_month=1, hour=9),  # 1st of month, 9 AM
    },
}
```

### Database Indexes (Performance)
- Ensure indexes on: clients.status, clients.account_manager_id, client_communications.client_id, client_communications.communication_date
- Add composite index: (client_id, date) on client_analytics for dashboard queries

### Monitoring & Alerts
- **Datadog/New Relic**: Track API response times (target: p95 < 3s for dashboard)
- **Sentry**: Error tracking for failed uploads, report generation
- **Cloudwatch/Application Insights**: Monitor S3 upload failures, email delivery
- **Alerts**: Dashboard load > 5s, report generation > 10s, failed background jobs

### Security Checklist
- [ ] File upload validation (magic bytes, not just extension)
- [ ] Virus scanning for attachments (ClamAV or cloud service)
- [ ] Rate limiting on bulk operations (max 50 clients)
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (sanitize client names, notes in templates)
- [ ] RBAC enforcement on all endpoints (permission decorators)
- [ ] Attachment access control (presigned URLs with expiration)
- [ ] Audit logging for deactivations, bulk operations

### Rollback Plan
1. **Code rollback**: Revert to previous deployment
2. **Database rollback**: Run reverse migration (drop tables, remove columns)
3. **Data preservation**: Export client data before rollback if needed
4. **Communication**: Notify users of downtime (if required)

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Database & Models (Week 1)
- [ ] Create migration script 011_add_client_management.py
- [ ] Define database models in models/database.py
- [ ] Create Pydantic schemas in models/client_schemas.py
- [ ] Run migration on dev database
- [ ] Test table creation and constraints

### Phase 2: Core Services (Week 2)
- [ ] Implement client_management_service.py
- [ ] Implement client_job_service.py
- [ ] Write unit tests for core services
- [ ] Test client CRUD operations

### Phase 3: API Endpoints (Week 3)
- [ ] Create api/clients.py with all 20 endpoints
- [ ] Add authentication/authorization decorators
- [ ] Write integration tests for APIs
- [ ] Test with Postman/Swagger

### Phase 4: Communication & Feedback (Week 4)
- [ ] Implement client_communication_service.py
- [ ] Implement client_feedback_service.py
- [ ] Add file upload handling
- [ ] Test attachment upload/download

### Phase 5: Analytics & Reports (Week 5)
- [ ] Implement client_analytics_service.py
- [ ] Add report generation (PDF)
- [ ] Create Celery tasks for background jobs
- [ ] Test analytics aggregation

### Phase 6: UI Development (Week 6-7)
- [ ] Create all template files
- [ ] Implement clients.js with validation
- [ ] Style with clients.css
- [ ] Test responsive design

### Phase 7: Integration (Week 8)
- [ ] Update job creation to include client_id
- [ ] Integrate with file storage service
- [ ] Integrate with email service
- [ ] Test end-to-end workflows

### Phase 8: Testing & Deployment (Week 9)
- [ ] Complete all unit tests (85% coverage)
- [ ] Complete integration tests
- [ ] Manual testing checklist
- [ ] Performance testing
- [ ] Security review
- [ ] Deploy to staging
- [ ] User acceptance testing
- [ ] Deploy to production
- [ ] Monitor for 48 hours

---

**End of Technical Implementation Guide**

*For detailed code examples, refer to existing services like `services/user_management_service.py` and `api/users.py` for similar patterns.*
