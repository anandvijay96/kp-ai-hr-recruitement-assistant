"""
Migration: Add Jobs Management tables and columns
Created: 2025-10-08
Feature: Jobs Management (Feature 8)
"""
import asyncio
from sqlalchemy import text
from core.database import engine
import logging

logger = logging.getLogger(__name__)


async def upgrade():
    """Apply migration - Create Jobs Management tables"""
    try:
        async with engine.begin() as conn:
            logger.info("Starting migration 008: Jobs Management tables")
            
            # Create job_analytics table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS job_analytics (
                    id VARCHAR(36) PRIMARY KEY,
                    job_id VARCHAR(36) NOT NULL,
                    date DATE NOT NULL,
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
                )
            """))
            logger.info("✓ Created job_analytics table")
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_analytics_job_id ON job_analytics(job_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_analytics_date ON job_analytics(date)
            """))
            
            # Create job_external_postings table
            await conn.execute(text("""
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
                )
            """))
            logger.info("✓ Created job_external_postings table")
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_external_postings_job_id 
                ON job_external_postings(job_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_external_postings_status 
                ON job_external_postings(status)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_external_postings_portal 
                ON job_external_postings(portal)
            """))
            
            # Create job_audit_log table
            await conn.execute(text("""
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
                )
            """))
            logger.info("✓ Created job_audit_log table")
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_audit_log_job_id ON job_audit_log(job_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_audit_log_timestamp ON job_audit_log(timestamp)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_audit_log_user_id ON job_audit_log(user_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_audit_log_action_type ON job_audit_log(action_type)
            """))
            
            # Create bulk_operations table
            await conn.execute(text("""
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
                )
            """))
            logger.info("✓ Created bulk_operations table")
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bulk_operations_status ON bulk_operations(status)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bulk_operations_initiated_by 
                ON bulk_operations(initiated_by)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bulk_operations_created_at 
                ON bulk_operations(created_at)
            """))
            
            # Modify jobs table - add new columns
            await conn.execute(text("""
                ALTER TABLE jobs ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP
            """))
            logger.info("✓ Added archived_at column to jobs table")
            
            await conn.execute(text("""
                ALTER TABLE jobs ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0
            """))
            logger.info("✓ Added view_count column to jobs table")
            
            await conn.execute(text("""
                ALTER TABLE jobs ADD COLUMN IF NOT EXISTS application_deadline TIMESTAMP
            """))
            logger.info("✓ Added application_deadline column to jobs table")
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_jobs_archived_at ON jobs(archived_at)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_jobs_application_deadline 
                ON jobs(application_deadline)
            """))
            
            # Add reason column to job_status_history if not exists
            await conn.execute(text("""
                ALTER TABLE job_status_history ADD COLUMN IF NOT EXISTS reason TEXT
            """))
            logger.info("✓ Added reason column to job_status_history table")
            
            logger.info("✅ Migration 008 completed successfully")
    
    except Exception as e:
        logger.error(f"❌ Migration 008 failed: {str(e)}", exc_info=True)
        raise


async def downgrade():
    """Rollback migration - Drop Jobs Management tables"""
    try:
        async with engine.begin() as conn:
            logger.info("Rolling back migration 008: Jobs Management tables")
            
            # Drop tables in reverse order (respecting foreign keys)
            await conn.execute(text("DROP TABLE IF EXISTS bulk_operations"))
            await conn.execute(text("DROP TABLE IF EXISTS job_audit_log"))
            await conn.execute(text("DROP TABLE IF EXISTS job_external_postings"))
            await conn.execute(text("DROP TABLE IF EXISTS job_analytics"))
            
            # Remove added columns from jobs table
            # Note: SQLite doesn't support DROP COLUMN, so this is PostgreSQL syntax
            # For SQLite, you'd need to recreate the table
            try:
                await conn.execute(text("ALTER TABLE jobs DROP COLUMN IF EXISTS archived_at"))
                await conn.execute(text("ALTER TABLE jobs DROP COLUMN IF EXISTS view_count"))
                await conn.execute(text("ALTER TABLE jobs DROP COLUMN IF EXISTS application_deadline"))
            except Exception as e:
                logger.warning(f"Could not drop columns (may be SQLite): {str(e)}")
            
            # Remove reason column from job_status_history
            try:
                await conn.execute(text("ALTER TABLE job_status_history DROP COLUMN IF EXISTS reason"))
            except Exception as e:
                logger.warning(f"Could not drop reason column: {str(e)}")
            
            logger.info("✅ Migration 008 rolled back successfully")
    
    except Exception as e:
        logger.error(f"❌ Migration 008 rollback failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run migration
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        print("Running downgrade...")
        asyncio.run(downgrade())
    else:
        print("Running upgrade...")
        asyncio.run(upgrade())
