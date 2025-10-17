"""
Phase 3 Database Migration Script (Synchronous Version)
========================================================
This is a synchronous version that works better on WSL/Windows filesystems.
Use this if the async version fails with "disk I/O error".

Usage:
    python migrations/apply_phase3_migration_sync.py
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
from core.database import Base, DATABASE_URL
from models.database import (
    UserActivityLog,
    UserDailyStats, 
    UserWeeklyStats,
    UserMonthlyStats,
    Interview,
    CandidateStatusHistory
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_migration():
    """Apply Phase 3 database migration using synchronous SQLAlchemy"""
    
    logger.info("="*70)
    logger.info("PHASE 3 DATABASE MIGRATION - STARTING (SYNC VERSION)")
    logger.info("="*70)
    
    try:
        # Create synchronous engine
        # Convert async URL to sync URL
        sync_url = DATABASE_URL.replace('+aiosqlite', '')
        engine = create_engine(sync_url, echo=False)
        
        # Step 0: Create all tables first
        logger.info("Step 0: Creating all Phase 3 tables...")
        Base.metadata.create_all(engine)
        logger.info("  ✓ All tables created (or already exist)")
        
        # Step 1: Check if user_activity_log needs enhancement
        logger.info("Step 1: Checking user_activity_log table...")
        
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('user_activity_log')]
        
        if 'entity_type' in columns:
            logger.info("  ✓ user_activity_log already enhanced (skipping)")
        else:
            logger.info("  → Enhancing user_activity_log table...")
            
            with engine.begin() as conn:
                alter_statements = [
                    "ALTER TABLE user_activity_log ADD COLUMN entity_type VARCHAR(50)",
                    "ALTER TABLE user_activity_log ADD COLUMN entity_id VARCHAR(36)",
                    "ALTER TABLE user_activity_log ADD COLUMN request_metadata TEXT",
                    "ALTER TABLE user_activity_log ADD COLUMN request_method VARCHAR(10)",
                    "ALTER TABLE user_activity_log ADD COLUMN request_path VARCHAR(500)",
                    "ALTER TABLE user_activity_log ADD COLUMN duration_ms INTEGER",
                ]
                
                for stmt in alter_statements:
                    try:
                        conn.execute(text(stmt))
                        logger.info(f"    ✓ Added column")
                    except Exception as e:
                        if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                            logger.info(f"    ⚠ Column already exists (skipping)")
                        else:
                            raise
        
        # Step 2: Create indexes
        logger.info("Step 2: Creating indexes on user_activity_log...")
        
        with engine.begin() as conn:
            index_statements = [
                "CREATE INDEX IF NOT EXISTS idx_user_activity_entity_type ON user_activity_log(entity_type)",
                "CREATE INDEX IF NOT EXISTS idx_user_activity_entity_id ON user_activity_log(entity_id)",
            ]
            
            for stmt in index_statements:
                try:
                    conn.execute(text(stmt))
                    logger.info(f"  ✓ Created index")
                except Exception as e:
                    logger.warning(f"  ⚠ Index creation skipped: {e}")
        
        logger.info("="*70)
        logger.info("PHASE 3 MIGRATION COMPLETED SUCCESSFULLY!")
        logger.info("="*70)
        logger.info("\nNew tables created:")
        logger.info("  ✓ user_activity_log (enhanced with entity tracking)")
        logger.info("  ✓ user_daily_stats")
        logger.info("  ✓ user_weekly_stats")
        logger.info("  ✓ user_monthly_stats")
        logger.info("  ✓ interviews")
        logger.info("  ✓ candidate_status_history")
        logger.info("\nYou can now proceed with Phase 3 implementation!")
        logger.info("="*70)
        
        return True
        
    except Exception as e:
        logger.error("="*70)
        logger.error("MIGRATION FAILED!")
        logger.error("="*70)
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        logger.error("\n❌ Migration failed! Please check the errors above.")
        return False


def verify_tables():
    """Verify that all Phase 3 tables exist"""
    logger.info("\nVerifying Phase 3 tables...")
    
    tables_to_check = [
        'user_activity_log',
        'user_daily_stats',
        'user_weekly_stats',
        'user_monthly_stats',
        'interviews',
        'candidate_status_history'
    ]
    
    sync_url = DATABASE_URL.replace('+aiosqlite', '')
    engine = create_engine(sync_url, echo=False)
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    for table in tables_to_check:
        exists = table in existing_tables
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {table}: {'EXISTS' if exists else 'NOT FOUND'}")
    
    logger.info("\nTable verification complete!")


def main():
    """Main migration function"""
    logger.info("\n🚀 Starting Phase 3 Database Migration...")
    logger.info("This will create tables for:")
    logger.info("  • User activity tracking (daily/weekly/monthly stats)")
    logger.info("  • Interview scheduling and management")
    logger.info("  • Candidate status history tracking")
    logger.info("")
    
    success = apply_migration()
    
    if success:
        verify_tables()
        logger.info("\n✅ Migration completed successfully!")
        logger.info("You can now start the application with: python main.py")
        return 0
    else:
        logger.error("\n❌ Migration failed!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
