"""
PostgreSQL Migration Script - Add missing columns
For production deployment with PostgreSQL database
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Get database URL from environment or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://user:password@localhost/dbname')

async def add_column_if_not_exists(session, table_name, column_name, column_type, default_value=None):
    """Add a column to a table if it doesn't exist"""
    try:
        # Check if column exists
        check_sql = f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='{table_name}' AND column_name='{column_name}'
        """
        result = await session.execute(text(check_sql))
        exists = result.fetchone() is not None
        
        if exists:
            print(f"✅ Column {table_name}.{column_name} already exists")
            return True
        
        # Add column
        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        if default_value is not None:
            alter_sql += f" DEFAULT {default_value}"
        
        await session.execute(text(alter_sql))
        await session.commit()
        print(f"✅ Added column: {table_name}.{column_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error adding {table_name}.{column_name}: {e}")
        await session.rollback()
        return False

async def create_table_if_not_exists(session, table_name, create_sql):
    """Create a table if it doesn't exist"""
    try:
        # Check if table exists
        check_sql = f"""
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename='{table_name}'
        """
        result = await session.execute(text(check_sql))
        exists = result.fetchone() is not None
        
        if exists:
            print(f"✅ Table {table_name} already exists")
            return True
        
        # Create table
        await session.execute(text(create_sql))
        await session.commit()
        print(f"✅ Created table: {table_name}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating {table_name}: {e}")
        await session.rollback()
        return False

async def run_migrations():
    """Run all migrations"""
    print("=" * 60)
    print("🔧 PostgreSQL Migration Script")
    print("=" * 60)
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("\n📋 Checking candidates table...")
        
        # Add github_url to candidates table
        await add_column_if_not_exists(
            session, 'candidates', 'github_url', 'VARCHAR(255)', 'NULL'
        )
        
        # Add linkedin_suggestions to candidates table (if not exists)
        await add_column_if_not_exists(
            session, 'candidates', 'linkedin_suggestions', 'TEXT', 'NULL'
        )
        
        print("\n📋 Checking resumes table...")
        
        # Add authenticity_details to resumes table
        await add_column_if_not_exists(
            session, 'resumes', 'authenticity_details', 'JSONB', 'NULL'
        )
        
        # Add jd_match_details to resumes table
        await add_column_if_not_exists(
            session, 'resumes', 'jd_match_details', 'JSONB', 'NULL'
        )
        
        print("\n📋 Checking clients table...")
        
        # Create clients table if it doesn't exist
        clients_create_sql = """
        CREATE TABLE IF NOT EXISTS clients (
            id VARCHAR(36) PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL UNIQUE,
            industry VARCHAR(100),
            website VARCHAR(255),
            description TEXT,
            contact_person VARCHAR(100) NOT NULL,
            contact_email VARCHAR(255) NOT NULL,
            contact_phone VARCHAR(20),
            address VARCHAR(255),
            city VARCHAR(100),
            state VARCHAR(100),
            country VARCHAR(100),
            postal_code VARCHAR(20),
            status VARCHAR(20) DEFAULT 'active',
            client_type VARCHAR(20) DEFAULT 'direct',
            priority VARCHAR(20) DEFAULT 'medium',
            contract_start_date VARCHAR(50),
            contract_end_date VARCHAR(50),
            contract_value VARCHAR(50),
            payment_terms VARCHAR(255),
            notes TEXT,
            tags TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(36),
            updated_by VARCHAR(36),
            is_deleted BOOLEAN DEFAULT false,
            deleted_at TIMESTAMP WITH TIME ZONE,
            deleted_by VARCHAR(36),
            CONSTRAINT chk_client_status CHECK (status IN ('active', 'inactive', 'on_hold')),
            CONSTRAINT chk_client_type CHECK (client_type IN ('direct', 'agency', 'partner')),
            CONSTRAINT chk_client_priority CHECK (priority IN ('low', 'medium', 'high'))
        )
        """
        
        await create_table_if_not_exists(session, 'clients', clients_create_sql)
        
        # Add missing columns to clients table if it exists
        clients_columns = [
            ('website', 'VARCHAR(255)', 'NULL'),
            ('description', 'TEXT', 'NULL'),
            ('industry', 'VARCHAR(100)', 'NULL'),
            ('contact_person', 'VARCHAR(100)', 'NULL'),
            ('contact_email', 'VARCHAR(255)', 'NULL'),
            ('contact_phone', 'VARCHAR(20)', 'NULL'),
            ('contract_value', 'VARCHAR(50)', 'NULL'),
            ('payment_terms', 'VARCHAR(255)', 'NULL'),
            ('tags', 'TEXT', 'NULL'),
            ('client_type', 'VARCHAR(20)', "'direct'"),
            ('priority', 'VARCHAR(20)', "'medium'"),
        ]
        
        for col_name, col_type, default in clients_columns:
            await add_column_if_not_exists(session, 'clients', col_name, col_type, default)
    
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print("✅ Migration completed!")
    print("=" * 60)

if __name__ == "__main__":
    print("\n⚠️  Make sure to set DATABASE_URL environment variable!")
    print("Example: export DATABASE_URL='postgresql+asyncpg://user:pass@host/db'\n")
    
    asyncio.run(run_migrations())
