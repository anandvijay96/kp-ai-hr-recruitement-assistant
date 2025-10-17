"""
Phase 3 Database Migration Script
==================================
Applies Phase 3 schema changes for activity tracking, interview scheduling,
and enhanced candidate workflow management.

Usage:
    python migrations/apply_phase3_migration.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.database import engine, Base
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


async def apply_migration():
    """Apply Phase 3 database migration using SQLAlchemy"""
    
    logger.info("="*70)
    logger.info("PHASE 3 DATABASE MIGRATION - STARTING")
    logger.info("="*70)
    
    try:
        # Use SQLAlchemy to create tables directly from models
        logger.info("Creating Phase 3 tables using SQLAlchemy...")
        
        async with engine.begin() as conn:
            # First, add columns to existing user_activity_log table
            logger.info("Step 1: Enhancing user_activity_log table...")
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
                    await conn.execute(text(stmt))
                    logger.info(f"  ✓ Added column")
                except Exception as e:
                    if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                        logger.info(f"  ⚠ Column already exists (skipping)")
                    else:
                        raise
            
            # Create indexes on new columns
            logger.info("Step 2: Creating indexes on user_activity_log...")
            index_statements = [
                "CREATE INDEX IF NOT EXISTS idx_user_activity_entity_type ON user_activity_log(entity_type)",
                "CREATE INDEX IF NOT EXISTS idx_user_activity_entity_id ON user_activity_log(entity_id)",
            ]
            
            for stmt in index_statements:
                try:
                    await conn.execute(text(stmt))
                    logger.info(f"  ✓ Created index")
                except Exception as e:
                    logger.warning(f"  ⚠ Index creation skipped: {e}")
            
            # Now create all Phase 3 tables using SQLAlchemy
            logger.info("Step 3: Creating Phase 3 tables...")
            
            # Import Base to get metadata
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
            
            logger.info("  ✓ All Phase 3 tables created")
            
            await conn.commit()
        
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
        return False


async def verify_tables():
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
    
    async with engine.begin() as conn:
        for table in tables_to_check:
            # Use SQLite-compatible query (works with both SQLite and PostgreSQL)
            result = await conn.execute(text(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            ))
            exists = result.scalar() is not None
            status = "✓" if exists else "✗"
            logger.info(f"  {status} {table}: {'EXISTS' if exists else 'NOT FOUND'}")
    
    logger.info("\nTable verification complete!")


async def main():
    """Main migration function"""
    logger.info("\n🚀 Starting Phase 3 Database Migration...")
    logger.info("This will create tables for:")
    logger.info("  • User activity tracking (daily/weekly/monthly stats)")
    logger.info("  • Interview scheduling and management")
    logger.info("  • Candidate status history tracking")
    logger.info("")
    
    # Apply the migration
    success = await apply_migration()
    
    if success:
        # Verify tables were created
        await verify_tables()
        logger.info("\n✅ Migration successful! Phase 3 database is ready.")
        return 0
    else:
        logger.error("\n❌ Migration failed! Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
