# Product Requirements Document (PRD)
# AI Powered Resume Tracker for HR Teams

**Document Version:** 1.0  
**Author:** Product Management Team  
**Date:** 2025-10-01  
**Status:** Draft  
**Priority:** High  

---

## 📋 Executive Summary

This PRD outlines requirements for an AI-powered HR Resume Tracker portal that streamlines recruitment, automates candidate evaluation, and provides intelligent job-candidate matching for HR teams.

**Product Vision**: Create an intelligent recruitment management system combining AI automation with human expertise to optimize hiring, reduce time-to-hire, and improve candidate quality.

**Target Users**: HR Administrators, HR Managers, Recruiters

---

## 🎯 Business Objectives

1. Reduce time-to-hire by 60% through automation
2. Improve candidate quality by 40% via AI matching
3. Enhance recruitment pipeline transparency
4. Enable data-driven hiring decisions
5. Streamline HR team collaboration

---

## 🏗️ System Architecture Overview

**Technology Stack**:
- Backend: Python 3.10+, FastAPI
- Frontend: Bootstrap 5, Jinja2, JavaScript
- Database: PostgreSQL
- AI/ML: PyMuPDF, pdfplumber, python-docx, NLTK, spaCy, scikit-learn
- Task Queue: Celery + Redis
- Authentication: JWT

---

## 🎨 Feature Specifications

## Feature 1: User Creation & Authentication

**Overview**: Secure authentication system for HR team members with role-based access control.

**Key Capabilities**:
- User registration with email verification
- Secure login/logout
- Password recovery
- Session management
- Account activation/deactivation

**Data Schema** (users table):
```
- id (UUID, PK)
- full_name, email (unique), mobile
- password_hash, role (admin/manager/recruiter)
- is_active, email_verified
- created_at, updated_at, last_login
```

**Business Rules**:
- Unique email per user
- Password: min 8 chars, uppercase, lowercase, number, special char
- Account locked after 5 failed login attempts (15 min cooldown)
- Sessions expire after 24 hours inactivity

