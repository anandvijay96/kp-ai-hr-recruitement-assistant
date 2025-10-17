"""
Script to add test LinkedIn suggestions to a candidate
This is for testing the LinkedIn selection feature
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, select
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_linkedin_suggestions(candidate_email: str, suggestions: list):
    """Add LinkedIn suggestions to a candidate for testing"""
    
    engine = create_async_engine(settings.database_url)
    
    async with engine.begin() as conn:
        try:
            # Check if candidate exists
            result = await conn.execute(
                text("SELECT id, full_name, linkedin_url FROM candidates WHERE email = :email"),
                {"email": candidate_email}
            )
            candidate = result.fetchone()
            
            if not candidate:
                logger.error(f"❌ Candidate with email '{candidate_email}' not found")
                return
            
            candidate_id, name, current_linkedin = candidate
            logger.info(f"Found candidate: {name} (ID: {candidate_id})")
            logger.info(f"Current LinkedIn URL: {current_linkedin or 'None'}")
            
            # Convert suggestions list to JSON string
            import json
            suggestions_json = json.dumps(suggestions)
            
            # Update candidate with LinkedIn suggestions
            await conn.execute(
                text("""
                    UPDATE candidates 
                    SET linkedin_suggestions = :suggestions
                    WHERE id = :id
                """),
                {"suggestions": suggestions_json, "id": candidate_id}
            )
            
            logger.info(f"✅ Added {len(suggestions)} LinkedIn suggestions to {name}")
            logger.info(f"Suggestions: {suggestions}")
            logger.info(f"\nNow visit: http://localhost:8000/candidates/{candidate_id}")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            raise
    
    await engine.dispose()


if __name__ == "__main__":
    # Example usage
    candidate_email = "lahariofficial799@gmail.com"
    
    # Test LinkedIn suggestions
    test_suggestions = [
        "https://www.linkedin.com/in/lahari-bayyakkagari-123456",
        "https://www.linkedin.com/in/bayyakkagari-lahari-789012",
        "https://www.linkedin.com/in/lahari-b-345678"
    ]
    
    print("=" * 60)
    print("Adding Test LinkedIn Suggestions")
    print("=" * 60)
    print(f"Candidate Email: {candidate_email}")
    print(f"Suggestions to add: {len(test_suggestions)}")
    print("=" * 60)
    
    asyncio.run(add_linkedin_suggestions(candidate_email, test_suggestions))
