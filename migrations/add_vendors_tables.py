"""Migration script to add Vendor Management tables"""
import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Run migration to add vendors and candidate_vendors tables"""
    engine = get_engine()
    async with engine.begin() as conn:
        try:
            # Create vendors table
            logger.info("Creating vendors table...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vendors (
                    id VARCHAR(36) PRIMARY KEY,
                    
                    -- Company Information
                    company_name VARCHAR(255) NOT NULL UNIQUE,
                    vendor_type VARCHAR(50) DEFAULT 'agency',
                    industry_specialization VARCHAR(255),
                    website VARCHAR(255),
                    description TEXT,
                    
                    -- Contact Information
                    contact_person VARCHAR(100) NOT NULL,
                    contact_email VARCHAR(255) NOT NULL,
                    contact_phone VARCHAR(20),
                    
                    -- Address
                    address VARCHAR(255),
                    city VARCHAR(100),
                    state VARCHAR(100),
                    country VARCHAR(100),
                    postal_code VARCHAR(20),
                    
                    -- Business Terms
                    status VARCHAR(20) DEFAULT 'active',
                    commission_rate DECIMAL(5, 2),
                    payment_terms VARCHAR(255),
                    contract_start_date DATE,
                    contract_end_date DATE,
                    
                    -- Performance Metrics (computed)
                    total_candidates_referred INTEGER DEFAULT 0,
                    candidates_hired INTEGER DEFAULT 0,
                    success_rate DECIMAL(5, 2) DEFAULT 0,
                    average_rating DECIMAL(3, 2),
                    
                    -- Settings
                    has_portal_access BOOLEAN DEFAULT FALSE,
                    can_submit_candidates BOOLEAN DEFAULT TRUE,
                    requires_approval BOOLEAN DEFAULT TRUE,
                    
                    -- Notes & Tags
                    notes TEXT,
                    tags JSON,
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    updated_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    
                    -- Soft Delete
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at TIMESTAMP,
                    deleted_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    
                    CONSTRAINT chk_vendor_status CHECK (status IN ('active', 'inactive', 'suspended')),
                    CONSTRAINT chk_vendor_type CHECK (vendor_type IN ('agency', 'freelancer', 'consultant', 'other'))
                )
            """))
            logger.info("✓ Vendors table created")
            
            # Create indexes for vendors
            logger.info("Creating indexes for vendors table...")
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_company_name ON vendors(company_name)"))
            logger.info("✓ company_name index created")
            
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_status ON vendors(status)"))
            logger.info("✓ status index created")
            
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_contact_email ON vendors(contact_email)"))
            logger.info("✓ contact_email index created")
            
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_created_at ON vendors(created_at)"))
            logger.info("✓ created_at index created")
            
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_is_deleted ON vendors(is_deleted)"))
            logger.info("✓ is_deleted index created")
            
            # Create candidate_vendors linking table
            logger.info("Creating candidate_vendors table...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS candidate_vendors (
                    id VARCHAR(36) PRIMARY KEY,
                    candidate_id VARCHAR(36) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
                    vendor_id VARCHAR(36) NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
                    
                    -- Referral Details
                    referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    referral_notes TEXT,
                    candidate_status VARCHAR(50) DEFAULT 'referred',
                    
                    -- Financial
                    agreed_rate DECIMAL(10, 2),
                    commission_amount DECIMAL(10, 2),
                    payment_status VARCHAR(50) DEFAULT 'pending',
                    payment_date TIMESTAMP,
                    
                    -- Performance
                    vendor_rating INTEGER,
                    feedback TEXT,
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    
                    CONSTRAINT chk_candidate_status CHECK (candidate_status IN ('referred', 'screened', 'submitted', 'hired', 'rejected')),
                    CONSTRAINT chk_payment_status CHECK (payment_status IN ('pending', 'paid', 'cancelled')),
                    CONSTRAINT chk_vendor_rating CHECK (vendor_rating >= 1 AND vendor_rating <= 5),
                    CONSTRAINT unique_candidate_vendor UNIQUE(candidate_id, vendor_id)
                )
            """))
            logger.info("✓ Candidate_vendors table created")
            
            # Create indexes for candidate_vendors
            logger.info("Creating indexes for candidate_vendors table...")
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidate_vendors_candidate ON candidate_vendors(candidate_id)"))
            logger.info("✓ candidate_id index created")
            
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidate_vendors_vendor ON candidate_vendors(vendor_id)"))
            logger.info("✓ vendor_id index created")
            
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidate_vendors_status ON candidate_vendors(candidate_status)"))
            logger.info("✓ candidate_status index created")
            
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_candidate_vendors_referral_date ON candidate_vendors(referral_date)"))
            logger.info("✓ referral_date index created")
            
            logger.info("✅ Migration completed successfully!")
            logger.info("\nCreated tables:")
            logger.info("  - vendors")
            logger.info("  - candidate_vendors")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