**API Endpoints**:
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/forgot-password` - Password reset request
- `POST /api/auth/reset-password` - Password reset
- `GET /api/auth/verify-email/{token}` - Email verification

---

## Feature 2: Resume Upload

**Overview**: Multi-format resume upload with drag-drop, bulk upload, and virus scanning.

**Key Capabilities**:
- Single/bulk upload (up to 50 files)
- Formats: PDF, DOCX, TXT
- Real-time progress indicators
- Virus scanning
- Duplicate detection
- Resume preview

**Data Schema** (resumes table):
```
- id (UUID, PK)
- file_name, file_path, file_size, file_type, file_hash
- candidate_name, candidate_email, candidate_phone
- extracted_text, parsed_data (JSONB)
- uploaded_by (FK users), upload_date
- status (uploaded/parsing/parsed/failed)
- virus_scan_status
```

**Business Rules**:
- Max file size: 10MB
- Bulk limit: 50 files
- Duplicate detection via file hash
- Auto-delete failed uploads after 24 hours
- Retention: 2 years

**API Endpoints**:
- `POST /api/resumes/upload` - Single upload
- `POST /api/resumes/bulk-upload` - Bulk upload
- `GET /api/resumes` - List resumes (paginated)
- `GET /api/resumes/{id}` - Get resume details
- `DELETE /api/resumes/{id}` - Delete resume

---

## Feature 3: Resume Filter

**Overview**: Advanced multi-criteria filtering with saved presets and boolean search.

**Key Capabilities**:
- Filter by skills, experience, education, certifications, location
- Keyword search with boolean operators
- Save/load filter presets
- Export to CSV/Excel

**Data Schema** (filter_presets table):
```
- id (UUID, PK)
- user_id (FK users), preset_name
- filter_criteria (JSONB)
- is_public, usage_count
- created_at, updated_at
```

**Business Rules**:
- Multiple filters combined (AND logic)
- Max 10 presets per user
- Case-insensitive search
- Results: 20 per page

**API Endpoints**:
- `POST /api/resumes/filter` - Apply filters
- `GET /api/filter-presets` - Get saved filters
- `POST /api/filter-presets` - Save filter
- `DELETE /api/filter-presets/{id}` - Delete filter

---

## Feature 4: Resume Tracking

**Overview**: Candidate pipeline management with status tracking and visual dashboards.

**Key Capabilities**:
- Multi-stage pipeline (Screened → Shortlisted → Interview → Hired/Rejected)
- Drag-drop status updates (Kanban)
- Status history tracking
- Bulk updates
- Email notifications
- Pipeline analytics

**Data Schema** (candidate_tracking table):
```
- id (UUID, PK)
- resume_id (FK), job_id (FK)
- current_status, previous_status
- status_changed_by (FK users), status_changed_at
- notes, rejection_reason
```

**Data Schema** (status_history table):
```
- id (UUID, PK)
- resume_id (FK), from_status, to_status
- changed_by (FK users), changed_at
- notes, duration_in_previous_stage
```

**Business Rules**:
- One active status per resume
- Immutable status history (audit trail)
- Auto-status "Stale" if no update in 30 days
- Only HR Managers can mark "Hired"
- Bulk updates: max 100 candidates

**API Endpoints**:
- `GET /api/tracking/pipeline` - Get pipeline overview
- `PUT /api/tracking/resume/{id}/status` - Update status
- `POST /api/tracking/bulk-update` - Bulk update
- `GET /api/tracking/history/{resume_id}` - Get history

---

## Feature 5: Resume Rating (User-Driven)

**Overview**: Collaborative 1-5 star rating system with multi-criteria scoring.

**Key Capabilities**:
- Multi-criteria scoring (skills, experience, education, cultural fit, communication)
- Written comments
- Rating aggregation
- Approval workflow (HR Manager)

**Data Schema** (resume_ratings table):
```
- id (UUID, PK)
- resume_id (FK), job_id (FK), rated_by (FK users)
- skills_match_score, experience_score, education_score
- cultural_fit_score, communication_score
- overall_rating (calculated avg)
- comments, is_final
- approved_by (FK users), approved_at
```

**Business Rules**:
- All team members can rate
- HR Managers approve final ratings
- One rating per user per resume (updatable)
- Min 2 ratings for average
- Comments mandatory for ratings < 3 stars

**API Endpoints**:
- `POST /api/ratings` - Submit rating
- `GET /api/ratings/resume/{id}` - Get all ratings
- `PUT /api/ratings/{id}` - Update rating
- `POST /api/ratings/{id}/approve` - Approve (manager only)

---

## Feature 6: Job Creation

**Overview**: Structured job posting with templates and rich text editor.

**Key Capabilities**:
- Rich text job descriptions
- Template library
- Custom fields
- Multi-location/remote support
- Salary range configuration
- Job status management (draft/active/closed)

**Data Schema** (jobs table):
```
- id (UUID, PK)
- job_code (auto-generated, unique)
- title, department, locations (JSONB)
- job_type, experience_level
- description, responsibilities (JSONB)
- required_skills (JSONB), preferred_skills (JSONB)
- education_requirements (JSONB), certifications (JSONB)
- min_experience, max_experience
- salary_min, salary_max, currency
- benefits (JSONB), application_deadline
- number_of_openings, status
- created_by (FK users), created_at, updated_at
```

**Business Rules**:
- Job code format: JOB-YYYY-XXXX
- Mandatory fields required before publishing
- Draft jobs not visible to candidates
- Closed jobs cannot accept applications
- Only HR Admins/Managers can create jobs

**API Endpoints**:
- `POST /api/jobs` - Create job
- `GET /api/jobs` - List jobs
- `GET /api/jobs/{id}` - Get job details
- `PUT /api/jobs/{id}` - Update job
- `POST /api/jobs/{id}/publish` - Publish draft
- `POST /api/jobs/{id}/close` - Close job

---

## Feature 7: Resume Matching (Automatic)

**Overview**: AI-powered matching engine ranking resumes against job descriptions.

**Key Capabilities**:
- Multi-factor scoring (skills, experience, education, keywords)
- Configurable criteria weights
- Batch matching
- Match explanation
- Top candidates recommendation

**Data Schema** (resume_job_matches table):
```
- id (UUID, PK)
- resume_id (FK), job_id (FK)
- overall_match_score (0-100)
- skills_match_score, experience_match_score
- education_match_score, keyword_match_score
- location_match_score
- matched_skills (JSONB), missing_skills (JSONB)
- match_explanation, criteria_weights (JSONB)
- matched_at, match_version
```

**Matching Criteria** (default weights):
- Skills: 40%
- Experience: 30%
- Education: 15%
- Keywords: 10%
- Location: 5%

**Business Rules**:
- Score range: 0-100%
- Min threshold: 50% (configurable)
- Auto-matching on new resume/job/updates
- Must-have skills missing: max 70% score
- Ties resolved by user rating, then upload date

**API Endpoints**:
- `POST /api/matching/job/{job_id}` - Match all resumes to job
- `GET /api/matching/job/{job_id}/results` - Get match results
- `POST /api/matching/configure` - Configure criteria
- `GET /api/matching/explanation/{match_id}` - Get explanation

---

## Feature 8: Jobs Management

**Overview**: Job lifecycle management with analytics and administrative controls.

**Key Capabilities**:
- Centralized job dashboard
- Status management (open/closed/on-hold/archived)
- Job analytics
- Application tracking
- Bulk operations
- Audit logging
- Post job to external portals (LinkedIn, Naukri, Indeed)

**Data Schema** (job_analytics table):
```
- id (UUID, PK)
- job_id (FK), date
- view_count, application_count
- shortlist_count, interview_count
- offer_count, hire_count
- avg_match_score, time_to_fill
```

**Business Rules**:
- Only HR Admins can delete jobs (soft delete)
- Closed jobs cannot accept applications
- Auto-close after application deadline
- Auto-archive after 90 days closed
- Bulk operations: max 50 jobs

**API Endpoints**:
- `GET /api/jobs-management/dashboard` - Get dashboard
- `PUT /api/jobs-management/{id}/status` - Update status
- `GET /api/jobs-management/{id}/analytics` - Get analytics
- `POST /api/jobs-management/bulk-update` - Bulk update
- `DELETE /api/jobs-management/{id}` - Delete (admin only)

---

## Feature 9: Resume Match Rating

**Overview**: Hybrid scoring combining AI match scores with human ratings.

**Key Capabilities**:
- Configurable AI/HR weighting
- Final score calculation
- Comparative analysis
- Score history
- Exportable scorecards

**Data Schema** (final_scores table):
```
- id (UUID, PK)
- resume_id (FK), job_id (FK)
- ai_match_score (0-100), hr_rating_score (0-100)
- final_score (0-100)
- ai_weight, hr_weight
- rank, calculated_at, calculation_version
```

**Business Rules**:
- Formula: `(AI Score × AI Weight) + (HR Rating × HR Weight)`
- Default weights: 60% AI, 40% HR (configurable 0-100%)
- HR rating conversion: Stars × 20
- Auto-recalculation on rating/match updates
- Tie-breaking: HR rating > submission date > education

**API Endpoints**:
- `GET /api/final-scores/job/{job_id}` - Get final scores
- `POST /api/final-scores/calculate` - Trigger calculation
- `PUT /api/final-scores/weights/{job_id}` - Update weights
- `POST /api/final-scores/export` - Export scorecards

---

## Feature 10: User Management

**Overview**: User administration with RBAC, permissions, and activity monitoring.

**Key Capabilities**:
- User CRUD operations
- Role-based access control (Admin/Manager/Recruiter)
- Permission management
- User activation/deactivation
- Activity monitoring
- Session management

**Permissions Matrix**:

| Permission | HR Admin | HR Manager | Recruiter |
|------------|----------|------------|-----------|
| User Management | ✓ | ✗ | ✗ |
| Create/Edit Jobs | ✓ | ✓ | ✗ |
| Delete Jobs | ✓ | ✗ | ✗ |
| Upload Resumes | ✓ | ✓ | ✓ |
| Rate Resumes | ✓ | ✓ | ✓ |
| Approve Ratings | ✓ | ✓ | ✗ |
| Hire Candidate | ✓ | ✓ | ✗ |
| System Settings | ✓ | ✗ | ✗ |

**Data Schema** (user_activity_log table):
```
- id (UUID, PK)
- user_id (FK), action_type, action_details (JSONB)
- ip_address, user_agent, timestamp
```

**Business Rules**:
- Only HR Admins manage users
- Cannot delete self or change own role
- Min 1 active Admin required
- Deactivated users cannot login
- Role changes effective on next login
- Bulk operations: max 100 users

**API Endpoints**:
- `POST /api/users` - Create user
- `GET /api/users` - List users
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user
- `POST /api/users/{id}/deactivate` - Deactivate
- `PUT /api/users/{id}/role` - Change role

---

## 🔗 Integration Requirements

### 1. Payroll System
- Transfer hired candidates to payroll
- Sync: name, email, salary, department, joining date
- REST API or webhook integration

### 2. Attendance System
- Create attendance profile on hire
- Transfer: employee ID, name, department, shift
- Real-time sync

### 3. Job Boards (LinkedIn, Indeed, Naukri)
- Post jobs to external platforms
- Import applications
- OAuth + API integration

### 4. Email/SMS Gateway (SendGrid, Twilio)
- Automated notifications
- Template-based messaging
- Async sending via Celery

### 5. Cloud Storage (AWS S3, Azure Blob)
- Scalable resume storage
- Presigned URLs for secure access
- Lifecycle policies

---

## 🛡️ Non-Functional Requirements

### Performance
- Page load: < 2 seconds
- API response: < 500ms (simple), < 3s (matching)
- File upload: < 5 seconds
- Support 100+ concurrent users

### Security
- JWT authentication with refresh tokens
- Password: min 8 chars, complexity requirements
- TLS 1.3, AES-256 encryption
- RBAC, session timeout: 24 hours
- SQL injection, XSS, CSRF protection

### Compliance
- GDPR: consent management, right to be forgotten
- Data retention: 2 years (rejected), 7 years (hired)
- Audit logging: 1 year

### Usability
- Responsive design (mobile/tablet/desktop)
- Browser support: Chrome, Firefox, Safari, Edge (latest 2)
- WCAG 2.1 Level AA accessibility
- Multi-language: English, Hindi

### Reliability
- Uptime: 99.5%
- Daily backups, 30-day retention
- RTO: 4 hours, RPO: 1 hour

---

## 📊 Success Metrics

**Product Metrics**:
- Time-to-hire: Reduce by 40%
- Quality of hire: Increase by 30%
- Cost per hire: Reduce by 25%
- Candidate experience: > 4.0/5.0

**Technical Metrics**:
- Uptime: 99.5%
- Page load: < 2s (95th percentile)
- Error rate: < 0.5%
- User satisfaction: > 4.2/5.0

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI matching accuracy | High | Continuous training, human oversight, feedback loop |
| Data privacy violations | Critical | GDPR compliance, encryption, audits |
| Integration failures | Medium | Error handling, retry mechanisms, monitoring |
| Performance degradation | High | Load testing, scaling, caching |
| User adoption resistance | High | Training, change management, phased rollout |

---

## 📅 Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
- User authentication, database, UI framework
- Resume upload, job creation
- CI/CD pipeline

### Phase 2: Core Features (Months 3-4)
- Resume parsing, filtering
- AI matching (v1), candidate tracking
- Rating system, basic analytics

### Phase 3: Advanced Features (Months 5-6)
- Hybrid scoring, jobs management
- Notifications, advanced analytics
- Bulk operations, exports

### Phase 4: Integrations (Months 7-8)
- Payroll, attendance, job boards
- Calendar, performance optimization
- Security hardening, training materials

### Phase 5: Launch (Month 9+)
- Production deployment
- User onboarding, monitoring
- Bug fixes, continuous improvement

---

## ✅ Acceptance Criteria Summary

- **User Creation**: Registration, login, password reset work end-to-end
- **Resume Upload**: Single/bulk upload, virus scanning, duplicate detection
- **Resume Filter**: Filters return correct results < 2s, presets work
- **Resume Tracking**: Status updates immediate, history tracked, notifications sent
- **Resume Rating**: Ratings saved, approval workflow, comments enforced
- **Job Creation**: Auto-generated ID, validation, templates work
- **Resume Matching**: Scores displayed, < 3s processing, 85% top-10 accuracy
- **Jobs Management**: Dashboard < 2s, status changes work, analytics accurate
- **Resume Match Rating**: Final scores correct, weights configurable, exports work
- **User Management**: RBAC enforced, activity logged, permissions work

---

## 🔮 Future Enhancements (v2.0+)

- Candidate self-service portal
- Video interview integration
- Advanced analytics dashboard
- Mobile native apps
- AI chatbot, sentiment analysis
- Background verification integration
- Workflow automation builder
- Custom reporting

---

## 📚 Assumptions & Constraints

**Assumptions**:
- HR provides accurate job descriptions
- Users have internet and modern browsers
- Candidates consent to data processing
- Third-party APIs available and stable

**Constraints**:
- Resume parsing accuracy depends on document quality
- AI matching improves with training data
- Integration requires third-party APIs
- Budget/timeline may require phased rollout

---

## 📞 Stakeholders

- **HR Director**: Executive sponsor, final approvals
- **HR Managers**: Primary users, requirements input
- **Recruiters**: Daily users, feedback providers
- **IT Team**: Infrastructure, security, integrations
- **Legal/Compliance**: GDPR, data privacy
- **Finance**: Budget approval, ROI tracking

---

## 📎 References

- BRD: Business Requirements Document v1.0
- Technical Architecture: [To be created]
- API Documentation: [To be created via Swagger]
- User Manual: [To be created]
- Training Materials: [To be created]

---

**Document Control**:
- Next Review Date: 2025-11-01
- Change Log: Track all updates with version control
- Approval Required: HR Director, IT Director

---

*This PRD serves as the master document for the AI Powered Resume Tracker. Individual feature PRDs will be created in `docs/prd/` following the template in `PRD_TEMPLATE.md` for detailed implementation.*
