#!/usr/bin/env python3
"""
Database initialization script for AI HR Assistant

This script initializes the database and creates all tables.
Run this before starting the application for the first time.

Usage:
    python init_db.py
"""

import sys
import logging
from core.database import init_db, engine
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database"""
    try:
        logger.info("=" * 60)
        logger.info("AI HR Assistant - Database Initialization")
        logger.info("=" * 60)
        logger.info(f"Database URL: {settings.database_url}")
        logger.info("")
        
        # Create all tables
        logger.info("Creating database tables...")
        init_db()
        
        logger.info("✅ Database initialized successfully!")
        logger.info("")
        logger.info("Tables created:")
        logger.info("  - candidates")
        logger.info("  - resumes")
        logger.info("  - education")
        logger.info("  - work_experience")
        logger.info("  - skills")
        logger.info("  - candidate_skills")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Start Redis: redis-server")
        logger.info("  2. Start Celery: celery -A core.celery_app worker --loglevel=info")
        logger.info("  3. Start API: uvicorn main:app --reload")
        logger.info("")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
