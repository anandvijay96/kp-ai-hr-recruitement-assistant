#!/usr/bin/env python3
"""Quick test to check if /api/candidates returns total_experience_months"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, '.')

from services.candidate_service import CandidateService

async def test():
    engine = create_async_engine("sqlite+aiosqlite:///hr_recruitment.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        service = CandidateService(db)
        result = await service.search_candidates(page=1, limit=3)
        
        print("\n" + "="*60)
        print("Testing /api/candidates response")
        print("="*60)
        
        for candidate in result['candidates']:
            print(f"\nCandidate: {candidate['full_name']}")
            print(f"  total_experience_months: {candidate.get('total_experience_months', 'NOT FOUND!')}")
            print(f"  All fields: {list(candidate.keys())}")
        
        print("\n" + "="*60)
        print(f"✅ Test complete - checked {len(result['candidates'])} candidates")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(test())
