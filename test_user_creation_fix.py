"""
Test user creation with manual password
"""
import asyncio
from services.password_service import PasswordService
from services.user_management_service import UserManagementService
from core.database import AsyncSessionLocal
from models.database import User
from models.user_management_schemas import UserCreateRequest, PasswordOption, UserRole, UserStatus
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_user_creation_with_password():
    print("="*60)
    print("🧪 TESTING USER CREATION WITH MANUAL PASSWORD")
    print("="*60)
    
    # Test password
    test_password = "TestPass@123"
    test_email = f"testuser_{asyncio.get_event_loop().time()}@test.com"
    
    print(f"\n📝 Creating user with:")
    print(f"   Email: {test_email}")
    print(f"   Password: {test_password}")
    
    async with AsyncSessionLocal() as db:
        # Get admin user to act as creator
        result = await db.execute(
            select(User).where(User.role == "admin").limit(1)
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            print("❌ No admin user found. Please create an admin first.")
            return False
        
        print(f"   Created by: {admin_user.full_name} ({admin_user.email})")
        
        # Create user
        service = UserManagementService(db)
        user_data = UserCreateRequest(
            full_name="Test User For Password Fix",
            email=test_email,
            mobile="+1234567890",
            role=UserRole.RECRUITER,
            department="Engineering",
            status=UserStatus.ACTIVE,
            password=test_password  # <--- This is the key field!
        )
        
        try:
            result = await service.create_user(
                user_data=user_data,
                created_by=admin_user,
                ip_address="127.0.0.1",
                user_agent="Test Script"
            )
            
            print(f"\n✅ User created!")
            print(f"   User ID: {result['id']}")
            print(f"   Email: {result['email']}")
            print(f"   Temporary Password Returned: {result['temporary_password']}")
            
            # Verify the password was hashed correctly
            new_user_result = await db.execute(
                select(User).where(User.id == result['id'])
            )
            new_user = new_user_result.scalar_one()
            
            print(f"\n🔍 Verifying password...")
            print(f"   Password hash: {new_user.password_hash[:30]}...")
            print(f"   Is bcrypt hash: {new_user.password_hash.startswith('$2b$')}")
            
            # Test password verification
            password_service = PasswordService()
            is_valid = password_service.verify_password(test_password, new_user.password_hash)
            
            if is_valid:
                print(f"   ✅ Password verification: PASS")
                print(f"\n🎉 SUCCESS! User can now login with the password: {test_password}")
                return True
            else:
                print(f"   ❌ Password verification: FAIL")
                print(f"   ⚠️  The password was NOT hashed correctly!")
                return False
                
        except Exception as e:
            print(f"\n❌ Error creating user: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    result = asyncio.run(test_user_creation_with_password())
    print("\n" + "="*60)
    if result:
        print("✅ TEST PASSED - User creation fix is working!")
    else:
        print("❌ TEST FAILED - User creation fix needs more work")
    print("="*60)
    
    import sys
    sys.exit(0 if result else 1)
