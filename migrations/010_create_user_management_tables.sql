-- Migration: Feature 10 - User Management Tables
-- Description: Creates tables for user roles, permissions, audit logs, and bulk operations
-- Date: 2025-10-08

BEGIN;

-- Add new columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active';
ALTER TABLE users ADD COLUMN IF NOT EXISTS deactivation_reason TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

-- Create indexes on users table
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- Create user_roles table
CREATE TABLE IF NOT EXISTS user_roles (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions TEXT NOT NULL DEFAULT '[]',
    is_system_role BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_roles_name ON user_roles(name);

-- Insert default roles
INSERT INTO user_roles (id, name, display_name, description, permissions) VALUES
(
    lower(hex(randomblob(16))),
    'admin',
    'HR Admin',
    'Full system access including user management',
    '["user.manage", "job.create", "job.edit", "job.delete", "resume.upload", "resume.rate", "resume.approve", "candidate.hire", "analytics.view_all", "settings.manage", "audit.view", "data.export"]'
),
(
    lower(hex(randomblob(16))),
    'manager',
    'HR Manager',
    'Manage jobs and candidates, view analytics',
    '["job.create", "job.edit", "resume.upload", "resume.rate", "resume.approve", "candidate.hire", "analytics.view_all", "audit.view_readonly", "data.export"]'
),
(
    lower(hex(randomblob(16))),
    'recruiter',
    'Recruiter',
    'Upload and rate resumes, view own analytics',
    '["resume.upload", "resume.rate", "analytics.view_own"]'
)
ON CONFLICT(name) DO NOTHING;

-- Create user_permissions table
CREATE TABLE IF NOT EXISTS user_permissions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(100) NOT NULL,
    granted BOOLEAN DEFAULT TRUE,
    granted_by VARCHAR(36) REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    reason TEXT,
    UNIQUE(user_id, permission)
);

CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_permission ON user_permissions(permission);

-- Create user_audit_log table
CREATE TABLE IF NOT EXISTS user_audit_log (
    id VARCHAR(36) PRIMARY KEY,
    target_user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    old_values TEXT,
    new_values TEXT,
    performed_by VARCHAR(36) NOT NULL REFERENCES users(id),
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_user_audit_log_target_user_id ON user_audit_log(target_user_id);
CREATE INDEX IF NOT EXISTS idx_user_audit_log_performed_by ON user_audit_log(performed_by);
CREATE INDEX IF NOT EXISTS idx_user_audit_log_timestamp ON user_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_audit_log_action_type ON user_audit_log(action_type);

-- Create bulk_user_operations table
CREATE TABLE IF NOT EXISTS bulk_user_operations (
    id VARCHAR(36) PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL,
    user_ids TEXT NOT NULL,
    parameters TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    total_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    error_details TEXT,
    initiated_by VARCHAR(36) NOT NULL REFERENCES users(id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bulk_user_operations_status ON bulk_user_operations(status);
CREATE INDEX IF NOT EXISTS idx_bulk_user_operations_initiated_by ON bulk_user_operations(initiated_by);
CREATE INDEX IF NOT EXISTS idx_bulk_user_operations_created_at ON bulk_user_operations(created_at);

COMMIT;
