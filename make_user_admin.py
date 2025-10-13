"""
Make Existing User Admin
Simple script to promote an existing user to admin role
"""
import asyncio
import sys
from sqlalchemy import select, update
from core.database import AsyncSessionLocal
from models.database import User

async def make_user_admin(email: str):
    """Promote existing user to admin role"""
    
    async with AsyncSessionLocal() as session:
        try:
            # Find user by email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User not found: {email}")
                return False
            
            # Update to admin
            user.role = "admin"
            user.status = "active"
            user.is_active = True
            user.email_verified = True
            
            await session.commit()
            
            print("=" * 60)
            print("✅ User promoted to admin successfully!")
            print("=" * 60)
            print(f"\nUser Details:")
            print(f"  Name: {user.full_name}")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            print(f"  Status: {user.status}")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False

async def main():
    """Main function"""
    print("=" * 60)
    print("Make User Admin")
    print("=" * 60)
    
    if len(sys.argv) >= 2:
        email = sys.argv[1]
    else:
        print("\nUsage: python make_user_admin.py <email>")
        print("\nExample:")
        print("  python make_user_admin.py user@company.com")
        print("\nOr enter email interactively:")
        print()
        
        email = input("Enter user email to make admin: ").strip()
    
    if not email:
        print("❌ Email is required!")
        return False
    
    print(f"\nPromoting user to admin: {email}")
    print()
    
    success = await make_user_admin(email)
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
