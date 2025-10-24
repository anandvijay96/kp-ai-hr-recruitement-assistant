"""Client Management Models"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, CheckConstraint, Integer, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base
import uuid


def generate_uuid():
    """Generate UUID as string"""
    return str(uuid.uuid4())


class Client(Base):
    """Client company model"""
    __tablename__ = "clients"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_name = Column(String(200), nullable=False, index=True)
    company_email = Column(String(255), unique=True, nullable=False, index=True)
    company_phone = Column(String(20))
    company_website = Column(String(255))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Business details
    industry = Column(String(100))
    company_size = Column(String(50))  # 1-10, 11-50, 51-200, 201-500, 501+
    tax_id = Column(String(50))
    
    # Status
    status = Column(String(50), default="active", index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Contract details
    contract_start_date = Column(DateTime(timezone=True))
    contract_end_date = Column(DateTime(timezone=True))
    contract_type = Column(String(50))  # monthly, annual, project-based
    billing_cycle = Column(String(50))  # monthly, quarterly, annual
    
    # Notes
    notes = Column(Text)
    
    # Metadata
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deactivated_at = Column(DateTime(timezone=True))
    deactivated_by = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    contacts = relationship("ClientContact", back_populates="client", cascade="all, delete-orphan")
    jobs = relationship("ClientJob", back_populates="client", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'suspended', 'pending')", name="chk_client_status"),
        CheckConstraint("company_size IN ('1-10', '11-50', '51-200', '201-500', '501-1000', '1000+')", name="chk_company_size"),
    )


class ClientContact(Base):
    """Client contact person model"""
    __tablename__ = "client_contacts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Contact details
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20))
    mobile = Column(String(20))
    designation = Column(String(100))
    department = Column(String(100))
    
    # Status
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # Portal access
    has_portal_access = Column(Boolean, default=False)
    portal_user_id = Column(String(36), ForeignKey("users.id"))
    
    # Notes
    notes = Column(Text)
    
    # Metadata
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="contacts")


class ClientJob(Base):
    """Jobs posted by clients"""
    __tablename__ = "client_jobs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    
    # Job details (if not linked to main jobs table)
    job_title = Column(String(200))
    job_description = Column(Text)
    requirements = Column(Text)
    location = Column(String(200))
    job_type = Column(String(50))  # full-time, part-time, contract
    experience_required = Column(String(50))
    salary_range = Column(String(100))
    
    # Status
    status = Column(String(50), default="open", index=True)
    priority = Column(String(50), default="medium")
    
    # Counts
    positions_count = Column(Integer, default=1)
    applications_count = Column(Integer, default=0)
    shortlisted_count = Column(Integer, default=0)
    hired_count = Column(Integer, default=0)
    
    # Dates
    posted_date = Column(DateTime(timezone=True), server_default=func.now())
    deadline = Column(DateTime(timezone=True))
    filled_date = Column(DateTime(timezone=True))
    
    # Metadata
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="jobs")
    
    __table_args__ = (
        CheckConstraint("status IN ('open', 'closed', 'on_hold', 'filled', 'cancelled')", name="chk_client_job_status"),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name="chk_job_priority"),
    )


class ClientActivity(Base):
    """Track client activities and interactions"""
    __tablename__ = "client_activities"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Activity details
    activity_type = Column(String(50), nullable=False, index=True)  # meeting, call, email, job_posted, etc.
    activity_title = Column(String(200))
    activity_description = Column(Text)
    
    # Participants
    performed_by = Column(String(36), ForeignKey("users.id"))
    contact_id = Column(String(36), ForeignKey("client_contacts.id"))
    
    # Status
    status = Column(String(50), default="completed")
    
    # Dates
    activity_date = Column(DateTime(timezone=True), server_default=func.now())
    scheduled_date = Column(DateTime(timezone=True))
    completed_date = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("activity_type IN ('meeting', 'call', 'email', 'job_posted', 'contract_signed', 'payment_received', 'other')", name="chk_activity_type"),
        CheckConstraint("status IN ('scheduled', 'completed', 'cancelled', 'rescheduled')", name="chk_activity_status"),
    )
