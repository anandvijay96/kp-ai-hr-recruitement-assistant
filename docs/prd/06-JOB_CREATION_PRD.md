# PRD: Job Creation & Management

**Feature ID:** 06  
**Feature Name:** Job Creation & Management  
**Priority:** P0 (Critical)  
**Complexity:** Medium  
**Estimated Effort:** 2-3 weeks  
**Phase:** 3 (Job Management & AI)  
**Dependencies:** Features 2, 4

---

## 1. Overview

### 1.1 Description
Create and manage job requisitions with detailed requirements, skill specifications, and workflow support from draft to closure, including job templates and cloning capabilities.

### 1.2 Business Value
- **Organization:** Centralized job requisition management
- **Efficiency:** Reduce job posting time by 60%
- **Consistency:** Standardized job descriptions
- **Tracking:** Complete job lifecycle visibility

### 1.3 Success Metrics
- Create job in < 2 minutes
- Support rich text formatting
- 100% validation of required fields
- Secure document storage
- Template reuse rate > 40%

---

## 2. User Stories

### US-6.1: Create Job
```
As a hiring manager
I want to create a new job requisition
So that I can start recruiting for an open position

Acceptance Criteria:
- [ ] Enter job title, description, requirements
- [ ] Add skill tags (mandatory/optional)
- [ ] Specify number of openings
- [ ] Set location and work type
- [ ] Add application closing date
- [ ] Attach job description document
- [ ] Save as draft or publish
```

### US-6.2: Use Job Templates
```
As a hiring manager
I want to use predefined job templates
So that I can create jobs quickly with standard formats

Acceptance Criteria:
- [ ] Browse available templates
- [ ] Preview template content
- [ ] Create job from template
- [ ] Customize template fields
- [ ] Create new templates
- [ ] Edit existing templates
```

### US-6.3: Clone Existing Job
```
As a hiring manager
I want to clone an existing job
So that I can create similar positions quickly

Acceptance Criteria:
- [ ] Select job to clone
- [ ] Preview cloned content
- [ ] Edit cloned fields
- [ ] Save as new job
- [ ] Preserve skill tags
```

### US-6.4: Manage Job Status
```
As a hiring manager
I want to manage job status (draft, open, closed)
So that I can control the hiring process

Acceptance Criteria:
- [ ] Draft: Not visible to recruiters
- [ ] Open: Active recruiting
- [ ] On Hold: Paused recruiting
- [ ] Closed: Position filled/cancelled
- [ ] Status change notifications
- [ ] Status change history
```

### US-6.5: Assign Recruiters
```
As a hiring manager
I want to assign recruiters to jobs
So that they can start sourcing candidates

Acceptance Criteria:
- [ ] Assign multiple recruiters
- [ ] Set primary recruiter
- [ ] Remove recruiters
- [ ] Send assignment notifications
- [ ] View assigned jobs
```

---

## 3. Functional Requirements

### 3.1 Job Fields

**FR-6.1.1: Basic Information**
```json
{
    "title": "Senior Software Engineer",
    "department": "Engineering",
    "location": {
        "city": "San Francisco",
        "state": "CA",
        "country": "USA",
        "is_remote": false
    },
    "work_type": "hybrid",  // onsite, remote, hybrid
    "employment_type": "full_time",  // full_time, part_time, contract
    "num_openings": 2,
    "salary_range": {
        "min": 150000,
        "max": 200000,
        "currency": "USD",
        "period": "annual"
    }
}
```

**FR-6.1.2: Job Description**
```json
{
    "description": "We are seeking a talented Senior Software Engineer...",
    "responsibilities": [
        "Design and develop scalable systems",
        "Lead technical architecture decisions",
        "Mentor junior engineers"
    ],
    "requirements": {
        "mandatory": [
            "5+ years software development",
            "Expert in Python/Java",
            "Experience with microservices"
        ],
        "preferred": [
            "Cloud platforms (AWS/Azure)",
            "Team leadership experience"
        ]
    },
    "qualifications": {
        "education": "Bachelor's in Computer Science or equivalent",
        "certifications": ["AWS Certified Solutions Architect (preferred)"]
    }
}
```

