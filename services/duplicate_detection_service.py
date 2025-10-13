"""Service for detecting duplicate candidates"""
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import re
import uuid

try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    logging.warning("fuzzywuzzy not available - name similarity matching will be disabled")

from models.database import Candidate, Resume, DuplicateCheck
from models.candidate_schemas import DuplicateMatch, ParsedResumeData

logger = logging.getLogger(__name__)


class DuplicateDetectionService:
    """Service for detecting duplicate candidates"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.name_similarity_threshold = 0.85
        self.content_similarity_threshold = 0.90
    
    def _normalize_email(self, email: Optional[str]) -> Optional[str]:
        """Normalize email for comparison"""
        if not email:
            return None
        return email.lower().strip()
    
    def _normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """Normalize phone number for comparison"""
        if not phone:
            return None
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        # Return last 10 digits for comparison
        return digits[-10:] if len(digits) >= 10 else digits
    
    async def check_duplicates(
        self,
        parsed_data: ParsedResumeData,
        resume_id: Optional[str] = None
    ) -> List[DuplicateMatch]:
        """
        Check for duplicate candidates using multiple methods
        
        Args:
            parsed_data: Parsed resume data
            resume_id: Optional resume ID for logging
            
        Returns:
            List of duplicate matches
        """
        try:
            duplicates = []
            
            # 1. Check email match (highest priority)
            if parsed_data.personal_info.email:
                email_match = await self.check_email_match(parsed_data.personal_info.email)
                if email_match:
                    duplicates.append(email_match)
                    # Email match is definitive, log and return
                    if resume_id:
                        await self.log_duplicate_check(
                            resume_id=resume_id,
                            match_type="email",
                            match_score=1.0,
                            matched_candidate_id=email_match["candidate_id"]
                        )
                    return duplicates
            
            # 2. Check phone match
            if parsed_data.personal_info.phone:
                phone_match = await self.check_phone_match(parsed_data.personal_info.phone)
                if phone_match:
                    duplicates.append(phone_match)
                    if resume_id:
                        await self.log_duplicate_check(
                            resume_id=resume_id,
                            match_type="phone",
                            match_score=1.0,
                            matched_candidate_id=phone_match["candidate_id"]
                        )
                    return duplicates
            
            # 3. Check name similarity (fuzzy match)
            if FUZZYWUZZY_AVAILABLE and parsed_data.personal_info.name:
                name_matches = await self.check_name_similarity(
                    parsed_data.personal_info.name,
                    threshold=self.name_similarity_threshold
                )
                duplicates.extend(name_matches)
                
                # Log name matches
                if resume_id:
                    for match in name_matches:
                        await self.log_duplicate_check(
                            resume_id=resume_id,
                            match_type="name",
                            match_score=match["match_score"],
                            matched_candidate_id=match["candidate_id"]
                        )
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Error checking duplicates: {str(e)}")
            return []
    
    async def check_email_match(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Check for exact email match
        
        Args:
            email: Email address to check
            
        Returns:
            Duplicate match info or None
        """
        try:
            normalized_email = self._normalize_email(email)
            if not normalized_email:
                return None
            
            result = await self.db.execute(
                select(Candidate).where(Candidate.email == normalized_email)
            )
            candidate = result.scalar_one_or_none()
            
            if candidate:
                return {
                    "candidate_id": candidate.id,
                    "name": candidate.full_name,
                    "email": candidate.email,
                    "phone": candidate.phone,
                    "match_type": "email",
                    "match_score": 1.0,
                    "uploaded_at": candidate.created_at
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking email match: {str(e)}")
            return None
    
    async def check_phone_match(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Check for phone number match (normalized)
        
        Args:
            phone: Phone number to check
            
        Returns:
            Duplicate match info or None
        """
        try:
            normalized_phone = self._normalize_phone(phone)
            if not normalized_phone or len(normalized_phone) < 10:
                return None
            
            # Get all candidates with phone numbers
            result = await self.db.execute(
                select(Candidate).where(Candidate.phone.isnot(None))
            )
            candidates = result.scalars().all()
            
            # Check normalized phone matches
            for candidate in candidates:
                candidate_phone = self._normalize_phone(candidate.phone)
                if candidate_phone and candidate_phone == normalized_phone:
                    return {
                        "candidate_id": candidate.id,
                        "name": candidate.full_name,
                        "email": candidate.email,
                        "phone": candidate.phone,
                        "match_type": "phone",
                        "match_score": 1.0,
                        "uploaded_at": candidate.created_at
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking phone match: {str(e)}")
            return None
    
    async def check_name_similarity(
        self,
        name: str,
        threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Check for fuzzy name match using Levenshtein distance
        
        Args:
            name: Name to check
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of similar name matches
        """
        try:
            if not FUZZYWUZZY_AVAILABLE:
                logger.warning("fuzzywuzzy not available for name similarity")
                return []
            
            matches = []
            
            # Get all candidates
            result = await self.db.execute(select(Candidate))
            candidates = result.scalars().all()
            
            # Calculate similarity for each candidate
            for candidate in candidates:
                similarity = fuzz.ratio(name.lower(), candidate.full_name.lower()) / 100.0
                
                if similarity >= threshold:
                    matches.append({
                        "candidate_id": candidate.id,
                        "name": candidate.full_name,
                        "email": candidate.email,
                        "phone": candidate.phone,
                        "match_type": "name",
                        "match_score": round(similarity, 4),
                        "uploaded_at": candidate.created_at
                    })
            
            # Sort by match score descending
            matches.sort(key=lambda x: x["match_score"], reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error checking name similarity: {str(e)}")
            return []
    
    async def check_resume_hash_duplicate(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if a resume with the same hash already exists
        
        Args:
            file_hash: SHA-256 hash of the file
            
        Returns:
            Existing resume info or None
        """
        try:
            result = await self.db.execute(
                select(Resume).where(
                    Resume.file_hash == file_hash,
                    Resume.deleted_at.is_(None)
                )
            )
            resume = result.scalar_one_or_none()
            
            if resume:
                return {
                    "resume_id": resume.id,
                    "filename": resume.original_file_name,
                    "uploaded_at": resume.upload_date,
                    "candidate_name": resume.candidate_name,
                    "candidate_email": resume.candidate_email
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking resume hash: {str(e)}")
            return None
    
    async def log_duplicate_check(
        self,
        resume_id: str,
        match_type: str,
        match_score: float,
        matched_candidate_id: Optional[str] = None,
        candidate_id: Optional[str] = None
    ) -> None:
        """
        Log a duplicate check for audit trail
        
        Args:
            resume_id: Resume ID
            match_type: Type of match (email, phone, name, content)
            match_score: Match score (0.0 to 1.0)
            matched_candidate_id: ID of matched candidate
            candidate_id: ID of new candidate (if created)
        """
        try:
            duplicate_check = DuplicateCheck(
                id=str(uuid.uuid4()),
                resume_id=resume_id,
                candidate_id=candidate_id,
                match_type=match_type,
                match_score=str(match_score),
                matched_candidate_id=matched_candidate_id
            )
            self.db.add(duplicate_check)
            await self.db.commit()
            
            logger.info(f"Logged duplicate check for resume {resume_id}: {match_type} match")
            
        except Exception as e:
            logger.error(f"Error logging duplicate check: {str(e)}")
            # Don't raise - logging failure shouldn't break the flow
    
    async def resolve_duplicate(
        self,
        resume_id: str,
        resolution: str,
        resolved_by: str,
        matched_candidate_id: Optional[str] = None
    ) -> bool:
        """
        Record the resolution of a duplicate
        
        Args:
            resume_id: Resume ID
            resolution: Resolution action (skip, merge, force_create)
            resolved_by: User ID who resolved
            matched_candidate_id: ID of matched candidate
            
        Returns:
            True if successful
        """
        try:
            # Find the duplicate check record
            result = await self.db.execute(
                select(DuplicateCheck)
                .where(DuplicateCheck.resume_id == resume_id)
                .order_by(DuplicateCheck.created_at.desc())
                .limit(1)
            )
            duplicate_check = result.scalar_one_or_none()
            
            if duplicate_check:
                duplicate_check.resolution = resolution
                duplicate_check.resolved_by = resolved_by
                from datetime import datetime
                duplicate_check.resolved_at = datetime.utcnow()
                
                await self.db.commit()
                logger.info(f"Resolved duplicate for resume {resume_id}: {resolution}")
                return True
            
            return False
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error resolving duplicate: {str(e)}")
            raise
    
    async def get_duplicate_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about duplicate detection
        
        Returns:
            Dictionary with duplicate statistics
        """
        try:
            from sqlalchemy import func
            
            # Total duplicate checks
            total_result = await self.db.execute(
                select(func.count()).select_from(DuplicateCheck)
            )
            total_checks = total_result.scalar()
            
            # Checks by match type
            type_result = await self.db.execute(
                select(
                    DuplicateCheck.match_type,
                    func.count()
                ).group_by(DuplicateCheck.match_type)
            )
            by_type = {row[0]: row[1] for row in type_result.all()}
            
            # Checks by resolution
            resolution_result = await self.db.execute(
                select(
                    DuplicateCheck.resolution,
                    func.count()
                ).group_by(DuplicateCheck.resolution)
            )
            by_resolution = {row[0]: row[1] for row in resolution_result.all()}
            
            return {
                "total_checks": total_checks,
                "by_match_type": by_type,
                "by_resolution": by_resolution
            }
            
        except Exception as e:
            logger.error(f"Error getting duplicate statistics: {str(e)}")
            return {
                "total_checks": 0,
                "by_match_type": {},
                "by_resolution": {}
            }
