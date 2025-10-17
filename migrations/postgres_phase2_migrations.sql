-- PostgreSQL Phase 2 Migrations
-- Run this on production PostgreSQL database

-- ============================================
-- PART 1: Soft Delete Columns (if missing)
-- ============================================

-- Add soft delete columns to candidates table (if they don't exist)
DO $$ 
BEGIN
    -- is_deleted column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'candidates' AND column_name = 'is_deleted'
    ) THEN
        ALTER TABLE candidates ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL;
        CREATE INDEX idx_candidates_is_deleted ON candidates(is_deleted);
        RAISE NOTICE 'Added is_deleted column to candidates';
    ELSE
        RAISE NOTICE 'is_deleted column already exists in candidates';
    END IF;

    -- deleted_at column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'candidates' AND column_name = 'deleted_at'
    ) THEN
        ALTER TABLE candidates ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
        RAISE NOTICE 'Added deleted_at column to candidates';
    ELSE
        RAISE NOTICE 'deleted_at column already exists in candidates';
    END IF;

    -- deleted_by column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'candidates' AND column_name = 'deleted_by'
    ) THEN
        ALTER TABLE candidates ADD COLUMN deleted_by VARCHAR(255);
        RAISE NOTICE 'Added deleted_by column to candidates';
    ELSE
        RAISE NOTICE 'deleted_by column already exists in candidates';
    END IF;

    -- deletion_reason column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'candidates' AND column_name = 'deletion_reason'
    ) THEN
        ALTER TABLE candidates ADD COLUMN deletion_reason TEXT;
        RAISE NOTICE 'Added deletion_reason column to candidates';
    ELSE
        RAISE NOTICE 'deletion_reason column already exists in candidates';
    END IF;

    -- professional_summary column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'candidates' AND column_name = 'professional_summary'
    ) THEN
        ALTER TABLE candidates ADD COLUMN professional_summary TEXT;
        RAISE NOTICE 'Added professional_summary column to candidates';
    ELSE
        RAISE NOTICE 'professional_summary column already exists in candidates';
    END IF;
END $$;

-- ============================================
-- PART 2: Phase 2 New Columns
-- ============================================

DO $$ 
BEGIN
    -- responsibilities column in work_experience
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'work_experience' AND column_name = 'responsibilities'
    ) THEN
        ALTER TABLE work_experience ADD COLUMN responsibilities JSONB;
        RAISE NOTICE 'Added responsibilities column to work_experience';
    ELSE
        RAISE NOTICE 'responsibilities column already exists in work_experience';
    END IF;

    -- linkedin_suggestions column in candidates
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'candidates' AND column_name = 'linkedin_suggestions'
    ) THEN
        ALTER TABLE candidates ADD COLUMN linkedin_suggestions JSONB;
        RAISE NOTICE 'Added linkedin_suggestions column to candidates';
    ELSE
        RAISE NOTICE 'linkedin_suggestions column already exists in candidates';
    END IF;
END $$;

-- ============================================
-- Verification
-- ============================================

-- Show all candidates columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'candidates'
ORDER BY ordinal_position;

-- Show all work_experience columns
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'work_experience'
ORDER BY ordinal_position;
