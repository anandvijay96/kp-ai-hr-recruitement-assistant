"""
Script to add professional_summary column to candidates table
Safe to run on production - checks if column exists first
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.database import get_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_professional_summary_column():
    """Add professional_summary column to candidates table if it doesn't exist"""
    
    engine = get_engine()
    
    async with engine.begin() as conn:
        # Check if column exists
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'candidates' 
        AND column_name = 'professional_summary'
        """
        
        result = await conn.execute(text(check_query))
        exists = result.fetchone() is not None
        
        if exists:
            logger.info("✅ Column 'professional_summary' already exists in candidates table")
            return
        
        # Add column
        logger.info("Adding 'professional_summary' column to candidates table...")
        
        alter_query = """
        ALTER TABLE candidates 
        ADD COLUMN professional_summary TEXT
        """
        
        await conn.execute(text(alter_query))
        
        logger.info("✅ Successfully added 'professional_summary' column to candidates table")


async def main():
    try:
        await add_professional_summary_column()
        logger.info("✅ Migration completed successfully!")
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
