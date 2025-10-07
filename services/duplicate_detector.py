"""
Duplicate Detection Service
Detects duplicate candidates and resumes using multiple strategies:
1. Email matching (exact)
2. Phone number matching (normalized)
3. Content similarity (fuzzy matching + hash comparison)
"""

import hashlib
import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from difflib import SequenceMatcher

from models.db import Candidate, Resume

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Service for detecting duplicate candidates and resumes"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize duplicate detector.
        
        Args:
            similarity_threshold: Minimum similarity score (0-1) to consider content as duplicate
        """
        self.similarity_threshold = similarity_threshold
    
    def check_duplicate_candidate(
        self, 
        email: Optional[str], 
        phone: Optional[str],
        name: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Check if candidate already exists in database.
        
        Args:
            email: Candidate email
            phone: Candidate phone number
            name: Candidate full name
            db: Database session
            
        Returns:
            Dict with duplicate status and matching candidates
        """
        try:
            matches = []
            confidence_scores = []
            
            # Strategy 1: Exact email match (highest confidence)
            if email:
                normalized_email = self._normalize_email(email)
                email_match = db.query(Candidate).filter(
                    Candidate.email == normalized_email
                ).first()
                
                if email_match:
                    matches.append({
                        'candidate_id': email_match.id,
                        'match_type': 'email',
                        'confidence': 1.0,
                        'matched_field': email_match.email,
                        'candidate': {
                            'id': email_match.id,
                            'name': email_match.full_name,
                            'email': email_match.email,
                            'phone': email_match.phone_number
                        }
                    })
                    confidence_scores.append(1.0)
            
            # Strategy 2: Phone number match (high confidence)
            if phone:
                normalized_phone = self._normalize_phone(phone)
                if normalized_phone:
                    phone_match = db.query(Candidate).filter(
                        Candidate.phone_number == normalized_phone
                    ).first()
                    
                    if phone_match:
                        # Check if already matched by email
                        if not any(m['candidate_id'] == phone_match.id for m in matches):
                            matches.append({
                                'candidate_id': phone_match.id,
                                'match_type': 'phone',
                                'confidence': 0.95,
                                'matched_field': phone_match.phone_number,
                                'candidate': {
                                    'id': phone_match.id,
                                    'name': phone_match.full_name,
                                    'email': phone_match.email,
                                    'phone': phone_match.phone_number
                                }
                            })
                            confidence_scores.append(0.95)
            
            # Strategy 3: Fuzzy name matching (if email/phone not found)
            if not matches and name and email:
                # Search for similar names with similar email domains
                email_domain = email.split('@')[1] if '@' in email else None
                
                potential_matches = db.query(Candidate).filter(
                    or_(
                        Candidate.full_name.ilike(f"%{name.split()[0]}%"),  # First name match
                        Candidate.email.ilike(f"%{email_domain}%") if email_domain else False
                    )
                ).limit(10).all()
                
                for candidate in potential_matches:
                    name_similarity = self._calculate_similarity(
                        name.lower(), 
                        candidate.full_name.lower()
                    )
                    
                    if name_similarity >= 0.8:
                        matches.append({
                            'candidate_id': candidate.id,
                            'match_type': 'fuzzy_name',
                            'confidence': name_similarity,
                            'matched_field': candidate.full_name,
                            'candidate': {
                                'id': candidate.id,
                                'name': candidate.full_name,
                                'email': candidate.email,
                                'phone': candidate.phone_number
                            }
                        })
                        confidence_scores.append(name_similarity)
            
            # Determine overall duplicate status
            is_duplicate = len(matches) > 0
            highest_confidence = max(confidence_scores) if confidence_scores else 0.0
            
            return {
                'is_duplicate': is_duplicate,
                'confidence': highest_confidence,
                'match_count': len(matches),
                'matches': matches,
                'recommendation': self._get_recommendation(is_duplicate, highest_confidence, matches)
            }
            
        except Exception as e:
            logger.error(f"Error checking duplicate candidate: {str(e)}")
            return {
                'is_duplicate': False,
                'confidence': 0.0,
                'match_count': 0,
                'matches': [],
                'recommendation': 'Error during duplicate check',
                'error': str(e)
            }
    
    def check_duplicate_resume(
        self,
        file_content: bytes,
        text_content: str,
        candidate_id: Optional[int],
        db: Session
    ) -> Dict[str, Any]:
        """
        Check if resume content already exists in database.
        
        Args:
            file_content: Raw file bytes
            text_content: Extracted text from resume
            candidate_id: Candidate ID (if known)
            db: Database session
            
        Returns:
            Dict with duplicate status and matching resumes
        """
        try:
            matches = []
            
            # Strategy 1: File hash match (exact duplicate file)
            file_hash = self._calculate_file_hash(file_content)
            hash_match = db.query(Resume).filter(
                Resume.file_hash == file_hash
            ).first()
            
            if hash_match:
                matches.append({
                    'resume_id': hash_match.id,
                    'match_type': 'file_hash',
                    'confidence': 1.0,
                    'file_name': hash_match.file_name,
                    'candidate_id': hash_match.candidate_id,
                    'uploaded_at': hash_match.uploaded_at.isoformat() if hash_match.uploaded_at else None
                })
                
                return {
                    'is_duplicate': True,
                    'confidence': 1.0,
                    'match_count': 1,
                    'matches': matches,
                    'recommendation': 'Exact duplicate file detected. This file has been uploaded before.'
                }
            
            # Strategy 2: Content similarity (fuzzy matching)
            if candidate_id:
                # Check other resumes from same candidate
                existing_resumes = db.query(Resume).filter(
                    Resume.candidate_id == candidate_id,
                    Resume.raw_text.isnot(None)
                ).all()
                
                for resume in existing_resumes:
                    if resume.raw_text:
                        similarity = self._calculate_similarity(
                            text_content[:5000],  # Compare first 5000 chars
                            resume.raw_text[:5000]
                        )
                        
                        if similarity >= self.similarity_threshold:
                            matches.append({
                                'resume_id': resume.id,
                                'match_type': 'content_similarity',
                                'confidence': similarity,
                                'file_name': resume.file_name,
                                'candidate_id': resume.candidate_id,
                                'uploaded_at': resume.uploaded_at.isoformat() if resume.uploaded_at else None
                            })
            
            # Determine overall duplicate status
            is_duplicate = len(matches) > 0
            highest_confidence = max([m['confidence'] for m in matches]) if matches else 0.0
            
            return {
                'is_duplicate': is_duplicate,
                'confidence': highest_confidence,
                'match_count': len(matches),
                'matches': matches,
                'recommendation': self._get_resume_recommendation(is_duplicate, highest_confidence)
            }
            
        except Exception as e:
            logger.error(f"Error checking duplicate resume: {str(e)}")
            return {
                'is_duplicate': False,
                'confidence': 0.0,
                'match_count': 0,
                'matches': [],
                'recommendation': 'Error during duplicate check',
                'error': str(e)
            }
    
    def find_similar_candidates(
        self,
        candidate_id: int,
        db: Session,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find candidates similar to the given candidate.
        Useful for deduplication and merge suggestions.
        
        Args:
            candidate_id: ID of candidate to find similar matches for
            db: Database session
            limit: Maximum number of similar candidates to return
            
        Returns:
            List of similar candidates with similarity scores
        """
        try:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                return []
            
            similar = []
            
            # Find candidates with similar emails (same domain)
            if candidate.email and '@' in candidate.email:
                email_domain = candidate.email.split('@')[1]
                domain_matches = db.query(Candidate).filter(
                    Candidate.id != candidate_id,
                    Candidate.email.ilike(f"%@{email_domain}")
                ).limit(limit * 2).all()
                
                for match in domain_matches:
                    similarity = self._calculate_similarity(
                        candidate.full_name.lower(),
                        match.full_name.lower()
                    )
                    
                    if similarity > 0.6:
                        similar.append({
                            'candidate_id': match.id,
                            'name': match.full_name,
                            'email': match.email,
                            'phone': match.phone_number,
                            'similarity_score': similarity,
                            'match_reason': 'Similar name and email domain'
                        })
            
            # Sort by similarity and return top matches
            similar.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar candidates: {str(e)}")
            return []
    
    # Helper methods
    
    def _normalize_email(self, email: str) -> str:
        """Normalize email for comparison"""
        return email.lower().strip()
    
    def _normalize_phone(self, phone: str) -> Optional[str]:
        """
        Normalize phone number for comparison.
        Removes all non-digit characters and standardizes format.
        """
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if len(digits) == 10:
            # US format: (XXX) XXX-XXXX -> XXXXXXXXXX
            return digits
        elif len(digits) == 11 and digits[0] == '1':
            # US format with country code: 1-XXX-XXX-XXXX -> XXXXXXXXXX
            return digits[1:]
        elif len(digits) >= 10:
            # International format: keep last 10 digits
            return digits[-10:]
        
        return digits if len(digits) >= 7 else None
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings using SequenceMatcher.
        Returns value between 0 (completely different) and 1 (identical).
        """
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _get_recommendation(
        self, 
        is_duplicate: bool, 
        confidence: float, 
        matches: List[Dict]
    ) -> str:
        """Generate recommendation based on duplicate check results"""
        if not is_duplicate:
            return "No duplicates found. Safe to create new candidate."
        
        if confidence >= 0.95:
            match_type = matches[0]['match_type']
            return f"High confidence duplicate detected ({match_type}). Use existing candidate record."
        elif confidence >= 0.8:
            return "Probable duplicate detected. Review before creating new candidate."
        else:
            return "Possible duplicate detected. Manual verification recommended."
    
    def _get_resume_recommendation(self, is_duplicate: bool, confidence: float) -> str:
        """Generate recommendation for resume duplicate check"""
        if not is_duplicate:
            return "No duplicate resume found. Safe to process."
        
        if confidence >= 0.95:
            return "Duplicate resume detected. Skip processing to avoid duplicates."
        elif confidence >= 0.85:
            return "Similar resume found. Consider if this is an updated version."
        else:
            return "Possibly related resume found. Review similarity before processing."
