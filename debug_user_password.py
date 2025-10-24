"""
Debug user password issue - check database state and verify password
"""
import asyncio
from services.password_service import PasswordService
from core.database import AsyncSessionLocal
from models.database import User
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_user():
    print("="*60)
    print("🔍 DEBUGGING USER PASSWORD ISSUE")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Find the test user
        result = await db.execute(
            select(User).where(User.email == "testuser_235354.5@test.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("\n❌ Test user not found in database")
            print("Let's check all recent users:")
            result = await db.execute(
                select(User).order_by(User.created_at.desc()).limit(5)
            )
            users = result.scalars().all()
            for u in users:
                print(f"\n📧 {u.email}")
                print(f"   Name: {u.full_name}")
                print(f"   Status: {u.status}")
                print(f"   Active: {u.is_active}")
                print(f"   Email Verified: {u.email_verified}")
                print(f"   Hash starts: {u.password_hash[:30]}...")
                print(f"   Hash length: {len(u.password_hash)}")
            return
        
        print(f"\n✅ Found user: {user.email}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Status: {user.status}")
        print(f"   Active: {user.is_active}")
        print(f"   Email Verified: {user.email_verified}")
        print(f"   Password Hash: {user.password_hash[:50]}...")
        print(f"   Hash Length: {len(user.password_hash)}")
        print(f"   Is bcrypt: {user.password_hash.startswith('$2b$')}")
        
        # Test password verification
        password_service = PasswordService()
        test_password = "TestPass@123"
        
        print(f"\n🔐 Testing password verification...")
        print(f"   Password: {test_password}")
        
        is_valid = password_service.verify_password(test_password, user.password_hash)
        print(f"   Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
        
        if not is_valid:
            print(f"\n❌ PASSWORD VERIFICATION FAILED!")
            print(f"   This explains why login is failing")
            
            # Try to figure out what password was actually used
            print(f"\n🔍 Testing common passwords...")
            test_passwords = [
                "TestPass@123",
                "Test@1234", 
                "Pass@12345",
                "password",
                "admin123"
            ]
            
            for pwd in test_passwords:
                if password_service.verify_password(pwd, user.password_hash):
                    print(f"   ✅ FOUND IT! Password is: {pwd}")
                    break
            else:
                print(f"   ❌ None of the test passwords matched")
                print(f"   The password hash might be corrupted or from a different password")

if __name__ == "__main__":
    asyncio.run(debug_user())
