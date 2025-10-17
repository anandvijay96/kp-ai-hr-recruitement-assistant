"""
Migration: Add responsibilities column to work_experience table
Date: 2025-10-16
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


async def upgrade():
    """Add responsibilities column to work_experience table"""
    
    engine = create_async_engine(settings.database_url)
    
    async with engine.begin() as conn:
        try:
            # For SQLite, check if column exists using pragma
            result = await conn.execute(text("PRAGMA table_info(work_experience)"))
            columns = result.fetchall()  # fetchall() is not async in SQLAlchemy
            column_names = [col[1] for col in columns]
            
            if 'responsibilities' in column_names:
                logger.info("✅ Column 'responsibilities' already exists in work_experience table")
                return
            
            # Add responsibilities column as JSON (SQLite stores as TEXT)
            logger.info("Adding 'responsibilities' column to work_experience table...")
            await conn.execute(text("""
                ALTER TABLE work_experience 
                ADD COLUMN responsibilities TEXT
            """))
            
            logger.info("✅ Successfully added 'responsibilities' column to work_experience table")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
    
    await engine.dispose()


async def downgrade():
    """Remove responsibilities column from work_experience table"""
    
    engine = create_async_engine(settings.database_url)
    
    async with engine.begin() as conn:
        try:
            logger.info("Removing 'responsibilities' column from work_experience table...")
            
            # SQLite doesn't support DROP COLUMN directly, need to recreate table
            # For simplicity, we'll just log a warning
            logger.warning("⚠️ SQLite doesn't support DROP COLUMN. Manual intervention required.")
            logger.warning("To downgrade, you need to recreate the table without the column.")
            
        except Exception as e:
            logger.error(f"❌ Downgrade failed: {e}")
            raise
    
    await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate work_experience table')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade migration')
    args = parser.parse_args()
    
    if args.downgrade:
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
