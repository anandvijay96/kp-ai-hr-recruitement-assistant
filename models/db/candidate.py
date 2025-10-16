from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, func
from sqlalchemy.orm import relationship
from core.database import Base

class Candidate(Base):
    """
    Candidate model - stores candidate master data
    """
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    professional_summary = Column(Text, nullable=True)
    search_vector = Column(Text, nullable=True)  # Full-text search vector (Text for SQLite compatibility)
    
    # Soft delete fields
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String(255), nullable=True)  # Admin username who deleted
    deletion_reason = Column(Text, nullable=True)  # Optional reason for deletion
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    education = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    work_experience = relationship("WorkExperience", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("Skill", secondary="candidate_skills", back_populates="candidates")
    certifications = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Candidate(id={self.id}, name='{self.full_name}', email='{self.email}')>"
