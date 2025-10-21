"""
Reset admin password - Simple script to reset password for any user
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, update
from core.database import AsyncSessionLocal
from models.database import User
from services.password_service import PasswordService

async def reset_password(email: str, new_password: str):
    """Reset password for a user"""
    
    async with AsyncSessionLocal() as session:
        try:
            # Find user
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User not found: {email}")
                return False
            
            # Hash new password
            password_service = PasswordService()
            new_hash = password_service.hash_password(new_password)
            
            # Update password
            user.password_hash = new_hash
            user.is_active = True
            user.email_verified = True
            
            await session.commit()
            
            print("=" * 60)
            print("✅ PASSWORD RESET SUCCESSFUL!")
            print("=" * 60)
            print(f"\nUser: {user.full_name}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"New Password: {new_password}")
            print("\n⚠️  IMPORTANT: Save this password securely!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reset_admin_password.py <email> <new_password>")
        print("\nExample:")
        print("  python reset_admin_password.py kp@admin.com NewSecurePass123!")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    success = asyncio.run(reset_password(email, new_password))
    sys.exit(0 if success else 1)
