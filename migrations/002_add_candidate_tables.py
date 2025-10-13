"""
Database migration script for Feature 2: Resume Upload & Data Extraction
Adds candidate management tables and enhances resume table

Migration ID: 002
Created: 2025-10-06
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)


def upgrade(db_path: str = "hr_recruitment.db"):
    """
    Apply migration to add candidate-related tables
    
    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        logger.info("Starting migration 002: Adding candidate tables")
        
        # 1. Create candidates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                uuid TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                linkedin_url TEXT,
                location TEXT,
                source TEXT DEFAULT 'upload',
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT REFERENCES users(id)
            )
        """)
        logger.info("✓ Created candidates table")
        
        # Create indexes for candidates
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_phone ON candidates(phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(full_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status)")
        logger.info("✓ Created indexes for candidates table")
        
        # 2. Create education table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS education (
                id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
                degree TEXT,
                field TEXT,
                institution TEXT,
                location TEXT,
                start_date TEXT,
                end_date TEXT,
                gpa TEXT,
                confidence_score TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_education_candidate ON education(candidate_id)")
        logger.info("✓ Created education table")
        
        # 3. Create work_experience table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_experience (
                id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
                company TEXT,
                title TEXT,
                location TEXT,
                start_date TEXT,
                end_date TEXT,
                is_current INTEGER DEFAULT 0,
                duration_months INTEGER,
                description TEXT,
                confidence_score TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_experience_candidate ON work_experience(candidate_id)")
        logger.info("✓ Created work_experience table")
        
        # 4. Create skills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name)")
        logger.info("✓ Created skills table")
        
        # 5. Create candidate_skills junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_skills (
                candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
                skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
                proficiency TEXT,
                confidence_score TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (candidate_id, skill_id)
            )
        """)
        logger.info("✓ Created candidate_skills table")
        
        # 6. Create certifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certifications (
                id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                issuer TEXT,
                issue_date TEXT,
                expiry_date TEXT,
                credential_id TEXT,
                confidence_score TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_certifications_candidate ON certifications(candidate_id)")
        logger.info("✓ Created certifications table")
        
        # 7. Create duplicate_checks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS duplicate_checks (
                id TEXT PRIMARY KEY,
                resume_id TEXT REFERENCES resumes(id) ON DELETE CASCADE,
                candidate_id TEXT REFERENCES candidates(id) ON DELETE CASCADE,
                match_type TEXT,
                match_score TEXT,
                matched_candidate_id TEXT REFERENCES candidates(id) ON DELETE SET NULL,
                resolution TEXT,
                resolved_by TEXT REFERENCES users(id) ON DELETE SET NULL,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_duplicate_checks_resume ON duplicate_checks(resume_id)")
        logger.info("✓ Created duplicate_checks table")
        
        # 8. Add new columns to resumes table
        try:
            cursor.execute("ALTER TABLE resumes ADD COLUMN candidate_id TEXT REFERENCES candidates(id) ON DELETE SET NULL")
            logger.info("✓ Added candidate_id column to resumes table")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                logger.info("  candidate_id column already exists")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE resumes ADD COLUMN processing_status TEXT DEFAULT 'pending'")
            logger.info("✓ Added processing_status column to resumes table")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                logger.info("  processing_status column already exists")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE resumes ADD COLUMN processing_error TEXT")
            logger.info("✓ Added processing_error column to resumes table")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                logger.info("  processing_error column already exists")
            else:
                raise
        
        try:
            cursor.execute("ALTER TABLE resumes ADD COLUMN processed_at TIMESTAMP")
            logger.info("✓ Added processed_at column to resumes table")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                logger.info("  processed_at column already exists")
            else:
                raise
        
        # Create index for candidate_id in resumes
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resumes_candidate ON resumes(candidate_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resumes_processing_status ON resumes(processing_status)")
            logger.info("✓ Created indexes for new resume columns")
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        logger.info("✅ Migration 002 completed successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Migration 002 failed: {str(e)}")
        raise
    
    finally:
        conn.close()


def downgrade(db_path: str = "hr_recruitment.db"):
    """
    Rollback migration (drop candidate-related tables)
    
    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        logger.info("Starting rollback of migration 002")
        
        # Drop tables in reverse order (respecting foreign keys)
        cursor.execute("DROP TABLE IF EXISTS duplicate_checks")
        cursor.execute("DROP TABLE IF EXISTS certifications")
        cursor.execute("DROP TABLE IF EXISTS candidate_skills")
        cursor.execute("DROP TABLE IF EXISTS skills")
        cursor.execute("DROP TABLE IF EXISTS work_experience")
        cursor.execute("DROP TABLE IF EXISTS education")
        cursor.execute("DROP TABLE IF EXISTS candidates")
        
        logger.info("✅ Migration 002 rolled back successfully")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Rollback of migration 002 failed: {str(e)}")
        raise
    
    finally:
        conn.close()


if __name__ == "__main__":
    """Run migration when script is executed directly"""
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
