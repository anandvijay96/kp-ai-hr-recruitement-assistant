from fastapi import APIRouter, Depends, Body
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import io

from core.database import get_db
from services.filter_service import FilterService
from services.preset_service import PresetService
from services.candidate_service import CandidateService
from services.export_service import ExportService
from models.filter_models import CandidateFilter, FilterPresetCreate, FilterPresetResponse

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

@router.get("/{candidate_id}")
async def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Get candidate by ID with all related data."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from models.database import Candidate
    
    # Query candidate with all relationships
    stmt = select(Candidate).options(
        selectinload(Candidate.resumes),
        selectinload(Candidate.skills),
        selectinload(Candidate.education),
        selectinload(Candidate.work_experience),
        selectinload(Candidate.certifications)
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
        } for c in candidate.certifications] if candidate.certifications else []
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
