#!/usr/bin/env python3
"""Quick script to check candidates in database"""
import asyncio
from sqlalchemy import select
from core.database import get_db
from models.database import Candidate

async def check_candidates():
    async for db in get_db():
        stmt = select(Candidate)
        result = await db.execute(stmt)
        candidates = result.scalars().all()
        
        print(f"\n=== Total Candidates: {len(candidates)} ===\n")
        
        for i, c in enumerate(candidates, 1):
            print(f"{i}. ID: {c.id}")
            print(f"   Name: {c.full_name}")
            print(f"   Email: {c.email}")
            print(f"   Phone: {c.phone}")
            print(f"   Source: {c.source}")
            print(f"   Status: {c.status}")
            print()

if __name__ == "__main__":
    asyncio.run(check_candidates())