**FR-6.1.3: Skills**
```json
{
    "skills": [
        {
            "name": "Python",
            "is_mandatory": true,
            "proficiency_level": "expert"
        },
        {
            "name": "AWS",
            "is_mandatory": false,
            "proficiency_level": "intermediate"
        }
    ]
}
```

**FR-6.1.4: Metadata**
```json
{
    "status": "open",  // draft, open, on_hold, closed
    "created_by": 5,
    "created_at": "2025-10-06",
    "published_at": "2025-10-07",
    "closing_date": "2025-11-30",
    "closed_at": null,
    "close_reason": null,  // filled, cancelled, budget_cut
    "assigned_recruiters": [8, 12],
    "primary_recruiter": 8
}
```

### 3.2 Job Templates

**FR-6.2.1: Template Structure**
```json
{
    "id": 1,
    "name": "Software Engineer Template",
    "category": "Engineering",
    "title_template": "{Level} {Role}",
    "description_template": "We are seeking a {level} {role} to join our {department} team...",
    "responsibilities_template": [...],
    "requirements_template": {...},
    "default_skills": [
        {"name": "Programming", "is_mandatory": true}
    ],
    "is_active": true,
    "created_by": 1,
    "created_at": "2025-09-01"
}
```

**FR-6.2.2: Template Variables**
- `{level}`: Junior, Mid, Senior, Staff, Principal
- `{role}`: Software Engineer, Product Manager, etc.
- `{department}`: Engineering, Sales, Marketing
- `{team}`: Backend, Frontend, DevOps

### 3.3 Rich Text Editor

**FR-6.3.1: Formatting Options**
- Bold, Italic, Underline
- Headings (H1-H6)
- Bulleted/Numbered lists
- Links
- Tables
- Code blocks
- Horizontal rules

**FR-6.3.2: Safety**
- HTML sanitization (prevent XSS)
- Allowed tags whitelist
- Max content length (50KB)

### 3.4 Document Attachments

**FR-6.4.1: File Support**
- PDF (job description, offer letter template)
- DOCX (editable documents)
- Max file size: 5MB per file
- Max 5 files per job

**FR-6.4.2: Storage**
- Store in S3/MinIO
- Generate signed URLs
- Virus scanning
- Access control (only assigned users)

---

## 4. Database Schema

```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    uuid UUID UNIQUE DEFAULT gen_random_uuid(),
    
    -- Basic Info
    title VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    
    -- Location
    location_city VARCHAR(100),
    location_state VARCHAR(100),
    location_country VARCHAR(100) DEFAULT 'USA',
    is_remote BOOLEAN DEFAULT FALSE,
    work_type VARCHAR(50),  -- onsite, remote, hybrid
    
    -- Employment
    employment_type VARCHAR(50),  -- full_time, part_time, contract
    num_openings INTEGER DEFAULT 1,
    
    -- Salary
    salary_min DECIMAL(12,2),
    salary_max DECIMAL(12,2),
    salary_currency VARCHAR(10) DEFAULT 'USD',
    salary_period VARCHAR(20) DEFAULT 'annual',
    
    -- Description (rich text)
    description TEXT NOT NULL,
    responsibilities TEXT[],
    mandatory_requirements TEXT[],
    preferred_requirements TEXT[],
    education_requirement TEXT,
    certifications TEXT[],
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft',  -- draft, open, on_hold, closed
    published_at TIMESTAMP,
    closing_date DATE,
    closed_at TIMESTAMP,
    close_reason VARCHAR(100),
    
    -- Metadata
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Template
    template_id INTEGER REFERENCES job_templates(id),
    
    -- Search
    search_vector TSVECTOR,
    
    INDEX idx_jobs_status (status),
    INDEX idx_jobs_department (department),
    INDEX idx_jobs_created_by (created_by),
    INDEX idx_jobs_search (search_vector) USING GIN
);

CREATE TABLE job_skills (
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    skill_id INTEGER REFERENCES skills(id),
    is_mandatory BOOLEAN DEFAULT FALSE,
    proficiency_level VARCHAR(50),  -- beginner, intermediate, expert
    
    PRIMARY KEY (job_id, skill_id)
);

CREATE TABLE job_documents (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_job_docs_job (job_id)
);

CREATE TABLE job_recruiters (
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    is_primary BOOLEAN DEFAULT FALSE,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER REFERENCES users(id),
    
    PRIMARY KEY (job_id, user_id)
);

CREATE TABLE job_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    
    title_template VARCHAR(255),
    description_template TEXT,
    responsibilities_template TEXT[],
    mandatory_requirements_template TEXT[],
    preferred_requirements_template TEXT[],
    
    default_skills JSONB,  -- Array of skill configs
    
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_templates_category (category),
    INDEX idx_templates_active (is_active)
);
```

