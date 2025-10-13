"""
Migration 011: Add Client Management Tables
Creates tables for client management feature including:
- clients
- client_contacts
- client_communications
- client_feedback
- client_job_assignments
- client_analytics
"""
import sqlite3
import logging

logger = logging.getLogger(__name__)


def apply_migration(db_path: str = "hr_recruitment.db"):
    """Apply migration to add client management tables"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Starting migration 011: Client Management")
        
        # 1. Create clients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                client_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                industry TEXT,
                website TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                country TEXT,
                postal_code TEXT,
                logo_url TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                account_manager_id TEXT REFERENCES users(id),
                created_by TEXT NOT NULL REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP,
                deactivation_reason TEXT,
                CHECK (status IN ('active', 'inactive', 'on-hold', 'archived'))
            )
        """)
        logger.info("✓ Created clients table")
        
        # Create indexes for clients
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_account_manager ON clients(account_manager_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_industry ON clients(industry)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_client_code ON clients(client_code)")
        
        # 2. Create client_contacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_contacts (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                full_name TEXT NOT NULL,
                title TEXT,
                email TEXT NOT NULL,
                phone TEXT,
                mobile TEXT,
                is_primary INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✓ Created client_contacts table")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_contacts_client_id ON client_contacts(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_contacts_email ON client_contacts(email)")
        
        # 3. Create client_communications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_communications (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                communication_type TEXT NOT NULL,
                subject TEXT,
                notes TEXT,
                communication_date TIMESTAMP NOT NULL,
                participants TEXT,
                job_reference_id TEXT REFERENCES jobs(id),
                logged_by TEXT NOT NULL REFERENCES users(id),
                is_important INTEGER DEFAULT 0,
                follow_up_required INTEGER DEFAULT 0,
                follow_up_date DATE,
                attachments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (communication_type IN ('meeting', 'phone_call', 'email', 'video_call', 'contract_signed'))
            )
        """)
        logger.info("✓ Created client_communications table")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_communications_client_id ON client_communications(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_communications_date ON client_communications(communication_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_communications_type ON client_communications(communication_type)")
        
        # 4. Create client_feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_feedback (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                feedback_period TEXT,
                feedback_date DATE NOT NULL,
                responsiveness_rating INTEGER NOT NULL,
                communication_rating INTEGER NOT NULL,
                requirements_clarity_rating INTEGER NOT NULL,
                decision_speed_rating INTEGER NOT NULL,
                overall_satisfaction INTEGER NOT NULL,
                written_feedback TEXT,
                submitted_by TEXT NOT NULL REFERENCES users(id),
                finalized_by TEXT REFERENCES users(id),
                is_finalized INTEGER DEFAULT 0,
                finalized_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (responsiveness_rating BETWEEN 1 AND 5),
                CHECK (communication_rating BETWEEN 1 AND 5),
                CHECK (requirements_clarity_rating BETWEEN 1 AND 5),
                CHECK (decision_speed_rating BETWEEN 1 AND 5),
                CHECK (overall_satisfaction BETWEEN 1 AND 5)
            )
        """)
        logger.info("✓ Created client_feedback table")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_feedback_client_id ON client_feedback(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_feedback_date ON client_feedback(feedback_date)")
        
        # 5. Create client_job_assignments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_job_assignments (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
                assigned_by TEXT NOT NULL REFERENCES users(id),
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                unassigned_at TIMESTAMP,
                unassigned_by TEXT REFERENCES users(id),
                is_active INTEGER DEFAULT 1,
                UNIQUE(client_id, job_id)
            )
        """)
        logger.info("✓ Created client_job_assignments table")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_job_assignments_client_id ON client_job_assignments(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_job_assignments_job_id ON client_job_assignments(job_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_job_assignments_is_active ON client_job_assignments(is_active)")
        
        # 6. Create client_analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_analytics (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                date DATE NOT NULL,
                active_jobs_count INTEGER DEFAULT 0,
                total_candidates_count INTEGER DEFAULT 0,
                screened_count INTEGER DEFAULT 0,
                shortlisted_count INTEGER DEFAULT 0,
                interviewed_count INTEGER DEFAULT 0,
                hired_count INTEGER DEFAULT 0,
                avg_time_to_fill_days INTEGER,
                avg_candidate_quality_score TEXT,
                revenue_generated TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(client_id, date)
            )
        """)
        logger.info("✓ Created client_analytics table")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_analytics_client_id ON client_analytics(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_analytics_date ON client_analytics(date)")
        
        # 7. Add client_id to jobs table (if not exists)
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'client_id' not in columns:
            cursor.execute("ALTER TABLE jobs ADD COLUMN client_id TEXT REFERENCES clients(id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_client_id ON jobs(client_id)")
            logger.info("✓ Added client_id to jobs table")
        
        # 8. Add client_id to resumes table (if not exists)
        cursor.execute("PRAGMA table_info(resumes)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'client_id' not in columns:
            cursor.execute("ALTER TABLE resumes ADD COLUMN client_id TEXT REFERENCES clients(id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resumes_client_id ON resumes(client_id)")
            logger.info("✓ Added client_id to resumes table")
        
        conn.commit()
        logger.info("✅ Migration 011 completed successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 011 failed: {str(e)}")
        conn.rollback()
        raise e
    finally:
        conn.close()


def rollback_migration(db_path: str = "hr_recruitment.db"):
    """Rollback migration (drop all client management tables)"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.warning("Rolling back migration 011: Client Management")
        
        # Drop tables in reverse order (respect foreign key constraints)
        tables = [
            "client_analytics",
            "client_job_assignments",
            "client_feedback",
            "client_communications",
            "client_contacts",
            "clients"
        ]
        
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            logger.info(f"✓ Dropped {table} table")
        
        # Remove client_id columns from jobs and resumes
        # Note: SQLite doesn't support DROP COLUMN, so we'd need to recreate tables
        # For now, just log a warning
        logger.warning("⚠️  client_id columns in jobs and resumes tables not removed (requires table recreation)")
        
        conn.commit()
        logger.info("✅ Migration 011 rollback completed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration 011 rollback failed: {str(e)}")
        conn.rollback()
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        apply_migration()
