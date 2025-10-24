"""Migration script to add Client table and update Job table"""
import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
            try:
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_company_name ON clients(company_name)"))
                logger.info("✓ company_name index created")
            except Exception as e:
                logger.warning(f"⚠ company_name index: {str(e)}")
            
            try:
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status)"))
                logger.info("✓ status index created")
            except Exception as e:
                logger.warning(f"⚠ status index: {str(e)}")
            
            try:
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_created_at ON clients(created_at)"))
                logger.info("✓ created_at index created")
            except Exception as e:
                logger.warning(f"⚠ created_at index: {str(e)}")
            
            try:
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_clients_is_deleted ON clients(is_deleted)"))
                logger.info("✓ is_deleted index created")
            except Exception as e:
                logger.warning(f"⚠ is_deleted index: {str(e)}")
            
            # Add client_id column to jobs table if it doesn't exist
            logger.info("Updating jobs table...")
            try:
                await conn.execute(text("""
                    ALTER TABLE jobs
                    ADD COLUMN client_id VARCHAR(36) REFERENCES clients(id) ON DELETE SET NULL
                """))
                logger.info("✓ client_id column added to jobs table")
            except Exception as e:
                logger.warning(f"⚠ client_id column: {str(e)}")
            
            try:
                await conn.execute(text("""
                    ALTER TABLE jobs
                    ADD COLUMN show_client_to_candidate BOOLEAN DEFAULT FALSE
                """))
                logger.info("✓ show_client_to_candidate column added to jobs table")
            except Exception as e:
                logger.warning(f"⚠ show_client_to_candidate column: {str(e)}")
            
            # Create index on jobs.client_id
            try:
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_client_id ON jobs(client_id)"))
                logger.info("✓ Job client_id index created")
            except Exception as e:
                logger.warning(f"⚠ Job client_id index: {str(e)}")
            
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            raise


def run_migration():
    """Run the migration"""
    asyncio.run(migrate())


if __name__ == "__main__":
    run_migration()
