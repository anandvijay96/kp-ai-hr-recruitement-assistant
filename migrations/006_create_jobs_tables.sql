-- Migration 006: Create Jobs Tables
-- Feature: Job Creation & Management
-- Date: 2025-10-07

-- ============================================================================
-- Jobs Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS jobs (
    id VARCHAR(36) PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    
    -- Basic Information
    title VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    
    -- Location
    location_city VARCHAR(100),
    location_state VARCHAR(100),
    location_country VARCHAR(100) DEFAULT 'USA',
    is_remote BOOLEAN DEFAULT 0,
    work_type VARCHAR(50),
    
    -- Employment Details
    employment_type VARCHAR(50),
    num_openings INTEGER DEFAULT 1,
    
    -- Salary Information
    salary_min VARCHAR(20),
    salary_max VARCHAR(20),
    salary_currency VARCHAR(10) DEFAULT 'USD',
    salary_period VARCHAR(20) DEFAULT 'annual',
    
    -- Job Description
    description TEXT NOT NULL,
    responsibilities TEXT,
    mandatory_requirements TEXT,
    preferred_requirements TEXT,
    education_requirement TEXT,
    certifications TEXT,
    
    -- Status & Workflow
    status VARCHAR(50) DEFAULT 'draft',
    published_at DATETIME,
    closing_date VARCHAR(20),
    closed_at DATETIME,
    close_reason VARCHAR(100),
    
    -- Metadata
    created_by VARCHAR(36) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Template Reference
    template_id VARCHAR(36),
    cloned_from_job_id VARCHAR(36),
    
    -- Search Optimization
    search_text TEXT,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (template_id) REFERENCES job_templates(id) ON DELETE SET NULL,
    FOREIGN KEY (cloned_from_job_id) REFERENCES jobs(id) ON DELETE SET NULL,
    
    CHECK (work_type IN ('onsite', 'remote', 'hybrid')),
    CHECK (employment_type IN ('full_time', 'part_time', 'contract', 'internship')),
    CHECK (status IN ('draft', 'open', 'on_hold', 'closed')),
    CHECK (num_openings > 0)
);

CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_jobs_department ON jobs(department);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_by ON jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_jobs_uuid ON jobs(uuid);

-- ============================================================================
-- Job Skills Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_skills (
    job_id VARCHAR(36) NOT NULL,
    skill_id VARCHAR(36) NOT NULL,
    is_mandatory BOOLEAN DEFAULT 0,
    proficiency_level VARCHAR(50),
    years_required INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_job_skills_mandatory ON job_skills(is_mandatory);

-- ============================================================================
-- Job Recruiters Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_recruiters (
    job_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    is_primary BOOLEAN DEFAULT 0,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(36) NOT NULL,
    removed_at DATETIME,
    removed_by VARCHAR(36),
    
    PRIMARY KEY (job_id, user_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (removed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_job_recruiters_primary ON job_recruiters(is_primary);
CREATE INDEX IF NOT EXISTS idx_job_recruiters_user ON job_recruiters(user_id);

-- ============================================================================
-- Job Documents Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_documents (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL,
    
    -- File Information
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    
    -- Document Type
    document_type VARCHAR(50),
    
    -- Upload Metadata
    uploaded_by VARCHAR(36) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Audit
    deleted_at DATETIME,
    deleted_by VARCHAR(36),
    
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL,
    
    CHECK (file_type IN ('pdf', 'docx', 'doc')),
    CHECK (file_size > 0 AND file_size <= 5242880)
);

CREATE INDEX IF NOT EXISTS idx_job_docs_job ON job_documents(job_id);

-- ============================================================================
-- Job Templates Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_templates (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    
    -- Template Content
    title_template VARCHAR(255),
    description_template TEXT,
    responsibilities_template TEXT,
    mandatory_requirements_template TEXT,
    preferred_requirements_template TEXT,
    education_requirement_template TEXT,
    
    -- Default Values
    default_work_type VARCHAR(50),
    default_employment_type VARCHAR(50),
    default_num_openings INTEGER DEFAULT 1,
    default_skills TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT 1,
    
    -- Metadata
    created_by VARCHAR(36) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_templates_category ON job_templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_active ON job_templates(is_active);

-- ============================================================================
-- Job Status History Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_status_history (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL,
    
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    reason TEXT,
    
    changed_by VARCHAR(36) NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_job_status_history_job ON job_status_history(job_id);
CREATE INDEX IF NOT EXISTS idx_job_status_history_date ON job_status_history(changed_at);

-- ============================================================================
-- Insert Sample Job Template
-- ============================================================================

INSERT INTO job_templates (
    id, name, category, title_template, description_template,
    responsibilities_template, mandatory_requirements_template,
    preferred_requirements_template, default_work_type,
    default_employment_type, created_by
) VALUES (
    'template-001',
    'Software Engineer Template',
    'Engineering',
    '{level} Software Engineer',
    'We are seeking a talented {level} Software Engineer to join our {department} team.',
    '["Design and develop scalable systems", "Collaborate with cross-functional teams", "Write clean, maintainable code"]',
    '["{years}+ years of software development experience", "Strong programming skills"]',
    '["Experience with cloud platforms", "Team leadership experience"]',
    'hybrid',
    'full_time',
    (SELECT id FROM users WHERE role = 'admin' LIMIT 1)
);

-- ============================================================================
-- Migration Complete
-- ============================================================================
