"""
Apply Migration 008 - Add Jobs Management columns
This script can safely add missing columns even if the application is running
"""
import asyncio
import sys
from sqlalchemy import text, inspect
from core.database import engine, AsyncSessionLocal
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result.fetchall()]
        return column_name in columns
    except Exception as e:
        logger.error(f"Error checking column {column_name}: {e}")
        return False


async def add_column_if_missing(conn, table_name, column_name, column_type):
    """Add a column if it doesn't exist"""
    exists = await check_column_exists(conn, table_name, column_name)
    
    if exists:
        logger.info(f"  ✓ Column {column_name} already exists")
        return False
    
    try:
        # For SQLite, we need to handle the special syntax
        if "DEFAULT" in column_type.upper():
            await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
        else:
            await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT NULL"))
        
        await conn.commit()
        logger.info(f"  ✓ Added column {column_name} to {table_name}")
        return True
    except Exception as e:
        logger.error(f"  ✗ Failed to add column {column_name}: {e}")
        return False


async def apply_migration():
    """Apply migration 008 - Add Jobs Management columns"""
    logger.info("=" * 70)
    logger.info("APPLYING MIGRATION 008: Jobs Management Columns")
    logger.info("=" * 70)
    
    try:
        async with engine.begin() as conn:
            # Check if jobs table exists
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"))
            if not result.fetchone():
                logger.error("❌ Jobs table does not exist! Run the base migration first.")
                return False
            
            logger.info("\n📋 Adding missing columns to 'jobs' table...")
            
            # Add columns
            changes_made = False
            
            # archived_at
            if await add_column_if_missing(conn, "jobs", "archived_at", "TIMESTAMP"):
                changes_made = True
            
            # view_count
            if await add_column_if_missing(conn, "jobs", "view_count", "INTEGER DEFAULT 0"):
                changes_made = True
            
            # application_deadline
            if await add_column_if_missing(conn, "jobs", "application_deadline", "TIMESTAMP"):
                changes_made = True
            
            # Create indexes
            logger.info("\n📋 Creating indexes...")
            
            try:
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_archived_at ON jobs(archived_at)"))
                logger.info("  ✓ Created index on archived_at")
            except Exception as e:
                logger.warning(f"  ⚠️  Could not create index on archived_at: {e}")
            
            try:
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_application_deadline ON jobs(application_deadline)"))
                logger.info("  ✓ Created index on application_deadline")
            except Exception as e:
                logger.warning(f"  ⚠️  Could not create index on application_deadline: {e}")
            
            await conn.commit()
            
            # Verify changes
            logger.info("\n📋 Verifying schema...")
            result = await conn.execute(text("PRAGMA table_info(jobs)"))
            columns = [row[1] for row in result.fetchall()]
            
            required_columns = ['archived_at', 'view_count', 'application_deadline']
            all_present = all(col in columns for col in required_columns)
            
            logger.info("\n" + "=" * 70)
            if all_present:
                logger.info("✅ MIGRATION SUCCESSFUL!")
                logger.info("✅ All required columns are present")
                if changes_made:
                    logger.info("\n⚠️  RESTART YOUR APPLICATION for changes to take effect!")
                else:
                    logger.info("\n✓ No changes needed - schema already up to date")
            else:
                logger.error("❌ MIGRATION FAILED!")
                missing = [col for col in required_columns if col not in columns]
                logger.error(f"Missing columns: {missing}")
            logger.info("=" * 70)
            
            return all_present
    
    except Exception as e:
        logger.error(f"❌ Migration failed with error: {e}", exc_info=True)
        return False
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        success = asyncio.run(apply_migration())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        sys.exit(1)
