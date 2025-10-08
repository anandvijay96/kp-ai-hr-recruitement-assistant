from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class Certification(Base):
    """
    Certification model - stores professional certifications
    """
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=True)
    issue_year = Column(String(4), nullable=True)
    expiry_year = Column(String(4), nullable=True)
    credential_id = Column(String(255), nullable=True)
    credential_url = Column(String(512), nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="certifications")

    def __repr__(self):
        return f"<Certification(id={self.id}, name='{self.name}', year='{self.issue_year}')>"
