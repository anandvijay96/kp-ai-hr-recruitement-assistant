"""
Check the actual failing user from the screenshot
"""
import asyncio
from services.password_service import PasswordService
from core.database import AsyncSessionLocal
from models.database import User
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_user():
    print("="*60)
    print("🔍 CHECKING REAL USER FROM SCREENSHOT")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # The screenshot shows testuser_235354.5@test.com with password Test@1234
        # But let me check ALL users created recently
        result = await db.execute(
            select(User).order_by(User.created_at.desc()).limit(10)
        )
        users = result.scalars().all()
        
        password_service = PasswordService()
        
        for user in users:
            print(f"\n{'='*60}")
            print(f"📧 Email: {user.email}")
            print(f"   Name: {user.full_name}")
            print(f"   Created: {user.created_at}")
            print(f"   Status: {user.status}")
            print(f"   Active: {user.is_active}")
            print(f"   Verified: {user.email_verified}")
            print(f"   Hash: {user.password_hash[:40]}...")
            
            # Test various common passwords
            test_passwords = ["TestPass@123", "Test@1234", "Pass@12345", "Test@12345"]
            
            for pwd in test_passwords:
                if password_service.verify_password(pwd, user.password_hash):
                    print(f"   ✅ Password: {pwd}")
                    break
            else:
                print(f"   ❌ Password: UNKNOWN (not in common list)")

if __name__ == "__main__":
    asyncio.run(check_user())
