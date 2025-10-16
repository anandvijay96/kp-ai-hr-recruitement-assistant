from fastapi import APIRouter, Depends, Body, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
import io
import logging

from core.database import get_db
from services.filter_service import FilterService
from services.preset_service import PresetService
from services.candidate_service import CandidateService
from services.export_service import ExportService
from services.jd_matcher import JDMatcher
from models.filter_models import CandidateFilter, FilterPresetCreate, FilterPresetResponse
from models.database import Candidate, Job, Resume

logger = logging.getLogger(__name__)

router = APIRouter()

# Services that don't need database session can be instantiated globally
filter_service = FilterService()
preset_service = PresetService()
export_service = ExportService()

# CandidateService needs database session - instantiate in endpoints via dependency injection

@router.post("/search")
async def search_candidates(filters: CandidateFilter, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Searches and filters candidates using database queries.
    If search_query is provided, uses full-text search with optional filters.
    """
    # If search_query is provided, use full-text search
    if filters.search_query:
        return await filter_service.full_text_search(filters.search_query, db, page, page_size)
    
    # Otherwise use traditional filtering
    return await filter_service.search_candidates(filters, db, page, page_size)

@router.get("/full-text-search")
async def full_text_search(q: str, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Perform full-text search across all candidate data.
    
    Supports:
    - Simple search: "Python developer"
    - Boolean AND: "Python AND React"
    - Boolean OR: "Java OR Kotlin"
    - Boolean NOT: "Python NOT Junior"
    - Phrase search: "senior software engineer"
    - Complex: "(Python OR Java) AND React NOT PHP"
    """
    return await filter_service.full_text_search(q, db, page, page_size)

@router.get("/filter-options")
async def get_filter_options(db: Session = Depends(get_db)) -> Dict[str, List]:
    """Retrieves available options for filters from the database."""
    return await filter_service.get_filter_options(db)

@router.post("/filter-presets", response_model=FilterPresetResponse)
def create_filter_preset(preset_data: FilterPresetCreate, user_id: int = 1) -> FilterPresetResponse: # Assuming user_id=1 for demo
    """Saves a new filter preset."""
    return preset_service.create_preset(user_id, preset_data)

@router.get("/filter-presets", response_model=List[FilterPresetResponse])
def get_filter_presets(user_id: int = 1) -> List[FilterPresetResponse]: # Assuming user_id=1 for demo
    """Retrieves all saved filter presets for the user."""
    return preset_service.get_presets_for_user(user_id)

@router.get("/")
def get_all_candidates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all candidates with pagination."""
    candidates = candidate_service.get_all_candidates(db, skip, limit)
    return {"candidates": candidates, "total": len(candidates)}

@router.put("/{candidate_id}")
async def update_candidate(candidate_id: str, updates: dict, db: Session = Depends(get_db)):
    """Update candidate profile with all related data."""
    from sqlalchemy import select, delete
    from sqlalchemy.orm import selectinload
    from models.database import Candidate, CandidateSkill, Skill, Education, WorkExperience, Certification
    
    try:
        # Get candidate
        stmt = select(Candidate).filter(Candidate.id == candidate_id)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Update personal info
        personal_info = updates.get('personal_info', {})
        if personal_info:
            candidate.full_name = personal_info.get('full_name', candidate.full_name)
            candidate.email = personal_info.get('email', candidate.email)
            candidate.phone = personal_info.get('phone', candidate.phone)
            candidate.linkedin_url = personal_info.get('linkedin_url', candidate.linkedin_url)
            candidate.location = personal_info.get('location', candidate.location)
            candidate.professional_summary = personal_info.get('professional_summary', candidate.professional_summary)
        
        # Update skills - delete all and recreate
        if 'skills' in updates:
            # Delete existing skills
            await db.execute(delete(CandidateSkill).where(CandidateSkill.candidate_id == candidate_id))
            
            # Add new skills
            for skill_data in updates['skills']:
                skill_name = skill_data.get('name')
                if not skill_name:
                    continue
                
                # Get or create skill
                stmt = select(Skill).filter(Skill.name == skill_name)
                result = await db.execute(stmt)
                skill = result.scalar_one_or_none()
                
                if not skill:
                    skill = Skill(name=skill_name, category="technical")
                    db.add(skill)
                    await db.flush()
                
                # Create candidate-skill relationship
                candidate_skill = CandidateSkill(
                    candidate_id=candidate_id,
                    skill_id=skill.id,
                    proficiency=skill_data.get('proficiency', 'intermediate')
                )
                db.add(candidate_skill)
        
        # Update work experience - delete all and recreate
        if 'work_experience' in updates:
            await db.execute(delete(WorkExperience).where(WorkExperience.candidate_id == candidate_id))
            
            for exp_data in updates['work_experience']:
                if not exp_data.get('company') and not exp_data.get('title'):
                    continue
                
                # Convert date strings to date objects
                start_date = exp_data.get('start_date')
                if start_date and isinstance(start_date, str):
                    try:
                        from dateutil import parser
                        start_date = parser.parse(start_date).date()
                    except:
                        start_date = None
                
                end_date = exp_data.get('end_date')
                if end_date and isinstance(end_date, str):
                    try:
                        from dateutil import parser
                        end_date = parser.parse(end_date).date()
                    except:
                        end_date = None
                
                work_exp = WorkExperience(
                    candidate_id=candidate_id,
                    company=exp_data.get('company'),
                    title=exp_data.get('title'),
                    location=exp_data.get('location'),
                    start_date=start_date,
                    end_date=end_date if not exp_data.get('is_current') else None,
                    is_current=exp_data.get('is_current', False),
                    description=exp_data.get('description')
                )
                db.add(work_exp)
        
        # Update education - delete all and recreate
        if 'education' in updates:
            await db.execute(delete(Education).where(Education.candidate_id == candidate_id))
            
            for edu_data in updates['education']:
                if not edu_data.get('degree') and not edu_data.get('institution'):
                    continue
                
                # Convert date strings to date objects
                start_date = edu_data.get('start_date')
                if start_date and isinstance(start_date, str):
                    try:
                        from dateutil import parser
                        start_date = parser.parse(start_date).date()
                    except:
                        start_date = None
                
                end_date = edu_data.get('end_date')
                if end_date and isinstance(end_date, str):
                    try:
                        from dateutil import parser
                        end_date = parser.parse(end_date).date()
                    except:
                        end_date = None
                
                education = Education(
                    candidate_id=candidate_id,
                    degree=edu_data.get('degree'),
                    field=edu_data.get('field'),
                    institution=edu_data.get('institution'),
                    location=edu_data.get('location'),
                    start_date=start_date,
                    end_date=end_date,
                    gpa=edu_data.get('gpa')
                )
                db.add(education)
        
        # Update certifications - delete all and recreate
        if 'certifications' in updates:
            await db.execute(delete(Certification).where(Certification.candidate_id == candidate_id))
            
            for cert_data in updates['certifications']:
                if not cert_data.get('name'):
                    continue
                
                # Convert date strings to date objects
                issue_date = cert_data.get('issue_date')
                if issue_date and isinstance(issue_date, str):
                    try:
                        from dateutil import parser
                        issue_date = parser.parse(issue_date).date()
                    except:
                        issue_date = None
                
                expiry_date = cert_data.get('expiry_date')
                if expiry_date and isinstance(expiry_date, str):
                    try:
                        from dateutil import parser
                        expiry_date = parser.parse(expiry_date).date()
                    except:
                        expiry_date = None
                
                certification = Certification(
                    candidate_id=candidate_id,
                    name=cert_data.get('name'),
                    issuer=cert_data.get('issuer'),
                    issue_date=issue_date,
                    expiry_date=expiry_date,
                    credential_id=cert_data.get('credential_id')
                )
                db.add(certification)
        
        # Commit all changes
        await db.commit()
        await db.refresh(candidate)
        
        return {
            "success": True,
            "message": "Candidate updated successfully",
            "candidate_id": candidate_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating candidate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update candidate: {str(e)}")

@router.get("/{candidate_id}")
async def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Get candidate by ID with all related data."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from models.database import Candidate, CandidateSkill
    
    # Query candidate with all relationships (eager load CandidateSkill.skill)
    stmt = select(Candidate).options(
        selectinload(Candidate.resumes),
        selectinload(Candidate.skills).selectinload(CandidateSkill.skill),
        selectinload(Candidate.education),
        selectinload(Candidate.work_experience),
        selectinload(Candidate.certifications),
        selectinload(Candidate.projects),
        selectinload(Candidate.languages)
    ).filter(Candidate.id == candidate_id)
    
    result = await db.execute(stmt)
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Format response
    return {
        "id": candidate.id,
        "uuid": candidate.uuid,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "linkedin_url": candidate.linkedin_url,
        "location": candidate.location,
        "professional_summary": candidate.professional_summary,
        "source": candidate.source,
        "status": candidate.status,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
        "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
        "resumes": [{
            "id": r.id,
            "file_name": r.file_name,
            "file_path": r.file_path,
            "file_size": r.file_size,
            "file_type": r.file_type,
            "status": r.status,
            "upload_date": r.upload_date.isoformat() if r.upload_date else None,
            "authenticity_score": r.authenticity_score,
            "jd_match_score": r.jd_match_score
        } for r in candidate.resumes] if candidate.resumes else [],
        "skills": [{
            "name": cs.skill.name if cs.skill else None,
            "proficiency": cs.proficiency
        } for cs in candidate.skills if cs.skill] if candidate.skills else [],
        "education": [{
            "degree": e.degree,
            "field": e.field,
            "institution": e.institution,
            "location": e.location,
            "start_date": e.start_date,
            "end_date": e.end_date,
            "gpa": e.gpa
        } for e in candidate.education] if candidate.education else [],
        "work_experience": [{
            "company": w.company,
            "title": w.title,
            "location": w.location,
            "start_date": w.start_date,
            "end_date": w.end_date,
            "is_current": w.is_current,
            "duration_months": w.duration_months,
            "description": w.description
        } for w in candidate.work_experience] if candidate.work_experience else [],
        "certifications": [{
            "name": c.name,
            "issuer": c.issuer,
            "issue_date": c.issue_date,
            "expiry_date": c.expiry_date,
            "credential_id": c.credential_id
        } for c in candidate.certifications] if candidate.certifications else [],
        "projects": [{
            "name": p.name,
            "description": p.description,
            "technologies": p.technologies
        } for p in candidate.projects] if candidate.projects else [],
        "languages": [{
            "language": l.language,
            "proficiency": l.proficiency
        } for l in candidate.languages] if candidate.languages else []
    }

@router.post("/check-duplicate")
def check_duplicate_candidate(
    email: Optional[str] = Body(None),
    phone: Optional[str] = Body(None),
    name: Optional[str] = Body(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check if candidate already exists in the database.
    Returns duplicate detection results with confidence scores.
    """
    if not email and not phone and not name:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400, 
            detail="At least one of email, phone, or name must be provided"
        )
    
    return candidate_service.check_duplicate(email, phone, name, db)

