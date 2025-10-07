from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from core.database import Base

class Skill(Base):
    """
    Skill model - stores unique skills
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True)  # e.g., "Programming", "Framework", "Tool", etc.

    # Relationships
    candidates = relationship("Candidate", secondary="candidate_skills", back_populates="skills")

    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}')>"
