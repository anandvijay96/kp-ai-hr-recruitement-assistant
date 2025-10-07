from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.database import Base

class WorkExperience(Base):
    """
    WorkExperience model - stores candidate work history
    """
    __tablename__ = "work_experience"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    company = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False)  # Is this the current job?
    description = Column(Text, nullable=True)  # Job responsibilities/achievements

    # Relationships
    candidate = relationship("Candidate", back_populates="work_experience")

    def __repr__(self):
        return f"<WorkExperience(id={self.id}, company='{self.company}', title='{self.job_title}')>"
