"""Fix migration to add missing columns to clients table"""
import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Add missing columns to clients table"""
    engine = get_engine()
    async with engine.begin() as conn:
        try:
            logger.info("Adding missing columns to clients table...")
            
            # Add is_deleted column
            try:
                await conn.execute(text("""
                    ALTER TABLE clients
                    ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE
                """))
                logger.info("✓ Added is_deleted column")
            except Exception as e:
                logger.warning(f"⚠ is_deleted column: {str(e)}")
            
            # Add deleted_at column
            try:
                await conn.execute(text("""
                    ALTER TABLE clients
                    ADD COLUMN deleted_at TIMESTAMP
                """))
                logger.info("✓ Added deleted_at column")
            except Exception as e:
                logger.warning(f"⚠ deleted_at column: {str(e)}")
            
            # Add deleted_by column
            try:
                await conn.execute(text("""
                    ALTER TABLE clients
                    ADD COLUMN deleted_by VARCHAR(36)
                """))
                logger.info("✓ Added deleted_by column")
            except Exception as e:
                logger.warning(f"⚠ deleted_by column: {str(e)}")
            
            # Create index on is_deleted
            try:
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_clients_is_deleted
                    ON clients(is_deleted)
                """))
                logger.info("✓ Created index on is_deleted")
            except Exception as e:
                logger.warning(f"⚠ index creation: {str(e)}")
            
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