---

## 5. API Specifications

### 5.1 Create Job

**Endpoint:** `POST /api/jobs`

**Request:**
```json
{
    "title": "Senior Software Engineer",
    "department": "Engineering",
    "location": {
        "city": "San Francisco",
        "state": "CA",
        "is_remote": false
    },
    "work_type": "hybrid",
    "employment_type": "full_time",
    "num_openings": 2,
    "salary_range": {
        "min": 150000,
        "max": 200000
    },
    "description": "We are seeking...",
    "responsibilities": [...],
    "requirements": {
        "mandatory": [...],
        "preferred": [...]
    },
    "skills": [
        {"name": "Python", "is_mandatory": true},
        {"name": "AWS", "is_mandatory": false}
    ],
    "closing_date": "2025-11-30",
    "assigned_recruiters": [8, 12],
    "primary_recruiter": 8,
    "status": "draft"
}
```

**Response:**
```json
{
    "id": 123,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Senior Software Engineer",
    "status": "draft",
    "created_at": "2025-10-06T10:00:00Z",
    "created_by": {
        "id": 5,
        "name": "John Manager"
    }
}
```

### 5.2 Get Job

**Endpoint:** `GET /api/jobs/{id}`

**Response:** Complete job details

### 5.3 Update Job

**Endpoint:** `PATCH /api/jobs/{id}`

**Request:** Partial update

### 5.4 Publish Job

**Endpoint:** `POST /api/jobs/{id}/publish`

**Response:**
```json
{
    "id": 123,
    "status": "open",
    "published_at": "2025-10-06T11:00:00Z",
    "notifications_sent": 2
}
```

### 5.5 Clone Job

**Endpoint:** `POST /api/jobs/{id}/clone`

**Response:** New job ID

### 5.6 Create from Template

**Endpoint:** `POST /api/jobs/from-template/{template_id}`

**Request:**
```json
{
    "variables": {
        "level": "Senior",
        "role": "Software Engineer",
        "department": "Engineering"
    }
}
```

---

## 6. UI/UX Specifications

### 6.1 Job Creation Form

```
┌──────────────────────────────────────────────────┐
│ 📝 Create New Job                                │
│ [Use Template ▼] [Clone Existing ▼]             │
├──────────────────────────────────────────────────┤
│                                                   │
│ Basic Information                                │
│ ┌──────────────────────────────────────────────┐│
│ │ Job Title *                                  ││
│ │ [Senior Software Engineer              ]    ││
│ │                                              ││
│ │ Department                                   ││
│ │ [Engineering                 ▼]             ││
│ │                                              ││
│ │ Location                                     ││
│ │ City: [San Francisco]  State: [CA ▼]       ││
│ │ ☑ Remote Work Available                     ││
│ │ Work Type: ○ Onsite  ● Hybrid  ○ Remote    ││
│ │                                              ││
│ │ Employment Type                              ││
│ │ ● Full-time  ○ Part-time  ○ Contract       ││
│ │                                              ││
│ │ Number of Openings: [2]                     ││
│ │                                              ││
│ │ Salary Range (Optional)                      ││
│ │ Min: [$150,000] Max: [$200,000] USD/year   ││
│ └──────────────────────────────────────────────┘│
│                                                   │
│ Job Description *                                │
│ ┌──────────────────────────────────────────────┐│
│ │ [B][I][U] [H1][H2] [•][1.] [🔗]  [</>]      ││
│ │─────────────────────────────────────────────││
│ │ We are seeking a talented Senior Software   ││
│ │ Engineer to join our Engineering team...     ││
│ │                                              ││
│ └──────────────────────────────────────────────┘│
│                                                   │
│ [Continue →]                                      │
│                                                   │
└──────────────────────────────────────────────────┘
```

