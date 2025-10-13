"""
Create Admin User for Production
Run this script to create an admin user in the production database
"""
import asyncio
import sys
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.database import User
from services.password_service import PasswordService
import uuid
from datetime import datetime

async def create_admin_user(email: str, password: str, full_name: str = "Admin User"):
    """Create an admin user in the database"""
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # Update existing user to admin
                print(f"✓ User {email} already exists. Updating to admin role...")
                existing_user.role = "admin"
                existing_user.status = "active"
                existing_user.is_active = True
                existing_user.email_verified = True
                
                # Update password if provided
                if password:
                    password_service = PasswordService()
                    existing_user.password_hash = password_service.hash_password(password)
                    existing_user.password_changed_at = datetime.utcnow()
                
                await session.commit()
                
                print("=" * 60)
                print("✅ User updated to admin successfully!")
                print("=" * 60)
                print(f"\nLogin Credentials:")
                print(f"  Email: {email}")
                if password:
                    print(f"  Password: {password}")
                print(f"  Role: admin")
                print("=" * 60)
                return True
            
            # Create new admin user
            print(f"Creating new admin user: {email}")
            
            password_service = PasswordService()
            password_hash = password_service.hash_password(password)
            
            new_user = User(
                id=str(uuid.uuid4()),
                full_name=full_name,
                email=email,
                mobile="0000000000",  # Placeholder
                password_hash=password_hash,
                role="admin",
                status="active",
                is_active=True,
                email_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                password_changed_at=datetime.utcnow()
            )
            
            session.add(new_user)
            await session.commit()
            
            print("=" * 60)
            print("✅ Admin user created successfully!")
            print("=" * 60)
            print(f"\nLogin Credentials:")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            print(f"  Role: admin")
            print("\n⚠️  IMPORTANT: Change this password after first login!")
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
    print("Create Admin User for Production")
    print("=" * 60)
    
    # Get user input
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
        full_name = sys.argv[3] if len(sys.argv) > 3 else "Admin User"
    else:
        print("\nUsage: python create_production_admin.py <email> <password> [full_name]")
        print("\nExample:")
        print("  python create_production_admin.py admin@company.com SecurePass123! \"John Doe\"")
        print("\nOr enter details interactively:")
        print()
        
        email = input("Enter admin email: ").strip()
        password = input("Enter admin password: ").strip()
        full_name = input("Enter full name (default: Admin User): ").strip() or "Admin User"
    
    if not email or not password:
        print("❌ Email and password are required!")
        return False
    
    print(f"\nCreating admin user:")
    print(f"  Email: {email}")
    print(f"  Name: {full_name}")
    print()
    
    success = await create_admin_user(email, password, full_name)
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
