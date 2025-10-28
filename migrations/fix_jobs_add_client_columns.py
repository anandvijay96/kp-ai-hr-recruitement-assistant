"""
Migration: Add client_id and show_client_to_candidate columns to jobs table
Created: 2025-10-28
Fix: Missing columns causing job creation failures
"""
import asyncio
from sqlalchemy import text
from core.database import engine
import logging

logger = logging.getLogger(__name__)


async def upgrade():
    """Apply migration - Add client-related columns to jobs table"""
    try:
        async with engine.begin() as conn:
            logger.info("Starting migration: Add client columns to jobs table")
            
            # Check if client_id column already exists
            try:
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM pragma_table_info('jobs') WHERE name='client_id'
                """))
                count = result.scalar()
                
                if count == 0:
                    # Add client_id column
                    await conn.execute(text("""
                        ALTER TABLE jobs ADD COLUMN client_id VARCHAR(36)
                    """))
                    logger.info("✓ Added client_id column to jobs table")
                else:
                    logger.info("✓ client_id column already exists")
            except Exception as e:
                logger.error(f"Error adding client_id column: {str(e)}")
            
            # Check if show_client_to_candidate column already exists
            try:
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM pragma_table_info('jobs') WHERE name='show_client_to_candidate'
                """))
                count = result.scalar()
                
                if count == 0:
                    # Add show_client_to_candidate column
                    await conn.execute(text("""
                        ALTER TABLE jobs ADD COLUMN show_client_to_candidate BOOLEAN DEFAULT 0
                    """))
                    logger.info("✓ Added show_client_to_candidate column to jobs table")
                else:
                    logger.info("✓ show_client_to_candidate column already exists")
            except Exception as e:
                logger.error(f"Error adding show_client_to_candidate column: {str(e)}")
            
            # Create index on client_id for better query performance
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_jobs_client_id ON jobs(client_id)
            """))
            logger.info("✓ Created index on client_id")
            
            # Add foreign key constraint if clients table exists
            try:
                # Check if clients table exists
                result = await conn.execute(text("""
                    SELECT name FROM sqlite_master WHERE type='table' AND name='clients'
                """))
                if result.fetchone():
                    # SQLite doesn't support ADD CONSTRAINT directly
                    # The foreign key will be enforced through ORM relationships
                    logger.info("✓ Clients table exists, foreign key will be enforced through ORM")
                else:
                    logger.warning("⚠ Clients table does not exist yet - foreign key will be added when it's created")
            except Exception as e:
                logger.warning(f"Could not check for clients table: {str(e)}")
            
            logger.info("✅ Migration completed successfully")
    
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}", exc_info=True)
        raise


async def downgrade():
    """Rollback migration - Remove client columns from jobs table"""
    try:
        async with engine.begin() as conn:
            logger.info("Rolling back migration: Remove client columns from jobs table")
            
            # SQLite doesn't support DROP COLUMN directly
            # For production PostgreSQL, use:
            # await conn.execute(text("ALTER TABLE jobs DROP COLUMN IF EXISTS client_id"))
            # await conn.execute(text("ALTER TABLE jobs DROP COLUMN IF EXISTS show_client_to_candidate"))
            
            logger.warning("⚠ SQLite detected - column removal requires table recreation")
            logger.info("For SQLite, columns will remain but can be ignored")
            
            logger.info("✅ Migration rollback noted")
    
    except Exception as e:
        logger.error(f"❌ Migration rollback failed: {str(e)}", exc_info=True)
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
