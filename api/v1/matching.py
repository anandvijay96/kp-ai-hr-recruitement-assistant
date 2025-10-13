"""
Resume-Job Matching API Endpoints
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.database import Resume, Job, ResumeJobMatch, CandidateSkill, JobSkill
from services.resume_job_matcher import get_matcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/match-resume/{resume_id}")
async def match_resume_to_all_jobs(
    resume_id: str,
    min_score: int = Query(default=0, ge=0, le=100),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Match a single resume to all active jobs.
    
    Args:
        resume_id: Resume ID to match
        min_score: Minimum match score to return (0-100)
        limit: Maximum number of matches to return
    
    Returns:
        List of job matches with scores
    """
    try:
        # Get resume with related data
        stmt = select(Resume).options(
            selectinload(Resume.candidate).selectinload('skills')
        ).filter(Resume.id == resume_id)
        
        result = await db.execute(stmt)
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Get all active jobs
        jobs_stmt = select(Job).options(
            selectinload('skills')
        ).filter(Job.status == 'open')
        
        jobs_result = await db.execute(jobs_stmt)
        jobs = jobs_result.scalars().all()
        
        if not jobs:
            return {
                "resume_id": resume_id,
                "total_jobs": 0,
                "matches": [],
                "message": "No active jobs found"
            }
        
        # Prepare resume data
        resume_data = {
            'skills': [{'name': cs.skill.name} for cs in resume.candidate.skills if cs.skill] if resume.candidate and resume.candidate.skills else [],
            'work_experience': resume.candidate.work_experience if resume.candidate else [],
            'education': resume.candidate.education if resume.candidate else [],
            'parsed_data': resume.parsed_data or {}
        }
        
        # Match against each job
        matcher = get_matcher()
        matches = []
        
        for job in jobs:
            # Prepare job data
            job_data = {
                'skills': [{'name': js.skill.name, 'is_mandatory': js.is_mandatory} for js in job.skills if hasattr(job, 'skills')] if hasattr(job, 'skills') else [],
                'required_experience_years': 0,  # TODO: Extract from job description
                'education_requirement': job.education_requirement
            }
            
            # Calculate match
            match_result = matcher.match_resume_to_job(resume_data, job_data)
            
            if match_result['match_score'] >= min_score:
                matches.append({
                    'job_id': job.id,
                    'job_title': job.title,
                    'job_department': job.department,
                    'job_location': f"{job.location_city}, {job.location_state}" if job.location_city else None,
                    'match_score': match_result['match_score'],
                    'skill_score': match_result['skill_score'],
                    'experience_score': match_result['experience_score'],
                    'education_score': match_result['education_score'],
                    'matched_skills': match_result['matched_skills'],
                    'missing_skills': match_result['missing_skills']
                })
        
        # Sort by match score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Limit results
        matches = matches[:limit]
        
        # Store matches in database
        for match in matches:
            # Check if match already exists
            existing_stmt = select(ResumeJobMatch).filter(
                and_(
                    ResumeJobMatch.resume_id == resume_id,
                    ResumeJobMatch.job_id == match['job_id']
                )
            )
            existing_result = await db.execute(existing_stmt)
            existing_match = existing_result.scalar_one_or_none()
            
            if existing_match:
                # Update existing match
                existing_match.match_score = match['match_score']
                existing_match.skill_score = match['skill_score']
                existing_match.experience_score = match['experience_score']
                existing_match.education_score = match['education_score']
                existing_match.matched_skills = match['matched_skills']
                existing_match.missing_skills = match['missing_skills']
            else:
                # Create new match
                new_match = ResumeJobMatch(
                    resume_id=resume_id,
                    job_id=match['job_id'],
                    match_score=match['match_score'],
                    skill_score=match['skill_score'],
                    experience_score=match['experience_score'],
                    education_score=match['education_score'],
                    matched_skills=match['matched_skills'],
                    missing_skills=match['missing_skills']
                )
                db.add(new_match)
        
        await db.commit()
        
        return {
            "resume_id": resume_id,
            "total_jobs": len(jobs),
            "matches_found": len(matches),
            "matches": matches
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to match resume: {str(e)}")


@router.post("/match-job/{job_id}")
async def match_job_to_all_resumes(
    job_id: str,
    min_score: int = Query(default=50, ge=0, le=100),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Match a single job to all resumes.
    
    Args:
        job_id: Job ID to match
        min_score: Minimum match score to return (default 50)
        limit: Maximum number of matches to return
    
    Returns:
        List of resume matches with scores
    """
    try:
        # Get job with related data
        stmt = select(Job).options(
            selectinload('skills')
        ).filter(Job.id == job_id)
        
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get all resumes
        resumes_stmt = select(Resume).options(
            selectinload(Resume.candidate).selectinload('skills'),
            selectinload(Resume.candidate).selectinload('work_experience'),
            selectinload(Resume.candidate).selectinload('education')
        ).filter(Resume.status == 'processed')
        
        resumes_result = await db.execute(resumes_stmt)
        resumes = resumes_result.scalars().all()
        
        if not resumes:
            return {
                "job_id": job_id,
                "total_resumes": 0,
                "matches": [],
                "message": "No processed resumes found"
            }
        
        # Prepare job data
        job_data = {
            'skills': [{'name': js.skill.name, 'is_mandatory': js.is_mandatory} for js in job.skills if hasattr(job, 'skills')] if hasattr(job, 'skills') else [],
            'required_experience_years': 0,  # TODO: Extract from job description
            'education_requirement': job.education_requirement
        }
        
        # Match against each resume
        matcher = get_matcher()
        matches = []
        
        for resume in resumes:
            if not resume.candidate:
                continue
            
            # Prepare resume data
            resume_data = {
                'skills': [{'name': cs.skill.name} for cs in resume.candidate.skills if cs.skill] if resume.candidate.skills else [],
                'work_experience': resume.candidate.work_experience or [],
                'education': resume.candidate.education or [],
                'parsed_data': resume.parsed_data or {}
            }
            
            # Calculate match
            match_result = matcher.match_resume_to_job(resume_data, job_data)
            
            if match_result['match_score'] >= min_score:
                matches.append({
                    'resume_id': resume.id,
                    'candidate_id': resume.candidate.id,
                    'candidate_name': resume.candidate.full_name,
                    'candidate_email': resume.candidate.email,
                    'match_score': match_result['match_score'],
                    'skill_score': match_result['skill_score'],
                    'experience_score': match_result['experience_score'],
                    'education_score': match_result['education_score'],
                    'matched_skills': match_result['matched_skills'],
                    'missing_skills': match_result['missing_skills']
                })
        
        # Sort by match score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Limit results
        matches = matches[:limit]
        
        # Store matches in database
        for match in matches:
            # Check if match already exists
            existing_stmt = select(ResumeJobMatch).filter(
                and_(
                    ResumeJobMatch.resume_id == match['resume_id'],
                    ResumeJobMatch.job_id == job_id
                )
            )
            existing_result = await db.execute(existing_stmt)
            existing_match = existing_result.scalar_one_or_none()
            
            if existing_match:
                # Update existing match
                existing_match.match_score = match['match_score']
                existing_match.skill_score = match['skill_score']
                existing_match.experience_score = match['experience_score']
                existing_match.education_score = match['education_score']
                existing_match.matched_skills = match['matched_skills']
                existing_match.missing_skills = match['missing_skills']
            else:
                # Create new match
                new_match = ResumeJobMatch(
                    resume_id=match['resume_id'],
                    job_id=job_id,
                    match_score=match['match_score'],
                    skill_score=match['skill_score'],
                    experience_score=match['experience_score'],
                    education_score=match['education_score'],
                    matched_skills=match['matched_skills'],
                    missing_skills=match['missing_skills']
                )
                db.add(new_match)
        
        await db.commit()
        
        return {
            "job_id": job_id,
            "job_title": job.title,
            "total_resumes": len(resumes),
            "matches_found": len(matches),
            "matches": matches
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to match job: {str(e)}")


@router.get("/resume/{resume_id}/matches")
async def get_resume_matches(
    resume_id: str,
    min_score: int = Query(default=0, ge=0, le=100),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get stored matches for a resume"""
    try:
        stmt = select(ResumeJobMatch).options(
            selectinload(ResumeJobMatch.job)
        ).filter(
            and_(
                ResumeJobMatch.resume_id == resume_id,
                ResumeJobMatch.match_score >= min_score
            )
        ).order_by(ResumeJobMatch.match_score.desc()).limit(limit)
        
        result = await db.execute(stmt)
        matches = result.scalars().all()
        
        return {
            "resume_id": resume_id,
            "total_matches": len(matches),
            "matches": [{
                "job_id": m.job_id,
                "job_title": m.job.title if m.job else None,
                "match_score": m.match_score,
                "skill_score": m.skill_score,
                "experience_score": m.experience_score,
                "education_score": m.education_score,
                "matched_skills": m.matched_skills,
                "missing_skills": m.missing_skills,
                "created_at": m.created_at.isoformat() if m.created_at else None
            } for m in matches]
        }
    except Exception as e:
        logger.error(f"Error getting matches for resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}/matches")
async def get_job_matches(
    job_id: str,
    min_score: int = Query(default=50, ge=0, le=100),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get stored matches for a job"""
    try:
        stmt = select(ResumeJobMatch).options(
            selectinload(ResumeJobMatch.resume).selectinload(Resume.candidate)
        ).filter(
            and_(
                ResumeJobMatch.job_id == job_id,
                ResumeJobMatch.match_score >= min_score
            )
        ).order_by(ResumeJobMatch.match_score.desc()).limit(limit)
        
        result = await db.execute(stmt)
        matches = result.scalars().all()
        
        return {
            "job_id": job_id,
            "total_matches": len(matches),
            "matches": [{
                "resume_id": m.resume_id,
                "candidate_id": m.resume.candidate.id if m.resume and m.resume.candidate else None,
                "candidate_name": m.resume.candidate.full_name if m.resume and m.resume.candidate else None,
                "candidate_email": m.resume.candidate.email if m.resume and m.resume.candidate else None,
                "match_score": m.match_score,
                "skill_score": m.skill_score,
                "experience_score": m.experience_score,
                "education_score": m.education_score,
                "matched_skills": m.matched_skills,
                "missing_skills": m.missing_skills,
                "created_at": m.created_at.isoformat() if m.created_at else None
            } for m in matches]
        }
    except Exception as e:
        logger.error(f"Error getting matches for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
