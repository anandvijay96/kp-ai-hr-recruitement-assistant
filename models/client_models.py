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
    """Client company model for managing client organizations"""
    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'on_hold')", name="chk_client_status"),
        CheckConstraint("client_type IN ('direct', 'agency', 'partner')", name="chk_client_type"),
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="chk_client_priority"),
        {'extend_existing': True}  # Allow redefinition if table already exists
    )
    
    # Primary Key
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Company Information
    company_name = Column(String(255), nullable=False, unique=True, index=True)
    industry = Column(String(100))
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
    
    # Business Details
    status = Column(String(20), default="active", index=True)  # 'active', 'inactive', 'on_hold'
    client_type = Column(String(20), default="direct")  # 'direct', 'agency', 'partner'
    priority = Column(String(20), default="medium")  # 'low', 'medium', 'high'
    
    # Contract/Agreement
    contract_start_date = Column(String(50))  # Changed to String to match migration (Date type)
    contract_end_date = Column(String(50))
    contract_value = Column(String(50))  # Store as string to handle various formats
    payment_terms = Column(String(255))
    
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
    jobs = relationship("Job", back_populates="client")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])

# NOTE: ClientContact, ClientJob, and ClientActivity models are not included
# because the migration that was executed (add_clients_table.py) only created
# the main 'clients' table. If you need these additional tables, run the
# add_client_management_tables.py migration instead.
