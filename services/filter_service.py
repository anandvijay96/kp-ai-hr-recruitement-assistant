from models.filter_models import CandidateFilter
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, extract
from models.db import Candidate, Resume, Skill, Education, WorkExperience
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FilterService:
    """Service for filtering and searching candidates using database queries"""
    
    def search_candidates(self, filters: CandidateFilter, db: Session, 
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
            # Base query with eager loading
            query = db.query(Candidate).options(
                joinedload(Candidate.resumes),
                joinedload(Candidate.skills),
                joinedload(Candidate.education),
                joinedload(Candidate.work_experience)
            )
            
            # Filter by skills (if any match)
            if filters.skills:
                query = query.join(Candidate.skills).filter(
                    Skill.name.in_([skill.lower() for skill in filters.skills])
                ).distinct()
            
            # Filter by experience years (calculate from work_experience)
            if filters.min_experience is not None or filters.max_experience is not None:
                # Subquery to calculate total experience
                exp_subquery = (
                    db.query(
                        WorkExperience.candidate_id,
                        func.sum(
                            func.coalesce(
                                extract('year', WorkExperience.end_date) - extract('year', WorkExperience.start_date),
                                extract('year', func.now()) - extract('year', WorkExperience.start_date)
                            )
                        ).label('total_years')
                    )
                    .group_by(WorkExperience.candidate_id)
                    .subquery()
                )
                
                query = query.outerjoin(exp_subquery, Candidate.id == exp_subquery.c.candidate_id)
                
                if filters.min_experience is not None:
                    query = query.filter(
                        func.coalesce(exp_subquery.c.total_years, 0) >= filters.min_experience
                    )
                if filters.max_experience is not None:
                    query = query.filter(
                        func.coalesce(exp_subquery.c.total_years, 999) <= filters.max_experience
                    )
            
            # Filter by education level
            if filters.education:
                query = query.join(Candidate.education).filter(
                    Education.degree.in_(filters.education)
                ).distinct()
            
            # Filter by location (search in work_experience or candidate data if available)
            if filters.location:
                # For now, filter by work experience location
                # In future, could add location field to Candidate model
                query = query.join(Candidate.work_experience).filter(
                    WorkExperience.location.ilike(f"%{filters.location}%")
                ).distinct()
            
            # Filter by status (from resume table)
            if filters.status:
                query = query.join(Candidate.resumes).filter(
                    Resume.upload_status.in_(filters.status)
                ).distinct()
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            candidates = query.offset(offset).limit(page_size).all()
            
            # Format results
            results = []
            for candidate in candidates:
                # Calculate experience years
                total_experience = 0
                for exp in candidate.work_experience:
                    if exp.end_date:
                        years = (exp.end_date - exp.start_date).days / 365.25
                    else:
                        years = (datetime.now() - exp.start_date).days / 365.25
                    total_experience += years
                
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
    
    def get_filter_options(self, db: Session) -> Dict[str, List]:
        """
        Retrieves distinct values for filter options from the database.
        
        Args:
            db: Database session
            
        Returns:
            Dict with available filter options
        """
        try:
            # Get distinct skills
            skills = db.query(Skill.name).distinct().order_by(Skill.name).all()
            skills_list = [skill[0] for skill in skills]
            
            # Get distinct education levels
            education_levels = db.query(Education.degree).distinct().order_by(Education.degree).all()
            education_list = [edu[0] for edu in education_levels if edu[0]]
            
            # Get distinct locations from work experience
            locations = db.query(WorkExperience.location).distinct().filter(
                WorkExperience.location.isnot(None)
            ).order_by(WorkExperience.location).all()
            location_list = [loc[0] for loc in locations if loc[0]]
            
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
