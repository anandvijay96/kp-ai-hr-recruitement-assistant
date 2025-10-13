-- Migration: Add Jobs Management tables and columns
-- Created: 2025-10-08
-- Feature: Jobs Management (Feature 8)

-- Create job_analytics table
CREATE TABLE IF NOT EXISTS job_analytics (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL,
    date VARCHAR(20) NOT NULL,
    view_count INTEGER DEFAULT 0,
    application_count INTEGER DEFAULT 0,
    shortlist_count INTEGER DEFAULT 0,
    interview_count INTEGER DEFAULT 0,
    offer_count INTEGER DEFAULT 0,
    hire_count INTEGER DEFAULT 0,
    avg_match_score VARCHAR(10),
    median_match_score VARCHAR(10),
    time_to_fill INTEGER,
    time_to_first_application INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, date),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_job_analytics_job_id ON job_analytics(job_id);
CREATE INDEX IF NOT EXISTS idx_job_analytics_date ON job_analytics(date);

-- Create job_external_postings table
CREATE TABLE IF NOT EXISTS job_external_postings (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL,
    portal VARCHAR(50) NOT NULL,
    external_job_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    posted_at TIMESTAMP,
    expires_at TIMESTAMP,
    error_message TEXT,
    portal_metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, portal),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_job_external_postings_job_id ON job_external_postings(job_id);
CREATE INDEX IF NOT EXISTS idx_job_external_postings_status ON job_external_postings(status);
CREATE INDEX IF NOT EXISTS idx_job_external_postings_portal ON job_external_postings(portal);

-- Create job_audit_log table
CREATE TABLE IF NOT EXISTS job_audit_log (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    old_values TEXT,
    new_values TEXT,
    user_id VARCHAR(36) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_job_audit_log_job_id ON job_audit_log(job_id);
CREATE INDEX IF NOT EXISTS idx_job_audit_log_timestamp ON job_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_job_audit_log_user_id ON job_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_job_audit_log_action_type ON job_audit_log(action_type);

-- Create bulk_operations table
CREATE TABLE IF NOT EXISTS bulk_operations (
    id VARCHAR(36) PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    job_ids TEXT NOT NULL,
    parameters TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    error_details TEXT,
    initiated_by VARCHAR(36) NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (initiated_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_bulk_operations_status ON bulk_operations(status);
CREATE INDEX IF NOT EXISTS idx_bulk_operations_initiated_by ON bulk_operations(initiated_by);
CREATE INDEX IF NOT EXISTS idx_bulk_operations_created_at ON bulk_operations(created_at);

-- Modify jobs table - add new columns
ALTER TABLE jobs ADD COLUMN archived_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN view_count INTEGER DEFAULT 0;
ALTER TABLE jobs ADD COLUMN application_deadline TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_jobs_archived_at ON jobs(archived_at);
CREATE INDEX IF NOT EXISTS idx_jobs_application_deadline ON jobs(application_deadline);

-- Add reason column to job_status_history if table exists
ALTER TABLE job_status_history ADD COLUMN reason TEXT;
