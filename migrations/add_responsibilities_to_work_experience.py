"""
Migration: Add responsibilities column to work_experience table
Date: 2025-10-16
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, JSON, Text
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade():
    """Add responsibilities column to work_experience table"""
    
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        try:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'work_experience' 
                AND column_name = 'responsibilities'
            """))
            
            exists = result.scalar() > 0
            
            if exists:
                logger.info("✅ Column 'responsibilities' already exists in work_experience table")
                return
            
            # Add responsibilities column as JSON
            logger.info("Adding 'responsibilities' column to work_experience table...")
            conn.execute(text("""
                ALTER TABLE work_experience 
                ADD COLUMN responsibilities JSON NULL
            """))
            conn.commit()
            
            logger.info("✅ Successfully added 'responsibilities' column to work_experience table")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            conn.rollback()
            raise


def downgrade():
    """Remove responsibilities column from work_experience table"""
    
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        try:
            logger.info("Removing 'responsibilities' column from work_experience table...")
            conn.execute(text("""
                ALTER TABLE work_experience 
                DROP COLUMN responsibilities
            """))
            conn.commit()
            
            logger.info("✅ Successfully removed 'responsibilities' column from work_experience table")
            
        except Exception as e:
            logger.error(f"❌ Downgrade failed: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate work_experience table')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade migration')
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade()
    else:
        upgrade()
