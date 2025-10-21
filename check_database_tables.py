"""
Check which tables exist in the database
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from core.database import get_engine

async def check_tables():
    """Check which tables exist in the database"""
    
    engine = get_engine()
    
    try:
        async with engine.begin() as conn:
            # Get all tables
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print("=" * 60)
            print("📊 DATABASE TABLES")
            print("=" * 60)
            
            if not tables:
                print("❌ No tables found in database!")
                print("\n💡 Database needs to be initialized:")
                print("   python init_database.py")
                return False
            
            print(f"\n✅ Found {len(tables)} tables:\n")
            
            required_tables = [
                'users',
                'candidates', 
                'resumes',
                'jobs',
                'user_activity_log',
                'interviews'
            ]
            
            for table in tables:
                is_required = table in required_tables
                status = "✅" if is_required else "  "
                print(f"{status} {table}")
            
            print("\n" + "=" * 60)
            print("📋 REQUIRED TABLES CHECK")
            print("=" * 60)
            
            missing_tables = [t for t in required_tables if t not in tables]
            
            if missing_tables:
                print(f"\n❌ Missing {len(missing_tables)} required tables:")
                for table in missing_tables:
                    print(f"  - {table}")
                print("\n💡 Run: python init_database.py")
                return False
            else:
                print("\n✅ All required tables exist!")
                
                # Check candidates table columns
                print("\n" + "=" * 60)
                print("📋 CANDIDATES TABLE COLUMNS")
                print("=" * 60)
                
                result = await conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'candidates'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                print(f"\n✅ Found {len(columns)} columns:\n")
                
                soft_delete_columns = ['is_deleted', 'deleted_at', 'deleted_by', 'deletion_reason']
                has_soft_delete = all(col[0] in [c[0] for c in columns] for col in soft_delete_columns)
                
                for col_name, col_type, nullable in columns:
                    is_soft_delete = col_name in soft_delete_columns
                    status = "🔴" if is_soft_delete else "  "
                    null_str = "NULL" if nullable == 'YES' else "NOT NULL"
                    print(f"{status} {col_name:<30} {col_type:<20} {null_str}")
                
                print("\n" + "=" * 60)
                print("🔴 SOFT DELETE COLUMNS CHECK")
                print("=" * 60)
                
                # Check which soft delete columns are missing
                existing_col_names = [col[0] for col in columns]
                missing_cols = [c for c in soft_delete_columns if c not in existing_col_names]
                
                if len(missing_cols) == 0:
                    print("\n✅ All soft delete columns exist!")
                    print("   - is_deleted")
                    print("   - deleted_at")
                    print("   - deleted_by")
                    print("   - deletion_reason")
                    print("\n🎉 DATABASE IS READY!")
                else:
                    print(f"\n❌ Missing {len(missing_cols)} soft delete columns:")
                    for col in missing_cols:
                        print(f"  - {col}")
                    print("\n💡 Run: python migrations/add_soft_delete_columns_postgres.py")
                    return False
                
                return True
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(check_tables())
    sys.exit(0 if success else 1)