@router.post("/export/csv")
async def export_candidates_csv(
    filters: CandidateFilter,
    include_scores: bool = True,
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Export filtered candidates to CSV format.
    
    Args:
        filters: Filter criteria (same as search endpoint)
        include_scores: Include authenticity/match scores in export
    """
    # Get filtered candidates (all results, no pagination)
    if filters.search_query:
        results = await filter_service.full_text_search(filters.search_query, db, page=1, page_size=10000)
    else:
        results = await filter_service.search_candidates(filters, db, page=1, page_size=10000)
    
    # Export to CSV
    csv_content = export_service.export_to_csv(results['results'], include_scores=include_scores)
    
    # Return as downloadable file
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=candidates_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.post("/export/excel")
async def export_candidates_excel(
    filters: CandidateFilter,
    include_scores: bool = True,
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Export filtered candidates to Excel format with formatting.
    
    Args:
        filters: Filter criteria (same as search endpoint)
        include_scores: Include authenticity/match scores in export
    """
    # Get filtered candidates (all results, no pagination)
    if filters.search_query:
        results = await filter_service.full_text_search(filters.search_query, db, page=1, page_size=10000)
    else:
        results = await filter_service.search_candidates(filters, db, page=1, page_size=10000)
    
    # Export to Excel
    excel_bytes = export_service.export_to_excel(results['results'], include_scores=include_scores)
    
    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=candidates_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    )

