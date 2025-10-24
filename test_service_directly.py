"""
Test the service layer directly with the exact UserCreateRequest format
"""
import asyncio
from services.user_management_service import UserManagementService
from services.password_service import PasswordService
from core.database import AsyncSessionLocal
from models.database import User
from models.user_management_schemas import UserCreateRequest, UserRole, UserStatus
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)

async def test_service():
    print("="*60)
    print("🧪 TESTING SERVICE LAYER DIRECTLY")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Get admin user
        admin_result = await db.execute(
            select(User).where(User.role == "admin").limit(1)
        )
        admin = admin_result.scalar_one()
        
        print(f"\n1️⃣ Creating user via UserManagementService...")
        print(f"   Admin: {admin.email}")
        
        # Create user data - EXACTLY as the API would
        test_email = f"servicetest_{asyncio.get_event_loop().time()}@test.com"
        test_password = "ServiceTest@123"
        
        print(f"   Test Email: {test_email}")
        print(f"   Test Password: {test_password}")
        
        user_data = UserCreateRequest(
            full_name="Service Test User",
            email=test_email,
            mobile="+1234567890",
            role=UserRole.RECRUITER,
            department="Engineering",
            status=UserStatus.ACTIVE,
            password=test_password  # CRITICAL: This should be used!
        )
        
        print(f"\n   UserCreateRequest fields:")
        print(f"   - password: {user_data.password}")
        print(f"   - password_option: {user_data.password_option}")
        
        service = UserManagementService(db)
        
        try:
            result = await service.create_user(
                user_data=user_data,
                created_by=admin,
                ip_address="127.0.0.1",
                user_agent="Test"
            )
            
            print(f"\n✅ User created!")
            print(f"   ID: {result['id']}")
            print(f"   Email: {result['email']}")
            print(f"   Temporary Password: {result.get('temporary_password')}")
            
            # Verify in database
            print(f"\n2️⃣ Verifying in database...")
            user_result = await db.execute(
                select(User).where(User.id == result['id'])
            )
            user = user_result.scalar_one()
            
            print(f"   Hash: {user.password_hash[:40]}...")
            
            # Test password
            password_service = PasswordService()
            is_valid = password_service.verify_password(test_password, user.password_hash)
            
            print(f"\n3️⃣ Password Verification:")
            print(f"   Password: {test_password}")
            print(f"   Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
            
            if is_valid:
                print(f"\n🎉 SUCCESS! The fix is working at the service layer!")
                return True
            else:
                print(f"\n❌ FAILED! The password is not matching!")
                # Try the temporary password that was returned
                if result.get('temporary_password'):
                    is_temp_valid = password_service.verify_password(result['temporary_password'], user.password_hash)
                    print(f"   Temp password valid: {is_temp_valid}")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    result = asyncio.run(test_service())
    print("\n" + "="*60)
    if result:
        print("✅ SERVICE LAYER FIX IS WORKING!")
    else:
        print("❌ SERVICE LAYER FIX IS NOT WORKING!")
    print("="*60)
