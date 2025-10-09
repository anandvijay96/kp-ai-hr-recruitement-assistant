#!/usr/bin/env python3
"""
Initialize database tables for HR Recruitment System
Run this once to create all necessary tables
"""
import asyncio
import logging
from core.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Initialize database tables"""
    try:
        logger.info("Starting database initialization...")
        await init_db()
        logger.info("✅ Database tables created successfully!")
        logger.info("You can now start the server and upload resumes.")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
