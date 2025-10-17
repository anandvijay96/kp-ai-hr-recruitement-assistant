"""Test activity API directly"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import AsyncSessionLocal
from services.activity_tracker import ActivityTracker
from datetime import date

async def test_api():
    async with AsyncSessionLocal() as session:
        tracker = ActivityTracker(session)
        
        # Test get_user_activity_summary
        print("Testing get_user_activity_summary...")
        try:
            summary = await tracker.get_user_activity_summary(
                user_id="2149a8a0-22f1-412d-9ee0-2994366069e9",
                days=1
            )
            print(f"Summary: {summary}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())
