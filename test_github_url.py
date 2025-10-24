#!/usr/bin/env python3
"""Test if GitHub URL is being saved correctly"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

sys.path.insert(0, '.')

from models.database import Candidate

async def test():
    engine = create_async_engine("sqlite+aiosqlite:///hr_recruitment.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get first candidate
        result = await db.execute(select(Candidate).limit(1))
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            print("❌ No candidates found in database")
            return
        
        print("\n" + "="*60)
        print(f"Testing GitHub URL for candidate: {candidate.full_name}")
        print("="*60)
        print(f"ID: {candidate.id}")
        print(f"GitHub URL: {candidate.github_url if hasattr(candidate, 'github_url') else 'COLUMN NOT FOUND!'}")
        print(f"LinkedIn URL: {candidate.linkedin_url}")
        print("="*60)
        
        # Check if column exists
        if not hasattr(candidate, 'github_url'):
            print("\n❌ ERROR: github_url column doesn't exist!")
            print("Run: python migrate_add_github_and_details.py")
        elif candidate.github_url:
            print(f"\n✅ GitHub URL exists: {candidate.github_url}")
        else:
            print("\n⚠️  GitHub URL is NULL/empty")
            print("Try editing this candidate and adding a GitHub URL")

if __name__ == "__main__":
    asyncio.run(test())