@router.get("/export/csv")
async def export_all_candidates_csv(
    include_scores: bool = True,
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Export all candidates to CSV format.
    
    Args:
        include_scores: Include authenticity/match scores in export
    """
    # Get all candidates
    empty_filter = CandidateFilter()
    results = await filter_service.search_candidates(empty_filter, db, page=1, page_size=10000)
    
    # Export to CSV
    csv_content = export_service.export_to_csv(results['results'], include_scores=include_scores)
    
    # Return as downloadable file
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=all_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@router.get("/export/excel")
async def export_all_candidates_excel(
    include_scores: bool = True,
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Export all candidates to Excel format.
    
    Args:
        include_scores: Include authenticity/match scores in export
    Returns:
        Excel file download
    """
    # Get all candidates
    empty_filter = CandidateFilter()
    results = await filter_service.search_candidates(empty_filter, db, page=1, page_size=10000)
    
    # Export to Excel
    excel_bytes = export_service.export_to_excel(results['results'], include_scores=include_scores)
    
    # Return as downloadable file
    from datetime import datetime
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=all_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    )

@router.get("/{candidate_id}/job-matches")
async def get_candidate_job_matches(
    candidate_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all job matches for a candidate.
    Matches the candidate's resume against all active jobs in the system.
    Returns jobs sorted by match score (highest first).
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Job matches request for candidate: {candidate_id}")
        
        # Get candidate with resume (async queries)
        stmt = select(Candidate).filter(Candidate.id == candidate_id)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            logger.error(f"Candidate not found: {candidate_id}")
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        logger.info(f"Found candidate: {candidate.full_name}")
        
        # Get candidate's resumes (get the latest one)
        stmt = select(Resume).filter(Resume.candidate_id == candidate_id).order_by(Resume.upload_date.desc())
        result = await db.execute(stmt)
        resume = result.scalars().first()
        
        if not resume:
            logger.warning(f"No resume found for candidate: {candidate_id}")
            return {
                "candidate_id": candidate_id,
                "candidate_name": candidate.full_name,
                "matches": [],
                "message": "No resume available for this candidate"
            }
        
        if not resume.extracted_text:
            logger.warning(f"No extracted_text for resume: {resume.id}")
            return {
                "candidate_id": candidate_id,
                "candidate_name": candidate.full_name,
                "matches": [],
                "message": "Resume text not yet extracted. Please re-upload the resume."
            }
        
        logger.info(f"Resume text length: {len(resume.extracted_text)} characters")
        
        # Get all active jobs
        stmt = select(Job).filter(Job.status == 'open')
        result = await db.execute(stmt)
        jobs = result.scalars().all()
        logger.info(f"Found {len(jobs)} open jobs")
        
        if not jobs:
            return {
                "candidate_id": candidate_id,
                "candidate_name": candidate.full_name,
                "matches": [],
                "message": "No active jobs available for matching"
            }
        
        # Initialize JD matcher
        jd_matcher = JDMatcher()
        
        # Match resume against each job
        matches = []
        for job in jobs:
            try:
                # Match resume with job description
                match_result = jd_matcher.match_resume_with_jd(
                    resume.extracted_text,
                    job.description
                )
                
                matches.append({
                    "job_id": job.id,
                    "job_title": job.title,
                    "department": job.department,
                    "location": f"{job.location_city or ''} {job.location_state or ''}".strip() or "Remote" if job.is_remote else "Not specified",
                    "employment_type": job.employment_type,
                    "match_score": match_result.get("overall_match", 0),
                    "skills_match": match_result.get("skills_match", 0),
                    "experience_match": match_result.get("experience_match", 0),
                    "education_match": match_result.get("education_match", 0),
                    "matched_skills": match_result.get("matched_skills", []),
                    "missing_skills": match_result.get("missing_skills", []),
                    "match_details": match_result.get("details", []),
                    "can_apply": match_result.get("overall_match", 0) >= 50  # Allow apply if match >= 50%
                })
            except Exception as e:
                # Log error but continue with other jobs
                print(f"Error matching job {job.id}: {str(e)}")
                continue
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        logger.info(f"Successfully matched {len(matches)} jobs for candidate {candidate_id}")
        
        return {
            "candidate_id": candidate_id,
            "candidate_name": candidate.full_name,
            "total_jobs": len(jobs),
            "matches": matches,
            "best_match_score": matches[0]["match_score"] if matches else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in job matches endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching job matches: {str(e)}")


@router.delete("/{candidate_id}/soft-delete")
async def soft_delete_candidate(
    candidate_id: int,
    reason: Optional[str] = None,
    deleted_by: str = "admin",  # TODO: Get from auth session
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Soft delete a candidate (admin only)
    
    Args:
        candidate_id: ID of candidate to delete
        reason: Optional reason for deletion
        deleted_by: Username of admin performing deletion
    
    Returns:
        Success message with deletion details
    """
    try:
        # Find candidate
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        if candidate.is_deleted:
            raise HTTPException(status_code=400, detail="Candidate already deleted")
        
        # Soft delete
        candidate.is_deleted = True
        candidate.deleted_at = datetime.now()
        candidate.deleted_by = deleted_by
        candidate.deletion_reason = reason
        
        db.commit()
        
        logger.info(f"✅ Candidate {candidate_id} ({candidate.full_name}) soft deleted by {deleted_by}")
        
        return {
            "success": True,
            "message": f"Candidate '{candidate.full_name}' deleted successfully",
            "candidate_id": candidate_id,
            "deleted_at": candidate.deleted_at.isoformat(),
            "deleted_by": deleted_by
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error soft deleting candidate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{candidate_id}/restore")
async def restore_candidate(
    candidate_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Restore a soft-deleted candidate (admin only)
    
    Args:
        candidate_id: ID of candidate to restore
    
    Returns:
        Success message
    """
    try:
        # Find candidate
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        if not candidate.is_deleted:
            raise HTTPException(status_code=400, detail="Candidate is not deleted")
        
        # Restore
        candidate.is_deleted = False
        candidate.deleted_at = None
        candidate.deleted_by = None
        candidate.deletion_reason = None
        
        db.commit()
        
        logger.info(f"✅ Candidate {candidate_id} ({candidate.full_name}) restored")
        
        return {
            "success": True,
            "message": f"Candidate '{candidate.full_name}' restored successfully",
            "candidate_id": candidate_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error restoring candidate: {e}")
        raise HTTPException(status_code=500, detail=str(e))
