-- Complete PostgreSQL Migration Script
-- Adds all missing columns to production database
-- Safe to run multiple times (idempotent)

-- ============================================================
-- CANDIDATES TABLE
-- ============================================================
DO $$
BEGIN
    -- github_url
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='candidates' AND column_name='github_url'
    ) THEN
        ALTER TABLE candidates ADD COLUMN github_url VARCHAR(500);
        RAISE NOTICE '✅ Added: candidates.github_url';
    ELSE
        RAISE NOTICE '⏭️  Skipped: candidates.github_url (already exists)';
    END IF;

    -- linkedin_suggestions
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='candidates' AND column_name='linkedin_suggestions'
    ) THEN
        ALTER TABLE candidates ADD COLUMN linkedin_suggestions JSONB;
        RAISE NOTICE '✅ Added: candidates.linkedin_suggestions';
    ELSE
        RAISE NOTICE '⏭️  Skipped: candidates.linkedin_suggestions (already exists)';
    END IF;
END $$;

-- ============================================================
-- RESUMES TABLE
-- ============================================================
DO $$
BEGIN
    -- authenticity_details
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='resumes' AND column_name='authenticity_details'
    ) THEN
        ALTER TABLE resumes ADD COLUMN authenticity_details JSONB;
        RAISE NOTICE '✅ Added: resumes.authenticity_details';
    ELSE
        RAISE NOTICE '⏭️  Skipped: resumes.authenticity_details (already exists)';
    END IF;

    -- jd_match_details
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='resumes' AND column_name='jd_match_details'
    ) THEN
        ALTER TABLE resumes ADD COLUMN jd_match_details JSONB;
        RAISE NOTICE '✅ Added: resumes.jd_match_details';
    ELSE
        RAISE NOTICE '⏭️  Skipped: resumes.jd_match_details (already exists)';
    END IF;
END $$;

-- ============================================================
-- CLIENTS TABLE (Create if not exists)
-- ============================================================
CREATE TABLE IF NOT EXISTS clients (
    id VARCHAR(36) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL UNIQUE,
    industry VARCHAR(100),
    website VARCHAR(255),
    description TEXT,
    contact_person VARCHAR(100) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(20),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',
    client_type VARCHAR(20) DEFAULT 'direct',
    priority VARCHAR(20) DEFAULT 'medium',
    contract_start_date VARCHAR(50),
    contract_end_date VARCHAR(50),
    contract_value VARCHAR(50),
    payment_terms VARCHAR(255),
    notes TEXT,
    tags TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by VARCHAR(36),
    CONSTRAINT chk_client_status CHECK (status IN ('active', 'inactive', 'on_hold')),
    CONSTRAINT chk_client_type CHECK (client_type IN ('direct', 'agency', 'partner')),
    CONSTRAINT chk_client_priority CHECK (priority IN ('low', 'medium', 'high'))
);

-- ============================================================
-- VERIFICATION
-- ============================================================
DO $$
DECLARE
    missing_count INT := 0;
BEGIN
    -- Check candidates columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='candidates' AND column_name='github_url') THEN
        RAISE WARNING '❌ Missing: candidates.github_url';
        missing_count := missing_count + 1;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='candidates' AND column_name='linkedin_suggestions') THEN
        RAISE WARNING '❌ Missing: candidates.linkedin_suggestions';
        missing_count := missing_count + 1;
    END IF;
    
    -- Check resumes columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resumes' AND column_name='authenticity_details') THEN
        RAISE WARNING '❌ Missing: resumes.authenticity_details';
        missing_count := missing_count + 1;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resumes' AND column_name='jd_match_details') THEN
        RAISE WARNING '❌ Missing: resumes.jd_match_details';
        missing_count := missing_count + 1;
    END IF;
    
    -- Final result
    IF missing_count = 0 THEN
        RAISE NOTICE '✅ All columns exist! Migration successful!';
    ELSE
        RAISE WARNING '⚠️  % column(s) still missing. Review errors above.', missing_count;
    END IF;
END $$;

-- Display added columns
SELECT 
    '✅ Migration Complete!' as status,
    'Check NOTICES above for details' as message;
