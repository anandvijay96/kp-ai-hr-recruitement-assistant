-- ============================================================================
-- PHASE 3: INTERNAL HR FEATURES - DATABASE MIGRATION
-- ============================================================================
-- Purpose: Add activity tracking, interview scheduling, and workflow tables
-- Date: October 17, 2025
-- Author: AI HR Assistant Team
-- ============================================================================

-- 1. Enhance user_activity_log table (add new columns to existing table)
-- ============================================================================
-- Note: SQLite requires adding columns one at a time
ALTER TABLE user_activity_log ADD COLUMN entity_type VARCHAR(50);
ALTER TABLE user_activity_log ADD COLUMN entity_id VARCHAR(36);
ALTER TABLE user_activity_log ADD COLUMN request_metadata TEXT;  -- SQLite uses TEXT for JSON
ALTER TABLE user_activity_log ADD COLUMN request_method VARCHAR(10);
ALTER TABLE user_activity_log ADD COLUMN request_path VARCHAR(500);
ALTER TABLE user_activity_log ADD COLUMN duration_ms INTEGER;

-- Add indexes for Phase 3 columns (after columns are created)
CREATE INDEX IF NOT EXISTS idx_user_activity_entity_type ON user_activity_log(entity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_entity_id ON user_activity_log(entity_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity_log(timestamp);

-- 2. Create user_daily_stats table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_daily_stats (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Activity Counts
    logins_count INTEGER DEFAULT 0,
    resumes_vetted INTEGER DEFAULT 0,
    candidates_viewed INTEGER DEFAULT 0,
    candidates_created INTEGER DEFAULT 0,
    candidates_updated INTEGER DEFAULT 0,
    searches_performed INTEGER DEFAULT 0,
    reports_generated INTEGER DEFAULT 0,
    jobs_created INTEGER DEFAULT 0,
    jobs_updated INTEGER DEFAULT 0,
    interviews_scheduled INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    
    -- Session Metrics
    total_session_time INTEGER DEFAULT 0,  -- in seconds
    avg_session_duration INTEGER DEFAULT 0,  -- in seconds
    total_actions INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_daily_logins_positive CHECK (logins_count >= 0),
    CONSTRAINT chk_daily_session_time_positive CHECK (total_session_time >= 0),
    CONSTRAINT unique_user_daily_stats UNIQUE(user_id, date)
);

-- Indexes for user_daily_stats
CREATE INDEX IF NOT EXISTS idx_user_daily_stats_user_id ON user_daily_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_user_daily_stats_date ON user_daily_stats(date);
CREATE INDEX IF NOT EXISTS idx_user_daily_stats_user_date ON user_daily_stats(user_id, date);

-- 3. Create user_weekly_stats table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_weekly_stats (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,  -- ISO week number (1-53)
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    
    -- Aggregated Activity Counts
    logins_count INTEGER DEFAULT 0,
    resumes_vetted INTEGER DEFAULT 0,
    candidates_viewed INTEGER DEFAULT 0,
    candidates_created INTEGER DEFAULT 0,
    searches_performed INTEGER DEFAULT 0,
    reports_generated INTEGER DEFAULT 0,
    jobs_created INTEGER DEFAULT 0,
    interviews_scheduled INTEGER DEFAULT 0,
    
    -- Performance Metrics
    total_session_time INTEGER DEFAULT 0,
    avg_daily_actions INTEGER DEFAULT 0,
    productivity_score INTEGER DEFAULT 0,  -- 0-100
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_week_number_range CHECK (week_number >= 1 AND week_number <= 53),
    CONSTRAINT chk_productivity_score_range CHECK (productivity_score >= 0 AND productivity_score <= 100),
    CONSTRAINT unique_user_weekly_stats UNIQUE(user_id, year, week_number)
);

-- Indexes for user_weekly_stats
CREATE INDEX IF NOT EXISTS idx_user_weekly_stats_user_id ON user_weekly_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_user_weekly_stats_year ON user_weekly_stats(year);
CREATE INDEX IF NOT EXISTS idx_user_weekly_stats_week ON user_weekly_stats(week_number);

-- 4. Create user_monthly_stats table
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_monthly_stats (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,  -- 1-12
    
    -- Aggregated Activity Counts
    logins_count INTEGER DEFAULT 0,
    resumes_vetted INTEGER DEFAULT 0,
    candidates_viewed INTEGER DEFAULT 0,
    candidates_created INTEGER DEFAULT 0,
    searches_performed INTEGER DEFAULT 0,
    reports_generated INTEGER DEFAULT 0,
    jobs_created INTEGER DEFAULT 0,
    interviews_scheduled INTEGER DEFAULT 0,
    
    -- Performance Metrics
    total_session_time INTEGER DEFAULT 0,
    avg_daily_actions INTEGER DEFAULT 0,
    productivity_score INTEGER DEFAULT 0,  -- 0-100
    quality_score INTEGER DEFAULT 0,  -- 0-100
    team_rank INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_month_range CHECK (month >= 1 AND month <= 12),
    CONSTRAINT chk_monthly_productivity_score_range CHECK (productivity_score >= 0 AND productivity_score <= 100),
    CONSTRAINT chk_quality_score_range CHECK (quality_score >= 0 AND quality_score <= 100),
    CONSTRAINT unique_user_monthly_stats UNIQUE(user_id, year, month)
);

-- Indexes for user_monthly_stats
CREATE INDEX IF NOT EXISTS idx_user_monthly_stats_user_id ON user_monthly_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_user_monthly_stats_year ON user_monthly_stats(year);
CREATE INDEX IF NOT EXISTS idx_user_monthly_stats_month ON user_monthly_stats(month);

-- 5. Create interviews table
-- ============================================================================
CREATE TABLE IF NOT EXISTS interviews (
    id VARCHAR(36) PRIMARY KEY,
    candidate_id VARCHAR(36) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id VARCHAR(36) NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Scheduling Information
    scheduled_by VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    interviewer_ids TEXT,  -- Array of user IDs (JSON stored as TEXT for SQLite)
    scheduled_datetime TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Interview Details
    interview_type VARCHAR(50) NOT NULL,
    interview_round INTEGER DEFAULT 1,
    location VARCHAR(500),
    meeting_link VARCHAR(500),
    meeting_id VARCHAR(100),
    meeting_password VARCHAR(100),
    
    -- Status Management
    status VARCHAR(50) DEFAULT 'scheduled',
    
    -- Notifications
    reminder_sent BOOLEAN DEFAULT FALSE,
    confirmation_sent BOOLEAN DEFAULT FALSE,
    
    -- Interview Notes and Results
    notes TEXT,
    feedback TEXT,
    rating INTEGER,
    recommendation VARCHAR(50),
    
    -- Rescheduling
    original_datetime TIMESTAMP,
    reschedule_reason TEXT,
    rescheduled_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    reschedule_count INTEGER DEFAULT 0,
    
    -- Cancellation
    cancelled_at TIMESTAMP,
    cancelled_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    cancellation_reason TEXT,
    
    -- Completion
    completed_at TIMESTAMP,
    completed_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_interview_type CHECK (interview_type IN ('phone', 'video', 'in_person', 'technical', 'hr_round', 'panel', 'behavioral')),
    CONSTRAINT chk_interview_status CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show', 'rescheduled')),
    CONSTRAINT chk_duration_range CHECK (duration_minutes > 0 AND duration_minutes <= 480),
    CONSTRAINT chk_interview_rating_range CHECK (rating >= 1 AND rating <= 5 OR rating IS NULL),
    CONSTRAINT chk_interview_round_positive CHECK (interview_round >= 1),
    CONSTRAINT chk_reschedule_count_positive CHECK (reschedule_count >= 0)
);

-- Indexes for interviews
CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON interviews(candidate_id);
CREATE INDEX IF NOT EXISTS idx_interviews_job_id ON interviews(job_id);
CREATE INDEX IF NOT EXISTS idx_interviews_scheduled_by ON interviews(scheduled_by);
CREATE INDEX IF NOT EXISTS idx_interviews_scheduled_datetime ON interviews(scheduled_datetime);
CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);
CREATE INDEX IF NOT EXISTS idx_interviews_interview_type ON interviews(interview_type);

-- 6. Create candidate_status_history table
-- ============================================================================
CREATE TABLE IF NOT EXISTS candidate_status_history (
    id VARCHAR(36) PRIMARY KEY,
    candidate_id VARCHAR(36) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    
    -- Status Change
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    
    -- Change Details
    changed_by VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    change_reason TEXT,
    notes TEXT,
    
    -- Related Entities
    related_job_id VARCHAR(36) REFERENCES jobs(id) ON DELETE SET NULL,
    related_interview_id VARCHAR(36) REFERENCES interviews(id) ON DELETE SET NULL,
    
    -- Metadata
    activity_metadata TEXT,  -- JSON stored as TEXT for SQLite
    
    -- Timestamp
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_status_history_to_status CHECK (to_status IN ('new', 'screened', 'interviewed', 'offered', 'hired', 'rejected', 'archived'))
);

-- Indexes for candidate_status_history
CREATE INDEX IF NOT EXISTS idx_candidate_status_history_candidate_id ON candidate_status_history(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_status_history_changed_by ON candidate_status_history(changed_by);
CREATE INDEX IF NOT EXISTS idx_candidate_status_history_from_status ON candidate_status_history(from_status);
CREATE INDEX IF NOT EXISTS idx_candidate_status_history_to_status ON candidate_status_history(to_status);
CREATE INDEX IF NOT EXISTS idx_candidate_status_history_changed_at ON candidate_status_history(changed_at);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables were created
DO $$
BEGIN
    RAISE NOTICE 'Phase 3 migration complete!';
    RAISE NOTICE 'Tables created/updated:';
    RAISE NOTICE '  - user_activity_log (enhanced)';
    RAISE NOTICE '  - user_daily_stats';
    RAISE NOTICE '  - user_weekly_stats';
    RAISE NOTICE '  - user_monthly_stats';
    RAISE NOTICE '  - interviews';
    RAISE NOTICE '  - candidate_status_history';
END $$;
