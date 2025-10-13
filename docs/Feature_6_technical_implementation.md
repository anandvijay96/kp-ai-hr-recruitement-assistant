# Feature 6: Job Creation & Management - Technical Implementation

**Feature ID:** 06  
**Priority:** P0 (Critical)  
**Estimated Effort:** 2-3 weeks  
**Dependencies:** Features 2 (User Management), 4 (Skills Master Data)

---

## 1. DATABASE DESIGN

### Core Tables

#### `jobs` Table
```sql
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    location_city VARCHAR(100),
    location_state VARCHAR(100),
    location_country VARCHAR(100) DEFAULT 'USA',
    is_remote BOOLEAN DEFAULT FALSE,
    work_type VARCHAR(50) CHECK(work_type IN ('onsite', 'remote', 'hybrid')),
    employment_type VARCHAR(50) CHECK(employment_type IN ('full_time', 'part_time', 'contract', 'internship')),
    num_openings INTEGER DEFAULT 1,
    salary_min DECIMAL(12,2),
    salary_max DECIMAL(12,2),
    salary_currency VARCHAR(10) DEFAULT 'USD',
    salary_period VARCHAR(20) DEFAULT 'annual',
    description TEXT NOT NULL,
    responsibilities TEXT,
    mandatory_requirements TEXT,
    preferred_requirements TEXT,
    education_requirement TEXT,
    certifications TEXT,
    status VARCHAR(50) DEFAULT 'draft' CHECK(status IN ('draft', 'open', 'on_hold', 'closed')),
    published_at DATETIME,
    closing_date DATE,
    closed_at DATETIME,
    close_reason VARCHAR(100),
    created_by VARCHAR(36) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    template_id VARCHAR(36),
    cloned_from_job_id VARCHAR(36),
    search_text TEXT,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

#### `job_skills` Table
```sql
CREATE TABLE job_skills (
    job_id VARCHAR(36) NOT NULL,
    skill_id VARCHAR(36) NOT NULL,
    is_mandatory BOOLEAN DEFAULT FALSE,
    proficiency_level VARCHAR(50),
    years_required INTEGER,
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);
```

#### `job_recruiters` Table
```sql
CREATE TABLE job_recruiters (
    job_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(36) NOT NULL,
    PRIMARY KEY (job_id, user_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### `job_documents` Table
```sql
CREATE TABLE job_documents (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    document_type VARCHAR(50),
    uploaded_by VARCHAR(36) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);
```

#### `job_templates` Table
```sql
CREATE TABLE job_templates (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    title_template VARCHAR(255),
    description_template TEXT,
    responsibilities_template TEXT,
    mandatory_requirements_template TEXT,
    preferred_requirements_template TEXT,
    default_skills TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(36) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. API DESIGN

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/jobs` | Create new job |
| GET | `/api/jobs` | List jobs (paginated) |
| GET | `/api/jobs/{id}` | Get job details |
| PATCH | `/api/jobs/{id}` | Update job |
| DELETE | `/api/jobs/{id}` | Delete job (draft only) |
| POST | `/api/jobs/{id}/publish` | Publish draft job |
| POST | `/api/jobs/{id}/close` | Close job |
| POST | `/api/jobs/{id}/clone` | Clone existing job |
| POST | `/api/jobs/from-template` | Create from template |
| POST | `/api/jobs/{id}/recruiters` | Assign recruiters |
| POST | `/api/jobs/{id}/documents` | Upload document |

### Request/Response Examples

**Create Job Request:**
```json
{
  "title": "Senior Software Engineer",
  "department": "Engineering",
  "location": {"city": "San Francisco", "state": "CA", "is_remote": false},
  "work_type": "hybrid",
  "employment_type": "full_time",
  "num_openings": 2,
  "salary_range": {"min": 150000, "max": 200000},
  "description": "We are seeking...",
  "responsibilities": ["Design systems", "Lead architecture"],
  "requirements": {
    "mandatory": ["5+ years experience"],
    "preferred": ["Cloud experience"]
  },
  "skills": [
    {"name": "Python", "is_mandatory": true, "proficiency_level": "expert"}
  ],
  "status": "draft"
}
```

---

## 3. SERVICE LAYER

### `services/job_service.py`

**Key Methods:**
- `create_job(job_data, created_by)` - Create new job
- `get_job_by_id(job_id, include_relations)` - Get job details
- `search_jobs(filters, page, limit)` - Search with pagination
- `update_job(job_id, update_data)` - Update job
- `delete_job(job_id)` - Delete draft job
- `publish_job(job_id, published_by)` - Publish to open
- `close_job(job_id, reason, closed_by)` - Close job
- `clone_job(job_id, new_title, created_by)` - Clone job
- `assign_recruiters(job_id, recruiters)` - Assign recruiters
- `upload_document(job_id, file)` - Upload document

### `services/job_template_service.py`

**Key Methods:**
- `list_templates(category, active_only)` - List templates
- `get_template_by_id(template_id)` - Get template
- `apply_template(template_id, variables)` - Apply with substitution

---

## 4. UI/UX DESIGN

### Templates Structure

```
templates/jobs/
├── job_list.html          # Job listing with filters
├── job_create.html        # Multi-step job creation form
├── job_detail.html        # Job details view
└── job_edit.html          # Edit job form
```

### Key UI Components

**Job List Page:**
- Search bar with filters (status, department, work type)
- Job cards showing: title, department, location, status, openings
- Pagination
- Create Job button

**Job Creation Form (Multi-step):**
1. **Basic Info:** Title, department, location, work type, salary
2. **Description:** Rich text editor for job description
3. **Skills & Requirements:** Add skills, responsibilities, requirements
4. **Recruiters:** Assign recruiters with primary flag
5. **Review:** Preview and submit

**Job Detail Page:**
- Full job information
- Assigned recruiters list
- Documents section
- Actions: Edit, Publish, Close, Clone

---

## 5. INTEGRATION POINTS

### Existing Modules Integration

**User Management (Feature 2):**
- Use `get_current_user()` dependency for authentication
- Link jobs to users via `created_by` field
- Assign recruiters from user table

**Skills Master Data (Feature 4):**
- Reference `skills` table for job skills
- Create skills on-the-fly if not exists
- Link via `job_skills` junction table

**File Storage:**
- Use existing `FileStorageService` for documents
- Store in `uploads/jobs/{job_id}/` directory
- Support PDF and DOCX formats

**Email Service:**
- Send notifications on job publish
- Notify recruiters on assignment
- Use existing `EmailService`

---

## 6. FILE STRUCTURE

### New Files to Create

```
models/
└── job_schemas.py                    # Pydantic models for jobs

api/
└── jobs.py                           # Job API endpoints

services/
├── job_service.py                    # Job business logic
└── job_template_service.py           # Template management

templates/jobs/
├── job_list.html                     # Job listing page
├── job_create.html                   # Job creation form
├── job_detail.html                   # Job details page
└── job_edit.html                     # Job edit form

tests/
├── test_job_service.py               # Service tests
└── test_job_api.py                   # API tests
```

### Files to Modify

```
models/database.py                    # Add Job, JobSkill, etc. models
main.py                               # Register jobs router
core/dependencies.py                  # Add job-related dependencies (if needed)
```

---

## 7. TESTING STRATEGY

### Unit Tests

**`tests/test_job_service.py`:**
```python
- test_create_job_success()
- test_create_job_validation_error()
- test_get_job_by_id()
- test_search_jobs_with_filters()
- test_update_job()
- test_publish_job()
- test_close_job()
- test_clone_job()
- test_assign_recruiters()
```

### Integration Tests

**`tests/test_job_api.py`:**
```python
- test_create_job_endpoint()
- test_list_jobs_endpoint()
- test_get_job_endpoint()
- test_update_job_endpoint()
- test_delete_job_endpoint()
- test_publish_job_endpoint()
- test_unauthorized_access()
```

### Manual Testing Checklist

- [ ] Create job as manager/admin
- [ ] Cannot create job as recruiter
- [ ] Search and filter jobs
- [ ] Update job details
- [ ] Publish draft job
- [ ] Close open job
- [ ] Clone existing job
- [ ] Assign/remove recruiters
- [ ] Upload/delete documents
- [ ] Pagination works correctly
- [ ] Form validation works
- [ ] Rich text editor saves HTML

---

## 8. DEPLOYMENT CONSIDERATIONS

### Database Migration

**Migration Script:** `migrations/006_create_jobs_tables.sql`
```sql
-- Create all job-related tables
-- Add indexes for performance
-- Set up foreign key constraints
```

### Environment Variables

No new environment variables required. Uses existing:
- `DATABASE_URL` - Database connection
- `UPLOAD_DIR` - File storage location
- `SENDGRID_API_KEY` - Email notifications

### Deployment Steps

1. **Run database migration:**
   ```bash
   # Apply migration script to create tables
   python migrations/run_migration.py 006
   ```

2. **Update dependencies:**
   ```bash
   uv sync
   ```

3. **Restart application:**
   ```bash
   uv run uvicorn main:app --reload
   ```

4. **Verify deployment:**
   - Access `/jobs` page
   - Create test job
   - Verify database records

### Performance Considerations

- **Indexes:** Add indexes on `status`, `department`, `created_by`, `published_at`
- **Caching:** Cache job templates for faster creation
- **Pagination:** Limit to 100 items per page
- **Search:** Use full-text search on `search_text` field

---

## Implementation Checklist

### Phase 1: Backend (Week 1)
- [ ] Create database models in `models/database.py`
- [ ] Create Pydantic schemas in `models/job_schemas.py`
- [ ] Implement `JobService` in `services/job_service.py`
- [ ] Implement `JobTemplateService`
- [ ] Create API endpoints in `api/jobs.py`
- [ ] Write unit tests

### Phase 2: Frontend (Week 2)
- [ ] Create job list page
- [ ] Create job creation form (multi-step)
- [ ] Create job detail page
- [ ] Create job edit page
- [ ] Add rich text editor integration
- [ ] Implement file upload UI

### Phase 3: Integration & Testing (Week 3)
- [ ] Integrate with user management
- [ ] Integrate with skills system
- [ ] Add email notifications
- [ ] Write integration tests
- [ ] Manual testing
- [ ] Bug fixes and polish

---

## Success Criteria

- ✅ Managers/admins can create jobs in < 2 minutes
- ✅ Support rich text formatting in descriptions
- ✅ 100% validation of required fields
- ✅ Secure document storage (5MB limit)
- ✅ Template reuse functionality
- ✅ Job cloning works correctly
- ✅ Status workflow (draft → open → closed)
- ✅ Recruiter assignment with notifications
- ✅ Search and filter jobs efficiently
- ✅ Responsive UI on all devices

---

**Status:** Ready for Implementation  
**Next Steps:** Create database migration script and begin Phase 1 implementation
