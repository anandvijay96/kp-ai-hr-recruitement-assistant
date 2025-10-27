"""Vendor Management Models"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, CheckConstraint, Integer, Float, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


def generate_uuid():
    """Generate UUID as string"""
    return str(uuid.uuid4())


class Vendor(Base):
    """Vendor/Agency model for managing recruitment vendors"""
    __tablename__ = "vendors"
    
    # Primary Key
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Company Information
    company_name = Column(String(255), nullable=False, unique=True, index=True)
    vendor_type = Column(String(50), default="agency")  # 'agency', 'freelancer', 'consultant', 'other'
    industry_specialization = Column(String(255))
    website = Column(String(255))
    description = Column(Text)
    
    # Contact Information
    contact_person = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=False, index=True)
    contact_phone = Column(String(20))
    
    # Address
    address = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Business Terms
    status = Column(String(20), default="active", index=True)  # 'active', 'inactive', 'suspended'
    commission_rate = Column(DECIMAL(5, 2))  # Percentage (e.g., 15.50 for 15.5%)
    payment_terms = Column(String(255))
    contract_start_date = Column(String(50))  # Store as string for flexibility
    contract_end_date = Column(String(50))
    
    # Performance Metrics (computed fields)
    total_candidates_referred = Column(Integer, default=0)
    candidates_hired = Column(Integer, default=0)
    success_rate = Column(DECIMAL(5, 2), default=0)  # Percentage
    average_rating = Column(DECIMAL(3, 2))  # 1.00 to 5.00
    
    # Settings
    has_portal_access = Column(Boolean, default=False)
    can_submit_candidates = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=True)
    
    # Notes & Tags
    notes = Column(Text)
    tags = Column(String)  # JSON field - SQLite stores as TEXT
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    updated_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Soft Delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Relationships
    candidate_relationships = relationship("CandidateVendor", back_populates="vendor", cascade="all, delete-orphan")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'suspended')", name="chk_vendor_status"),
        CheckConstraint("vendor_type IN ('agency', 'freelancer', 'consultant', 'other')", name="chk_vendor_type"),
    )


class CandidateVendor(Base):
    """Linking table between candidates and vendors with referral details"""
    __tablename__ = "candidate_vendors"
    
    # Primary Key
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Foreign Keys
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Referral Details
    referral_date = Column(DateTime(timezone=True), server_default=func.now())
    referral_notes = Column(Text)
    candidate_status = Column(String(50), default="referred", index=True)  # 'referred', 'screened', 'submitted', 'hired', 'rejected'
    
    # Financial
    agreed_rate = Column(DECIMAL(10, 2))  # Agreed placement fee
    commission_amount = Column(DECIMAL(10, 2))  # Calculated commission
    payment_status = Column(String(50), default="pending")  # 'pending', 'paid', 'cancelled'
    payment_date = Column(DateTime(timezone=True))
    
    # Performance
    vendor_rating = Column(Integer)  # 1-5 rating
    feedback = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Relationships
    vendor = relationship("Vendor", back_populates="candidate_relationships")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        CheckConstraint("candidate_status IN ('referred', 'screened', 'submitted', 'hired', 'rejected')", name="chk_candidate_status"),
        CheckConstraint("payment_status IN ('pending', 'paid', 'cancelled')", name="chk_payment_status"),
        CheckConstraint("vendor_rating >= 1 AND vendor_rating <= 5", name="chk_vendor_rating"),
    )
