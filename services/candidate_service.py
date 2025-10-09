import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.db import Candidate, Resume, Education, WorkExperience, Skill
from services.duplicate_detector import DuplicateDetector

logger = logging.getLogger(__name__)


class CandidateService:
    """
    Handles candidate-related business logic.
    """
    
    def __init__(self):
        """Initialize candidate service with duplicate detector"""
        self.duplicate_detector = DuplicateDetector(similarity_threshold=0.85)
    
    def check_duplicate(
        self, 
        email: Optional[str], 
        phone: Optional[str],
        name: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Check for duplicate candidates using advanced detection.
        
        Args:
            email: Candidate email
            phone: Candidate phone number  
            name: Candidate full name
            db: Database session
            
        Returns:
            Dict with duplicate detection results
        """
        return self.duplicate_detector.check_duplicate_candidate(
            email=email,
            phone=phone,
            name=name,
            db=db
        )
    
    def find_duplicate(self, email: str, phone: str, db: Session) -> Optional[Candidate]:
        """
        Checks for duplicate candidates by email or phone number.
        
        Args:
            email: Email address to check
            phone: Phone number to check
            db: Database session
            
        Returns:
            Candidate if found, None otherwise
        """
        try:
            filters = []
            if email:
                filters.append(Candidate.email == email)
            if phone:
                filters.append(Candidate.phone_number == phone)
            
            if not filters:
                return None
            
            candidate = db.query(Candidate).filter(or_(*filters)).first()
            return candidate
        
        except Exception as e:
            logger.error(f"Error finding duplicate candidate: {str(e)}")
            return None
    
    def create_candidate(self, data: Dict[str, Any], db: Session) -> Candidate:
        """
        Creates a new candidate profile in the database.
        
        Args:
            data: Candidate data dict
            db: Database session
            
        Returns:
            Created Candidate object
        """
        try:
            candidate = Candidate(
                full_name=data.get('full_name', 'Unknown'),
                email=data.get('email'),
                phone_number=data.get('phone_number'),
                linkedin_url=data.get('linkedin_url'),
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            
            logger.info(f"Created candidate: {candidate.id} - {candidate.email}")
            return candidate
        
        except Exception as e:
            logger.error(f"Error creating candidate: {str(e)}")
            db.rollback()
            raise
    
    def get_candidate_by_id(self, candidate_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get candidate by ID with all related data
        
        Returns:
            Dict with candidate data including skills, education, work_experience, resumes
        """
        from sqlalchemy.orm import joinedload
        
        candidate = db.query(Candidate).options(
            joinedload(Candidate.skills),
            joinedload(Candidate.education),
            joinedload(Candidate.work_experience),
            joinedload(Candidate.resumes)
        ).filter(Candidate.id == candidate_id).first()
        
        if not candidate:
            return None
        
        # Convert to dict with all relationships
        return {
            "id": candidate.id,
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone_number": candidate.phone_number,
            "linkedin_url": candidate.linkedin_url,
            "github_url": candidate.github_url,
            "portfolio_url": candidate.portfolio_url,
            "location": candidate.location,
            "professional_summary": candidate.professional_summary,
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
            "skills": [{"id": s.id, "name": s.name, "category": s.category} for s in candidate.skills],
            "education": [{
                "id": e.id,
                "degree": e.degree,
                "field_of_study": e.field_of_study,
                "institution": e.institution,
                "grade": e.grade,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None
            } for e in candidate.education],
            "work_experience": [{
                "id": w.id,
                "job_title": w.job_title,
                "company": w.company,
                "location": w.location,
                "start_date": w.start_date.isoformat() if w.start_date else None,
                "end_date": w.end_date.isoformat() if w.end_date else None,
                "is_current": w.is_current,
                "description": w.description
            } for w in candidate.work_experience],
            "resumes": [{
                "id": r.id,
                "file_name": r.file_name,
                "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
                "authenticity_score": r.authenticity_score,
                "upload_status": r.upload_status
            } for r in candidate.resumes]
        }
    
    def get_candidate_by_email(self, email: str, db: Session) -> Optional[Candidate]:
        """Get candidate by email"""
        return db.query(Candidate).filter(Candidate.email == email).first()
    
    def get_all_candidates(self, db: Session, skip: int = 0, limit: int = 100) -> List[Candidate]:
        """Get all candidates with pagination"""
        return db.query(Candidate).offset(skip).limit(limit).all()
    
    def update_candidate(self, candidate_id: int, data: Dict[str, Any], db: Session) -> Optional[Candidate]:
        """Update candidate information"""
        try:
            candidate = self.get_candidate_by_id(candidate_id, db)
            if not candidate:
                return None
            
            # Update fields
            if 'full_name' in data:
                candidate.full_name = data['full_name']
            if 'email' in data:
                candidate.email = data['email']
            if 'phone_number' in data:
                candidate.phone_number = data['phone_number']
            if 'linkedin_url' in data:
                candidate.linkedin_url = data['linkedin_url']
            
            db.commit()
            db.refresh(candidate)
            
            return candidate
        
        except Exception as e:
            logger.error(f"Error updating candidate: {str(e)}")
            db.rollback()
            raise
