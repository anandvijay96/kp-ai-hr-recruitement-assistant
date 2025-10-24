"""
Test password creation and verification
"""
import asyncio
from services.password_service import PasswordService
from services.user_management_service import UserManagementService
from core.database import get_db, AsyncSessionLocal
from models.database import User
from models.user_management_schemas import UserCreateRequest, PasswordOption, UserRole, UserStatus
from sqlalchemy import select

async def test_password_creation():
    print("="*60)
    print("🔍 TESTING PASSWORD CREATION BUG")
    print("="*60)
    
    # Test 1: Direct password hashing
    print("\n1️⃣ Testing direct password hashing...")
    password_service = PasswordService()
    test_password = "Pass@12345"
    
    print(f"   Original password: {test_password}")
    hashed = password_service.hash_password(test_password)
    print(f"   Hashed: {hashed[:50]}...")
    
    # Verify it
    is_valid = password_service.verify_password(test_password, hashed)
    print(f"   Verification: {'✅ PASS' if is_valid else '❌ FAIL'}")
    
    # Test 2: Check a real user in database
    print("\n2️⃣ Checking last created user in database...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).order_by(User.created_at.desc()).limit(1)
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"   User: {user.full_name} ({user.email})")
            print(f"   Password hash starts with: {user.password_hash[:20]}...")
            print(f"   Password hash length: {len(user.password_hash)}")
            print(f"   Is bcrypt hash: {user.password_hash.startswith('$2b$')}")
            
            # Try to verify with common test passwords
            print("\n   Testing common passwords:")
            test_passwords = [
                "Pass@12345",
                "password",
                "admin123",
                "Admin@123",
                "Test@1234"
            ]
            
            for pwd in test_passwords:
                is_valid = password_service.verify_password(pwd, user.password_hash)
                if is_valid:
                    print(f"   ✅ Password is: {pwd}")
                    break
            else:
                print(f"   ❌ None of the common passwords matched")
        else:
            print("   No users found in database")
    
    print("\n" + "="*60)
    print("Test complete")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_password_creation())
