from models.filter_models import CandidateFilter
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, or_, and_, extract, text
from sqlalchemy.dialects.postgresql import TSVECTOR
from models.database import Candidate, Resume, CandidateSkill, Skill, Education, WorkExperience
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class FilterService:
    """Service for filtering and searching candidates using database queries"""
    
    async def full_text_search(self, query: str, db: AsyncSession, 
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Perform full-text search across candidates using basic LIKE search.
        
        Args:
            query: Search query string
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of results per page
            
        Returns:
            Dict with results and pagination info
        """
        try:
            # Use basic LIKE search
            search_term = f"%{query}%"
            stmt = select(Candidate).filter(
                or_(
                    Candidate.full_name.ilike(search_term),
                    Candidate.email.ilike(search_term),
                    Candidate.location.ilike(search_term)
                )
            ).distinct()
            
            # Get total count
            count_stmt = select(func.count(Candidate.id)).filter(
                or_(
                    Candidate.full_name.ilike(search_term),
                    Candidate.email.ilike(search_term),
                    Candidate.location.ilike(search_term)
                )
            )
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
            logger.exception(e)
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
            # Build base query with relationships preloaded for filtering
            stmt = select(Candidate)
            
            # Track if we need joins
            needs_skill_join = False
            needs_education_join = False
            needs_experience_join = False
            
            # Apply filters
            filter_conditions = []
            
            # Filter by search query (name, email, location)
            if filters.search_query:
                search_term = f"%{filters.search_query}%"
                filter_conditions.append(
                    or_(
                        Candidate.full_name.ilike(search_term),
                        Candidate.email.ilike(search_term),
                        Candidate.location.ilike(search_term)
                    )
                )
            
            # Filter by location (exact or partial match)
            if filters.location:
                # Handle both string and list
                if isinstance(filters.location, list):
                    location_conditions = []
                    for loc in filters.location:
                        if loc:
                            location_conditions.append(Candidate.location.ilike(f"%{loc}%"))
                    if location_conditions:
                        filter_conditions.append(or_(*location_conditions))
                else:
                    filter_conditions.append(Candidate.location.ilike(f"%{filters.location}%"))
            
            # Filter by status
            if filters.status:
                # Handle both string and list
                if isinstance(filters.status, list):
                    filter_conditions.append(Candidate.status.in_(filters.status))
                else:
                    filter_conditions.append(Candidate.status == filters.status)
            
            # Filter by skills (match ANY of the selected skills)
            if filters.skills and len(filters.skills) > 0:
                needs_skill_join = True
                stmt = stmt.join(CandidateSkill, Candidate.id == CandidateSkill.candidate_id)
                stmt = stmt.join(Skill, CandidateSkill.skill_id == Skill.id)
                filter_conditions.append(Skill.name.in_(filters.skills))
                logger.info(f"Filtering by skills: {filters.skills}")
            
            # Filter by education level
            if filters.education and len(filters.education) > 0:
                needs_education_join = True
                if not needs_skill_join:  # Avoid duplicate candidate selection
                    stmt = stmt.join(Education, Candidate.id == Education.candidate_id)
                else:
                    stmt = stmt.outerjoin(Education, Candidate.id == Education.candidate_id)
                filter_conditions.append(Education.degree.in_(filters.education))
                logger.info(f"Filtering by education: {filters.education}")
            
            # Filter by experience range (in months)
            if filters.min_experience is not None or filters.max_experience is not None:
                needs_experience_join = True
                # Subquery to calculate total experience per candidate
                exp_subquery = (
                    select(
                        WorkExperience.candidate_id,
                        func.sum(WorkExperience.duration_months).label('total_months')
                    )
                    .group_by(WorkExperience.candidate_id)
                    .subquery()
                )
                
                # FIXED: Properly join with explicit ON condition to avoid cartesian product
                if needs_skill_join or needs_education_join:
                    # Already have joins, use outerjoin
                    stmt = stmt.outerjoin(exp_subquery, Candidate.id == exp_subquery.c.candidate_id)
                else:
                    # First join, use regular join
                    stmt = stmt.join(exp_subquery, Candidate.id == exp_subquery.c.candidate_id, isouter=True)
                
                if filters.min_experience is not None:
                    min_months = filters.min_experience * 12
                    filter_conditions.append(
                        or_(
                            exp_subquery.c.total_months >= min_months,
                            exp_subquery.c.total_months.is_(None)  # Include candidates with no experience data
                        )
                    )
                    logger.info(f"Filtering by min experience: {filters.min_experience} years ({min_months} months)")
                
                if filters.max_experience is not None:
                    max_months = filters.max_experience * 12
                    filter_conditions.append(
                        or_(
                            exp_subquery.c.total_months <= max_months,
                            exp_subquery.c.total_months.is_(None)  # Include candidates with no experience data
                        )
                    )
                    logger.info(f"Filtering by max experience: {filters.max_experience} years ({max_months} months)")
            
            # Apply all filter conditions
            if filter_conditions:
                stmt = stmt.filter(and_(*filter_conditions))
            
            stmt = stmt.distinct()
            
            # Get total count before pagination
            count_stmt = select(func.count(Candidate.id)).select_from(Candidate)
            if filter_conditions:
                count_stmt = count_stmt.filter(and_(*filter_conditions))
            count_result = await db.execute(count_stmt)
            total_count = count_result.scalar() or 0
            
            # Apply pagination and eager load relationships
            offset = (page - 1) * page_size
            stmt = stmt.options(
                selectinload(Candidate.skills).selectinload(CandidateSkill.skill),
                selectinload(Candidate.education),
                selectinload(Candidate.work_experience)
            ).offset(offset).limit(page_size)
            result = await db.execute(stmt)
            candidates = result.scalars().unique().all()
            
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
                    "search_query": filters.search_query,
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
            logger.exception(e)
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
            # Get distinct skills from skills table
            skills_stmt = select(Skill.name).distinct().order_by(Skill.name)
            skills_result = await db.execute(skills_stmt)
            skills_list = [skill[0] for skill in skills_result.all() if skill[0]]
            
            # Get distinct education levels from education table
            edu_stmt = select(Education.degree).distinct().filter(
                Education.degree.isnot(None)
            ).order_by(Education.degree)
            edu_result = await db.execute(edu_stmt)
            education_list = [edu[0] for edu in edu_result.all() if edu[0]]
            
            # Get distinct locations from candidates
            loc_stmt = select(Candidate.location).distinct().filter(
                Candidate.location.isnot(None)
            ).order_by(Candidate.location)
            loc_result = await db.execute(loc_stmt)
            location_list = [loc[0] for loc in loc_result.all() if loc[0]]
            
            # Get available statuses from Candidate model
            status_stmt = select(Candidate.status).distinct().filter(
                Candidate.status.isnot(None)
            ).order_by(Candidate.status)
            status_result = await db.execute(status_stmt)
            status_list = [status[0] for status in status_result.all() if status[0]]
            
            # If no statuses in DB, use defaults
            if not status_list:
                status_list = ["new", "screened", "interviewed", "rejected", "hired"]
            
            # If no skills in DB, use fallback
            if not skills_list:
                skills_list = ["Python", "Java", "JavaScript", "SQL", "React", "Node.js", "AWS", "Docker"]
            
            # If no education in DB, use fallback
            if not education_list:
                education_list = ["High School", "Bachelor's", "Master's", "PhD"]
            
            return {
                "skills": skills_list,
                "locations": location_list if location_list else [],
                "education_levels": education_list,
                "statuses": status_list
            }
            
        except Exception as e:
            logger.error(f"Error getting filter options: {str(e)}")
            logger.exception(e)
            # Return default options on error
            return {
                "skills": ["Python", "Java", "JavaScript", "SQL", "React", "Node.js"],
                "locations": [],
                "education_levels": ["High School", "Bachelor's", "Master's", "PhD"],
                "statuses": ["new", "screened", "interviewed", "rejected", "hired"]
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
            # Skip invalid candidates
            if not candidate.full_name or not candidate.email:
                continue
            if '@' not in candidate.email:
                continue
            
            # Get skills list (from candidate_skills relationship)
            skills_list = []
            try:
                if hasattr(candidate, 'skills') and candidate.skills:
                    skills_list = [cs.skill.name for cs in candidate.skills if cs.skill] 
            except Exception as e:
                logger.debug(f"Error loading skills for candidate {candidate.id}: {e}")
            
            # Calculate total experience years
            experience_years = 0
            try:
                if hasattr(candidate, 'work_experience') and candidate.work_experience:
                    total_months = sum(exp.duration_months or 0 for exp in candidate.work_experience)
                    experience_years = round(total_months / 12, 1) if total_months > 0 else 0
            except Exception as e:
                logger.debug(f"Error calculating experience for candidate {candidate.id}: {e}")
            
            # Get highest education level
            education = "N/A"
            try:
                if hasattr(candidate, 'education') and candidate.education:
                    # Get the highest or most recent education
                    edu_records = candidate.education
                    if edu_records:
                        education = edu_records[0].degree or "N/A"
            except Exception as e:
                logger.debug(f"Error loading education for candidate {candidate.id}: {e}")
            
            results.append({
                "id": candidate.id,
                "name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone or "N/A",
                "linkedin": candidate.linkedin_url or "",
                "skills": skills_list,
                "experience_years": experience_years,
                "education": education,
                "status": candidate.status or "new",
                "location": candidate.location or "N/A",
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None
            })
        
        return results
