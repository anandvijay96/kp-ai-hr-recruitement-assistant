from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class Education(Base):
    """
    Education model - stores candidate education records
    """
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    institution = Column(String(255), nullable=True)
    degree = Column(String(255), nullable=True)
    field_of_study = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    grade = Column(String(50), nullable=True)  # GPA, percentage, etc.

    # Relationships
    candidate = relationship("Candidate", back_populates="education")

    def __repr__(self):
        return f"<Education(id={self.id}, degree='{self.degree}', institution='{self.institution}')>"
