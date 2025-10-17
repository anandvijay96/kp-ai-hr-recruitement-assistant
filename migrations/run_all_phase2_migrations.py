"""
Consolidated Phase 2 Migrations Runner
Runs all Phase 2 migrations in correct order
Safe to run multiple times (idempotent)
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_all_migrations():
    """Run all Phase 2 migrations"""
    
    engine = create_async_engine(settings.database_url)
    
    logger.info("="*60)
    logger.info("PHASE 2 MIGRATIONS - STARTING")
    logger.info("="*60)
    
    async with engine.begin() as conn:
        try:
            # Migration 1: Add responsibilities column
            logger.info("\n[1/2] Adding 'responsibilities' column to work_experience...")
            
            result = await conn.execute(text("PRAGMA table_info(work_experience)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'responsibilities' in column_names:
                logger.info("✅ Column 'responsibilities' already exists - SKIPPING")
            else:
                await conn.execute(text("""
                    ALTER TABLE work_experience 
                    ADD COLUMN responsibilities TEXT
                """))
                logger.info("✅ Successfully added 'responsibilities' column")
            
            # Migration 2: Add linkedin_suggestions column
            logger.info("\n[2/2] Adding 'linkedin_suggestions' column to candidates...")
            
            result = await conn.execute(text("PRAGMA table_info(candidates)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'linkedin_suggestions' in column_names:
                logger.info("✅ Column 'linkedin_suggestions' already exists - SKIPPING")
            else:
                await conn.execute(text("""
                    ALTER TABLE candidates 
                    ADD COLUMN linkedin_suggestions TEXT
                """))
                logger.info("✅ Successfully added 'linkedin_suggestions' column")
            
            logger.info("\n" + "="*60)
            logger.info("✅ ALL PHASE 2 MIGRATIONS COMPLETED SUCCESSFULLY")
            logger.info("="*60)
            
            # Verify migrations
            logger.info("\nVerifying migrations...")
            
            result = await conn.execute(text("PRAGMA table_info(work_experience)"))
            we_columns = [col[1] for col in result.fetchall()]
            logger.info(f"work_experience columns: {', '.join(we_columns)}")
            
            result = await conn.execute(text("PRAGMA table_info(candidates)"))
            c_columns = [col[1] for col in result.fetchall()]
            logger.info(f"candidates columns: {', '.join(c_columns)}")
            
            if 'responsibilities' in we_columns and 'linkedin_suggestions' in c_columns:
                logger.info("\n✅ VERIFICATION PASSED - All columns present")
            else:
                logger.error("\n❌ VERIFICATION FAILED - Some columns missing")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"\n❌ Migration failed: {e}")
            raise
    
    await engine.dispose()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PHASE 2 MIGRATIONS - PRODUCTION DEPLOYMENT")
    print("="*60)
    print("\nThis script will:")
    print("1. Add 'responsibilities' column to work_experience table")
    print("2. Add 'linkedin_suggestions' column to candidates table")
    print("\nThese migrations are:")
    print("✅ Idempotent (safe to run multiple times)")
    print("✅ Additive only (no data loss)")
    print("✅ Backward compatible")
    print("\n" + "="*60)
    
    response = input("\nProceed with migrations? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Migrations cancelled")
        sys.exit(0)
    
    success = asyncio.run(run_all_migrations())
    
    if success:
        print("\n" + "="*60)
        print("🎉 DEPLOYMENT READY")
        print("="*60)
        print("\nNext steps:")
        print("1. Restart the application")
        print("2. Run smoke tests")
        print("3. Monitor logs for errors")
        sys.exit(0)
    else:
        print("\n❌ Migration verification failed")
        sys.exit(1)
