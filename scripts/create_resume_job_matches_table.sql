-- Create resume_job_matches table manually
-- Run this with: sqlite3 hr_recruitment.db < scripts/create_resume_job_matches_table.sql

CREATE TABLE IF NOT EXISTS resume_job_matches (
    id TEXT PRIMARY KEY,
    resume_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    match_score INTEGER NOT NULL CHECK (match_score >= 0 AND match_score <= 100),
    skill_score INTEGER CHECK (skill_score >= 0 AND skill_score <= 100),
    experience_score INTEGER CHECK (experience_score >= 0 AND experience_score <= 100),
    education_score INTEGER CHECK (education_score >= 0 AND education_score <= 100),
    matched_skills TEXT,  -- JSON array stored as TEXT
    missing_skills TEXT,  -- JSON array stored as TEXT
    match_details TEXT,   -- JSON object stored as TEXT
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    UNIQUE(resume_id, job_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_resume_job_matches_resume ON resume_job_matches(resume_id);
CREATE INDEX IF NOT EXISTS idx_resume_job_matches_job ON resume_job_matches(job_id);
CREATE INDEX IF NOT EXISTS idx_resume_job_matches_score ON resume_job_matches(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_resume_job_matches_created ON resume_job_matches(created_at DESC);

-- Verify table was created
SELECT 'Table created successfully!' as status;
SELECT name FROM sqlite_master WHERE type='table' AND name='resume_job_matches';
