"""
Add Client Management Tables

This migration creates the following tables:
- clients: Client company information
- client_contacts: Contact persons for clients
- client_jobs: Jobs posted by clients
- client_activities: Track client interactions

Run this migration with:
python migrations/add_client_management_tables.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import get_engine


async def run_migration():
    """Run the migration"""
    print("🔄 Starting Client Management tables migration...")
    
    engine = get_engine()
    async with engine.begin() as conn:
        # Create clients table
        print("📝 Creating clients table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clients (
                id VARCHAR(36) PRIMARY KEY,
                company_name VARCHAR(200) NOT NULL,
                company_email VARCHAR(255) UNIQUE NOT NULL,
                company_phone VARCHAR(20),
                company_website VARCHAR(255),
                
                -- Address
                address_line1 VARCHAR(255),
                address_line2 VARCHAR(255),
                city VARCHAR(100),
                state VARCHAR(100),
                country VARCHAR(100),
                postal_code VARCHAR(20),
                
                -- Business details
                industry VARCHAR(100),
                company_size VARCHAR(50),
                tax_id VARCHAR(50),
                
                -- Status
                status VARCHAR(50) DEFAULT 'active' NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                
                -- Contract details
                contract_start_date TIMESTAMP WITH TIME ZONE,
                contract_end_date TIMESTAMP WITH TIME ZONE,
                contract_type VARCHAR(50),
                billing_cycle VARCHAR(50),
                
                -- Notes
                notes TEXT,
                
                -- Metadata
                created_by VARCHAR(36) REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deactivated_at TIMESTAMP WITH TIME ZONE,
                deactivated_by VARCHAR(36) REFERENCES users(id),
                
                CONSTRAINT chk_client_status CHECK (status IN ('active', 'inactive', 'suspended', 'pending')),
                CONSTRAINT chk_company_size CHECK (company_size IN ('1-10', '11-50', '51-200', '201-500', '501-1000', '1000+'))
            );
        """))
        
        # Create indexes for clients
        print("📝 Creating indexes for clients table...")
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_company_name ON clients(company_name);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_company_email ON clients(company_email);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_is_active ON clients(is_active);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_created_at ON clients(created_at);"))
        
        # Create client_contacts table
        print("📝 Creating client_contacts table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS client_contacts (
                id VARCHAR(36) PRIMARY KEY,
                client_id VARCHAR(36) NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                
                -- Contact details
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                mobile VARCHAR(20),
                designation VARCHAR(100),
                department VARCHAR(100),
                
                -- Status
                is_primary BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                
                -- Portal access
                has_portal_access BOOLEAN DEFAULT FALSE,
                portal_user_id VARCHAR(36) REFERENCES users(id),
                
                -- Notes
                notes TEXT,
                
                -- Metadata
                created_by VARCHAR(36) REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create indexes for client_contacts
        print("📝 Creating indexes for client_contacts table...")
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_contacts_client_id ON client_contacts(client_id);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_contacts_email ON client_contacts(email);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_contacts_is_active ON client_contacts(is_active);"))
        
        # Create client_jobs table
        print("📝 Creating client_jobs table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS client_jobs (
                id VARCHAR(36) PRIMARY KEY,
                client_id VARCHAR(36) NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                job_id VARCHAR(36) REFERENCES jobs(id) ON DELETE CASCADE,
                
                -- Job details
                job_title VARCHAR(200),
                job_description TEXT,
                requirements TEXT,
                location VARCHAR(200),
                job_type VARCHAR(50),
                experience_required VARCHAR(50),
                salary_range VARCHAR(100),
                
                -- Status
                status VARCHAR(50) DEFAULT 'open' NOT NULL,
                priority VARCHAR(50) DEFAULT 'medium',
                
                -- Counts
                positions_count INTEGER DEFAULT 1,
                applications_count INTEGER DEFAULT 0,
                shortlisted_count INTEGER DEFAULT 0,
                hired_count INTEGER DEFAULT 0,
                
                -- Dates
                posted_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                deadline TIMESTAMP WITH TIME ZONE,
                filled_date TIMESTAMP WITH TIME ZONE,
                
                -- Metadata
                created_by VARCHAR(36) REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT chk_client_job_status CHECK (status IN ('open', 'closed', 'on_hold', 'filled', 'cancelled')),
                CONSTRAINT chk_job_priority CHECK (priority IN ('low', 'medium', 'high', 'urgent'))
            );
        """))
        
        # Create indexes for client_jobs
        print("📝 Creating indexes for client_jobs table...")
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_jobs_client_id ON client_jobs(client_id);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_jobs_job_id ON client_jobs(job_id);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_jobs_status ON client_jobs(status);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_jobs_created_at ON client_jobs(created_at);"))
        
        # Create client_activities table
        print("📝 Creating client_activities table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS client_activities (
                id VARCHAR(36) PRIMARY KEY,
                client_id VARCHAR(36) NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                
                -- Activity details
                activity_type VARCHAR(50) NOT NULL,
                activity_title VARCHAR(200),
                activity_description TEXT,
                
                -- Participants
                performed_by VARCHAR(36) REFERENCES users(id),
                contact_id VARCHAR(36) REFERENCES client_contacts(id),
                
                -- Status
                status VARCHAR(50) DEFAULT 'completed',
                
                -- Dates
                activity_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                scheduled_date TIMESTAMP WITH TIME ZONE,
                completed_date TIMESTAMP WITH TIME ZONE,
                
                -- Metadata
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT chk_activity_type CHECK (activity_type IN ('meeting', 'call', 'email', 'job_posted', 'contract_signed', 'payment_received', 'other')),
                CONSTRAINT chk_activity_status CHECK (status IN ('scheduled', 'completed', 'cancelled', 'rescheduled'))
            );
        """))
        
        # Create indexes for client_activities
        print("📝 Creating indexes for client_activities table...")
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_activities_client_id ON client_activities(client_id);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_activities_activity_type ON client_activities(activity_type);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_client_activities_created_at ON client_activities(created_at);"))
        
        print("✅ Client Management tables created successfully!")
        print("\nCreated tables:")
        print("  - clients")
        print("  - client_contacts")
        print("  - client_jobs")
        print("  - client_activities")


async def rollback_migration():
    """Rollback the migration"""
    print("🔄 Rolling back Client Management tables migration...")
    
    engine = get_engine()
    async with engine.begin() as conn:
        print("📝 Dropping client_activities table...")
        await conn.execute(text("DROP TABLE IF EXISTS client_activities CASCADE;"))
        
        print("📝 Dropping client_jobs table...")
        await conn.execute(text("DROP TABLE IF EXISTS client_jobs CASCADE;"))
        
        print("📝 Dropping client_contacts table...")
        await conn.execute(text("DROP TABLE IF EXISTS client_contacts CASCADE;"))
        
        print("📝 Dropping clients table...")
        await conn.execute(text("DROP TABLE IF EXISTS clients CASCADE;"))
        
        print("✅ Client Management tables dropped successfully!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback_migration())
    else:
        asyncio.run(run_migration())
