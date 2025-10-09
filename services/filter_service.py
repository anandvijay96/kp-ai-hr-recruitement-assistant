from models.filter_models import CandidateFilter
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, or_, and_, extract, text
from sqlalchemy.dialects.postgresql import TSVECTOR
from models.db import Candidate, Resume, Skill, Education, WorkExperience
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class FilterService:
    """Service for filtering and searching candidates using database queries"""
    
    async def full_text_search(self, query: str, db: AsyncSession, 
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Perform full-text search across candidates and resumes using PostgreSQL FTS.
        
        Args:
            query: Search query string
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Dict with results and pagination info
        """
        try:
            # Parse query and create tsquery
            tsquery = self._parse_search_query(query)
            
            # Search in candidates table using async select()
            stmt = select(Candidate).options(
                selectinload(Candidate.resumes),
                selectinload(Candidate.skills),
                selectinload(Candidate.education),
                selectinload(Candidate.work_experience)
            )
            
            # Join with resumes for comprehensive search
            stmt = stmt.outerjoin(Candidate.resumes)
            
            # Apply full-text search filter
            stmt = stmt.filter(
                or_(
                    Candidate.search_vector.op('@@')(func.to_tsquery('english', tsquery)),
                    Resume.search_vector.op('@@')(func.to_tsquery('english', tsquery))
                )
            ).distinct()
            
            # Get total count
            count_stmt = select(func.count()).select_from(stmt.alias())
            count_result = await db.execute(count_stmt)
            total_count = count_result.scalar() or 0
            
            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)
            result = await db.execute(stmt)
            candidates = result.scalars().all()
            
            # Format results
            results = self._format_candidate_results(candidates)
            
            return {
                "results": results,
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": max(1, (total_count + page_size - 1) // page_size)
                },
                "search_query": query
            }
            
        except Exception as e:
            logger.error(f"Error in full-text search: {str(e)}")
            raise
    
    async def search_candidates(self, filters: CandidateFilter, db: AsyncSession, 
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Filters candidates based on the provided criteria using database queries.
        
        Args:
            filters: CandidateFilter object with filter criteria
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Dict with results and pagination info
        """
        try:
            # Base query with eager loading using async select()
            stmt = select(Candidate).options(
                selectinload(Candidate.resumes),
                selectinload(Candidate.skills),
                selectinload(Candidate.education),
                selectinload(Candidate.work_experience)
            )
            
            # Filter by skills (if any match)
            if filters.skills:
                stmt = stmt.join(Candidate.skills).filter(
                    Skill.name.in_([skill.lower() for skill in filters.skills])
                ).distinct()
            
            # Filter by education level
            if filters.education:
                stmt = stmt.join(Candidate.education).filter(
                    Education.degree.in_(filters.education)
                ).distinct()
            
            # Filter by location (search in work_experience or candidate data if available)
            if filters.location:
                stmt = stmt.join(Candidate.work_experience).filter(
                    WorkExperience.location.ilike(f"%{filters.location}%")
                ).distinct()
            
            # Filter by status (from resume table)
            if filters.status:
                stmt = stmt.join(Candidate.resumes).filter(
                    Resume.upload_status.in_(filters.status)
                ).distinct()
            
            # Get total count before pagination
            count_stmt = select(func.count()).select_from(stmt.alias())
            count_result = await db.execute(count_stmt)
            total_count = count_result.scalar() or 0
            
            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)
            result = await db.execute(stmt)
            candidates = result.scalars().all()
            
            # Format results
            results = self._format_candidate_results(candidates)
            
            return {
                "results": results,
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": max(1, (total_count + page_size - 1) // page_size)
                },
                "filters_applied": {
                    "skills": filters.skills,
                    "min_experience": filters.min_experience,
                    "max_experience": filters.max_experience,
                    "education": filters.education,
                    "location": filters.location,
                    "status": filters.status
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching candidates: {str(e)}")
            raise
    
    async def get_filter_options(self, db: AsyncSession) -> Dict[str, List]:
        """
        Retrieves distinct values for filter options from the database.
        
        Args:
            db: Database session
            
        Returns:
            Dict with available filter options
        """
        try:
            # Get distinct skills
            skills_stmt = select(Skill.name).distinct().order_by(Skill.name)
            skills_result = await db.execute(skills_stmt)
            skills_list = [skill[0] for skill in skills_result.all()]
            
            # Get distinct education levels
            edu_stmt = select(Education.degree).distinct().order_by(Education.degree)
            edu_result = await db.execute(edu_stmt)
            education_list = [edu[0] for edu in edu_result.all() if edu[0]]
            
            # Get distinct locations from work experience
            loc_stmt = select(WorkExperience.location).distinct().filter(
                WorkExperience.location.isnot(None)
            ).order_by(WorkExperience.location)
            loc_result = await db.execute(loc_stmt)
            location_list = [loc[0] for loc in loc_result.all() if loc[0]]
            
            # Get available statuses
            statuses = ["New", "Screened", "Interviewed", "Rejected", "Hired"]
            
            return {
                "skills": skills_list if skills_list else ["Python", "Java", "JavaScript", "SQL"],  # Fallback
                "locations": location_list if location_list else [],
                "education_levels": education_list if education_list else ["Bachelor's", "Master's", "PhD"],
                "statuses": statuses
            }
            
        except Exception as e:
            logger.error(f"Error getting filter options: {str(e)}")
            # Return default options on error
            return {
                "skills": ["Python", "Java", "JavaScript", "SQL"],
                "locations": [],
                "education_levels": ["Bachelor's", "Master's", "PhD"],
                "statuses": ["New", "Screened", "Interviewed", "Rejected", "Hired"]
            }
    
    def _parse_search_query(self, query: str) -> str:
        """
        Parse search query and convert to PostgreSQL tsquery format.
        Supports AND, OR, NOT operators.
        
        Args:
            query: Raw search query string
            
        Returns:
            Formatted tsquery string
        """
        if not query:
            return ''
        
        # Replace common operators with PostgreSQL equivalents
        # AND -> &, OR -> |, NOT -> !
        query = query.strip()
        
        # Handle quoted phrases
        phrases = re.findall(r'"([^"]+)"', query)
        for phrase in phrases:
            # Replace spaces with <-> for phrase search
            phrase_query = '<->'.join(phrase.split())
            query = query.replace(f'"{phrase}"', phrase_query)
        
        # Replace boolean operators (case insensitive)
        query = re.sub(r'\bAND\b', '&', query, flags=re.IGNORECASE)
        query = re.sub(r'\bOR\b', '|', query, flags=re.IGNORECASE)
        query = re.sub(r'\bNOT\b', '!', query, flags=re.IGNORECASE)
        
        # Remove extra spaces
        query = ' '.join(query.split())
        
        # If no operators, connect words with &
        if '&' not in query and '|' not in query and '!' not in query:
            words = query.split()
            query = ' & '.join(words)
        
        return query
    
    def _format_candidate_results(self, candidates: List[Candidate]) -> List[Dict[str, Any]]:
        """
        Format candidate objects into result dictionaries.
        
        Args:
            candidates: List of Candidate model objects
            
        Returns:
            List of formatted candidate dictionaries
        """
        results = []
        for candidate in candidates:
            # Calculate experience years
            total_experience = 0
            for exp in candidate.work_experience:
                if exp.start_date:
                    if exp.end_date:
                        years = (exp.end_date - exp.start_date).days / 365.25
                    else:
                        years = (datetime.now().date() - exp.start_date).days / 365.25
                    total_experience += max(0, years)
            
            # Get education level
            education_level = None
            if candidate.education:
                education_level = candidate.education[0].degree
            
            # Get skills list
            skills_list = [skill.name for skill in candidate.skills]
            
            # Get latest resume status
            status = "New"
            if candidate.resumes:
                latest_resume = sorted(candidate.resumes, key=lambda r: r.uploaded_at, reverse=True)[0]
                status = latest_resume.upload_status
            
            results.append({
                "id": candidate.id,
                "name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone_number,
                "linkedin": candidate.linkedin_url,
                "skills": skills_list,
                "experience_years": round(total_experience, 1),
                "education": education_level,
                "status": status,
                "resume_count": len(candidate.resumes),
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None
            })
        
        return results
