"""
Resume-Job Matching Service
Matches resumes to job postings based on skills, experience, and education
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ResumeJobMatcher:
    """Service for matching resumes to job postings"""
    
    def __init__(
        self,
        skill_weight: float = 0.5,
        experience_weight: float = 0.3,
        education_weight: float = 0.2
    ):
        """
        Initialize matcher with scoring weights.
        
        Args:
            skill_weight: Weight for skill matching (default 50%)
            experience_weight: Weight for experience matching (default 30%)
            education_weight: Weight for education matching (default 20%)
        """
        # Validate weights sum to 1.0
        total = skill_weight + experience_weight + education_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        
        self.skill_weight = skill_weight
        self.experience_weight = experience_weight
        self.education_weight = education_weight
    
    def match_resume_to_job(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Match a single resume to a single job.
        
        Args:
            resume_data: Dict with keys: skills, work_experience, education, parsed_data
            job_data: Dict with keys: skills, required_experience_years, education_requirement
        
        Returns:
            Dict with match_score, skill_score, experience_score, education_score,
            matched_skills, missing_skills, match_details
        """
        try:
            # Calculate individual scores
            skill_result = self._match_skills(resume_data, job_data)
            experience_result = self._match_experience(resume_data, job_data)
            education_result = self._match_education(resume_data, job_data)
            
            # Calculate weighted composite score
            match_score = int(
                skill_result['score'] * self.skill_weight +
                experience_result['score'] * self.experience_weight +
                education_result['score'] * self.education_weight
            )
            
            return {
                'match_score': max(0, min(100, match_score)),  # Clamp to 0-100
                'skill_score': skill_result['score'],
                'experience_score': experience_result['score'],
                'education_score': education_result['score'],
                'matched_skills': skill_result['matched'],
                'missing_skills': skill_result['missing'],
                'match_details': {
                    'skill_details': skill_result['details'],
                    'experience_details': experience_result['details'],
                    'education_details': education_result['details'],
                    'weights': {
                        'skill': self.skill_weight,
                        'experience': self.experience_weight,
                        'education': self.education_weight
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error matching resume to job: {e}")
            return {
                'match_score': 0,
                'skill_score': 0,
                'experience_score': 0,
                'education_score': 0,
                'matched_skills': [],
                'missing_skills': [],
                'match_details': {'error': str(e)}
            }
    
    def _match_skills(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Match skills between resume and job.
        
        Returns:
            Dict with score (0-100), matched skills, missing skills, details
        """
        # Extract skills from resume
        resume_skills = set()
        if 'skills' in resume_data and resume_data['skills']:
            for skill in resume_data['skills']:
                if isinstance(skill, dict):
                    resume_skills.add(skill.get('name', '').lower().strip())
                elif isinstance(skill, str):
                    resume_skills.add(skill.lower().strip())
        
        # Extract required skills from job
        job_skills = set()
        mandatory_skills = set()
        
        if 'skills' in job_data and job_data['skills']:
            for skill in job_data['skills']:
                if isinstance(skill, dict):
                    skill_name = skill.get('name', '').lower().strip()
                    job_skills.add(skill_name)
                    if skill.get('is_mandatory', False):
                        mandatory_skills.add(skill_name)
                elif isinstance(skill, str):
                    job_skills.add(skill.lower().strip())
        
        # Remove empty strings
        resume_skills = {s for s in resume_skills if s}
        job_skills = {s for s in job_skills if s}
        mandatory_skills = {s for s in mandatory_skills if s}
        
        # Calculate matches
        matched_skills = resume_skills & job_skills
        missing_skills = job_skills - resume_skills
        missing_mandatory = mandatory_skills - resume_skills
        
        # Calculate score
        if not job_skills:
            score = 50  # No requirements, give neutral score
        else:
            # Base score from overall match percentage
            base_score = (len(matched_skills) / len(job_skills)) * 100
            
            # Penalty for missing mandatory skills
            if mandatory_skills:
                mandatory_match = len(mandatory_skills & resume_skills) / len(mandatory_skills)
                # Mandatory skills are critical - weight them heavily
                score = (base_score * 0.4) + (mandatory_match * 100 * 0.6)
            else:
                score = base_score
        
        return {
            'score': int(max(0, min(100, score))),
            'matched': list(matched_skills),
            'missing': list(missing_skills),
            'details': {
                'total_job_skills': len(job_skills),
                'total_resume_skills': len(resume_skills),
                'matched_count': len(matched_skills),
                'missing_count': len(missing_skills),
                'mandatory_skills': list(mandatory_skills),
                'missing_mandatory': list(missing_mandatory),
                'match_percentage': round((len(matched_skills) / len(job_skills) * 100) if job_skills else 0, 2)
            }
        }
    
    def _match_experience(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Match experience level between resume and job.
        
        Returns:
            Dict with score (0-100) and details
        """
        # Calculate total years of experience from resume
        total_months = 0
        experience_count = 0
        
        if 'work_experience' in resume_data and resume_data['work_experience']:
            for exp in resume_data['work_experience']:
                if isinstance(exp, dict):
                    duration = exp.get('duration_months', 0)
                    if duration:
                        total_months += duration
                        experience_count += 1
                    else:
                        # Try to calculate from dates
                        start = exp.get('start_date')
                        end = exp.get('end_date') or 'Present'
                        if start:
                            months = self._calculate_months_from_dates(start, end)
                            if months:
                                total_months += months
                                experience_count += 1
        
        resume_years = total_months / 12 if total_months > 0 else 0
        
        # Get required experience from job
        required_years = 0
        if 'required_experience_years' in job_data:
            required_years = job_data['required_experience_years'] or 0
        elif 'experience_required' in job_data:
            # Try to extract years from text
            exp_text = str(job_data['experience_required'])
            years_match = re.search(r'(\d+)\+?\s*years?', exp_text, re.IGNORECASE)
            if years_match:
                required_years = int(years_match.group(1))
        
        # Calculate score
        if required_years == 0:
            score = 50  # No requirement, neutral score
        elif resume_years >= required_years:
            # Has enough experience - score based on how much more
            excess = resume_years - required_years
            if excess <= 2:
                score = 100  # Perfect match
            elif excess <= 5:
                score = 95  # Slightly overqualified
            else:
                score = 85  # Significantly overqualified (might be flight risk)
        else:
            # Doesn't meet requirement - score based on how close
            shortfall = required_years - resume_years
            if shortfall <= 1:
                score = 80  # Close enough
            elif shortfall <= 2:
                score = 60  # Somewhat short
            elif shortfall <= 3:
                score = 40  # Significantly short
            else:
                score = 20  # Far from requirement
        
        return {
            'score': int(max(0, min(100, score))),
            'details': {
                'resume_years': round(resume_years, 1),
                'required_years': required_years,
                'experience_count': experience_count,
                'meets_requirement': resume_years >= required_years,
                'shortfall_years': max(0, round(required_years - resume_years, 1))
            }
        }
    
    def _match_education(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Match education level between resume and job.
        
        Returns:
            Dict with score (0-100) and details
        """
        # Education level hierarchy
        education_levels = {
            'phd': 5,
            'doctorate': 5,
            'masters': 4,
            'master': 4,
            'mba': 4,
            'bachelors': 3,
            'bachelor': 3,
            'b.tech': 3,
            'b.e': 3,
            'b.sc': 3,
            'associate': 2,
            'diploma': 1,
            'high school': 0,
            'secondary': 0
        }
        
        # Get highest education from resume
        resume_level = 0
        resume_degree = 'None'
        
        if 'education' in resume_data and resume_data['education']:
            for edu in resume_data['education']:
                if isinstance(edu, dict):
                    degree = str(edu.get('degree', '')).lower()
                    for key, level in education_levels.items():
                        if key in degree:
                            if level > resume_level:
                                resume_level = level
                                resume_degree = edu.get('degree', 'Unknown')
                            break
        
        # Get required education from job
        required_level = 0
        required_degree = 'None'
        
        if 'education_requirement' in job_data and job_data['education_requirement']:
            req_text = str(job_data['education_requirement']).lower()
            for key, level in education_levels.items():
                if key in req_text:
                    if level > required_level:
                        required_level = level
                        required_degree = key.title()
                    break
        
        # Calculate score
        if required_level == 0:
            score = 50  # No requirement, neutral score
        elif resume_level >= required_level:
            # Meets or exceeds requirement
            if resume_level == required_level:
                score = 100  # Perfect match
            elif resume_level == required_level + 1:
                score = 95  # One level higher
            else:
                score = 85  # Significantly overqualified
        else:
            # Doesn't meet requirement
            shortfall = required_level - resume_level
            if shortfall == 1:
                score = 60  # One level short
            elif shortfall == 2:
                score = 30  # Two levels short
            else:
                score = 10  # Significantly under-qualified
        
        return {
            'score': int(max(0, min(100, score))),
            'details': {
                'resume_degree': resume_degree,
                'resume_level': resume_level,
                'required_degree': required_degree,
                'required_level': required_level,
                'meets_requirement': resume_level >= required_level
            }
        }
    
    def _calculate_months_from_dates(self, start_date: str, end_date: str) -> Optional[int]:
        """
        Calculate months between two date strings.
        
        Args:
            start_date: Start date (various formats supported)
            end_date: End date or 'Present'
        
        Returns:
            Number of months or None if calculation fails
        """
        try:
            from dateutil import parser as date_parser
            
            # Parse start date
            start = date_parser.parse(start_date, fuzzy=True)
            
            # Parse end date
            if end_date.lower() in ['present', 'current', 'now']:
                end = datetime.now()
            else:
                end = date_parser.parse(end_date, fuzzy=True)
            
            # Calculate months
            months = (end.year - start.year) * 12 + (end.month - start.month)
            return max(0, months)
        except Exception as e:
            logger.warning(f"Failed to calculate months from dates: {start_date} to {end_date}: {e}")
            return None


# Singleton instance
_matcher_instance = None


def get_matcher() -> ResumeJobMatcher:
    """Get or create singleton matcher instance"""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = ResumeJobMatcher()
    return _matcher_instance
