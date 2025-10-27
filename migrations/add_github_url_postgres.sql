-- PostgreSQL Migration: Add github_url to candidates table
-- Run this directly in psql or pgAdmin

-- Add github_url column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='candidates' AND column_name='github_url'
    ) THEN
        ALTER TABLE candidates ADD COLUMN github_url VARCHAR(500);
        RAISE NOTICE 'Added column: candidates.github_url';
    ELSE
        RAISE NOTICE 'Column candidates.github_url already exists';
    END IF;
END $$;

-- Add linkedin_suggestions column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='candidates' AND column_name='linkedin_suggestions'
    ) THEN
        ALTER TABLE candidates ADD COLUMN linkedin_suggestions JSONB;
        RAISE NOTICE 'Added column: candidates.linkedin_suggestions';
    ELSE
        RAISE NOTICE 'Column candidates.linkedin_suggestions already exists';
    END IF;
END $$;

-- Verify columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'candidates' 
AND column_name IN ('github_url', 'linkedin_suggestions')
ORDER BY column_name;
