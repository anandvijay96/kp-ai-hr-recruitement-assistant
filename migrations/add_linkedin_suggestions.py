"""
Migration: Add linkedin_suggestions column to candidates table
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
    """Add linkedin_suggestions column to candidates table"""
    
    engine = create_async_engine(settings.database_url)
    
    async with engine.begin() as conn:
        try:
            # For SQLite, check if column exists using pragma
            result = await conn.execute(text("PRAGMA table_info(candidates)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'linkedin_suggestions' in column_names:
                logger.info("✅ Column 'linkedin_suggestions' already exists in candidates table")
                return
            
            # Add linkedin_suggestions column as JSON (SQLite stores as TEXT)
            logger.info("Adding 'linkedin_suggestions' column to candidates table...")
            await conn.execute(text("""
                ALTER TABLE candidates 
                ADD COLUMN linkedin_suggestions TEXT
            """))
            
            logger.info("✅ Successfully added 'linkedin_suggestions' column to candidates table")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(upgrade())
