#!/usr/bin/env python3
"""
Migration script to add authenticity_score and jd_match_score columns to resumes table
"""
import asyncio
from sqlalchemy import text
from core.database import get_engine

async def migrate():
    """Add score columns to resumes table"""
    engine = get_engine()
    
    async with engine.begin() as conn:
        try:
            # Check if columns exist
            result = await conn.execute(text("PRAGMA table_info(resumes)"))
            columns = [row[1] for row in result.fetchall()]
            
            # Add authenticity_score if not exists
            if 'authenticity_score' not in columns:
                print("Adding authenticity_score column...")
                await conn.execute(text(
                    "ALTER TABLE resumes ADD COLUMN authenticity_score INTEGER"
                ))
                print("✅ Added authenticity_score column")
            else:
                print("✅ authenticity_score column already exists")
            
            # Add jd_match_score if not exists
            if 'jd_match_score' not in columns:
                print("Adding jd_match_score column...")
                await conn.execute(text(
                    "ALTER TABLE resumes ADD COLUMN jd_match_score INTEGER"
                ))
                print("✅ Added jd_match_score column")
            else:
                print("✅ jd_match_score column already exists")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    print("Starting migration...")
    asyncio.run(migrate())
