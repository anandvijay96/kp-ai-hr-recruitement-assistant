from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from core.database import Base

class Resume(Base):
    """
    Resume model - stores resume documents and metadata
    """
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="SET NULL"), nullable=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 hash
    upload_status = Column(String(20), nullable=False, default="pending", index=True)  # pending, processing, completed, failed
    raw_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)  # Store extracted structured data as JSON
    
    # Authenticity Analysis Results
    authenticity_score = Column(Integer, nullable=True)  # Overall score 0-100
    authenticity_details = Column(JSON, nullable=True)  # Detailed breakdown
    
    # JD Matching Results
    jd_match_score = Column(Integer, nullable=True)  # Match score 0-100
    jd_match_details = Column(JSON, nullable=True)  # Matching details
    
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")

    def __repr__(self):
        return f"<Resume(id={self.id}, file='{self.file_name}', status='{self.upload_status}')>"
