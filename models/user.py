"""
User and API Credentials Models
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Date, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses String(36)
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    hashed_password = Column(String(255))  # Optional for OAuth-only users
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    api_credentials = relationship("UserAPICredential", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("APIUsageLog", back_populates="user", cascade="all, delete-orphan")


class UserAPICredential(Base):
    """Store encrypted API credentials per user"""
    __tablename__ = "user_api_credentials"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_type = Column(String(50), nullable=False)  # 'google_search', 'openai', etc.
    
    # OAuth credentials (encrypted)
    oauth_access_token = Column(Text)  # Encrypted
    oauth_refresh_token = Column(Text)  # Encrypted
    oauth_expires_at = Column(DateTime)
    oauth_scope = Column(String(500))
    
    # Manual API key (encrypted)
    api_key = Column(Text)  # Encrypted
    api_engine_id = Column(String(255))  # For Google Custom Search Engine ID
    
    # Usage tracking
    quota_used_today = Column(Integer, default=0)
    quota_limit_daily = Column(Integer, default=100)
    last_reset_date = Column(Date, default=datetime.utcnow().date)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_credentials")
    usage_logs = relationship("APIUsageLog", back_populates="credential", cascade="all, delete-orphan")


class APIUsageLog(Base):
    """Log API usage for billing and analytics"""
    __tablename__ = "api_usage_logs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    credential_id = Column(GUID(), ForeignKey("user_api_credentials.id", ondelete="CASCADE"))
    
    service_type = Column(String(50), nullable=False)
    endpoint = Column(String(255))
    request_count = Column(Integer, default=1)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Extra data (JSON string)
    # Note: 'metadata' is reserved in SQLAlchemy, so we use 'extra_data'
    extra_data = Column(Text)  # JSON string for additional info
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    credential = relationship("UserAPICredential", back_populates="usage_logs")
