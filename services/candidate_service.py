import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.db import Candidate, Resume, Education, WorkExperience, Skill

logger = logging.getLogger(__name__)


class CandidateService:
    """
    Handles candidate-related business logic.
    """
    
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
    
    def get_candidate_by_id(self, candidate_id: int, db: Session) -> Optional[Candidate]:
        """Get candidate by ID"""
        return db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
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
