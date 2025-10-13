"""
Migration 012: Add Vendor Management Tables
Feature 12: Vendor Management

This migration creates all tables required for vendor management including:
- vendors
- vendor_contracts
- vendor_performance_reviews
- vendor_compliance_documents
- vendor_communications
- vendor_notifications
- vendor_job_assignments
- vendor_analytics
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./hr_recruitment.db")


async def run_migration():
    """Run the vendor management migration"""
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            logger.info("Starting migration 012: Vendor Management Tables")
            
            # ================================================================
            # VENDORS TABLE
            # ================================================================
            
            logger.info("Creating vendors table...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS vendors (
                    id VARCHAR(36) PRIMARY KEY,
                    vendor_code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    service_category VARCHAR(100) NOT NULL,
                    contact_person VARCHAR(255),
                    contact_email VARCHAR(255) NOT NULL,
                    contact_phone VARCHAR(50),
                    alternate_contact VARCHAR(255),
                    website VARCHAR(255),
                    address TEXT,
                    city VARCHAR(100),
                    state VARCHAR(100),
                    country VARCHAR(100),
                    postal_code VARCHAR(20),
                    tax_id VARCHAR(100),
                    logo_url VARCHAR(500),
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    overall_rating VARCHAR(10),
                    total_contracts INTEGER DEFAULT 0,
                    active_contracts INTEGER DEFAULT 0,
                    vendor_manager_id VARCHAR(36),
                    created_by VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deactivated_at TIMESTAMP,
                    deactivation_reason TEXT,
                    last_evaluation_date DATE,
                    compliance_status VARCHAR(50) DEFAULT 'pending',
                    
                    FOREIGN KEY (vendor_manager_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                    CHECK (status IN ('active', 'inactive', 'on-hold', 'blacklisted')),
                    CHECK (compliance_status IN ('pending', 'compliant', 'non_compliant', 'under_review'))
                )
            """))
            
            # Create indexes for vendors
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_status ON vendors(status)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_service_category ON vendors(service_category)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_vendor_manager ON vendors(vendor_manager_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_name ON vendors(name)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_contact_email ON vendors(contact_email)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_vendor_code ON vendors(vendor_code)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendors_compliance_status ON vendors(compliance_status)"))
            
            # ================================================================
            # VENDOR CONTRACTS TABLE
            # ================================================================
            
            logger.info("Creating vendor_contracts table...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS vendor_contracts (
                    id VARCHAR(36) PRIMARY KEY,
                    vendor_id VARCHAR(36) NOT NULL,
                    contract_number VARCHAR(100) UNIQUE NOT NULL,
                    contract_type VARCHAR(100) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    contract_value VARCHAR(20),
                    currency VARCHAR(10) DEFAULT 'USD',
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    payment_terms TEXT,
                    renewal_terms TEXT,
                    file_url VARCHAR(500) NOT NULL,
                    file_name VARCHAR(255),
                    file_size INTEGER,
                    version INTEGER DEFAULT 1,
                    status VARCHAR(50) NOT NULL DEFAULT 'draft',
                    approval_status VARCHAR(50) DEFAULT 'pending',
                    approved_by VARCHAR(36),
                    approved_at TIMESTAMP,
                    termination_date DATE,
                    termination_reason TEXT,
                    auto_renew BOOLEAN DEFAULT 0,
                    renewal_notice_days INTEGER DEFAULT 90,
                    created_by VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    parent_contract_id VARCHAR(36),
                    
                    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
                    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (parent_contract_id) REFERENCES vendor_contracts(id) ON DELETE SET NULL,
                    CHECK (status IN ('draft', 'pending_approval', 'approved', 'active', 'expired', 'terminated')),
                    CHECK (approval_status IN ('pending', 'approved', 'rejected'))
                )
            """))
            
            # Create indexes for vendor_contracts
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_contracts_vendor ON vendor_contracts(vendor_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_contracts_status ON vendor_contracts(status)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_contracts_contract_number ON vendor_contracts(contract_number)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_contracts_start_date ON vendor_contracts(start_date)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_contracts_end_date ON vendor_contracts(end_date)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_contracts_approval_status ON vendor_contracts(approval_status)"))
            
            # ================================================================
            # VENDOR PERFORMANCE REVIEWS TABLE
            # ================================================================
            
            logger.info("Creating vendor_performance_reviews table...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS vendor_performance_reviews (
                    id VARCHAR(36) PRIMARY KEY,
                    vendor_id VARCHAR(36) NOT NULL,
                    review_period VARCHAR(50) NOT NULL,
                    review_date DATE NOT NULL,
                    review_type VARCHAR(50) NOT NULL,
                    service_quality_rating INTEGER NOT NULL,
                    timeliness_rating INTEGER NOT NULL,
                    communication_rating INTEGER NOT NULL,
                    cost_effectiveness_rating INTEGER NOT NULL,
                    compliance_rating INTEGER NOT NULL,
                    overall_rating VARCHAR(10) NOT NULL,
                    strengths TEXT,
                    areas_for_improvement TEXT,
                    recommendations TEXT,
                    written_feedback TEXT,
                    status VARCHAR(50) DEFAULT 'draft',
                    finalized_by VARCHAR(36),
                    finalized_at TIMESTAMP,
                    reviewed_by VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
                    FOREIGN KEY (finalized_by) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
                    CHECK (service_quality_rating BETWEEN 1 AND 5),
                    CHECK (timeliness_rating BETWEEN 1 AND 5),
                    CHECK (communication_rating BETWEEN 1 AND 5),
                    CHECK (cost_effectiveness_rating BETWEEN 1 AND 5),
                    CHECK (compliance_rating BETWEEN 1 AND 5),
                    CHECK (status IN ('draft', 'finalized', 'archived'))
                )
            """))
            
            # Create indexes for vendor_performance_reviews
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_reviews_vendor ON vendor_performance_reviews(vendor_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_reviews_review_date ON vendor_performance_reviews(review_date)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_reviews_status ON vendor_performance_reviews(status)"))
            
            # ================================================================
            # VENDOR COMPLIANCE DOCUMENTS TABLE
            # ================================================================
            
            logger.info("Creating vendor_compliance_documents table...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS vendor_compliance_documents (
                    id VARCHAR(36) PRIMARY KEY,
                    vendor_id VARCHAR(36) NOT NULL,
                    document_type VARCHAR(100) NOT NULL,
                    document_name VARCHAR(255) NOT NULL,
                    document_number VARCHAR(100),
                    issue_date DATE,
                    expiry_date DATE,
                    issuing_authority VARCHAR(255),
                    file_url VARCHAR(500) NOT NULL,
                    file_name VARCHAR(255),
                    file_size INTEGER,
                    status VARCHAR(50) NOT NULL DEFAULT 'valid',
                    verification_status VARCHAR(50) DEFAULT 'pending',
                    verified_by VARCHAR(36),
                    verified_at TIMESTAMP,
                    notes TEXT,
                    uploaded_by VARCHAR(36) NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    parent_document_id VARCHAR(36),
                    
                    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
                    FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (parent_document_id) REFERENCES vendor_compliance_documents(id) ON DELETE SET NULL,
                    CHECK (status IN ('valid', 'expiring_soon', 'expired', 'pending_review', 'rejected')),
                    CHECK (verification_status IN ('pending', 'verified', 'rejected', 'expired'))
                )
            """))
            
            # Create indexes for vendor_compliance_documents
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_documents_vendor ON vendor_compliance_documents(vendor_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_documents_status ON vendor_compliance_documents(status)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_documents_expiry ON vendor_compliance_documents(expiry_date)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_documents_document_type ON vendor_compliance_documents(document_type)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_documents_verification_status ON vendor_compliance_documents(verification_status)"))
            
            # ================================================================
            # VENDOR COMMUNICATIONS TABLE
            # ================================================================
            
            logger.info("Creating vendor_communications table...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS vendor_communications (
                    id VARCHAR(36) PRIMARY KEY,
                    vendor_id VARCHAR(36) NOT NULL,
                    communication_type VARCHAR(50) NOT NULL,
                    communication_date TIMESTAMP NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    details TEXT,
                    attendees TEXT,
                    outcome TEXT,
                    follow_up_required BOOLEAN DEFAULT 0,
                    follow_up_date DATE,
                    follow_up_notes TEXT,
                    tags VARCHAR(255),
                    attachment_urls TEXT,
                    is_important BOOLEAN DEFAULT 0,
                    logged_by VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
                    FOREIGN KEY (logged_by) REFERENCES users(id) ON DELETE SET NULL,
                    CHECK (communication_type IN ('meeting', 'phone_call', 'email', 'video_call', 'site_visit', 'other'))
                )
            """))
            
            # Create indexes for vendor_communications
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_comms_vendor ON vendor_communications(vendor_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_comms_date ON vendor_communications(communication_date)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_comms_is_important ON vendor_communications(is_important)"))
            
            # ================================================================
            # VENDOR NOTIFICATIONS TABLE
            # ================================================================
            
            logger.info("Creating vendor_notifications table...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS vendor_notifications (
                    id VARCHAR(36) PRIMARY KEY,
                    vendor_id VARCHAR(36) NOT NULL,
                    notification_type VARCHAR(100) NOT NULL,
                    priority VARCHAR(50) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    action_required TEXT,
                    deadline DATE,
                    recipient_id VARCHAR(36) NOT NULL,
                    is_read BOOLEAN DEFAULT 0,
                    read_at TIMESTAMP,
                    is_actioned BOOLEAN DEFAULT 0,
                    actioned_at TIMESTAMP,
                    related_entity_type VARCHAR(50),
                    related_entity_id VARCHAR(36),
                    sent_via_email BOOLEAN DEFAULT 0,
                    email_sent_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
                    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE,
                    CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
                    CHECK (notification_type IN ('contract_expiry', 'document_expiry', 'review_due', 'compliance_alert', 'general'))
                )
            """))
            
            # Create indexes for vendor_notifications
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_notifications_recipient ON vendor_notifications(recipient_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_notifications_read ON vendor_notifications(is_read)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_notifications_created_at ON vendor_notifications(created_at)"))
            
            # ================================================================
            # VENDOR JOB ASSIGNMENTS TABLE
            # ================================================================
            
            logger.info("Creating vendor_job_assignments table...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS vendor_job_assignments (
                    id VARCHAR(36) PRIMARY KEY,
                    vendor_id VARCHAR(36) NOT NULL,
                    job_id VARCHAR(36) NOT NULL,
                    contract_id VARCHAR(36),
                    assignment_date DATE NOT NULL,
                    status VARCHAR(50) DEFAULT 'active',
                    fee_structure VARCHAR(100),
                    fee_amount VARCHAR(20),
                    candidates_submitted INTEGER DEFAULT 0,
                    candidates_hired INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                    FOREIGN KEY (contract_id) REFERENCES vendor_contracts(id) ON DELETE SET NULL,
                    CHECK (status IN ('active', 'completed', 'cancelled'))
                )
            """))
            
            # Create indexes for vendor_job_assignments
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_jobs_vendor ON vendor_job_assignments(vendor_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_jobs_job ON vendor_job_assignments(job_id)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_jobs_assignment_date ON vendor_job_assignments(assignment_date)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_jobs_status ON vendor_job_assignments(status)"))
            
            # ================================================================
            # VENDOR ANALYTICS TABLE
            # ================================================================
            
            logger.info("Creating vendor_analytics table...")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS vendor_analytics (
                    id VARCHAR(36) PRIMARY KEY,
                    vendor_id VARCHAR(36) NOT NULL,
                    date DATE NOT NULL,
                    total_jobs_assigned INTEGER DEFAULT 0,
                    active_jobs INTEGER DEFAULT 0,
                    candidates_submitted INTEGER DEFAULT 0,
                    candidates_interviewed INTEGER DEFAULT 0,
                    candidates_hired INTEGER DEFAULT 0,
                    total_revenue VARCHAR(20) DEFAULT '0',
                    average_rating VARCHAR(10),
                    response_time_hours VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
                    UNIQUE (vendor_id, date)
                )
            """))
            
            # Create indexes for vendor_analytics
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_analytics_date ON vendor_analytics(date)"))
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_vendor_analytics_vendor ON vendor_analytics(vendor_id)"))
            
            # Commit all changes
            await session.commit()
            
            logger.info("✅ Migration 012 completed successfully!")
            logger.info("Created 8 vendor management tables with indexes")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Migration failed: {str(e)}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())