### 6.2 Skills & Requirements

```
┌──────────────────────────────────────────────────┐
│ Step 2: Skills & Requirements                    │
├──────────────────────────────────────────────────┤
│                                                   │
│ Required Skills *                                │
│ [Search skills...]                               │
│ ┌──────────────────────────────────────────────┐│
│ │ ☑ Python (Expert)                       [×] ││
│ │ ☑ Java (Expert)                         [×] ││
│ │ ☑ Microservices Architecture (Intermediate) ││
│ └──────────────────────────────────────────────┘│
│ [+ Add Skill]                                    │
│                                                   │
│ Preferred Skills                                 │
│ ┌──────────────────────────────────────────────┐│
│ │ ☐ AWS (Intermediate)                    [×] ││
│ │ ☐ Docker/Kubernetes (Intermediate)      [×] ││
│ └──────────────────────────────────────────────┘│
│ [+ Add Skill]                                    │
│                                                   │
│ Responsibilities                                 │
│ ┌──────────────────────────────────────────────┐│
│ │ • Design and develop scalable systems   [×] ││
│ │ • Lead technical architecture decisions [×] ││
│ │ • Mentor junior engineers               [×] ││
│ └──────────────────────────────────────────────┘│
│ [+ Add Responsibility]                           │
│                                                   │
│ Mandatory Requirements                           │
│ ┌──────────────────────────────────────────────┐│
│ │ • 5+ years software development         [×] ││
│ │ • Expert in Python/Java                 [×] ││
│ └──────────────────────────────────────────────┘│
│ [+ Add Requirement]                              │
│                                                   │
│ [← Back]  [Continue →]                           │
│                                                   │
└──────────────────────────────────────────────────┘
```

### 6.3 Job List View

```
┌──────────────────────────────────────────────────┐
│ 💼 Jobs                          [+ Create Job]  │
│ Filter: [All ▼] [Engineering ▼] [Open ▼]        │
├──────────────────────────────────────────────────┤
│                                                   │
│ ┌──────────────────────────────────────────────┐│
│ │ Senior Software Engineer           [Open]    ││
│ │ Engineering • San Francisco, CA • Hybrid     ││
│ │ 2 openings • Closing: Nov 30, 2025          ││
│ │ 15 applicants • Assigned: Sarah, Mike        ││
│ │ [View] [Edit] [Close]                        ││
│ └──────────────────────────────────────────────┘│
│                                                   │
│ ┌──────────────────────────────────────────────┐│
│ │ Product Manager                     [Draft]  ││
│ │ Product • Remote • Full-time                 ││
│ │ 1 opening • Created: Oct 5, 2025            ││
│ │ 0 applicants • Assigned: John                ││
│ │ [Edit] [Publish] [Delete]                    ││
│ └──────────────────────────────────────────────┘│
│                                                   │
└──────────────────────────────────────────────────┘
```

---

## 7. Implementation Plan

### Week 1: Database & Backend
- Database schema
- CRUD APIs
- Template system
- File upload

### Week 2: UI & Features
- Job creation form
- Rich text editor
- Skill selector
- Template picker

### Week 3: Polish & Testing
- Job list view
- Status management
- Recruiter assignment
- Testing

---

**Status:** Ready for Implementation  
**Dependencies:** Features 2, 4
