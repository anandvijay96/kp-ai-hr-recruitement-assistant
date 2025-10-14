"""
Script to fix foreign key constraints for system-created records
Makes uploaded_by and created_by nullable to allow system uploads
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


async def fix_foreign_key_constraints():
    """Make uploaded_by and created_by nullable for system records"""
    
    engine = get_engine()
    
    async with engine.begin() as conn:
        logger.info("Fixing foreign key constraints...")
        
        # 1. Make resumes.uploaded_by nullable
        try:
            logger.info("Making resumes.uploaded_by nullable...")
            await conn.execute(text("""
                ALTER TABLE resumes 
                ALTER COLUMN uploaded_by DROP NOT NULL
            """))
            logger.info("✅ resumes.uploaded_by is now nullable")
        except Exception as e:
            if "does not exist" in str(e) or "already" in str(e).lower():
                logger.info("✅ resumes.uploaded_by already nullable or doesn't exist")
            else:
                logger.error(f"Error making resumes.uploaded_by nullable: {e}")
        
        # 2. Make candidates.created_by nullable (should already be nullable)
        try:
            logger.info("Checking candidates.created_by...")
            result = await conn.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'candidates' 
                AND column_name = 'created_by'
            """))
            row = result.fetchone()
            if row and row[0] == 'YES':
                logger.info("✅ candidates.created_by is already nullable")
            else:
                logger.info("Making candidates.created_by nullable...")
                await conn.execute(text("""
                    ALTER TABLE candidates 
                    ALTER COLUMN created_by DROP NOT NULL
                """))
                logger.info("✅ candidates.created_by is now nullable")
        except Exception as e:
            logger.error(f"Error checking candidates.created_by: {e}")


async def main():
    try:
        await fix_foreign_key_constraints()
        logger.info("✅ Migration completed successfully!")
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
