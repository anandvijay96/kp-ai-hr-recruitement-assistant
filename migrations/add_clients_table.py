"""Migration script to add Client table and update Job table"""
import asyncio
import logging
from sqlalchemy import text
from core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Run migration to add clients table"""
    async with engine.begin() as conn:
        try:
            # Create clients table
            logger.info("Creating clients table...")
            await conn.execute(text("""
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
                    contract_start_date DATE,
                    contract_end_date DATE,
                    contract_value VARCHAR(50),
                    payment_terms VARCHAR(255),
                    notes TEXT,
                    tags JSON,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    updated_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at TIMESTAMP WITH TIME ZONE,
                    deleted_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    
                    CONSTRAINT chk_client_status CHECK (status IN ('active', 'inactive', 'on_hold')),
                    CONSTRAINT chk_client_type CHECK (client_type IN ('direct', 'agency', 'partner')),
                    CONSTRAINT chk_client_priority CHECK (priority IN ('low', 'medium', 'high'))
                )
            """))
            logger.info("✓ Clients table created")
            
            # Create indexes
            logger.info("Creating indexes...")
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_company_name ON clients(company_name)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_contact_email ON clients(contact_email)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_created_at ON clients(created_at)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_is_deleted ON clients(is_deleted)"))
            logger.info("✓ Indexes created")
            
            # Add client_id column to jobs table if it doesn't exist
            logger.info("Updating jobs table...")
            await conn.execute(text("""
                ALTER TABLE jobs
                ADD COLUMN IF NOT EXISTS client_id VARCHAR(36) REFERENCES clients(id) ON DELETE SET NULL,
                ADD COLUMN IF NOT EXISTS show_client_to_candidate BOOLEAN DEFAULT FALSE
            """))
            logger.info("✓ Jobs table updated")
            
            # Create index on jobs.client_id
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_client_id ON jobs(client_id)"))
            logger.info("✓ Job client_id index created")
            
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            raise


def run_migration():
    """Run the migration"""
    asyncio.run(migrate())


if __name__ == "__main__":
    run_migration()
