"""Script to set a user as admin"""
import asyncio
import sys
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, '.')

from models.database import User
from core.config import settings


async def set_user_as_admin(email: str):
    """Set a user as admin by email"""
    
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=True)
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Find user by email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User with email '{email}' not found!")
                print("\nAvailable users:")
                all_users = await session.execute(select(User))
                for u in all_users.scalars().all():
                    print(f"  - {u.email} (role: {u.role})")
                return False
            
            # Update user role to admin
            old_role = user.role
            user.role = "admin"
            
            await session.commit()
            
            print(f"✅ Successfully updated user!")
            print(f"   Email: {user.email}")
            print(f"   Name: {user.full_name}")
            print(f"   Old Role: {old_role}")
            print(f"   New Role: {user.role}")
            
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {str(e)}")
            return False
        finally:
            await engine.dispose()


async def main():
    """Main function"""
    email = "Kartik@kloudportal.com"
    
    print("=" * 60)
    print("Setting User as Admin")
    print("=" * 60)
    print(f"Target Email: {email}")
    print()
    
    success = await set_user_as_admin(email)
    
    if success:
        print("\n✅ User is now an admin and can create jobs!")
    else:
        print("\n❌ Failed to set user as admin")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
