"""
List all users in the database
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.database import User

async def list_users():
    """List all users"""
    
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(User).order_by(User.created_at.desc())
            )
            users = result.scalars().all()
            
            if not users:
                print("❌ No users found in database")
                return
            
            print("=" * 100)
            print("👥 ALL USERS")
            print("=" * 100)
            print(f"\nTotal users: {len(users)}\n")
            
            for i, user in enumerate(users, 1):
                status = "✅ Active" if user.is_active else "❌ Inactive"
                verified = "✅" if user.email_verified else "❌"
                
                print(f"{i}. {user.full_name}")
                print(f"   Email: {user.email}")
                print(f"   Role: {user.role}")
                print(f"   Status: {status}")
                print(f"   Email Verified: {verified}")
                print(f"   Created: {user.created_at}")
                print(f"   ID: {user.id}")
                print()
            
            print("=" * 100)
            print("\n💡 To reset a password:")
            print("   python reset_admin_password.py <email> <new_password>")
            print("\n💡 Example:")
            print("   python reset_admin_password.py kp@admin.com NewPass123!")
            print("=" * 100)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(list_users())
